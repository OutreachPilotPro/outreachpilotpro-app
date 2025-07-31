# bulk_email_sender.py - High-volume email sending system

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor
import queue
import threading
from datetime import datetime, timedelta
import json
import redis
from jinja2 import Template

class BulkEmailSender:
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.sending_queue = queue.Queue()
        self.smtp_pools = {}
        
        # Email sending configuration
        self.config = {
            'max_sends_per_hour': 500,
            'max_sends_per_day': 10000,
            'batch_size': 50,
            'retry_attempts': 3,
            'retry_delay': 300,  # 5 minutes
            'concurrent_connections': 5
        }
        
    def create_campaign(self, user_id, campaign_data):
        """Create a new email campaign"""
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        
        # Check subscription limits
        sub_mgr = SubscriptionManager()
        limit_check = sub_mgr.check_limit(user_id, 'campaigns')
        if not limit_check['allowed']:
            return {
                'success': False,
                'error': f"Campaign limit reached ({limit_check['current']}/{limit_check['limit']})"
            }
        
        # Create campaign
        c.execute("""
            INSERT INTO campaigns 
            (user_id, name, subject, body, from_name, reply_to, 
             recipient_list_id, scheduled_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft')
        """, (
            user_id,
            campaign_data['name'],
            campaign_data['subject'],
            campaign_data['body'],
            campaign_data.get('from_name', 'OutreachPilot User'),
            campaign_data.get('reply_to'),
            campaign_data.get('list_id'),
            campaign_data.get('scheduled_time')
        ))
        
        campaign_id = c.lastrowid
        
        # Add recipients to queue
        if campaign_data.get('recipients'):
            for email in campaign_data['recipients']:
                c.execute("""
                    INSERT INTO email_queue 
                    (campaign_id, recipient_email, scheduled_for)
                    VALUES (?, ?, ?)
                """, (campaign_id, email, campaign_data.get('scheduled_time')))
        
        conn.commit()
        conn.close()
        
        # Increment usage
        sub_mgr.increment_usage(user_id, 'campaigns')
        
        return {
            'success': True,
            'campaign_id': campaign_id
        }
    
    def send_campaign(self, campaign_id):
        """Send a campaign to all recipients"""
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        
        # Get campaign details
        c.execute("""
            SELECT c.*, u.email as sender_email, gt.access_token
            FROM campaigns c
            JOIN users u ON c.user_id = u.id
            LEFT JOIN google_tokens gt ON u.id = gt.user_id
            WHERE c.id = ?
        """, (campaign_id,))
        
        campaign = c.fetchone()
        if not campaign:
            return {'success': False, 'error': 'Campaign not found'}
        
        # Check email sending limits
        sub_mgr = SubscriptionManager()
        
        # Get recipients count
        c.execute("""
            SELECT COUNT(*) FROM email_queue 
            WHERE campaign_id = ? AND status = 'pending'
        """, (campaign_id,))
        
        recipient_count = c.fetchone()[0]
        
        limit_check = sub_mgr.check_limit(campaign[1], 'emails')
        if not limit_check['allowed'] or recipient_count > limit_check['remaining']:
            return {
                'success': False,
                'error': f"Email limit exceeded. You can send {limit_check['remaining']} more emails this month."
            }
        
        # Update campaign status
        c.execute("""
            UPDATE campaigns SET status = 'sending', started_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (campaign_id,))
        conn.commit()
        
        # Start sending process
        self._process_campaign_queue(campaign_id, campaign)
        
        return {'success': True, 'message': 'Campaign sending started'}
    
    def _process_campaign_queue(self, campaign_id, campaign_data):
        """Process email queue for a campaign"""
        # Use thread pool for concurrent sending
        with ThreadPoolExecutor(max_workers=self.config['concurrent_connections']) as executor:
            conn = sqlite3.connect("outreachpilot.db")
            c = conn.cursor()
            
            while True:
                # Get batch of pending emails
                c.execute("""
                    SELECT id, recipient_email FROM email_queue
                    WHERE campaign_id = ? AND status = 'pending'
                    LIMIT ?
                """, (campaign_id, self.config['batch_size']))
                
                batch = c.fetchall()
                if not batch:
                    break
                
                # Check rate limits
                self._check_rate_limits()
                
                # Send emails in parallel
                futures = []
                for email_id, recipient in batch:
                    future = executor.submit(
                        self._send_single_email,
                        email_id,
                        recipient,
                        campaign_data
                    )
                    futures.append((email_id, future))
                
                # Wait for batch to complete
                for email_id, future in futures:
                    try:
                        result = future.result(timeout=30)
                        if result['success']:
                            c.execute("""
                                UPDATE email_queue 
                                SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (email_id,))
                        else:
                            c.execute("""
                                UPDATE email_queue 
                                SET status = 'failed', error_message = ?
                                WHERE id = ?
                            """, (result['error'], email_id))
                    except Exception as e:
                        c.execute("""
                            UPDATE email_queue 
                            SET status = 'failed', error_message = ?
                            WHERE id = ?
                        """, (str(e), email_id))
                
                conn.commit()
                
                # Update usage tracking
                sub_mgr = SubscriptionManager()
                sub_mgr.increment_usage(campaign_data[1], 'emails', len(batch))
            
            # Update campaign status
            c.execute("""
                UPDATE campaigns 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (campaign_id,))
            
            conn.commit()
            conn.close()
    
    def _send_single_email(self, email_id, recipient, campaign_data):
        """Send a single email"""
        try:
            # Personalize content
            template = Template(campaign_data[4])  # body
            personalized_body = template.render(
                email=recipient,
                first_name=recipient.split('@')[0],  # Basic personalization
                company=self._extract_company_from_email(recipient)
            )
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = campaign_data[3]  # subject
            msg['From'] = f"{campaign_data[5]} <{campaign_data[8]}>"  # from_name, sender_email
            msg['To'] = recipient
            
            # Add tracking pixel
            tracking_pixel = f'<img src="https://outreachpilotpro.com/track/open/{email_id}" width="1" height="1" />'
            html_body = f"{personalized_body}{tracking_pixel}"
            
            # Add unsubscribe link
            unsubscribe_link = f'<br><br><a href="https://outreachpilotpro.com/unsubscribe/{email_id}">Unsubscribe</a>'
            html_body += unsubscribe_link
            
            # Attach parts
            text_part = MIMEText(personalized_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            if campaign_data[9]:  # Has Google token
                return self._send_via_gmail_api(msg, campaign_data[9])
            else:
                return self._send_via_smtp(msg, campaign_data[8])
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_via_gmail_api(self, message, access_token):
        """Send email using Gmail API"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            
            creds = Credentials(token=access_token)
            service = build('gmail', 'v1', credentials=creds)
            
            message_bytes = message.as_bytes()
            message_b64 = base64.urlsafe_b64encode(message_bytes).decode()
            
            result = service.users().messages().send(
                userId='me',
                body={'raw': message_b64}
            ).execute()
            
            return {'success': True, 'message_id': result['id']}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_via_smtp(self, message, sender_email):
        """Send email using SMTP"""
        try:
            # Use connection pooling for better performance
            smtp_key = f"smtp_{sender_email}"
            
            if smtp_key not in self.smtp_pools:
                self.smtp_pools[smtp_key] = smtplib.SMTP('smtp.gmail.com', 587)
                self.smtp_pools[smtp_key].starttls()
                # Note: In production, use app-specific passwords or OAuth
                self.smtp_pools[smtp_key].login(sender_email, 'app_specific_password')
            
            smtp = self.smtp_pools[smtp_key]
            smtp.send_message(message)
            
            return {'success': True}
            
        except Exception as e:
            # Remove failed connection from pool
            if smtp_key in self.smtp_pools:
                del self.smtp_pools[smtp_key]
            return {'success': False, 'error': str(e)}
    
    def _check_rate_limits(self):
        """Check and enforce rate limits"""
        # Hourly rate limit
        hourly_key = f"rate_limit:hourly:{datetime.now().strftime('%Y%m%d%H')}"
        hourly_count = self.redis_client.incr(hourly_key)
        self.redis_client.expire(hourly_key, 3600)
        
        if hourly_count > self.config['max_sends_per_hour']:
            # Wait until next hour
            sleep_time = 3600 - (datetime.now().minute * 60 + datetime.now().second)
            time.sleep(sleep_time)
        
        # Daily rate limit
        daily_key = f"rate_limit:daily:{datetime.now().strftime('%Y%m%d')}"
        daily_count = self.redis_client.incr(daily_key)
        self.redis_client.expire(daily_key, 86400)
        
        if daily_count > self.config['max_sends_per_day']:
            raise Exception("Daily sending limit reached")
    
    def _extract_company_from_email(self, email):
        """Extract company name from email domain"""
        domain = email.split('@')[1]
        company = domain.split('.')[0]
        return company.title()

# Email templates
EMAIL_TEMPLATES = {
    "cold_outreach": {
        "subject": "Quick question about {{company}}",
        "body": """Hi {{first_name}},

I noticed {{company}} is [specific observation about their business].

We help companies like yours [specific value proposition]. 

Our clients typically see [specific results].

Would you be interested in a brief call to discuss how we could help {{company}}?

Best regards,
{{sender_name}}"""
    },
    "follow_up": {
        "subject": "Following up on my previous email",
        "body": """Hi {{first_name}},

I wanted to follow up on my previous email about [topic].

I understand you're busy, so I'll keep this brief. 

[One specific benefit or case study]

Are you available for a quick 15-minute call this week?

Best,
{{sender_name}}"""
    },
    "product_launch": {
        "subject": "Introducing our new solution for {{company}}",
        "body": """Hello {{first_name}},

We just launched a new feature that could significantly benefit {{company}}.

[Brief description of the feature and its benefits]

I'd love to show you how it works. Do you have 20 minutes this week?

Looking forward to hearing from you,
{{sender_name}}"""
    }
}