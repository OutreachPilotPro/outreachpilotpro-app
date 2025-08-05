# OutreachPilotPro Production Deployment Guide

## 🚀 Deploy to outreachpilotpro.com

### 1. Domain Setup
- Point outreachpilotpro.com to your hosting provider
- Set up SSL certificate (required for Google OAuth)

### 2. Google OAuth Configuration
1. Go to https://console.cloud.google.com/
2. Create/select your project
3. Go to "APIs & Services" > "Credentials"
4. Edit your OAuth 2.0 Client ID
5. Add authorized redirect URIs:
   - https://outreachpilotpro.com/login/google/authorize
   - https://outreachpilotpro.com/oauth2callback
6. Add authorized JavaScript origins:
   - https://outreachpilotpro.com

### 3. Environment Variables
Copy .env.template to .env and fill in:
- Google OAuth credentials
- Stripe live keys
- Email configuration
- Secret key

### 4. Database Setup
- Ensure database is properly configured
- Run: python3 fix_database_issues.py

### 5. Webhook Configuration
- Go to Stripe Dashboard > Webhooks
- Add endpoint: https://outreachpilotpro.com/webhook/stripe
- Select events: checkout.session.completed, customer.subscription.updated, etc.

### 6. Deployment Options

#### Option A: VPS/Server
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=production

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Option B: Heroku
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku create outreachpilotpro
git push heroku main
```

#### Option C: Railway/Render
- Connect your GitHub repository
- Set environment variables
- Deploy automatically

### 7. Testing
- Test Google OAuth login
- Test Stripe payments
- Test email functionality
- Test all features

### 8. Monitoring
- Set up error monitoring (Sentry)
- Set up uptime monitoring
- Monitor Stripe webhooks
- Monitor email delivery

## 🔧 Troubleshooting

### Google OAuth Issues
- Ensure redirect URIs are correct
- Check domain verification
- Verify OAuth consent screen

### Stripe Issues
- Use live keys in production
- Configure webhooks properly
- Test with real cards

### Database Issues
- Run database fix script
- Check connection strings
- Monitor database performance
