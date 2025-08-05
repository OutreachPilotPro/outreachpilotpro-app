# Render Deployment Guide for OutreachPilotPro

## 🚀 Deploy to Render (Recommended)

Render is an excellent choice for hosting OutreachPilotPro! It's easy to set up, has automatic deployments, and includes SSL certificates.

### Step 1: Prepare Your Code

1. **Push to GitHub**
   ```bash
   # Initialize git if not already done
   git init
   git add .
   git commit -m "Initial commit for Render deployment"
   
   # Create GitHub repository and push
   git remote add origin https://github.com/yourusername/outreachpilotpro.git
   git push -u origin main
   ```

2. **Ensure these files exist:**
   - `app_production.py` (main Flask app)
   - `requirements.txt` (dependencies)
   - `config.py` (configuration)
   - All template files in `templates/`

### Step 2: Create Render Account

1. Go to https://render.com/
2. Sign up with your GitHub account
3. Connect your GitHub repository

### Step 3: Deploy Web Service

1. **Click "New +" → "Web Service"**
2. **Connect your GitHub repository**
3. **Configure the service:**

   ```
   Name: outreachpilotpro
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app_production:app
   ```

4. **Set Environment Variables:**
   ```
   FLASK_ENV=production
   BASE_URL=https://outreachpilotpro.onrender.com
   SECRET_KEY=your-super-secret-production-key
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   STRIPE_SECRET_KEY=sk_live_your_live_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=whsec_your_live_webhook_secret
   ```

5. **Click "Create Web Service"**

### Step 4: Configure Custom Domain

1. **In your Render dashboard:**
   - Go to your web service
   - Click "Settings" tab
   - Scroll to "Custom Domains"
   - Click "Add Domain"
   - Enter: `outreachpilotpro.com`

2. **Update DNS:**
   - Go to your domain registrar (GoDaddy, Namecheap, etc.)
   - Add CNAME record:
     ```
     Name: @ (or leave blank)
     Value: your-app-name.onrender.com
     ```

3. **SSL Certificate:**
   - Render automatically provides SSL certificates
   - Your site will be available at `https://outreachpilotpro.com`

### Step 5: Update Google OAuth

1. **Go to Google Cloud Console:**
   - https://console.cloud.google.com/
   - Navigate to "APIs & Services" → "Credentials"

2. **Update OAuth 2.0 Client:**
   ```
   Authorized JavaScript origins:
   - https://outreachpilotpro.com
   - https://your-app-name.onrender.com
   
   Authorized redirect URIs:
   - https://outreachpilotpro.com/login/google/authorize
   - https://your-app-name.onrender.com/login/google/authorize
   ```

### Step 6: Configure Stripe Webhooks

1. **Go to Stripe Dashboard:**
   - https://dashboard.stripe.com/webhooks

2. **Add webhook endpoint:**
   ```
   URL: https://outreachpilotpro.com/webhook/stripe
   Events: checkout.session.completed, customer.subscription.updated
   ```

### Step 7: Test Your Deployment

1. **Visit your site:**
   - https://outreachpilotpro.com
   - https://your-app-name.onrender.com

2. **Test features:**
   - [ ] Google OAuth login
   - [ ] Email search functionality
   - [ ] Subscription system
   - [ ] Campaign creation

### Render-Specific Benefits

✅ **Automatic Deployments** - Deploy on every git push
✅ **SSL Certificates** - Free HTTPS for your domain
✅ **Custom Domains** - Easy domain configuration
✅ **Environment Variables** - Secure credential management
✅ **Logs & Monitoring** - Built-in logging and monitoring
✅ **Auto-scaling** - Handles traffic spikes automatically

### Troubleshooting Render Issues

#### Common Issues:

1. **Build Fails:**
   - Check `requirements.txt` has all dependencies
   - Ensure Python version is compatible

2. **App Won't Start:**
   - Check logs in Render dashboard
   - Verify `gunicorn app_production:app` command

3. **Environment Variables:**
   - Double-check all variables are set correctly
   - No spaces around `=` in environment variables

4. **Database Issues:**
   - Render provides persistent disk storage
   - SQLite database will persist between deployments

### Render vs Other Platforms

| Feature | Render | Heroku | Railway | VPS |
|---------|--------|--------|---------|-----|
| Free Tier | ✅ | ❌ | ✅ | ❌ |
| Custom Domain | ✅ | ✅ | ✅ | ✅ |
| SSL Certificate | ✅ | ✅ | ✅ | Manual |
| Auto Deploy | ✅ | ✅ | ✅ | Manual |
| Database | ✅ | ✅ | ✅ | Manual |
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

### Cost Comparison

- **Render Free:** $0/month (with limitations)
- **Render Paid:** $7/month for more resources
- **Heroku:** $7/month minimum
- **Railway:** $5/month minimum
- **VPS:** $5-20/month + setup time

### Final Steps

1. **Monitor your app:**
   - Check Render dashboard for logs
   - Monitor error rates and performance

2. **Set up monitoring:**
   - Consider adding Sentry for error tracking
   - Set up uptime monitoring

3. **Backup strategy:**
   - Render provides automatic backups
   - Consider additional database backups

4. **Scale when needed:**
   - Upgrade Render plan as your app grows
   - Monitor resource usage

## 🎉 You're Live!

Your OutreachPilotPro will be available at:
- **Primary:** https://outreachpilotpro.com
- **Backup:** https://your-app-name.onrender.com

Render is an excellent choice for your project - it's modern, reliable, and developer-friendly! 