#!/usr/bin/env python3
"""
Improved Database Initialization Script
Consolidates features from final_database_fix.py and init_db.py
Creates all necessary tables with proper schema and optimizations
"""

import sqlite3
import sys
import os
from datetime import datetime

DATABASE_FILE = 'outreachpilot.db'

def init_database(force=False):
    """Initialize the database with all necessary tables and optimizations"""
    
    # Check if database exists and handle force flag
    if os.path.exists(DATABASE_FILE) and not force:
        print(f"Database {DATABASE_FILE} already exists.")
        print("Use --force to reinitialize the database.")
        return False
    
    if force and os.path.exists(DATABASE_FILE):
        print(f"Removing existing database {DATABASE_FILE}...")
        os.remove(DATABASE_FILE)
    
    print(f"Initializing database: {DATABASE_FILE}")
    
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        # Apply database optimizations
        print("🔧 Applying database optimizations...")
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA cache_size=10000")
        c.execute("PRAGMA temp_store=MEMORY")
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA mmap_size=268435456")
        
        # Create all necessary tables with proper schema
        print("📋 Creating database tables...")
        
        # Users table - based on actual schema
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                google_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Created users table")
        
        # Company database table - based on actual schema
        c.execute('''
            CREATE TABLE IF NOT EXISTS company_database (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                domain TEXT NOT NULL,
                industry TEXT,
                size TEXT,
                location TEXT,
                website TEXT,
                linkedin_url TEXT,
                employee_count INTEGER,
                founded_year INTEGER,
                revenue_range TEXT,
                source TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name TEXT,
                subcategory TEXT,
                revenue TEXT,
                employees INTEGER,
                website_url TEXT,
                twitter_url TEXT,
                facebook_url TEXT,
                description TEXT,
                tags TEXT,
                verified BOOLEAN DEFAULT 0,
                last_verified TIMESTAMP,
                data_source TEXT,
                confidence_score REAL DEFAULT 0.0,
                technology TEXT
            )
        ''')
        print("  ✅ Created company_database table")
        
        # Subscriptions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                stripe_subscription_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("  ✅ Created subscriptions table")
        
        # Usage tracking table
        c.execute('''
            CREATE TABLE IF NOT EXISTS usage_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("  ✅ Created usage_tracking table")
        
        # Payment history table
        c.execute('''
            CREATE TABLE IF NOT EXISTS payment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                stripe_payment_id TEXT,
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("  ✅ Created payment_history table")
        
        # Campaigns table
        c.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                target_companies TEXT,
                email_template TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("  ✅ Created campaigns table")
        
        # Email queue table
        c.execute('''
            CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER,
                recipient_email TEXT NOT NULL,
                recipient_name TEXT,
                company_name TEXT,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                scheduled_at TIMESTAMP,
                sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
            )
        ''')
        print("  ✅ Created email_queue table")
        
        # Scraped emails table
        c.execute('''
            CREATE TABLE IF NOT EXISTS scraped_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                name TEXT,
                company_name TEXT,
                domain TEXT,
                source TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 0,
                verification_date TIMESTAMP
            )
        ''')
        print("  ✅ Created scraped_emails table")
        
        # Email usage table
        c.execute('''
            CREATE TABLE IF NOT EXISTS email_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                emails_sent INTEGER DEFAULT 0,
                emails_verified INTEGER DEFAULT 0,
                last_usage_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("  ✅ Created email_usage table")
        
        # Email verification table
        c.execute('''
            CREATE TABLE IF NOT EXISTS email_verification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                verification_code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Created email_verification table")
        
        # Google tokens table
        c.execute('''
            CREATE TABLE IF NOT EXISTS google_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("  ✅ Created google_tokens table")
        
        # Stripe products table
        c.execute('''
            CREATE TABLE IF NOT EXISTS stripe_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                interval TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Created stripe_products table")
        
        # Data sources table
        c.execute('''
            CREATE TABLE IF NOT EXISTS data_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                url TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Created data_sources table")
        
        # Email patterns table
        c.execute('''
            CREATE TABLE IF NOT EXISTS email_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                description TEXT,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Created email_patterns table")
        
        # Create performance indexes
        print("🚀 Creating performance indexes...")
        indexes = [
            ("idx_users_email", "users", "email"),
            ("idx_users_google_id", "users", "google_id"),
            ("idx_company_domain", "company_database", "domain"),
            ("idx_company_industry", "company_database", "industry"),
            ("idx_company_size", "company_database", "size"),
            ("idx_company_location", "company_database", "location"),
            ("idx_subscriptions_user", "subscriptions", "user_id"),
            ("idx_subscriptions_status", "subscriptions", "status"),
            ("idx_usage_tracking_user", "usage_tracking", "user_id"),
            ("idx_usage_tracking_date", "usage_tracking", "action_date"),
            ("idx_campaigns_user", "campaigns", "user_id"),
            ("idx_campaigns_status", "campaigns", "status"),
            ("idx_email_queue_campaign", "email_queue", "campaign_id"),
            ("idx_email_queue_status", "email_queue", "status"),
            ("idx_scraped_emails_domain", "scraped_emails", "domain"),
            ("idx_scraped_emails_verified", "scraped_emails", "verified"),
            ("idx_google_tokens_user", "google_tokens", "user_id"),
            ("idx_stripe_products_active", "stripe_products", "active")
        ]
        
        for index_name, table_name, column_name in indexes:
            try:
                c.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})")
                print(f"  ✅ Created index: {index_name}")
            except Exception as e:
                print(f"  ⚠️  Could not create index {index_name}: {e}")
        
        # Insert initial data
        print("📝 Inserting initial data...")
        
        # Insert demo user
        c.execute('''
            INSERT OR IGNORE INTO users (email, name, created_at)
            VALUES (?, ?, ?)
        ''', ('demo@outreachpilot.com', 'Demo User', datetime.now()))
        print("  ✅ Added demo user")
        
        # Insert sample companies
        sample_companies = [
            ('TechCorp Inc', 'techcorp.com', 'Technology', 'Medium', 'San Francisco, CA'),
            ('DataFlow Solutions', 'dataflow.com', 'Software', 'Small', 'Austin, TX'),
            ('GreenEnergy Co', 'greenenergy.com', 'Energy', 'Large', 'Denver, CO'),
            ('InnovateLab', 'innovatelab.com', 'Research', 'Startup', 'Boston, MA'),
            ('CloudScale Systems', 'cloudscale.com', 'Cloud Computing', 'Medium', 'Seattle, WA')
        ]
        
        for company_name, domain, industry, size, location in sample_companies:
            c.execute('''
                INSERT OR IGNORE INTO company_database 
                (company_name, domain, industry, size, location, website, source, name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (company_name, domain, industry, size, location, f'https://{domain}', 'sample', company_name))
        print("  ✅ Added sample companies")
        
        # Insert default Stripe products
        default_products = [
            ('prod_basic', 'Basic Plan', 'Essential features for small businesses', 29.99, 'monthly'),
            ('prod_pro', 'Professional Plan', 'Advanced features for growing companies', 79.99, 'monthly'),
            ('prod_enterprise', 'Enterprise Plan', 'Full features for large organizations', 199.99, 'monthly')
        ]
        
        for product_id, name, description, price, interval in default_products:
            c.execute('''
                INSERT OR IGNORE INTO stripe_products 
                (product_id, name, description, price, interval)
                VALUES (?, ?, ?, ?, ?)
            ''', (product_id, name, description, price, interval))
        print("  ✅ Added default Stripe products")
        
        # Insert default data sources
        default_sources = [
            ('LinkedIn', 'Professional networking platform for company research'),
            ('Company Websites', 'Direct company website scraping'),
            ('Industry Databases', 'Professional industry databases and directories'),
            ('Public Records', 'Government and public business records')
        ]
        
        for name, description in default_sources:
            c.execute('''
                INSERT OR IGNORE INTO data_sources (name, description)
                VALUES (?, ?)
            ''', (name, description))
        print("  ✅ Added default data sources")
        
        # Commit all changes
        conn.commit()
        print(f"\n🎉 Database initialization completed successfully!")
        print(f"Database file: {DATABASE_FILE}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def test_database():
    """Test the database connection and basic operations"""
    print("\n🧪 Testing database...")
    
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        # Test table creation
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print(f"  ✅ Found {len(tables)} tables")
        
        # Test basic queries
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        print(f"  ✅ Users table has {user_count} records")
        
        c.execute("SELECT COUNT(*) FROM company_database")
        company_count = c.fetchone()[0]
        print(f"  ✅ Company database has {company_count} records")
        
        c.execute("SELECT COUNT(*) FROM stripe_products")
        product_count = c.fetchone()[0]
        print(f"  ✅ Stripe products has {product_count} records")
        
        # Test database optimizations
        c.execute("PRAGMA journal_mode")
        journal_mode = c.fetchone()[0]
        print(f"  ✅ Journal mode: {journal_mode}")
        
        c.execute("PRAGMA foreign_keys")
        foreign_keys = c.fetchone()[0]
        print(f"  ✅ Foreign keys: {foreign_keys}")
        
        conn.close()
        print("  ✅ Database test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def show_database_info():
    """Show information about the database"""
    print(f"\n📊 Database Information: {DATABASE_FILE}")
    
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        # Get table information
        c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = c.fetchall()
        
        print(f"Tables ({len(tables)}):")
        for table in tables:
            table_name = table[0]
            c.execute(f"PRAGMA table_info({table_name})")
            columns = c.fetchall()
            print(f"  {table_name}: {len(columns)} columns")
        
        # Get database size
        if os.path.exists(DATABASE_FILE):
            size = os.path.getsize(DATABASE_FILE)
            size_mb = size / (1024 * 1024)
            print(f"\nDatabase size: {size_mb:.2f} MB")
        
        conn.close()
        
    except Exception as e:
        print(f"Error getting database info: {e}")

def main():
    """Main function to handle command line arguments"""
    force = '--force' in sys.argv
    non_interactive = '--non-interactive' in sys.argv
    
    print("🚀 OutreachPilot Database Initialization")
    print("=" * 50)
    
    if force:
        print("⚠️  Force mode enabled - will reinitialize existing database")
    
    # Initialize database
    if init_database(force=force):
        # Test the database
        test_database()
        
        # Show database information
        show_database_info()
        
        print("\n✅ Database setup completed successfully!")
        print("You can now run your OutreachPilot application.")
        
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
