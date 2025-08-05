#!/bin/bash

# OutreachPilotPro Production Deployment Script
# This script helps deploy your app to production

echo "🚀 OutreachPilotPro Production Deployment"
echo "=========================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file from .env.template and fill in your credentials"
    exit 1
fi

# Check if database is ready
echo "🔧 Checking database..."
python3 fix_database_issues.py

# Check if all required files exist
echo "📋 Checking required files..."
required_files=(
    "app_production.py"
    "config.py"
    "subscription_manager.py"
    "templates/"
    "static/"
)

for file in "${required_files[@]}"; do
    if [ ! -e "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All required files found"

# Check environment variables
echo "🔍 Checking environment variables..."
source .env

required_vars=(
    "GOOGLE_CLIENT_ID"
    "GOOGLE_CLIENT_SECRET"
    "SECRET_KEY"
    "BASE_URL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing environment variable: $var"
        exit 1
    fi
done

echo "✅ Environment variables configured"

# Install production dependencies
echo "📦 Installing production dependencies..."
pip install gunicorn
pip install -r requirements.txt

# Create production configuration
echo "⚙️  Creating production configuration..."

# Create Procfile for Heroku/Railway
cat > Procfile << EOF
web: gunicorn app_production:app --bind 0.0.0.0:\$PORT --workers 4 --timeout 120
EOF

# Create runtime.txt for Python version
cat > runtime.txt << EOF
python-3.9.18
EOF

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Environment variables
.env
.env.local

# Database
*.db
*.sqlite3

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Logs
*.log

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
EOF
fi

echo "✅ Production configuration created"

# Test the application
echo "🧪 Testing application..."
export FLASK_ENV=production
python3 -c "
import app_production
print('✅ Application imports successfully')
"

if [ $? -eq 0 ]; then
    echo "✅ Application test passed"
else
    echo "❌ Application test failed"
    exit 1
fi

echo ""
echo "🎉 Deployment preparation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Deploy to your hosting provider:"
echo "   - Heroku: git push heroku main"
echo "   - Railway: Connect GitHub repository"
echo "   - VPS: Upload files and run with gunicorn"
echo ""
echo "2. Set environment variables on your hosting platform"
echo ""
echo "3. Configure domain: outreachpilotpro.com"
echo ""
echo "4. Test all features:"
echo "   - Google OAuth login"
echo "   - Email search"
echo "   - Subscription system"
echo "   - Campaign creation"
echo ""
echo "📚 See DEPLOYMENT_GUIDE.md for detailed instructions"
echo "🔧 See GOOGLE_OAUTH_SETUP.md for OAuth configuration" 