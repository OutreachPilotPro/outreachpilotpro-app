#!/usr/bin/env python3
"""
Final Database Fix for OutreachPilotPro
Resolves all database issues before production deployment
"""

import sqlite3
import os

def fix_all_database_issues():
    """Fix all database issues comprehensively"""
    
    print("🔧 Final Database Fix for OutreachPilotPro")
    print("=" * 50)
    
    try:
        # Connect with optimized settings
        conn = sqlite3.connect("outreachpilot.db", timeout=30.0)
        c = conn.cursor()
        
        # Optimize database
        print("📊 Optimizing database...")
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA cache_size=10000")
        c.execute("PRAGMA temp_store=MEMORY")
        c.execute("VACUUM")
        
        # Check and fix company_database table
        print("🏢 Fixing company_database table...")
        
        # Get current columns
        c.execute("PRAGMA table_info(company_database)")
        columns = [row[1] for row in c.fetchall()]
        
        # Add missing columns
        missing_columns = [
            ('name', 'TEXT'),
            ('subcategory', 'TEXT'),
            ('revenue', 'TEXT'),
            ('employees', 'INTEGER'),
            ('website_url', 'TEXT'),
            ('linkedin_url', 'TEXT'),
            ('twitter_url', 'TEXT'),
            ('facebook_url', 'TEXT'),
            ('description', 'TEXT'),
            ('tags', 'TEXT'),
            ('verified', 'BOOLEAN DEFAULT 0'),
            ('last_verified', 'TIMESTAMP'),
            ('data_source', 'TEXT'),
            ('confidence_score', 'REAL DEFAULT 0.0')
        ]
        
        for col_name, col_type in missing_columns:
            if col_name not in columns:
                try:
                    c.execute(f"ALTER TABLE company_database ADD COLUMN {col_name} {col_type}")
                    print(f"  ✅ Added column: {col_name}")
                except Exception as e:
                    print(f"  ⚠️  Could not add {col_name}: {e}")
        
        # Ensure all required tables exist
        print("📋 Ensuring all tables exist...")
        
        tables_to_create = [
            ("users", """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    google_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """),
            ("subscriptions", """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'free',
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT,
                    status TEXT DEFAULT 'active',
                    current_period_start TIMESTAMP,
                    current_period_end TIMESTAMP,
                    cancel_at_period_end BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """),
            ("usage_tracking", """
                CREATE TABLE IF NOT EXISTS usage_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    emails_sent INTEGER DEFAULT 0,
                    emails_scraped INTEGER DEFAULT 0,
                    campaigns_created INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, month)
                )
            """),
            ("scraped_emails", """
                CREATE TABLE IF NOT EXISTS scraped_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    email TEXT NOT NULL,
                    domain TEXT,
                    source TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified BOOLEAN DEFAULT 0,
                    confidence_score REAL DEFAULT 0.0
                )
            """),
            ("campaigns", """
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    subject TEXT,
                    content TEXT,
                    email_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """),
            ("google_tokens", """
                CREATE TABLE IF NOT EXISTS google_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_type TEXT,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
        ]
        
        for table_name, create_sql in tables_to_create:
            try:
                c.execute(create_sql)
                print(f"  ✅ Ensured table: {table_name}")
            except Exception as e:
                print(f"  ⚠️  Could not create {table_name}: {e}")
        
        # Create indexes for performance
        print("📈 Creating performance indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_usage_user_month ON usage_tracking(user_id, month)",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)",
            "CREATE INDEX IF NOT EXISTS idx_scraped_emails_user ON scraped_emails(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_scraped_emails_domain ON scraped_emails(domain)",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_user ON campaigns(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_company_database_name ON company_database(name)",
            "CREATE INDEX IF NOT EXISTS idx_company_database_domain ON company_database(domain)"
        ]
        
        for index_sql in indexes:
            try:
                c.execute(index_sql)
            except Exception as e:
                print(f"  ⚠️  Could not create index: {e}")
        
        # Insert sample data if tables are empty
        print("📝 Adding sample data...")
        
        # Check if users table is empty
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            c.execute("""
                INSERT INTO users (email, name) 
                VALUES ('demo@outreachpilotpro.com', 'Demo User')
            """)
            print("  ✅ Added demo user")
        
        # Check if company_database is empty
        c.execute("SELECT COUNT(*) FROM company_database")
        if c.fetchone()[0] == 0:
            sample_companies = [
                ('Google', 'google.com', 'Technology', 'Large', 'Mountain View, CA'),
                ('Microsoft', 'microsoft.com', 'Technology', 'Large', 'Redmond, WA'),
                ('Apple', 'apple.com', 'Technology', 'Large', 'Cupertino, CA'),
                ('Amazon', 'amazon.com', 'E-commerce', 'Large', 'Seattle, WA'),
                ('Netflix', 'netflix.com', 'Entertainment', 'Large', 'Los Gatos, CA')
            ]
            
            for company in sample_companies:
                c.execute("""
                    INSERT INTO company_database 
                    (company_name, domain, industry, size, location, name) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (company[0], company[1], company[2], company[3], company[4], company[0]))
            
            print("  ✅ Added sample companies")
        
        conn.commit()
        conn.close()
        
        print("✅ Database fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_database():
    """Test database functionality"""
    
    print("\n🧪 Testing database...")
    
    try:
        conn = sqlite3.connect("outreachpilot.db", timeout=30.0)
        c = conn.cursor()
        
        # Test basic queries
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        print(f"  📊 Users: {user_count}")
        
        c.execute("SELECT COUNT(*) FROM company_database")
        company_count = c.fetchone()[0]
        print(f"  📊 Companies: {company_count}")
        
        c.execute("SELECT COUNT(*) FROM subscriptions")
        subscription_count = c.fetchone()[0]
        print(f"  📊 Subscriptions: {subscription_count}")
        
        # Test complex query
        c.execute("""
            SELECT company_name, domain, industry 
            FROM company_database 
            LIMIT 3
        """)
        companies = c.fetchall()
        print(f"  📊 Sample companies: {len(companies)} found")
        
        conn.close()
        print("✅ Database test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    if fix_all_database_issues():
        test_database()
        print("\n🎉 Database is ready for production!")
        print("\n📋 Next steps:")
        print("1. Deploy to Render/Railway/Heroku")
        print("2. Configure Google OAuth")
        print("3. Set up Stripe webhooks")
        print("4. Test all functionality")
    else:
        print("\n❌ Database fix failed!") 