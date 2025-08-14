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
from jinja2 import Template
from config import get_smtp_config
# ADD: Import requests for making API calls to Microsoft
import requests
import sqlite3
import base64

# Make redis optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: Redis not available. Rate limiting will be disabled.")

class BulkEmailSender:
    def __init__(self, redis_url="redis://localhost:6379"):
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                print(f"Warning: Could not connect to Redis: {e}")
                self.redis_client = None
        else:
            self.redis_client = None
            
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
            SELECT c.*, u.email as sender_email
            FROM campaigns c
            JOIN users u ON c.user_id = u.id
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
                if not self._check_rate_limits():
                    print(f"Rate limit exceeded for campaign {campaign_id}. Waiting...")
                    time.sleep(self.config['retry_delay']) # Wait before retrying
                    continue
                
                # Send emails in parallel
                futures = []
                for email_id, recipient in batch:
                    future = executor.submit(
                        self._send_single_email,
                        email_id,
                        recipient,
                        campaign_data,
                        campaign_data[1]  # user_id from campaign_data
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
    
    def _send_single_email(self, email_id, recipient, campaign_data, user_id):
        """Send a single email using the correct provider for the user."""
        try:
            # Determine which provider to use by checking for tokens
            conn = sqlite3.connect("outreachpilot.db")
            c = conn.cursor()
            c.execute("SELECT provider, access_token FROM user_oauth_tokens WHERE user_id = ?", (user_id,))
            token_info = c.fetchone()
            conn.close()

            if not token_info:
                return {'success': False, 'error': 'No connected email account found for user.'}

            provider, access_token = token_info
            
            # Personalize content
            template = Template(campaign_data[4])  # body
            personalized_body = template.render(
                email=recipient,
                first_name=recipient.split('@')[0],  # Basic personalization
                company=self._extract_company_from_email(recipient)
            )
            
            # Add tracking pixel
            tracking_pixel = f'<img src="https://outreachpilotpro.com/track/open/{email_id}" width="1" height="1" />'
            html_body = f"{personalized_body}{tracking_pixel}"
            
            # Add unsubscribe link
            unsubscribe_link = f'<br><br><a href="https://outreachpilotpro.com/unsubscribe/{email_id}">Unsubscribe</a>'
            html_body += unsubscribe_link
            
            if provider == 'google':
                # Create message for Gmail API
                msg = MIMEMultipart('alternative')
                msg['Subject'] = campaign_data[3]  # subject
                msg['From'] = f"{campaign_data[5]} <{campaign_data[8]}>"  # from_name, sender_email
                msg['To'] = recipient
                
                # Attach parts
                text_part = MIMEText(personalized_body, 'plain')
                html_part = MIMEText(html_body, 'html')
                msg.attach(text_part)
                msg.attach(html_part)
                
                return self._send_via_gmail_api(msg, access_token)
            elif provider == 'microsoft':
                # For Microsoft, we need to construct a JSON payload
                payload = {
                    "message": {
                        "subject": campaign_data[3],  # subject
                        "body": {
                            "contentType": "HTML",
                            "content": html_body
                        },
                        "toRecipients": [{"emailAddress": {"address": recipient}}]
                    },
                    "saveToSentItems": "true"
                }
                return self._send_via_microsoft_graph_api(payload, access_token)
            else:
                return {'success': False, 'error': f'Unsupported provider: {provider}'}
                
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

    # ADD: New function to send via Microsoft Graph API
    def _send_via_microsoft_graph_api(self, payload, access_token):
        """Send email using Microsoft Graph API."""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/sendMail',
                headers=headers,
                json=payload
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            
            return {'success': True}
        except requests.exceptions.HTTPError as e:
            # Provide more details on failure
            try:
                error_details = e.response.json()
                error_message = error_details.get('error', {}).get('message', str(e))
            except:
                error_message = str(e)
            return {'success': False, 'error': f"Microsoft Graph API Error: {error_message}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_via_smtp(self, message, sender_email):
        """Send email using generic SMTP settings from config."""
        try:
            smtp_key = f"smtp_{sender_email}"
            
            if smtp_key not in self.smtp_pools:
                # FIX: Use the new universal SMTP config
                smtp_config = get_smtp_config() # Can be extended to use a specific provider
                
                server = smtp_config['server']
                port = smtp_config['port']
                use_tls = smtp_config['use_tls']
                use_ssl = smtp_config['use_ssl']
                username = smtp_config['username']
                password = smtp_config['password']

                if not all([server, port, username, password]):
                    raise ConnectionError("SMTP settings are not fully configured in your .env file.")

                if use_ssl:
                    smtp_conn = smtplib.SMTP_SSL(server, port)
                else:
                    smtp_conn = smtplib.SMTP(server, port)
                
                if use_tls:
                    smtp_conn.starttls()
                
                smtp_conn.login(username, password)
                self.smtp_pools[smtp_key] = smtp_conn
            
            smtp = self.smtp_pools[smtp_key]
            smtp.send_message(message)
            
            return {'success': True}
            
        except Exception as e:
            if smtp_key in self.smtp_pools:
                self.smtp_pools.pop(smtp_key, None)
            return {'success': False, 'error': str(e)}
    
    def _check_rate_limits(self):
        """Check and enforce rate limits"""
        if not self.redis_client:
            print("Rate limiting is disabled because Redis is not available.")
            return True  # Allow sending if no rate limiting

        # Hourly rate limit
        hourly_key = f"rate_limit:hourly:{datetime.now().strftime('%Y%m%d%H')}"
        hourly_count = self.redis_client.incr(hourly_key)
        self.redis_client.expire(hourly_key, 3600)
        
        if hourly_count > self.config['max_sends_per_hour']:
            print(f"Hourly rate limit exceeded: {hourly_count}/{self.config['max_sends_per_hour']}")
            return False
        
        # Daily rate limit
        daily_key = f"rate_limit:daily:{datetime.now().strftime('%Y%m%d')}"
        daily_count = self.redis_client.incr(daily_key)
        self.redis_client.expire(daily_key, 86400)
        
        if daily_count > self.config['max_sends_per_day']:
            print(f"Daily rate limit exceeded: {daily_count}/{self.config['max_sends_per_day']}")
            return False
        
        return True
    
    def _extract_company_from_email(self, email):
        """Extract company name from email domain"""
        domain = email.split('@')[1]
        company = domain.split('.')[0]
        return company.title()

    def check_user_oauth_status(self, user_id):
        """Check if user has connected OAuth accounts"""
        try:
            conn = sqlite3.connect("outreachpilot.db")
            c = conn.cursor()
            c.execute("SELECT provider, expires_at FROM user_oauth_tokens WHERE user_id = ?", (user_id,))
            tokens = c.fetchall()
            conn.close()
            
            status = {
                'google': False,
                'microsoft': False,
                'has_any': len(tokens) > 0
            }
            
            for provider, expires_at in tokens:
                if expires_at and datetime.now() < datetime.fromisoformat(expires_at):
                    status[provider] = True
            
            return status
            
        except Exception as e:
            print(f"Error checking OAuth status: {e}")
            return {'google': False, 'microsoft': False, 'has_any': False}

    def send_test_email(self, user_id, to_email, subject="Test Email from OutreachPilotPro", body="This is a test email to verify your OAuth connection is working properly."):
        """Send a test email to verify OAuth connectivity"""
        try:
            # Check OAuth status
            oauth_status = self.check_user_oauth_status(user_id)
            if not oauth_status['has_any']:
                return {'success': False, 'error': 'No OAuth accounts connected. Please connect your email account first.'}
            
            # Get the first available provider
            conn = sqlite3.connect("outreachpilot.db")
            c = conn.cursor()
            c.execute("SELECT provider, access_token FROM user_oauth_tokens WHERE user_id = ? LIMIT 1", (user_id,))
            token_info = c.fetchone()
            conn.close()
            
            if not token_info:
                return {'success': False, 'error': 'No valid OAuth tokens found.'}
            
            provider, access_token = token_info
            
            if provider == 'google':
                # Create message for Gmail API
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = f"OutreachPilotPro <test@outreachpilotpro.com>"
                msg['To'] = to_email
                
                # Attach parts
                text_part = MIMEText(body, 'plain')
                html_part = MIMEText(f"<html><body>{body}</body></html>", 'html')
                msg.attach(text_part)
                msg.attach(html_part)
                
                return self._send_via_gmail_api(msg, access_token)
            elif provider == 'microsoft':
                # Create payload for Microsoft Graph API
                payload = {
                    "message": {
                        "subject": subject,
                        "body": {
                            "contentType": "HTML",
                            "content": f"<html><body>{body}</body></html>"
                        },
                        "toRecipients": [{"emailAddress": {"address": to_email}}]
                    },
                    "saveToSentItems": "true"
                }
                return self._send_via_microsoft_graph_api(payload, access_token)
            else:
                return {'success': False, 'error': f'Unsupported provider: {provider}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

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