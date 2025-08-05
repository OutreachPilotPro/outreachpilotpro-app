#!/usr/bin/env python3
"""
Get Stripe Products and Prices
Helps identify Product IDs for better Stripe integration
"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def get_stripe_products():
    """Get all Stripe products and their prices"""
    
    print("🔍 Fetching Stripe Products and Prices")
    print("=" * 50)
    
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEY not found in environment")
        return
    
    try:
        # Get all products
        products = stripe.Product.list(limit=100)
        
        print(f"📦 Found {len(products.data)} products:")
        print()
        
        for product in products.data:
            print(f"🏷️  Product: {product.name}")
            print(f"   ID: {product.id}")
            print(f"   Description: {product.description or 'No description'}")
            print(f"   Active: {product.active}")
            print(f"   Created: {product.created}")
            
            # Get prices for this product
            prices = stripe.Price.list(product=product.id, active=True)
            
            if prices.data:
                print(f"   💰 Prices:")
                for price in prices.data:
                    print(f"      - {price.id}: ${price.unit_amount/100} {price.currency.upper()}")
                    if price.recurring:
                        print(f"        (recurring: {price.recurring.interval})")
            else:
                print("   💰 No active prices")
            
            print()
        
        # Get all prices
        print("💰 All Active Prices:")
        print("-" * 30)
        prices = stripe.Price.list(active=True, limit=100)
        
        for price in prices.data:
            product = stripe.Product.retrieve(price.product)
            print(f"   {price.id}: {product.name} - ${price.unit_amount/100} {price.currency.upper()}")
            if price.recurring:
                print(f"      Recurring: {price.recurring.interval}")
        
        print()
        print("✅ Stripe data fetched successfully!")
        
    except stripe.error.AuthenticationError:
        print("❌ Authentication failed. Check your STRIPE_SECRET_KEY")
    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_price_ids():
    """Test the current price IDs in subscription_manager.py"""
    
    print("\n🧪 Testing Current Price IDs")
    print("=" * 30)
    
    current_prices = [
        "price_1RsBiFLeRd30DB0ZUMfZIGCZ",  # Starter
        "price_1RsBiGLeRd30DB0Z7Ak9FUwB",  # Professional  
        "price_1RsBiGLeRd30DB0ZMhbFVQsi"   # Enterprise
    ]
    
    for price_id in current_prices:
        try:
            price = stripe.Price.retrieve(price_id)
            product = stripe.Product.retrieve(price.product)
            print(f"✅ {price_id}: {product.name} - ${price.unit_amount/100}")
        except stripe.error.InvalidRequestError:
            print(f"❌ {price_id}: Price not found")
        except Exception as e:
            print(f"❌ {price_id}: Error - {e}")

if __name__ == "__main__":
    get_stripe_products()
    test_price_ids()
    
    print("\n📋 Next Steps:")
    print("1. Copy the Product IDs you want to use")
    print("2. Update subscription_manager.py with Product IDs")
    print("3. Test the subscription flow") 