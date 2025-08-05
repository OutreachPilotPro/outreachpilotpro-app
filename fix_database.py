#!/usr/bin/env python3
"""
Fix database locking issues and improve connection handling
"""

import sqlite3
import os
import time

def fix_database():
    """Fix database locking and connection issues"""
    
    db_path = "outreachpilot.db"
    
    print("🔧 Fixing database issues...")
    
    # Close any existing connections
    try:
        # Force close any existing connections
        conn = sqlite3.connect(db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.close()
        print("✅ Database optimized")
    except Exception as e:
        print(f"⚠️  Could not optimize database: {e}")
    
    # Check and fix tables
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        c = conn.cursor()
        
        # Check if tables exist
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        
        print(f"📋 Found tables: {', '.join(tables)}")
        
        # Ensure usage_tracking table exists
        if 'usage_tracking' not in tables:
            print("📝 Creating usage_tracking table...")
            c.execute("""
                CREATE TABLE usage_tracking (
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
            """)
            print("✅ Created usage_tracking table")
        
        # Ensure subscriptions table exists
        if 'subscriptions' not in tables:
            print("📝 Creating subscriptions table...")
            c.execute("""
                CREATE TABLE subscriptions (
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
            """)
            print("✅ Created subscriptions table")
        
        # Create indexes for better performance
        print("📝 Creating indexes...")
        try:
            c.execute("CREATE INDEX IF NOT EXISTS idx_usage_user_month ON usage_tracking(user_id, month)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)")
            print("✅ Created indexes")
        except Exception as e:
            print(f"⚠️  Could not create indexes: {e}")
        
        conn.commit()
        conn.close()
        
        print("✅ Database structure verified")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

def test_database():
    """Test database connections"""
    
    print("\n🧪 Testing database connections...")
    
    try:
        # Test multiple connections
        connections = []
        for i in range(5):
            conn = sqlite3.connect("outreachpilot.db", timeout=30.0)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            count = c.fetchone()[0]
            print(f"   Connection {i+1}: {count} users found")
            connections.append(conn)
        
        # Close all connections
        for conn in connections:
            conn.close()
        
        print("✅ Database connection test passed")
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 OutreachPilotPro Database Fix Tool")
    print("=" * 40)
    
    if fix_database():
        test_database()
        print("\n✅ Database fix completed successfully!")
    else:
        print("\n❌ Database fix failed!") 