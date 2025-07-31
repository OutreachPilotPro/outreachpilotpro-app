# subscription_manager.py - Complete subscription management system

import stripe
from datetime import datetime, timedelta
from enum import Enum

class SubscriptionTier(Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class SubscriptionPlans:
    PLANS = {
        "free": {
            "name": "Free Trial",
            "price": 0,
            "stripe_price_id": None,
            "limits": {
                "emails_per_month": 100,
                "scrapes_per_month": 50,
                "campaigns_per_month": 1,
                "email_verification": False,
                "custom_templates": 1,
                "api_access": False,
                "priority_support": False
            }
        },
        "starter": {
            "name": "Starter",
            "price": 49,  # per month
            "stripe_price_id": "price_starter_monthly",
            "limits": {
                "emails_per_month": 5000,
                "scrapes_per_month": 2000,
                "campaigns_per_month": 10,
                "email_verification": True,
                "custom_templates": 5,
                "api_access": False,
                "priority_support": False
            }
        },
        "professional": {
            "name": "Professional",
            "price": 149,
            "stripe_price_id": "price_professional_monthly",
            "limits": {
                "emails_per_month": 50000,
                "scrapes_per_month": 20000,
                "campaigns_per_month": 50,
                "email_verification": True,
                "custom_templates": 20,
                "api_access": True,
                "priority_support": True,
                "team_members": 3
            }
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 499,
            "stripe_price_id": "price_enterprise_monthly",
            "limits": {
                "emails_per_month": 500000,
                "scrapes_per_month": 100000,
                "campaigns_per_month": -1,  # Unlimited
                "email_verification": True,
                "custom_templates": -1,  # Unlimited
                "api_access": True,
                "priority_support": True,
                "team_members": -1,  # Unlimited
                "dedicated_ip": True,
                "white_label": True
            }
        }
    }

def create_subscription_tables():
    """Create subscription-related database tables"""
    return """
    -- User subscriptions
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tier TEXT NOT NULL DEFAULT 'free',
        stripe_customer_id TEXT,
        stripe_subscription_id TEXT,
        status TEXT DEFAULT 'active', -- active, cancelled, past_due, trialing
        current_period_start TIMESTAMP,
        current_period_end TIMESTAMP,
        cancel_at_period_end BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );

    -- Usage tracking
    CREATE TABLE IF NOT EXISTS usage_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        month TEXT NOT NULL, -- YYYY-MM format
        emails_sent INTEGER DEFAULT 0,
        emails_scraped INTEGER DEFAULT 0,
        campaigns_created INTEGER DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, month)
    );

    -- Payment history
    CREATE TABLE IF NOT EXISTS payment_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        stripe_payment_intent_id TEXT,
        amount INTEGER NOT NULL, -- in cents
        currency TEXT DEFAULT 'usd',
        status TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );

    -- Email sending queue
    CREATE TABLE IF NOT EXISTS email_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        recipient_email TEXT NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, sending, sent, failed, bounced
        scheduled_for TIMESTAMP,
        sent_at TIMESTAMP,
        opened_at TIMESTAMP,
        clicked_at TIMESTAMP,
        error_message TEXT,
        retry_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
    );
    """

class SubscriptionManager:
    def __init__(self, db_path="outreachpilot.db"):
        self.db_path = db_path
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    def check_limit(self, user_id, limit_type):
        """Check if user has reached their subscription limit"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get user's subscription tier
        c.execute("""
            SELECT s.tier, u.month, u.emails_sent, u.emails_scraped, u.campaigns_created
            FROM subscriptions s
            JOIN usage_tracking u ON s.user_id = u.user_id
            WHERE s.user_id = ? AND s.status = 'active'
            AND u.month = strftime('%Y-%m', 'now')
        """, (user_id,))
        
        result = c.fetchone()
        if not result:
            # Create usage tracking for this month
            self._create_usage_record(user_id)
            tier = 'free'
            current_usage = 0
        else:
            tier, month, emails_sent, emails_scraped, campaigns = result
            usage_map = {
                'emails': emails_sent,
                'scrapes': emails_scraped,
                'campaigns': campaigns
            }
            current_usage = usage_map.get(limit_type, 0)
        
        # Get limit for this tier
        plan = SubscriptionPlans.PLANS[tier]
        limit_map = {
            'emails': plan['limits']['emails_per_month'],
            'scrapes': plan['limits']['scrapes_per_month'],
            'campaigns': plan['limits']['campaigns_per_month']
        }
        
        limit = limit_map.get(limit_type, 0)
        conn.close()
        
        return {
            'allowed': limit == -1 or current_usage < limit,
            'current': current_usage,
            'limit': limit,
            'remaining': max(0, limit - current_usage) if limit != -1 else -1
        }
    
    def increment_usage(self, user_id, usage_type, amount=1):
        """Increment usage counter"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        column_map = {
            'emails': 'emails_sent',
            'scrapes': 'emails_scraped',
            'campaigns': 'campaigns_created'
        }
        
        column = column_map.get(usage_type)
        if column:
            c.execute(f"""
                UPDATE usage_tracking 
                SET {column} = {column} + ?, last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ? AND month = strftime('%Y-%m', 'now')
            """, (amount, user_id))
            
            if c.rowcount == 0:
                # Create record if doesn't exist
                self._create_usage_record(user_id)
                c.execute(f"""
                    UPDATE usage_tracking 
                    SET {column} = ?
                    WHERE user_id = ? AND month = strftime('%Y-%m', 'now')
                """, (amount, user_id))
            
            conn.commit()
        
        conn.close()
    
    def _create_usage_record(self, user_id):
        """Create usage tracking record for current month"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO usage_tracking (user_id, month)
            VALUES (?, strftime('%Y-%m', 'now'))
        """, (user_id,))
        conn.commit()
        conn.close()
    
    def create_checkout_session(self, user_id, plan_id):
        """Create Stripe checkout session"""
        plan = SubscriptionPlans.PLANS.get(plan_id)
        if not plan or plan['stripe_price_id'] is None:
            return None
        
        # Get user email
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        user_email = c.fetchone()[0]
        conn.close()
        
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=user_email,
            line_items=[{
                'price': plan['stripe_price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://outreachpilotpro.com/subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://outreachpilotpro.com/pricing',
            metadata={
                'user_id': user_id,
                'plan_id': plan_id
            }
        )
        
        return session
    
    def handle_webhook(self, event):
        """Handle Stripe webhooks"""
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session['metadata']['user_id']
            plan_id = session['metadata']['plan_id']
            
            # Update user subscription
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("""
                INSERT OR REPLACE INTO subscriptions 
                (user_id, tier, stripe_customer_id, stripe_subscription_id, status, 
                 current_period_start, current_period_end)
                VALUES (?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, 
                        datetime('now', '+1 month'))
            """, (user_id, plan_id, session['customer'], session['subscription']))
            
            conn.commit()
            conn.close()
        
        elif event['type'] == 'invoice.payment_failed':
            # Handle failed payment
            subscription_id = event['data']['object']['subscription']
            self._update_subscription_status(subscription_id, 'past_due')
        
        elif event['type'] == 'customer.subscription.deleted':
            # Handle subscription cancellation
            subscription_id = event['data']['object']['id']
            self._update_subscription_status(subscription_id, 'cancelled')