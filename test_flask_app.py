#!/usr/bin/env python3
"""
Test Flask app directly
"""

from app_minimal import app

def test_app():
    """Test the Flask app directly"""
    with app.test_client() as client:
        print("🧪 Testing Flask app directly")
        print("=" * 40)
        
        # Test home page
        response = client.get('/')
        print(f"Home page: {response.status_code}")
        
        # Test features page
        response = client.get('/features')
        print(f"Features page: {response.status_code}")
        
        # Test pricing page
        response = client.get('/pricing')
        print(f"Pricing page: {response.status_code}")
        
        # Test about page
        response = client.get('/about')
        print(f"About page: {response.status_code}")
        
        # Test contact page
        response = client.get('/contact')
        print(f"Contact page: {response.status_code}")

if __name__ == "__main__":
    test_app()
