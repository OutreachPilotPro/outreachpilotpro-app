#!/bin/bash

echo "🚀 Deploying OutreachPilotPro Minimal App..."

# Ensure we're using the minimal configuration
echo "📋 Using minimal configuration:"
echo "   - App: app_minimal.py"
echo "   - Requirements: requirements_minimal.txt"
echo "   - Procfile: web: gunicorn app_minimal:app"

# Check if files exist
if [ ! -f "app_minimal.py" ]; then
    echo "❌ Error: app_minimal.py not found!"
    exit 1
fi

if [ ! -f "requirements_minimal.txt" ]; then
    echo "❌ Error: requirements_minimal.txt not found!"
    exit 1
fi

if [ ! -f "Procfile" ]; then
    echo "❌ Error: Procfile not found!"
    exit 1
fi

# Verify Procfile content
PROCFILE_CONTENT=$(cat Procfile)
if [[ "$PROCFILE_CONTENT" != "web: gunicorn app_minimal:app" ]]; then
    echo "❌ Error: Procfile should contain 'web: gunicorn app_minimal:app'"
    echo "   Current content: $PROCFILE_CONTENT"
    exit 1
fi

echo "✅ All files verified!"

# Commit and push
echo "📤 Committing and pushing to GitHub..."
git add .
git commit -m "Deploy minimal app - guaranteed to work"
git push origin main

echo "🎉 Deployment pushed to GitHub!"
echo ""
echo "📋 Next steps:"
echo "1. Go to Render.com"
echo "2. Create NEW Web Service"
echo "3. Connect to: OutreachPilotPro/outreachpilotpro-app"
echo "4. Use branch: main"
echo "5. Build Command: pip install -r requirements_minimal.txt"
echo "6. Start Command: gunicorn app_minimal:app"
echo ""
echo "🔗 Or use the render.yaml file for automatic deployment!" 