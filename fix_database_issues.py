#!/usr/bin/env python3
"""
Fix database issues and prepare for production deployment
"""

import sqlite3
import os

def fix_database_issues():
    """Fix database column and initialization issues"""
    
    print("🔧 Fixing database issues...")
    
    try:
        conn = sqlite3.connect("outreachpilot.db", timeout=30.0)
        c = conn.cursor()
        
        # Fix company_database table - add name column if it doesn't exist
        try:
            c.execute("ALTER TABLE company_database ADD COLUMN name TEXT")
            print("✅ Added 'name' column to company_database")
        except sqlite3.OperationalError:
            print("ℹ️  'name' column already exists in company_database")
        
        # Copy company_name to name for compatibility
        try:
            c.execute("UPDATE company_database SET name = company_name WHERE name IS NULL")
            print("✅ Updated company names for compatibility")
        except Exception as e:
            print(f"⚠️  Could not update company names: {e}")
        
        # Ensure all required tables exist with correct structure
        tables_to_check = [
            ("users", """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    google_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """),
            ("subscriptions", """
                CREATE TABLE IF NOT EXISTS subscriptions (
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
                )
            """),
            ("usage_tracking", """
                CREATE TABLE IF NOT EXISTS usage_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    emails_sent INTEGER DEFAULT 0,
                    emails_scraped INTEGER DEFAULT 0,
                    campaigns_created INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, month)
                )
            """)
        ]
        
        for table_name, create_sql in tables_to_check:
            try:
                c.execute(create_sql)
                print(f"✅ Ensured {table_name} table exists")
            except Exception as e:
                print(f"⚠️  Could not create {table_name} table: {e}")
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_usage_user_month ON usage_tracking(user_id, month)",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)"
        ]
        
        for index_sql in indexes:
            try:
                c.execute(index_sql)
            except Exception as e:
                print(f"⚠️  Could not create index: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Database issues fixed")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

def create_production_config():
    """Create production configuration"""
    
    print("\n🌐 Creating production configuration...")
    
    # Note: Configuration is now centralized in config.py
    # Just create the .env template for production
    
    # Create .env template
    env_template = '''# Production Environment Variables
# Copy this to .env and fill in your actual values

# Flask Environment
FLASK_ENV=production
FLASK_DEBUG=false

# Security
SECRET_KEY=your-super-secret-production-key-here

# Google OAuth (for outreachpilotpro.com)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Stripe (Live Keys)
STRIPE_SECRET_KEY=sk_live_your_live_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_live_webhook_secret
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_stripe_publishable_key

# Email Configuration
MAIL_USERNAME=your-email@outreachpilotpro.com
MAIL_PASSWORD=your-email-app-password

# Database (if using external database)
DATABASE_URL=sqlite:///outreachpilot.db

# Note: All configuration is now centralized in config.py
# This .env file provides the environment variables
'''
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("✅ Created .env.template")
    print("ℹ️  Configuration is now centralized in config.py")

def create_deployment_guide():
    """Create deployment guide"""
    
    guide = '''# OutreachPilotPro Production Deployment Guide

## 🚀 Deploy to outreachpilotpro.com

### 1. Domain Setup
- Point outreachpilotpro.com to your hosting provider
- Set up SSL certificate (required for Google OAuth)

### 2. Google OAuth Configuration
1. Go to https://console.cloud.google.com/
2. Create/select your project
3. Go to "APIs & Services" > "Credentials"
4. Edit your OAuth 2.0 Client ID
5. Add authorized redirect URIs:
   - https://outreachpilotpro.com/login/google/authorize
   - https://outreachpilotpro.com/oauth2callback
6. Add authorized JavaScript origins:
   - https://outreachpilotpro.com

### 3. Environment Variables
Copy .env.template to .env and fill in:
- Google OAuth credentials
- Stripe live keys
- Email configuration
- Secret key

### 4. Database Setup
- Ensure database is properly configured
- Run: python3 fix_database_issues.py

### 5. Webhook Configuration
- Go to Stripe Dashboard > Webhooks
- Add endpoint: https://outreachpilotpro.com/webhook/stripe
- Select events: checkout.session.completed, customer.subscription.updated, etc.

### 6. Deployment Options

#### Option A: VPS/Server
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=production

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Option B: Heroku
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku create outreachpilotpro
git push heroku main
```

#### Option C: Railway/Render
- Connect your GitHub repository
- Set environment variables
- Deploy automatically

### 7. Testing
- Test Google OAuth login
- Test Stripe payments
- Test email functionality
- Test all features

### 8. Monitoring
- Set up error monitoring (Sentry)
- Set up uptime monitoring
- Monitor Stripe webhooks
- Monitor email delivery

## 🔧 Troubleshooting

### Google OAuth Issues
- Ensure redirect URIs are correct
- Check domain verification
- Verify OAuth consent screen

### Stripe Issues
- Use live keys in production
- Configure webhooks properly
- Test with real cards

### Database Issues
- Run database fix script
- Check connection strings
- Monitor database performance
'''
    
    with open('DEPLOYMENT_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print("✅ Created DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    print("🚀 OutreachPilotPro Production Setup")
    print("=" * 40)
    
    if fix_database_issues():
        create_production_config()
        create_deployment_guide()
        print("\n✅ Production setup completed!")
        print("\n📋 Next steps:")
        print("1. Configure Google OAuth for outreachpilotpro.com")
        print("2. Set up Stripe live keys")
        print("3. Deploy to your hosting provider")
        print("4. Test all functionality")
    else:
        print("\n❌ Setup failed!") 