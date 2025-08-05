# Environment Variables for OutreachPilotPro Deployment

## 🚀 **Required for Minimal Deployment (Start Here)**

These are the **minimum required** environment variables to get your app running:

```bash
# Flask Configuration
SECRET_KEY=your_super_secret_key_here_make_it_long_and_random
FLASK_ENV=production

# Python Version (Render will set this automatically)
PYTHON_VERSION=3.11.0
```

## 🔧 **Optional but Recommended**

```bash
# App Configuration
BASE_URL=https://your-app-name.onrender.com
DEBUG=False
```

## 💳 **For Stripe Integration (Add Later)**

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_51Rqmq7LeRd30DB0ZUMfZIGCZ
STRIPE_PUBLISHABLE_KEY=pk_live_51Rqmq7LeRd30DB0ZUMfZIGCZ
STRIPE_WEBHOOK_SECRET=whsec_dnAVwr0SDIyUDj5vR5JAzxX6Lqgp4WM9
```

## 🔐 **For Google OAuth (Add Later)**

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

## 📋 **How to Set Environment Variables in Render**

### **Option 1: Through Render Dashboard**
1. Go to your service in Render
2. Click "Environment" tab
3. Click "Add Environment Variable"
4. Add each variable one by one

### **Option 2: Through render.yaml (Automatic)**
The `render.yaml` file will automatically set some variables:

```yaml
envVars:
  - key: SECRET_KEY
    generateValue: true  # Render generates this automatically
  - key: FLASK_ENV
    value: production
  - key: PYTHON_VERSION
    value: 3.11.0
```

## 🎯 **For Initial Deployment (Minimal Setup)**

**Start with just these 2 variables:**

| Variable | Value | Purpose |
|----------|-------|---------|
| `SECRET_KEY` | `your_super_secret_key_here_make_it_long_and_random` | Flask session security |
| `FLASK_ENV` | `production` | Production environment |

## 🔑 **Generate a Good SECRET_KEY**

You can generate a secure secret key using Python:

```python
import secrets
print(secrets.token_hex(32))
```

Or use this one (replace with your own):
```
SECRET_KEY=8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92
```

## 📝 **Step-by-Step Setup**

1. **Deploy with minimal variables first**
2. **Test the basic functionality**
3. **Add Stripe variables** when ready for payments
4. **Add Google OAuth** when ready for email features

## ⚠️ **Important Notes**

- **Never commit secrets to Git**
- **Use different keys for development and production**
- **Keep your Stripe keys secure**
- **Test with minimal setup first**

## 🚀 **Quick Start Commands**

```bash
# Generate a secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Test locally with environment variables
export SECRET_KEY="your_secret_key_here"
export FLASK_ENV="production"
python3 app_minimal.py
``` 