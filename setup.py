#!/usr/bin/env python3
"""
Setup script for OutreachPilotPro
Initializes database and installs dependencies
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    return True

def create_database():
    """Create and initialize database tables"""
    print("🗄️  Creating database...")
    
    # Import modules to get table schemas
    from subscription_manager import create_subscription_tables
    from services.email_finder import EmailFinder
    
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    
    try:
        # Create users table
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                google_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create subscription tables
        tables_sql = create_subscription_tables()
        for statement in tables_sql.split(';'):
            if statement.strip():
                c.execute(statement)
        
        # Create scraped_emails table
        c.execute("""
            CREATE TABLE IF NOT EXISTS scraped_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_name TEXT NOT NULL,
                email TEXT NOT NULL,
                source TEXT DEFAULT 'manual',
                verified BOOLEAN DEFAULT 1,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create campaigns table
        c.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                from_name TEXT,
                reply_to TEXT,
                recipient_list_id INTEGER,
                scheduled_time TIMESTAMP,
                status TEXT DEFAULT 'draft',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create email_queue table
        c.execute("""
            CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                recipient_email TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                scheduled_for TIMESTAMP,
                sent_at TIMESTAMP,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
            )
        """)
        
        # Create google_tokens table
        c.execute("""
            CREATE TABLE IF NOT EXISTS google_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()
        print("✅ Database created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    finally:
        conn.close()
    
    return True

def create_env_file():
    """Create .env file with default configuration"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists, skipping...")
        return True
    
    print("🔧 Creating .env file...")
    
    env_content = """# OutreachPilotPro Configuration

# Flask Configuration
SECRET_KEY=your-secret-key-here-change-this-in-production
FLASK_ENV=development

# Database Configuration
DATABASE_URL=sqlite:///outreachpilot.db

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Stripe Configuration (for payments)
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Redis Configuration (for rate limiting and caching)
REDIS_URL=redis://localhost:6379

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("⚠️  Please update the .env file with your actual credentials")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False
    
    return True

def check_requirements():
    """Check if all required services are available"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check if Redis is available (optional)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        r.ping()
        print("✅ Redis is available")
    except:
        print("⚠️  Redis not available - rate limiting will be disabled")
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up OutreachPilotPro...")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("❌ Setup failed - requirements not met")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed - could not install dependencies")
        sys.exit(1)
    
    # Create database
    if not create_database():
        print("❌ Setup failed - could not create database")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("❌ Setup failed - could not create .env file")
        sys.exit(1)
    
    print("=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update the .env file with your actual credentials")
    print("2. Set up Google OAuth in Google Cloud Console")
    print("3. Set up Stripe account for payments (optional)")
    print("4. Run: python app.py")
    print("\n🌐 Your app will be available at: http://localhost:5000")

if __name__ == "__main__":
    main() 