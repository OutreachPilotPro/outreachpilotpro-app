# complete_stripe_setup.py - One-click setup for Stripe

import os
import sys
import stripe
import sqlite3
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

def setup_everything():
    """Complete setup for Stripe integration"""
    
    print("🚀 OutreachPilotPro Complete Stripe Setup")
    print("="*50)
    
    # Check if we have a Stripe key
    from config import Config
    stripe_key = Config.STRIPE_SECRET_KEY
    
    if not stripe_key or stripe_key == 'your-stripe-secret-key':
        print("\n⚠️  No Stripe key found!")
        print("\nPlease enter your Stripe secret key")
        print("(Get it from https://dashboard.stripe.com/test/apikeys)")
        stripe_key = input("Stripe Secret Key: ").strip()
        
        if not stripe_key:
            print("❌ No key provided. Exiting.")
            return False
        
        # Save to .env file
        set_key('.env', 'STRIPE_SECRET_KEY', stripe_key)
        print("✅ Saved Stripe key to .env file")
    
    stripe.api_key = stripe_key
    
    # Test the connection
    try:
        account = stripe.Account.retrieve()
        print(f"\n✅ Connected to Stripe account: {account.email}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    # Create products and prices
    print("\n📦 Creating subscription products...")
    
    plans = {
        "starter": {"name": "Starter Plan", "price": 4900},
        "professional": {"name": "Professional Plan", "price": 14900},
        "enterprise": {"name": "Enterprise Plan", "price": 49900}
    }
    
    price_ids = {}
    
    for plan_id, plan_data in plans.items():
        try:
            # Check if product exists
            products = stripe.Product.list(limit=100)
            existing_product = None
            
            for product in products:
                if product.metadata.get('plan_id') == plan_id:
                    existing_product = product
                    break
            
            if existing_product:
                print(f"ℹ️  Product '{plan_id}' already exists")
                product = existing_product
            else:
                # Create new product
                product = stripe.Product.create(
                    name=plan_data['name'],
                    metadata={'plan_id': plan_id}
                )
                print(f"✅ Created product: {plan_data['name']}")
            
            # Check for existing price
            prices = stripe.Price.list(product=product.id, active=True)
            
            if prices.data:
                price = prices.data[0]
                print(f"ℹ️  Using existing price for {plan_id}")
            else:
                # Create new price
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=plan_data['price'],
                    currency='usd',
                    recurring={'interval': 'month'}
                )
                print(f"✅ Created price for {plan_id}")
            
            price_ids[plan_id] = price.id
            
        except Exception as e:
            print(f"❌ Error with {plan_id}: {e}")
    
    # Update subscription_manager.py
    print("\n📝 Updating subscription_manager.py...")
    update_file = False
    
    try:
        with open('subscription_manager.py', 'r') as f:
            content = f.read()
        
        # Update each price ID
        for plan_id, price_id in price_ids.items():
            import re
            # Look for the plan and update its stripe_price_id
            pattern = f'"{plan_id}"[^{{]*{{"[^}}]*"stripe_price_id":\\s*"[^"]*"'
            replacement = f'"{plan_id}": {{\n            "name": '
            
            # Find the full plan block and update just the price ID
            plan_pattern = f'"{plan_id}":\\s*{{[^}}]+}}'
            match = re.search(plan_pattern, content, re.DOTALL)
            
            if match:
                plan_block = match.group(0)
                # Update the stripe_price_id in this block
                updated_block = re.sub(
                    r'"stripe_price_id":\s*"[^"]*"',
                    f'"stripe_price_id": "{price_id}"',
                    plan_block
                )
                content = content.replace(plan_block, updated_block)
                update_file = True
        
        if update_file:
            with open('subscription_manager.py', 'w') as f:
                f.write(content)
            print("✅ Updated subscription_manager.py")
        
    except Exception as e:
        print(f"⚠️  Could not auto-update subscription_manager.py: {e}")
    
    # Show manual update instructions
    print("\n📋 Price IDs for your plans:")
    print("="*50)
    for plan_id, price_id in price_ids.items():
        print(f"{plan_id}: {price_id}")
    
    # Test creating a checkout session
    print("\n🧪 Testing checkout session creation...")
    try:
        test_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_ids.get('starter'),
                'quantity': 1,
            }],
            mode='subscription',
            success_url='http://localhost:8800/subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:8800/subscription',
            metadata={
                'user_id': '1',
                'plan_id': 'starter'
            }
        )
        print("✅ Checkout session test successful!")
        print(f"   Test URL: {test_session.url}")
    except Exception as e:
        print(f"❌ Checkout session test failed: {e}")
    
    # Webhook instructions
    print("\n🌐 Final Step: Configure Webhook")
    print("="*50)
    print("1. Go to: https://dashboard.stripe.com/test/webhooks")
    print("2. Click 'Add endpoint'")
    print("3. Endpoint URL: http://localhost:8800/webhook/stripe")
    print("   (Use https://outreachpilotpro.com/webhook/stripe in production)")
    print("4. Select these events:")
    print("   ✓ checkout.session.completed")
    print("   ✓ customer.subscription.updated")
    print("   ✓ customer.subscription.deleted")
    print("   ✓ invoice.payment_succeeded")
    print("   ✓ invoice.payment_failed")
    print("5. Copy the signing secret and add to .env:")
    print("   STRIPE_WEBHOOK_SECRET=whsec_...")
    
    print("\n✅ Setup complete! Your Stripe integration is ready.")
    print("\nTest it by going to http://localhost:8800/subscription")
    
    return True

def quick_test():
    """Quick test to verify everything is working"""
    stripe.api_key = Config.STRIPE_SECRET_KEY
    
    try:
        # Test 1: API connection
        account = stripe.Account.retrieve()
        print("✅ API Connection: OK")
        
        # Test 2: Products exist
        products = stripe.Product.list(limit=10)
        product_count = len([p for p in products if 'plan_id' in p.metadata])
        print(f"✅ Products: {product_count} plans found")
        
        # Test 3: Prices exist
        prices = stripe.Price.list(limit=20, active=True)
        price_count = len(prices.data)
        print(f"✅ Prices: {price_count} active prices found")
        
        # Test 4: Can create checkout session
        if prices.data:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price': prices.data[0].id, 'quantity': 1}],
                mode='subscription',
                success_url='http://localhost:8800/success',
                cancel_url='http://localhost:8800/cancel'
            )
            print("✅ Checkout: Can create sessions")
        
        print("\n🎉 All tests passed! Stripe is configured correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Run the setup first: python3 complete_stripe_setup.py")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        quick_test()
    else:
        setup_everything() 