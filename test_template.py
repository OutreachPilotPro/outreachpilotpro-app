from app_minimal import app

# Test if the routes are registered
print("Testing route registration...")
with app.app_context():
    routes = [rule.rule for rule in app.url_map.iter_rules() if 'gdpr' in rule.rule or 'anti-spam' in rule.rule]
    print("Found routes:", routes)

# Test if the functions exist
print("\nTesting function existence...")
try:
    from app_minimal import gdpr, anti_spam
    print("Functions imported successfully")
except ImportError as e:
    print("Import error:", e)
