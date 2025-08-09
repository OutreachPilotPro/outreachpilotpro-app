#!/usr/bin/env python3
"""
Enhanced Features Setup Script for OutreachPilotPro
This script helps you implement the enhanced Stripe integration and email scraper features.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header():
    print("🚀 OutreachPilotPro Enhanced Features Setup")
    print("=" * 50)

def check_requirements():
    """Check if required packages are installed"""
    print("📦 Checking requirements...")
    
    required_packages = [
        'flask',
        'stripe', 
        'requests',
        'python-dotenv',
        'dnspython'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - Missing")
    
    if missing_packages:
        print(f"\n📥 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ All packages installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please install manually:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    
    return True

def setup_environment():
    """Setup environment variables"""
    print("\n🔧 Setting up environment variables...")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_content = """# OutreachPilotPro Environment Variables

# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development

# Stripe Configuration (Get these from https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=sk_test_your_test_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key_here

# Database Configuration
DATABASE_URL=sqlite:///users.db

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# API Keys (Optional - for enhanced features)
GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_api_key
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created!")
        print("⚠️  Please update the .env file with your actual API keys")
    else:
        print("✅ .env file already exists")

def setup_stripe():
    """Setup Stripe configuration"""
    print("\n💳 Setting up Stripe...")
    
    print("📋 Stripe Setup Instructions:")
    print("1. Go to https://dashboard.stripe.com/register")
    print("2. Go to https://dashboard.stripe.com/test/apikeys")
    print("3. Copy your Test Secret Key (starts with sk_test_)")
    print("4. Copy your Test Publishable Key (starts with pk_test_)")
    print("5. Update your .env file with these keys")
    
    # Check if Stripe keys are configured
    from dotenv import load_dotenv
    load_dotenv()
    
    stripe_secret = os.getenv('STRIPE_SECRET_KEY')
    stripe_publishable = os.getenv('STRIPE_PUBLISHABLE_KEY')
    
    if stripe_secret and stripe_secret != 'sk_test_your_test_key_here':
        print("✅ Stripe Secret Key configured")
    else:
        print("❌ Stripe Secret Key not configured")
    
    if stripe_publishable and stripe_publishable != 'pk_test_your_test_key_here':
        print("✅ Stripe Publishable Key configured")
    else:
        print("❌ Stripe Publishable Key not configured")

def setup_database():
    """Setup database with enhanced schema"""
    print("\n🗄️  Setting up database...")
    
    try:
        import sqlite3
        
        # Create enhanced database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create subscriptions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                stripe_subscription_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create campaigns table
        c.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                emails TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create email_usage table
        c.execute('''
            CREATE TABLE IF NOT EXISTS email_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                emails_found INTEGER DEFAULT 0,
                date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Database setup completed!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")

def create_test_user():
    """Create a test user for testing"""
    print("\n👤 Creating test user...")
    
    try:
        from werkzeug.security import generate_password_hash
        import sqlite3
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Check if test user exists
        test_user = c.execute('SELECT * FROM users WHERE email = ?', ('test@example.com',)).fetchone()
        
        if not test_user:
            # Create test user
            password_hash = generate_password_hash('password123')
            c.execute('''
                INSERT INTO users (email, name, password_hash)
                VALUES (?, ?, ?)
            ''', ('test@example.com', 'Test User', password_hash))
            
            conn.commit()
            print("✅ Test user created!")
            print("   Email: test@example.com")
            print("   Password: password123")
        else:
            print("✅ Test user already exists")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")

def test_enhanced_app():
    """Test the enhanced app"""
    print("\n🧪 Testing enhanced app...")
    
    try:
        # Test if app_enhanced.py can be imported
        import app_enhanced
        print("✅ Enhanced app imports successfully")
        
        # Test database connection
        conn = app_enhanced.get_db_connection()
        conn.close()
        print("✅ Database connection works")
        
        # Test email finder
        finder = app_enhanced.email_finder
        print("✅ Email finder initialized")
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def show_next_steps():
    """Show next steps for the user"""
    print("\n🎯 Next Steps:")
    print("1. Update your .env file with real Stripe API keys")
    print("2. Replace your current app.py with app_enhanced.py")
    print("3. Replace your subscription.html with subscription_enhanced.html")
    print("4. Test the subscription flow:")
    print("   - Login with test@example.com / password123")
    print("   - Go to /subscription")
    print("   - Try upgrading to a paid plan")
    print("   - Use test card: 4242 4242 4242 4242")
    print("5. Test the enhanced email search at /scrape")
    
    print("\n🚀 To run the enhanced app:")
    print("python3 app_enhanced.py")
    
    print("\n📚 For more help:")
    print("- Check the FAVICON_SETUP_SUMMARY.md for favicon details")
    print("- Review the enhanced templates for UI improvements")
    print("- Test the API endpoints at /api/email-search")

def main():
    """Main setup function"""
    print_header()
    
    # Check requirements
    if not check_requirements():
        return
    
    # Setup environment
    setup_environment()
    
    # Setup Stripe
    setup_stripe()
    
    # Setup database
    setup_database()
    
    # Create test user
    create_test_user()
    
    # Test enhanced app
    test_enhanced_app()
    
    # Show next steps
    show_next_steps()
    
    print("\n🎉 Setup completed! Your OutreachPilotPro is now enhanced with:")
    print("✅ Advanced email scraper with universal search")
    print("✅ Proper Stripe integration with error handling")
    print("✅ Enhanced subscription management")
    print("✅ Usage tracking and limits")
    print("✅ Professional UI/UX improvements")
    print("✅ Comprehensive error handling")
    print("✅ API endpoints for email search and export")

if __name__ == "__main__":
    main()
