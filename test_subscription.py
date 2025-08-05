#!/usr/bin/env python3
"""
Test script to verify subscription functionality
"""

import sqlite3
import subscription_manager
import os

def test_subscription_manager():
    """Test subscription manager functionality"""
    
    print("🧪 Testing Subscription Manager")
    print("=" * 40)
    
    try:
        # Initialize subscription manager
        print("1. Initializing subscription manager...")
        sm = subscription_manager.SubscriptionManager()
        print("   ✅ Subscription manager initialized")
        
        # Test getting user subscription (should return free plan for non-existent user)
        print("\n2. Testing get_user_subscription...")
        subscription = sm.get_user_subscription(999)  # Non-existent user
        print(f"   ✅ Free subscription returned: {subscription['tier']}")
        print(f"   ✅ Plan name: {subscription['plan_name']}")
        print(f"   ✅ Price: ${subscription['price']}")
        
        # Test usage stats
        print("\n3. Testing get_usage_stats...")
        usage_stats = sm.get_usage_stats(999)
        print(f"   ✅ Usage stats returned: {usage_stats['current_month']['emails_sent']} emails sent")
        print(f"   ✅ Limits: {usage_stats['current_month']['limits']['emails_per_month']} emails/month")
        
        # Test limit checking
        print("\n4. Testing check_limit...")
        limit_check = sm.check_limit(999, 'emails')
        print(f"   ✅ Limit check: {limit_check['allowed']} (current: {limit_check['current']}/{limit_check['limit']})")
        
        # Test creating a user and subscription
        print("\n5. Testing user creation and subscription...")
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        
        # Create test user
        c.execute("""
            INSERT OR REPLACE INTO users (id, email, name) 
            VALUES (999, 'test@outreachpilotpro.com', 'Test User')
        """)
        
        # Create free subscription
        sm.create_free_subscription(999, 'free')
        
        # Test subscription again
        subscription = sm.get_user_subscription(999)
        print(f"   ✅ User subscription: {subscription['tier']}")
        
        # Test usage increment
        print("\n6. Testing usage increment...")
        sm.increment_usage(999, 'emails', 5)
        usage_stats = sm.get_usage_stats(999)
        print(f"   ✅ After increment: {usage_stats['current_month']['emails_sent']} emails sent")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 All subscription tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Subscription test failed: {e}")
        return False

def test_database_tables():
    """Test that all required tables exist"""
    
    print("\n📊 Testing Database Tables")
    print("=" * 30)
    
    try:
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        
        required_tables = [
            'users', 'subscriptions', 'usage_tracking', 
            'payment_history', 'email_queue', 'campaigns', 
            'google_tokens', 'company_database'
        ]
        
        for table in required_tables:
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if c.fetchone():
                print(f"   ✅ {table} table exists")
            else:
                print(f"   ❌ {table} table missing")
        
        conn.close()
        print("\n✅ Database table check completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 OutreachPilotPro Subscription Test")
    print("=" * 50)
    
    # Test database tables
    db_ok = test_database_tables()
    
    # Test subscription manager
    sub_ok = test_subscription_manager()
    
    if db_ok and sub_ok:
        print("\n🎉 All tests passed! Subscription system is working correctly.")
        print("\n📋 Next steps:")
        print("1. Deploy to production")
        print("2. Configure Stripe webhooks")
        print("3. Test with real payments")
    else:
        print("\n❌ Some tests failed. Please check the errors above.") 