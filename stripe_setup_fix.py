# stripe_setup_fix.py - Complete Stripe setup with error handling

import stripe
import os
import sys
import sqlite3
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

def setup_stripe():
    """Complete setup for Stripe integration"""
    
    print("🚀 Setting up Stripe Integration...")
    
    # Get Stripe key from environment or prompt user
    stripe_key = os.getenv('STRIPE_SECRET_KEY')
    
    if not stripe_key or stripe_key == 'sk_test_your_test_key_here':
        print("❌ No valid Stripe key found!")
        print("\n📋 Setup Instructions:")
        print("1. Go to https://dashboard.stripe.com/register")
        print("2. Go to https://dashboard.stripe.com/test/apikeys")
        print("3. Copy your Test Secret Key (starts with sk_test_)")
        print("4. Add it to your .env file as STRIPE_SECRET_KEY=sk_test_your_key")
        print("\nOr enter your Stripe key now:")
        
        stripe_key = input("Stripe Secret Key: ").strip()
        
        if stripe_key:
            # Save to .env file
            set_key('.env', 'STRIPE_SECRET_KEY', stripe_key)
            print("✅ Stripe key saved to .env file")
        else:
            print("❌ No key provided. Please add STRIPE_SECRET_KEY to your .env file")
            return False
    
    # Configure Stripe
    stripe.api_key = stripe_key
    
    try:
        # Test the connection
        stripe.Account.retrieve()
        print("✅ Stripe connection successful")
    except Exception as e:
        print(f"❌ Stripe connection failed: {str(e)}")
        return False
    
    # Create products and prices
    products = create_stripe_products()
    
    if products:
        print("✅ Stripe products and prices created successfully")
        save_products_to_db(products)
        return True
    else:
        print("❌ Failed to create Stripe products")
        return False

def create_stripe_products():
    """Create products and prices in Stripe"""
    
    products = {
        'free': {
            'name': 'Free Plan',
            'description': 'Basic email finding with limited searches',
            'price': 0,
            'currency': 'usd',
            'interval': None,
            'features': ['100 emails per month', 'Basic search', 'Email verification']
        },
        'starter': {
            'name': 'Starter Plan',
            'description': 'Perfect for small businesses and startups',
            'price': 29,
            'currency': 'usd',
            'interval': 'month',
            'features': ['1,000 emails per month', 'Advanced search', 'Email verification', 'Campaign management']
        },
        'professional': {
            'name': 'Professional Plan',
            'description': 'For growing businesses and marketing teams',
            'price': 99,
            'currency': 'usd',
            'interval': 'month',
            'features': ['10,000 emails per month', 'Universal search', 'Advanced targeting', 'Campaign analytics', 'Priority support']
        },
        'enterprise': {
            'name': 'Enterprise Plan',
            'description': 'For large organizations with unlimited needs',
            'price': 299,
            'currency': 'usd',
            'interval': 'month',
            'features': ['Unlimited emails', 'Universal search', 'Advanced targeting', 'Custom integrations', 'Dedicated support', 'API access']
        }
    }
    
    created_products = {}
    
    for plan_id, plan_data in products.items():
        try:
            print(f"Creating {plan_data['name']}...")
            
            # Create product
            product = stripe.Product.create(
                name=plan_data['name'],
                description=plan_data['description'],
                metadata={'plan_id': plan_id}
            )
            
            # Create price (skip for free plan)
            if plan_data['price'] > 0:
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=plan_data['price'] * 100,  # Convert to cents
                    currency=plan_data['currency'],
                    recurring={'interval': plan_data['interval']},
                    metadata={'plan_id': plan_id}
                )
                price_id = price.id
            else:
                price_id = None
            
            created_products[plan_id] = {
                'product_id': product.id,
                'price_id': price_id,
                'name': plan_data['name'],
                'price': plan_data['price'],
                'currency': plan_data['currency'],
                'interval': plan_data['interval'],
                'features': plan_data['features']
            }
            
            print(f"✅ Created {plan_data['name']} - Product: {product.id}, Price: {price_id}")
            
        except Exception as e:
            print(f"❌ Failed to create {plan_data['name']}: {str(e)}")
            return None
    
    return created_products

def save_products_to_db(products):
    """Save product information to database"""
    
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    
    # Create products table if it doesn't exist
    c.execute("""
        CREATE TABLE IF NOT EXISTS stripe_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id TEXT UNIQUE NOT NULL,
            product_id TEXT NOT NULL,
            price_id TEXT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            currency TEXT NOT NULL,
            interval TEXT,
            features TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Clear existing products
    c.execute("DELETE FROM stripe_products")
    
    # Insert new products
    for plan_id, product_data in products.items():
        features_json = ','.join(product_data['features'])
        
        c.execute("""
            INSERT INTO stripe_products 
            (plan_id, product_id, price_id, name, price, currency, interval, features)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan_id,
            product_data['product_id'],
            product_data['price_id'],
            product_data['name'],
            product_data['price'],
            product_data['currency'],
            product_data['interval'],
            features_json
        ))
    
    conn.commit()
    conn.close()
    
    print("✅ Product information saved to database")

def setup_webhook():
    """Instructions for setting up webhook"""
    
    print("\n🌐 Webhook Setup Instructions:")
    print("1. Go to https://dashboard.stripe.com/test/webhooks")
    print("2. Click 'Add endpoint'")
    print("3. Enter endpoint URL: http://localhost:8800/webhook/stripe")
    print("4. Select these events:")
    print("   - checkout.session.completed")
    print("   - customer.subscription.updated")
    print("   - customer.subscription.deleted")
    print("   - invoice.payment_succeeded")
    print("   - invoice.payment_failed")
    print("5. Copy the signing secret (starts with whsec_)")
    print("6. Add it to your .env file as STRIPE_WEBHOOK_SECRET=whsec_your_secret_here")

def main():
    """Main setup function"""
    
    print("🎯 OutreachPilotPro Stripe Setup")
    print("=" * 50)
    
    # Setup Stripe
    if setup_stripe():
        print("\n✅ Stripe setup completed successfully!")
        
        # Show webhook instructions
        setup_webhook()
        
        print("\n🚀 Next Steps:")
        print("1. Set up webhook endpoint (see instructions above)")
        print("2. Add webhook secret to .env file")
        print("3. Run your Flask app: python3 app.py")
        print("4. Test subscription flow at http://localhost:8800/subscription")
        
    else:
        print("\n❌ Stripe setup failed. Please check your configuration.")

if __name__ == "__main__":
    main() 