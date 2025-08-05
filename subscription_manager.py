# subscription_manager.py - Complete subscription management system

import stripe
import sqlite3
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            "stripe_product_id": "prod_SnnIvAhTzg60nA",
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
            "price": 29,  # Updated to match Stripe
            "stripe_product_id": "prod_SnnIncx8mICyRV",
            "stripe_price_id": "price_1RsBiFLeRd30DB0ZUMfZIGCZ",
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
            "price": 99,  # Updated to match Stripe
            "stripe_product_id": "prod_SnnIzXmKiyl77j",
            "stripe_price_id": "price_1RsBiGLeRd30DB0Z7Ak9FUwB",
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
            "price": 299,  # Updated to match Stripe
            "stripe_product_id": "prod_SnnIxmqFVE67Dv",
            "stripe_price_id": "price_1RsBiGLeRd30DB0ZMhbFVQsi",
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

    -- Campaigns table
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        from_name TEXT,
        reply_to TEXT,
        recipient_list_id INTEGER,
        scheduled_time TIMESTAMP,
        status TEXT DEFAULT 'draft', -- draft, scheduled, sending, completed, paused
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );

    -- Google OAuth tokens
    CREATE TABLE IF NOT EXISTS google_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        access_token TEXT NOT NULL,
        refresh_token TEXT,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """

class SubscriptionManager:
    def __init__(self, db_path="outreachpilot.db"):
        self.db_path = db_path
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create tables - execute each statement individually
        table_statements = [
            """CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tier TEXT NOT NULL DEFAULT 'free',
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                status TEXT DEFAULT 'active',
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                cancel_at_period_end BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS usage_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                emails_sent INTEGER DEFAULT 0,
                emails_scraped INTEGER DEFAULT 0,
                campaigns_created INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, month)
            )""",
            
            """CREATE TABLE IF NOT EXISTS payment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stripe_payment_intent_id TEXT,
                amount INTEGER NOT NULL,
                currency TEXT DEFAULT 'usd',
                status TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                recipient_email TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                scheduled_for TIMESTAMP,
                sent_at TIMESTAMP,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                from_name TEXT,
                reply_to TEXT,
                recipient_list_id INTEGER,
                scheduled_time TIMESTAMP,
                status TEXT DEFAULT 'draft',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS google_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for statement in table_statements:
            try:
                c.execute(statement)
            except Exception as e:
                logger.warning(f"Could not execute statement: {e}")
        
        conn.commit()
        conn.close()
    
    def get_user_subscription(self, user_id: int) -> Dict:
        """Get user's current subscription"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            c = conn.cursor()
            
            c.execute("""
                SELECT tier, status, current_period_start, current_period_end, 
                       cancel_at_period_end, stripe_subscription_id
                FROM subscriptions 
                WHERE user_id = ? AND status IN ('active', 'trialing')
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                tier, status, period_start, period_end, cancel_at_end, stripe_sub_id = result
                plan = SubscriptionPlans.PLANS.get(tier, SubscriptionPlans.PLANS['free'])
                
                return {
                    'tier': tier,
                    'status': status,
                    'plan_name': plan['name'],
                    'price': plan['price'],
                    'limits': plan['limits'],
                    'current_period_start': period_start,
                    'current_period_end': period_end,
                    'cancel_at_period_end': bool(cancel_at_end),
                    'stripe_subscription_id': stripe_sub_id
                }
            else:
                # Return free plan if no subscription found
                plan = SubscriptionPlans.PLANS['free']
                return {
                    'tier': 'free',
                    'status': 'active',
                    'plan_name': plan['name'],
                    'price': plan['price'],
                    'limits': plan['limits'],
                    'current_period_start': None,
                    'current_period_end': None,
                    'cancel_at_period_end': False,
                    'stripe_subscription_id': None
                }
        except Exception as e:
            logger.error(f"Error getting user subscription: {e}")
            # Return free plan if error
            plan = SubscriptionPlans.PLANS['free']
            return {
                'tier': 'free',
                'status': 'active',
                'plan_name': plan['name'],
                'price': plan['price'],
                'limits': plan['limits'],
                'current_period_start': None,
                'current_period_end': None,
                'cancel_at_period_end': False,
                'stripe_subscription_id': None
            }
    
    def check_limit(self, user_id: int, limit_type: str) -> Dict:
        """Check if user has reached their subscription limit"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            c = conn.cursor()
            
            # Get user's subscription tier
            subscription = self.get_user_subscription(user_id)
            tier = subscription['tier']
            
            # Get current month's usage
            current_month = datetime.now().strftime('%Y-%m')
            c.execute("""
                SELECT emails_sent, emails_scraped, campaigns_created
                FROM usage_tracking 
                WHERE user_id = ? AND month = ?
            """, (user_id, current_month))
            
            result = c.fetchone()
            if not result:
                # Create usage tracking for this month
                self._create_usage_record(user_id, current_month)
                current_usage = 0
            else:
                emails_sent, emails_scraped, campaigns_created = result
                usage_map = {
                    'emails': emails_sent,
                    'scrapes': emails_scraped,
                    'campaigns': campaigns_created
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
        except Exception as e:
            logger.error(f"Error checking limit: {e}")
            # Return default values if error
            return {
                'allowed': True,
                'current': 0,
                'limit': 100,
                'remaining': 100
            }
    
    def increment_usage(self, user_id: int, usage_type: str, amount: int = 1):
        """Increment usage counter"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        current_month = datetime.now().strftime('%Y-%m')
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
                WHERE user_id = ? AND month = ?
            """, (amount, user_id, current_month))
            
            if c.rowcount == 0:
                # Create record if doesn't exist
                self._create_usage_record(user_id, current_month)
                c.execute(f"""
                    UPDATE usage_tracking 
                    SET {column} = ?
                    WHERE user_id = ? AND month = ?
                """, (amount, user_id, current_month))
            
            conn.commit()
        
        conn.close()
    
    def _create_usage_record(self, user_id: int, month: str):
        """Create usage tracking record for a month"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO usage_tracking (user_id, month)
            VALUES (?, ?)
        """, (user_id, month))
        conn.commit()
        conn.close()
    
    def create_checkout_session(self, user_id: int, plan_id: str) -> Optional[Dict]:
        """Create Stripe checkout session"""
        plan = SubscriptionPlans.PLANS.get(plan_id)
        if not plan or plan['stripe_price_id'] is None:
            return None
        
        # Get user email
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            c = conn.cursor()
            c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
            result = c.fetchone()
            conn.close()
            
            if not result:
                logger.error(f"User {user_id} not found")
                return None
                
            user_email = result[0]
            
        except Exception as e:
            logger.error(f"Error getting user email: {e}")
            return None
        
        try:
            # Create Stripe checkout session with product metadata
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=user_email,
                line_items=[{
                    'price': plan['stripe_price_id'],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url='https://outreachpilotpro.com/subscription/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://outreachpilotpro.com/subscription',
                metadata={
                    'user_id': user_id,
                    'plan_id': plan_id,
                    'product_id': plan.get('stripe_product_id', ''),
                    'plan_name': plan['name']
                },
                subscription_data={
                    'metadata': {
                        'user_id': user_id,
                        'plan_id': plan_id,
                        'product_id': plan.get('stripe_product_id', ''),
                        'plan_name': plan['name']
                    }
                }
            )
            
            return {
                'session_id': session.id,
                'url': session.url
            }
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return None
    
    def handle_webhook(self, event: Dict) -> bool:
        """Handle Stripe webhooks"""
        try:
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                user_id = int(session['metadata']['user_id'])
                plan_id = session['metadata']['plan_id']
                
                # Update user subscription
                self._update_user_subscription(user_id, plan_id, session)
                
            elif event['type'] == 'invoice.payment_failed':
                # Handle failed payment
                subscription_id = event['data']['object']['subscription']
                self._update_subscription_status(subscription_id, 'past_due')
                
            elif event['type'] == 'customer.subscription.deleted':
                # Handle subscription cancellation
                subscription_id = event['data']['object']['id']
                self._update_subscription_status(subscription_id, 'cancelled')
                
            elif event['type'] == 'customer.subscription.updated':
                # Handle subscription updates
                subscription = event['data']['object']
                self._update_subscription_from_stripe(subscription)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return False
    
    def _update_user_subscription(self, user_id: int, plan_id: str, session: Dict):
        """Update user subscription after successful payment"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Calculate period dates
        current_time = datetime.now()
        period_end = current_time + timedelta(days=30)
        
        c.execute("""
            INSERT OR REPLACE INTO subscriptions 
            (user_id, tier, stripe_customer_id, stripe_subscription_id, status, 
             current_period_start, current_period_end, updated_at)
            VALUES (?, ?, ?, ?, 'active', ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, plan_id, session['customer'], session['subscription'], 
              current_time, period_end))
        
        conn.commit()
        conn.close()
    
    def _update_subscription_status(self, stripe_subscription_id: str, status: str):
        """Update subscription status"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            UPDATE subscriptions 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE stripe_subscription_id = ?
        """, (status, stripe_subscription_id))
        
        conn.commit()
        conn.close()
    
    def _update_subscription_from_stripe(self, subscription: Dict):
        """Update subscription from Stripe webhook"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get the plan tier from metadata or determine from price
        plan_tier = 'professional'  # Default fallback
        
        c.execute("""
            UPDATE subscriptions 
            SET status = ?, current_period_start = ?, current_period_end = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE stripe_subscription_id = ?
        """, (subscription['status'], 
              datetime.fromtimestamp(subscription['current_period_start']),
              datetime.fromtimestamp(subscription['current_period_end']),
              subscription['id']))
        
        conn.commit()
        conn.close()
    
    def cancel_subscription(self, user_id: int) -> bool:
        """Cancel user subscription"""
        try:
            subscription = self.get_user_subscription(user_id)
            stripe_sub_id = subscription.get('stripe_subscription_id')
            
            if stripe_sub_id:
                # Cancel in Stripe
                stripe.Subscription.modify(
                    stripe_sub_id,
                    cancel_at_period_end=True
                )
            
            # Update local database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                UPDATE subscriptions 
                SET cancel_at_period_end = 1, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return False
    
    def get_usage_stats(self, user_id: int) -> Dict:
        """Get user's usage statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Get current month usage
            current_month = datetime.now().strftime('%Y-%m')
            c.execute("""
                SELECT emails_sent, emails_scraped, campaigns_created
                FROM usage_tracking 
                WHERE user_id = ? AND month = ?
            """, (user_id, current_month))
            
            current_usage = c.fetchone()
            if not current_usage:
                # Create usage tracking for this month
                self._create_usage_record(user_id, current_month)
                current_usage = (0, 0, 0)
            
            # Get last 6 months usage
            c.execute("""
                SELECT month, emails_sent, emails_scraped, campaigns_created
                FROM usage_tracking 
                WHERE user_id = ? 
                ORDER BY month DESC
                LIMIT 6
            """, (user_id,))
            
            historical_usage = c.fetchall()
            conn.close()
            
            subscription = self.get_user_subscription(user_id)
            
            return {
                'current_month': {
                    'emails_sent': current_usage[0],
                    'emails_scraped': current_usage[1],
                    'campaigns_created': current_usage[2],
                    'limits': subscription['limits']
                },
                'historical': [
                    {
                        'month': row[0],
                        'emails_sent': row[1],
                        'emails_scraped': row[2],
                        'campaigns_created': row[3]
                    }
                    for row in historical_usage
                ]
            }
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            # Return default stats if error
            subscription = self.get_user_subscription(user_id)
            return {
                'current_month': {
                    'emails_sent': 0,
                    'emails_scraped': 0,
                    'campaigns_created': 0,
                    'limits': subscription['limits']
                },
                'historical': []
            }
    
    def upgrade_subscription(self, user_id: int, new_plan_id: str) -> Dict:
        """Upgrade user subscription"""
        try:
            current_subscription = self.get_user_subscription(user_id)
            stripe_sub_id = current_subscription.get('stripe_subscription_id')
            
            if stripe_sub_id:
                # Update in Stripe
                new_price_id = SubscriptionPlans.PLANS[new_plan_id]['stripe_price_id']
                stripe.Subscription.modify(
                    stripe_sub_id,
                    items=[{
                        'id': stripe.Subscription.retrieve(stripe_sub_id)['items']['data'][0]['id'],
                        'price': new_price_id,
                    }],
                    proration_behavior='create_prorations',
                )
            
            # Update local database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                UPDATE subscriptions 
                SET tier = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND status = 'active'
            """, (new_plan_id, user_id))
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Subscription upgraded successfully'}
            
        except Exception as e:
            logger.error(f"Error upgrading subscription: {str(e)}")
            return {'success': False, 'error': str(e)}

    def create_paid_subscription(self, user_id: int, plan_id: str, stripe_subscription_id: str, stripe_customer_id: str):
        """Create a paid subscription for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Insert or update subscription
            c.execute("""
                INSERT OR REPLACE INTO subscriptions 
                (user_id, tier, stripe_customer_id, stripe_subscription_id, status, 
                 current_period_start, current_period_end, updated_at)
                VALUES (?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, 
                        datetime('now', '+1 month'), CURRENT_TIMESTAMP)
            """, (user_id, plan_id, stripe_customer_id, stripe_subscription_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created paid subscription for user {user_id}, plan {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating paid subscription: {str(e)}")
            return False

    def create_free_subscription(self, user_id: int, plan_id: str):
        """Create a free subscription for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Insert or update subscription
            c.execute("""
                INSERT OR REPLACE INTO subscriptions 
                (user_id, tier, status, current_period_start, current_period_end, updated_at)
                VALUES (?, ?, 'active', CURRENT_TIMESTAMP, 
                        datetime('now', '+1 month'), CURRENT_TIMESTAMP)
            """, (user_id, plan_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created free subscription for user {user_id}, plan {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating free subscription: {str(e)}")
            return False
