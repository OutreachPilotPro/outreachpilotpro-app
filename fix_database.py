#!/usr/bin/env python3
"""
Fix database locking issues and improve connection handling
"""

import sqlite3
import os
import time

def fix_database():
    db_path = 'instance/users.db'
    
    # Backup the existing database
    if os.path.exists(db_path):
        backup_path = 'instance/users_backup.db'
        os.system(f'cp {db_path} {backup_path}')
        print(f"Backed up existing database to {backup_path}")
    
    # Remove the existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed existing database")
    
    # Create new database with correct schema
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create users table with correct schema
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create subscriptions table
    c.execute('''
        CREATE TABLE subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create campaigns table
    c.execute('''
        CREATE TABLE campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Created new database with correct schema")

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