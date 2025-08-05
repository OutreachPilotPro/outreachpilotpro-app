#!/usr/bin/env python3
"""
Quick Stripe Integration Setup for OutreachPilotPro
"""

import os
import sys
from dotenv import load_dotenv

def main():
    print("🚀 OutreachPilotPro Stripe Integration Setup")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ No .env file found!")
        print("Please create a .env file with your configuration.")
        return False
    
    # Check for required environment variables
    required_vars = ['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var) or os.environ.get(var) == 'your-stripe-secret-key':
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease add these to your .env file:")
        for var in missing_vars:
            if var == 'STRIPE_SECRET_KEY':
                print(f"{var}=sk_test_your_actual_stripe_secret_key")
            elif var == 'STRIPE_WEBHOOK_SECRET':
                print(f"{var}=whsec_your_webhook_signing_secret")
        return False
    
    print("✅ Environment variables configured")
    
    # Check if database tables exist
    try:
        import sqlite3
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        
        # Check if subscription tables exist
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'")
        if not c.fetchone():
            print("❌ Subscription tables not found!")
            print("Please run the complete setup script first:")
            print("python3 complete_stripe_setup.py")
            return False
        
        print("✅ Database tables exist")
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Test Stripe connection
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        account = stripe.Account.retrieve()
        print(f"✅ Connected to Stripe account: {account.email}")
        
    except Exception as e:
        print(f"❌ Stripe connection failed: {e}")
        return False
    
    print("\n🎉 Stripe integration is ready!")
    print("\nNext steps:")
    print("1. Run the complete setup: python3 complete_stripe_setup.py")
    print("2. Configure webhooks in your Stripe dashboard")
    print("3. Test the integration: python3 complete_stripe_setup.py test")
    print("4. Start your app: python3 app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 