# 🚀 Deployment Guide for OutreachPilotPro

## Option 1: Deploy to Render (Recommended - Free)

1. **Go to [render.com](https://render.com)** and sign up/login
2. **Connect your GitHub** account
3. **Create a new Web Service**
4. **Connect your repository** (you'll need to push this to GitHub first)
5. **Configure the service:**
   - **Name**: outreachpilotpro
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. **Deploy!**

## Option 2: Deploy to Heroku

1. **Install Heroku CLI:**
   ```bash
   brew install heroku/brew/heroku
   ```

2. **Login and deploy:**
   ```bash
   heroku login
   heroku create outreachpilotpro
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

## Option 3: Deploy to Google Cloud (Requires Billing)

1. **Set up billing** in Google Cloud Console
2. **Deploy to App Engine:**
   ```bash
   gcloud app deploy
   ```

## Option 4: Deploy to Railway (Limited Plan)

1. **Upgrade your Railway plan** or use the free tier
2. **Deploy:**
   ```bash
   railway up
   ```

## Environment Variables Needed

Make sure to set these environment variables in your deployment platform:

- `SECRET_KEY` - Your Flask secret key
- `GOOGLE_CLIENT_ID` - Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Your Google OAuth client secret
- `STRIPE_SECRET_KEY` - Your Stripe secret key (optional)
- `STRIPE_PUBLISHABLE_KEY` - Your Stripe publishable key (optional)

## After Deployment

1. **Update Google OAuth redirect URIs** to include your new domain
2. **Test the app** at your new URL
3. **Set up your domain** (outreachpilotpro.com) to point to your deployed app

## Quick GitHub Push (if needed)

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/outreachpilotpro.git
git push -u origin main
``` 