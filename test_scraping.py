#!/usr/bin/env python3
"""Test script for email scraping functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.email_finder import EmailFinder

def test_scraping():
    """Test the email scraper"""
    print("🧪 Testing Email Scraper...")
    
    scraper = EmailFinder()
    
    # Test with a real website that should have contact info
    test_url = "https://github.com"
    print(f"Testing with: {test_url}")
    
    try:
        emails = scraper.scrape_website_emails(test_url)
        print(f"✅ Found {len(emails)} emails: {emails}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with another site
    test_url2 = "https://stackoverflow.com"
    print(f"\nTesting with: {test_url2}")
    
    try:
        emails2 = scraper.scrape_website_emails(test_url2)
        print(f"✅ Found {len(emails2)} emails: {emails2}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraping() 