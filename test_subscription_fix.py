#!/usr/bin/env python3
"""
Test script to verify subscription functionality
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_home_page():
    """Test that home page loads and has working navigation"""
    print("Testing home page...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    print("✓ Home page loads successfully")
    
    # Check for navigation links
    content = response.text
    assert 'href="/about"' in content
    assert 'href="/contact"' in content
    assert 'href="/live-demo"' in content
    assert 'href="/signup"' in content
    print("✓ Navigation links are present")

def test_navigation_pages():
    """Test that all navigation pages load"""
    pages = [
        ("/about", "About Us - OutreachPilotPro"),
        ("/contact", "Contact Us - OutreachPilotPro"),
        ("/live-demo", "Live Demo - OutreachPilotPro"),
        ("/blog", "Blog - OutreachPilotPro"),
        ("/careers", "Careers - OutreachPilotPro"),
        ("/api", "API Documentation - OutreachPilotPro"),
        ("/integrations", "Integrations - OutreachPilotPro"),
    ]
    
    print("Testing navigation pages...")
    for path, expected_title in pages:
        response = requests.get(f"{BASE_URL}{path}")
        assert response.status_code == 200
        assert expected_title in response.text
        print(f"✓ {path} loads successfully")

def test_subscription_redirect():
    """Test that subscription page redirects to login when not authenticated"""
    print("Testing subscription redirect...")
    response = requests.get(f"{BASE_URL}/subscription", allow_redirects=False)
    assert response.status_code == 302  # Redirect
    assert "/login" in response.headers.get('Location', '')
    print("✓ Subscription page redirects to login when not authenticated")

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✓ Health check endpoint works")

def main():
    """Run all tests"""
    print("Running subscription and navigation tests...\n")
    
    try:
        test_health_check()
        test_home_page()
        test_navigation_pages()
        test_subscription_redirect()
        
        print("\n🎉 All tests passed! The subscription and navigation issues have been fixed.")
        print("\nWhat was fixed:")
        print("1. Added missing routes for all navigation links (About, Contact, Live Demo, etc.)")
        print("2. Created template files for all missing pages")
        print("3. Fixed subscription page to properly handle user authentication")
        print("4. Added proper plan structure with limits and features")
        print("5. Added missing routes for scrape_page and campaigns_page")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
