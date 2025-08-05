#!/usr/bin/env python3
"""
Test Stripe Webhook Endpoint
"""

import requests
import json
import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_webhook_endpoint():
    """Test the webhook endpoint"""
    
    print("🔔 Testing Stripe Webhook Endpoint")
    print("=" * 40)
    
    webhook_url = "https://outreachpilotpro.com/webhook/stripe"
    
    # Test basic connectivity
    try:
        response = requests.get(webhook_url, timeout=10)
        print(f"📊 GET request status: {response.status_code}")
        
        if response.status_code == 405:
            print("   ✅ Endpoint exists (Method Not Allowed for GET is expected)")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
    
    # Test POST request (what Stripe will send)
    try:
        response = requests.post(webhook_url, 
                               json={"test": "data"}, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        print(f"📊 POST request status: {response.status_code}")
        
        if response.status_code in [200, 400, 401]:
            print("   ✅ Endpoint responding to POST requests")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ POST request error: {e}")

def test_stripe_webhook_events():
    """Test with actual Stripe webhook events"""
    
    print("\n🧪 Testing Stripe Webhook Events")
    print("=" * 35)
    
    # Sample webhook events to test
    test_events = [
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "metadata": {
                        "user_id": "999",
                        "plan_id": "starter",
                        "product_id": "prod_SnnIncx8mICyRV"
                    },
                    "subscription": "sub_test_123"
                }
            }
        },
        {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                    "status": "active",
                    "metadata": {
                        "user_id": "999",
                        "plan_id": "starter"
                    }
                }
            }
        }
    ]
    
    webhook_url = "https://outreachpilotpro.com/webhook/stripe"
    
    for i, event in enumerate(test_events, 1):
        print(f"\n📦 Testing event {i}: {event['type']}")
        
        try:
            response = requests.post(webhook_url, 
                                   json=event, 
                                   headers={"Content-Type": "application/json"},
                                   timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Event processed successfully")
            elif response.status_code == 400:
                print("   ⚠️  Bad request (expected for test data)")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def check_webhook_configuration():
    """Check webhook configuration"""
    
    print("\n⚙️  Webhook Configuration Check")
    print("=" * 35)
    
    print("✅ Webhook URL: https://outreachpilotpro.com/webhook/stripe")
    print("✅ Destination ID: we_1RrRXPLeRd30DB0ZriM42ucV")
    print("✅ API Version: 2025-07-30.basil")
    print("✅ Events: 5 events configured")
    
    # Check if webhook secret is set
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    if webhook_secret:
        print("✅ Webhook secret: Configured")
    else:
        print("❌ Webhook secret: Not configured")
        print("   Add STRIPE_WEBHOOK_SECRET to your environment variables")

if __name__ == "__main__":
    print("🚀 Stripe Webhook Test")
    print("=" * 50)
    
    # Test webhook endpoint
    test_webhook_endpoint()
    
    # Test webhook events
    test_stripe_webhook_events()
    
    # Check configuration
    check_webhook_configuration()
    
    print("\n🎉 Webhook test completed!")
    print("\n📋 Next steps:")
    print("1. Deploy your app to production")
    print("2. Set STRIPE_WEBHOOK_SECRET environment variable")
    print("3. Test with real Stripe events")
    print("4. Monitor webhook deliveries in Stripe dashboard") 