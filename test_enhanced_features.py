#!/usr/bin/env python3
"""
Quick test script to verify enhanced features are working
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_home_page():
    """Test the home page loads"""
    print("🏠 Testing home page...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200 and "OutreachPilotPro" in response.text:
            print("✅ Home page loads correctly")
            return True
        else:
            print(f"❌ Home page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Home page error: {e}")
        return False

def test_subscription_redirect():
    """Test subscription page redirects to login when not authenticated"""
    print("🔒 Testing subscription redirect...")
    try:
        response = requests.get(f"{BASE_URL}/subscription", allow_redirects=False)
        if response.status_code == 302 and "/login" in response.headers.get('Location', ''):
            print("✅ Subscription redirects to login correctly")
            return True
        else:
            print(f"❌ Subscription redirect failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Subscription redirect error: {e}")
        return False

def test_favicon():
    """Test favicon is accessible"""
    print("🎨 Testing favicon...")
    try:
        response = requests.get(f"{BASE_URL}/static/favicon.svg")
        if response.status_code == 200 and "svg" in response.text:
            print("✅ Favicon is accessible")
            return True
        else:
            print(f"❌ Favicon failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Favicon error: {e}")
        return False

def test_enhanced_routes():
    """Test enhanced routes are working"""
    print("🛣️  Testing enhanced routes...")
    routes = [
        "/features",
        "/pricing", 
        "/about",
        "/contact",
        "/live-demo"
    ]
    
    working_routes = 0
    for route in routes:
        try:
            response = requests.get(f"{BASE_URL}{route}")
            if response.status_code == 200:
                working_routes += 1
                print(f"✅ {route} - OK")
            else:
                print(f"❌ {route} - {response.status_code}")
        except Exception as e:
            print(f"❌ {route} - Error: {e}")
    
    print(f"📊 Routes working: {working_routes}/{len(routes)}")
    return working_routes == len(routes)

def main():
    """Run all tests"""
    print("🧪 Testing Enhanced OutreachPilotPro Features")
    print("=" * 50)
    
    tests = [
        test_health_endpoint,
        test_home_page,
        test_subscription_redirect,
        test_favicon,
        test_enhanced_routes
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Your enhanced features are working perfectly!")
        print("\n🚀 Next steps:")
        print("1. Visit http://localhost:5001")
        print("2. Login with test@example.com / password123")
        print("3. Test the subscription flow")
        print("4. Try the enhanced email search")
    else:
        print("⚠️  Some tests failed. Please check the server logs.")
    
    print("\n🔗 Your enhanced OutreachPilotPro is running at:")
    print(f"   http://localhost:5001")

if __name__ == "__main__":
    main()
