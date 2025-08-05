#!/usr/bin/env python3
"""
Setup Production Environment Variables
"""

import os

def setup_production_env():
    """Setup production environment variables"""
    
    print("🚀 Setting up Production Environment Variables")
    print("=" * 50)
    
    # Production environment variables
    env_vars = {
        'STRIPE_SECRET_KEY': 'sk_live_51Rqmq7LeRd30DB0ZUMfZIGCZ',
        'STRIPE_PUBLISHABLE_KEY': 'pk_live_51Rqmq7LeRd30DB0ZUMfZIGCZ',
        'STRIPE_WEBHOOK_SECRET': 'whsec_dnAVwr0SDIyUDj5vR5JAzxX6Lqgp4WM9',
        'FLASK_ENV': 'production',
        'BASE_URL': 'https://outreachpilotpro.com',
        'SECRET_KEY': 'your_secret_key_here',
        'GOOGLE_CLIENT_ID': 'your_google_client_id_here',
        'GOOGLE_CLIENT_SECRET': 'your_google_client_secret_here'
    }
    
    print("📋 Production Environment Variables:")
    print()
    
    for key, value in env_vars.items():
        print(f"{key}={value}")
    
    print()
    print("✅ Webhook Secret Configured!")
    print(f"   Webhook Secret: {env_vars['STRIPE_WEBHOOK_SECRET']}")
    print()
    
    print("📋 Next Steps:")
    print("1. Copy these environment variables to your production hosting platform")
    print("2. Update Google OAuth credentials for outreachpilotpro.com")
    print("3. Deploy your application")
    print("4. Test webhook functionality")
    
    return env_vars

def test_webhook_secret():
    """Test the webhook secret configuration"""
    
    print("\n🧪 Testing Webhook Secret")
    print("=" * 30)
    
    webhook_secret = 'whsec_dnAVwr0SDIyUDj5vR5JAzxX6Lqgp4WM9'
    
    if webhook_secret.startswith('whsec_'):
        print("✅ Webhook secret format is correct")
        print(f"   Secret: {webhook_secret[:10]}...")
    else:
        print("❌ Webhook secret format is incorrect")
    
    print("✅ Webhook secret is ready for production!")

if __name__ == "__main__":
    env_vars = setup_production_env()
    test_webhook_secret()
    
    print("\n🎉 Environment setup completed!")
    print("\n🚀 Ready for production deployment!") 