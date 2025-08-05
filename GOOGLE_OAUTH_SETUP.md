# Google OAuth Setup for outreachpilotpro.com

## 🔧 Fix Google OAuth "Blocked" Issue

The "blocked" error occurs because Google OAuth needs to be properly configured for your domain. Here's how to fix it:

### Step 1: Google Cloud Console Setup

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create/Select Project**
   - Create a new project or select existing one
   - Project name: `OutreachPilotPro`

3. **Enable Google+ API**
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it
   - Search for "Gmail API" and enable it

### Step 2: Configure OAuth Consent Screen

1. **Go to OAuth Consent Screen**
   - Navigate to "APIs & Services" > "OAuth consent screen"

2. **Choose User Type**
   - Select "External" (if you want anyone to use it)
   - Or "Internal" (if only your organization)

3. **Fill in App Information**
   ```
   App name: OutreachPilotPro
   User support email: your-email@outreachpilotpro.com
   App logo: Upload your logo
   App domain: outreachpilotpro.com
   Developer contact information: your-email@outreachpilotpro.com
   ```

4. **Add Scopes**
   - Click "Add or Remove Scopes"
   - Add these scopes:
     - `openid`
     - `email`
     - `profile`
     - `https://www.googleapis.com/auth/gmail.send`

5. **Add Test Users** (if External)
   - Add your email and any test users
   - These users can test before publishing

### Step 3: Create OAuth 2.0 Credentials

1. **Go to Credentials**
   - Navigate to "APIs & Services" > "Credentials"

2. **Create OAuth 2.0 Client ID**
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Application type: "Web application"

3. **Configure Client**
   ```
   Name: OutreachPilotPro Web Client
   
   Authorized JavaScript origins:
   - https://outreachpilotpro.com
   - http://localhost:8800 (for development)
   
   Authorized redirect URIs:
   - https://outreachpilotpro.com/login/google/authorize
   - https://outreachpilotpro.com/oauth2callback
   - http://localhost:8800/login/google/authorize (for development)
   ```

4. **Save Credentials**
   - Copy the Client ID and Client Secret
   - You'll need these for your .env file

### Step 4: Update Environment Variables

1. **Create .env file**
   ```bash
   cp .env.template .env
   ```

2. **Add Google OAuth credentials**
   ```env
   # Google OAuth (for outreachpilotpro.com)
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   
   # Production settings
   FLASK_ENV=production
   BASE_URL=https://outreachpilotpro.com
   ```

### Step 5: Domain Verification

1. **Verify Domain Ownership**
   - Go to "APIs & Services" > "OAuth consent screen"
   - Click "Add domain" under "Authorized domains"
   - Add: `outreachpilotpro.com`
   - Follow verification steps (usually adding a DNS record)

2. **SSL Certificate**
   - Ensure your domain has SSL (https://)
   - Google OAuth requires HTTPS in production

### Step 6: Test OAuth

1. **Local Testing**
   ```bash
   # Test locally first
   python3 app_production.py
   ```

2. **Production Testing**
   - Deploy to your hosting provider
   - Test with your domain: https://outreachpilotpro.com

### Step 7: Publish App (Optional)

1. **Submit for Verification**
   - Go to "OAuth consent screen"
   - Click "Submit for verification"
   - This allows any user to use your app

2. **Or Keep in Testing**
   - Add specific users as test users
   - They can use the app without verification

## 🔧 Troubleshooting

### "Blocked" Error Solutions

1. **Check Authorized Domains**
   - Ensure `outreachpilotpro.com` is in authorized domains
   - Verify domain ownership

2. **Check Redirect URIs**
   - Must exactly match: `https://outreachpilotpro.com/login/google/authorize`
   - No trailing slashes or typos

3. **Check JavaScript Origins**
   - Must include: `https://outreachpilotpro.com`
   - Protocol must match (http vs https)

4. **Test User Access**
   - If app is in testing, user must be added as test user
   - Or publish the app for public access

### Common Issues

1. **"redirect_uri_mismatch"**
   - Check redirect URIs in Google Console
   - Must match exactly what your app sends

2. **"access_denied"**
   - User denied permission
   - Check OAuth consent screen settings

3. **"invalid_client"**
   - Check Client ID and Secret
   - Ensure they're correct in .env file

## 🚀 Production Deployment

### Environment Variables for Production

```env
# Production Environment
FLASK_ENV=production
BASE_URL=https://outreachpilotpro.com

# Google OAuth
GOOGLE_CLIENT_ID=your-production-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-production-client-secret

# Security
SECRET_KEY=your-super-secret-production-key

# Stripe (Live Keys)
STRIPE_SECRET_KEY=sk_live_your_live_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_live_webhook_secret
```

### Deployment Checklist

- [ ] Google OAuth configured for outreachpilotpro.com
- [ ] SSL certificate installed
- [ ] Environment variables set
- [ ] Database configured
- [ ] Stripe webhooks configured
- [ ] Test OAuth login
- [ ] Test all features

## 📞 Support

If you still have issues:

1. Check Google Cloud Console error logs
2. Verify all URLs and credentials
3. Test with a different browser/incognito mode
4. Check browser console for JavaScript errors

The key is ensuring your domain `outreachpilotpro.com` is properly configured in Google Cloud Console and your redirect URIs match exactly. 