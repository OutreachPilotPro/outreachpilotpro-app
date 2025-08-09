#!/usr/bin/env python3
"""
Test script to verify environment variable loading
"""

import os
from dotenv import load_dotenv

print("🔍 Testing Environment Variable Loading")
print("=" * 50)

# Test 1: Check if .env file exists
print("1. Checking .env file existence:")
if os.path.exists('.env'):
    print("   ✅ .env file found")
else:
    print("   ❌ .env file not found")
    exit(1)

# Test 2: Load environment variables
print("\n2. Loading environment variables:")
load_dotenv()
print("   ✅ load_dotenv() called")

# Test 3: Check critical environment variables
print("\n3. Checking critical environment variables:")
critical_vars = [
    'SECRET_KEY',
    'FLASK_ENV',
    'STRIPE_SECRET_KEY',
    'STRIPE_PUBLISHABLE_KEY',
    'GOOGLE_CLIENT_ID',
    'DATABASE_URL'
]

for var in critical_vars:
    value = os.environ.get(var)
    if value:
        # Mask sensitive values
        if 'SECRET' in var or 'KEY' in var:
            masked_value = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
            print(f"   ✅ {var}: {masked_value}")
        else:
            print(f"   ✅ {var}: {value}")
    else:
        print(f"   ❌ {var}: Not set")

# Test 4: Import and test Config class
print("\n4. Testing Config class:")
try:
    from config import Config
    config = Config()
    print("   ✅ Config class loaded successfully")
except Exception as e:
    print(f"   ❌ Error loading Config class: {e}")

# Test 5: Verify specific values
print("\n5. Verifying specific values:")
print(f"   FLASK_ENV: {os.environ.get('FLASK_ENV', 'Not set')}")
print(f"   SECRET_KEY length: {len(os.environ.get('SECRET_KEY', ''))} characters")
print(f"   STRIPE_SECRET_KEY starts with: {os.environ.get('STRIPE_SECRET_KEY', 'Not set')[:8] if os.environ.get('STRIPE_SECRET_KEY') else 'Not set'}")

print("\n" + "=" * 50)
print("🎯 Environment variable verification complete!")
