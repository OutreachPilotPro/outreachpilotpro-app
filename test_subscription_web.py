#!/usr/bin/env python3
"""
Web test for subscription functionality
"""

import requests
import sqlite3
import time

def create_test_user():
    """Create a test user in the database"""
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    
    # Create test user
    c.execute("""
        INSERT OR REPLACE INTO users (id, email, name) 
        VALUES (999, 'test@outreachpilotpro.com', 'Test User')
    """)
    
    conn.commit()
    conn.close()
    print("✅ Test user created")

def test_subscription_page():
    """Test the subscription page functionality"""
    
    print("🌐 Testing Subscription Web Interface")
    print("=" * 40)
    
    # Create test user
    create_test_user()
    
    # Test subscription page
    try:
        response = requests.get('http://localhost:8800/subscription', timeout=10)
        print(f"📊 Subscription page status: {response.status_code}")
        
        if response.status_code == 302:
            print("   ✅ Redirecting to login (expected)")
        elif response.status_code == 200:
            print("   ✅ Subscription page loaded")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error accessing subscription page: {e}")
    
    # Test login page
    try:
        response = requests.get('http://localhost:8800/login', timeout=10)
        print(f"📊 Login page status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Login page loaded")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error accessing login page: {e}")
    
    # Test home page
    try:
        response = requests.get('http://localhost:8800/', timeout=10)
        print(f"📊 Home page status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Home page loaded")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error accessing home page: {e}")

def test_api_endpoints():
    """Test API endpoints"""
    
    print("\n🔌 Testing API Endpoints")
    print("=" * 30)
    
    # Test usage API
    try:
        response = requests.get('http://localhost:8800/api/usage', timeout=10)
        print(f"📊 Usage API status: {response.status_code}")
        
        if response.status_code == 302:
            print("   ✅ Redirecting to login (expected)")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error accessing usage API: {e}")
    
    # Test universal search API
    try:
        response = requests.post('http://localhost:8800/api/search/universal', 
                               json={'domain': 'test.com'}, 
                               timeout=10)
        print(f"📊 Universal search API status: {response.status_code}")
        
        if response.status_code == 302:
            print("   ✅ Redirecting to login (expected)")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error accessing universal search API: {e}")

if __name__ == "__main__":
    print("🚀 OutreachPilotPro Web Test")
    print("=" * 50)
    
    # Wait for app to start
    print("⏳ Waiting for app to start...")
    time.sleep(3)
    
    # Test web interface
    test_subscription_page()
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n🎉 Web test completed!")
    print("\n📋 To test subscription functionality:")
    print("1. Visit: http://localhost:8800")
    print("2. Click 'Login' or 'Sign Up'")
    print("3. Create an account or login")
    print("4. Navigate to 'Subscription' page")
    print("5. Test the subscription features") 