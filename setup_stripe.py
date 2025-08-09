#!/usr/bin/env python3
"""
Stripe Setup Script for OutreachPilotPro
This script helps you create the necessary Stripe products and prices for your subscription plans.
"""

import stripe
from config import Config

def setup_stripe_products():
    """Create Stripe products and prices for subscription plans"""
    
    # Set your Stripe secret key
    stripe.api_key = Config.STRIPE_SECRET_KEY
    
    if not stripe.api_key:
        print("❌ Error: STRIPE_SECRET_KEY not found in configuration")
        print("Please add your Stripe secret key to your .env file")
        return
    
    print("🚀 Setting up Stripe products and prices...")
    
    # Define subscription plans
    plans = {
        "starter": {
            "name": "Starter Plan",
            "description": "Perfect for small businesses and startups",
            "price": 4900,  # $49.00 in cents
            "price_id": "price_starter_monthly"
        },
        "professional": {
            "name": "Professional Plan", 
            "description": "For growing businesses and teams",
            "price": 14900,  # $149.00 in cents
            "price_id": "price_professional_monthly"
        },
        "enterprise": {
            "name": "Enterprise Plan",
            "description": "For large organizations with unlimited needs",
            "price": 49900,  # $499.00 in cents
            "price_id": "price_enterprise_monthly"
        }
    }
    
    created_products = {}
    
    for plan_id, plan_data in plans.items():
        try:
            print(f"\n📦 Creating product: {plan_data['name']}")
            
            # Create product
            product = stripe.Product.create(
                name=plan_data['name'],
                description=plan_data['description'],
                metadata={
                    'plan_id': plan_id,
                    'app': 'outreachpilotpro'
                }
            )
            
            print(f"✅ Product created: {product.id}")
            
            # Create price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=plan_data['price'],
                currency='usd',
                recurring={'interval': 'month'},
                metadata={
                    'plan_id': plan_id,
                    'price_id': plan_data['price_id']
                }
            )
            
            print(f"✅ Price created: {price.id}")
            
            created_products[plan_id] = {
                'product_id': product.id,
                'price_id': price.id,
                'stripe_price_id': plan_data['price_id']
            }
            
        except Exception as e:
            print(f"❌ Error creating {plan_id}: {str(e)}")
    
    # Print summary
    print("\n" + "="*50)
    print("📋 STRIPE SETUP SUMMARY")
    print("="*50)
    
    for plan_id, data in created_products.items():
        print(f"\n{plan_id.upper()} PLAN:")
        print(f"  Product ID: {data['product_id']}")
        print(f"  Price ID: {data['price_id']}")
        print(f"  Price ID (for config): {data['stripe_price_id']}")
    
    print("\n" + "="*50)
    print("🔧 NEXT STEPS:")
    print("1. Update your subscription_manager.py with the new price IDs")
    print("2. Create a webhook endpoint in Stripe Dashboard")
    print("3. Add the webhook secret to your .env file")
    print("="*50)
    
    return created_products

def create_webhook_endpoint():
    """Instructions for creating webhook endpoint"""
    print("\n🌐 WEBHOOK SETUP INSTRUCTIONS:")
    print("1. Go to https://dashboard.stripe.com/webhooks")
    print("2. Click 'Add endpoint'")
    print("3. Enter endpoint URL: https://outreachpilotpro.com/webhook/stripe")
    print("4. Select events to listen for:")
    print("   - customer.subscription.created")
    print("   - customer.subscription.updated") 
    print("   - customer.subscription.deleted")
    print("   - invoice.payment_succeeded")
    print("   - invoice.payment_failed")
    print("5. Copy the webhook signing secret")
    print("6. Add it to your .env file as STRIPE_WEBHOOK_SECRET")

if __name__ == "__main__":
    print("🎯 OutreachPilotPro Stripe Setup")
    print("="*40)
    
    # Check if we have the secret key
    if not os.environ.get('STRIPE_SECRET_KEY'):
        print("❌ STRIPE_SECRET_KEY not found!")
        print("\nPlease add your Stripe secret key to your .env file:")
        print("STRIPE_SECRET_KEY=sk_test_your_key_here")
        print("\nYou can find your keys at: https://dashboard.stripe.com/apikeys")
    else:
        # Create products and prices
        setup_stripe_products()
        
        # Show webhook instructions
        create_webhook_endpoint() 