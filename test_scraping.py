#!/usr/bin/env python3
"""
Test script to verify email scraping functionality
"""
import requests
import json

def test_infinite_search_direct():
    """Test the infinite email search directly by calling the method"""
    print("Testing infinite email search directly...")
    
    # Import the database class directly
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from email_database import InfiniteEmailDatabase
    
    # Create database instance
    db = InfiniteEmailDatabase()
    
    # Test the search method directly
    result = db.search_infinite_emails(
        industry='technology',
        location='Minnesota',
        company_size='startup',
        limit=100
    )
    
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Emails found: {len(result.get('emails', []))}")
        print(f"Companies searched: {result.get('companies_searched', 0)}")
        print(f"Sources used: {result.get('sources_used', [])}")
        print(f"First 5 emails: {result.get('emails', [])[:5]}")
    else:
        print(f"Error: {result.get('error')}")

def test_website_scraping():
    """Test the website scraping API"""
    print("\nTesting website scraping...")
    test_url = "https://example.com"
    response = requests.post(
        'http://localhost:8800/api/scrape/website',
        headers={'Content-Type': 'application/json'},
        json={'url': test_url}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        if result.get('success'):
            print(f"Emails found: {len(result.get('emails', []))}")
            print(f"Emails: {result.get('emails', [])}")
    
def test_infinite_search():
    """Test the infinite email search API"""
    print("\nTesting infinite email search...")
    test_data = {
        'industry': 'technology',
        'location': '',
        'company_size': '',
        'limit': 100
    }
    response = requests.post(
        'http://localhost:8800/api/search/infinite',
        headers={'Content-Type': 'application/json'},
        json=test_data
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        if result.get('success'):
            print(f"Emails found: {len(result.get('emails', []))}")
            print(f"Sources used: {result.get('sources_used', [])}")

if __name__ == "__main__":
    print("Starting scraping tests...")
    try:
        # Test the database directly first
        test_infinite_search_direct()
        
        # Then test the API endpoints
        test_website_scraping()
        test_infinite_search()
    except Exception as e:
        print(f"Error during testing: {e}")
    print("\nTests completed!") 