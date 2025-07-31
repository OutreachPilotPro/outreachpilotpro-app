#!/bin/bash

echo "🚀 Deploying OutreachPilotPro to Railway..."

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please run: railway login"
    exit 1
fi

# Initialize Railway project if not already done
if [ ! -f ".railway" ]; then
    echo "📦 Initializing Railway project..."
    railway init
fi

# Deploy the app
echo "🚀 Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo "🌐 Your app should be live at: https://your-app-name.railway.app"
echo "📊 View logs with: railway logs" 