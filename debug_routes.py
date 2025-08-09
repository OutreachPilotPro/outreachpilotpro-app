#!/usr/bin/env python3
"""
Debug script to check Flask routes
"""

from app_minimal import app

print("🔍 Debugging Flask Routes")
print("=" * 40)

# List all routes
print("📋 All registered routes:")
for rule in app.url_map.iter_rules():
    print(f"  {rule.rule} -> {rule.endpoint}")

print("\n🔍 Checking specific routes:")
routes_to_check = ['/features', '/pricing', '/about', '/contact']

for route in routes_to_check:
    print(f"\n{route}:")
    try:
        # Try to find the rule
        rule = app.url_map.bind('localhost').match(route)
        print(f"  ✅ Route found: {rule}")
    except Exception as e:
        print(f"  ❌ Route not found: {e}")

print("\n🔍 Testing template rendering:")
try:
    with app.test_request_context():
        from flask import render_template
        result = render_template('features.html')
        print("  ✅ features.html template renders successfully")
except Exception as e:
    print(f"  ❌ Template error: {e}")

print("\n🔍 Flask app configuration:")
print(f"  Debug mode: {app.debug}")
print(f"  Secret key set: {bool(app.secret_key)}")
print(f"  Template folder: {app.template_folder}")
