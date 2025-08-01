# 🚀 Stripe Integration Setup Guide

This guide will help you set up Stripe payments for OutreachPilotPro.

## 📋 Prerequisites

1. **Stripe Account**: Sign up at https://stripe.com
2. **Domain**: Your app must be accessible via HTTPS (outreachpilotpro.com)

## 🔑 Step 1: Get Your Stripe API Keys

1. **Go to Stripe Dashboard**: https://dashboard.stripe.com/
2. **Navigate to Developers → API Keys**
3. **Copy your keys**:
   - **Publishable Key** (starts with `pk_`)
   - **Secret Key** (starts with `sk_`)

## 🔧 Step 2: Add Keys to Environment Variables

Add these to your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

## 🛠️ Step 3: Create Stripe Products and Prices

### Option A: Use the Setup Script (Recommended)

1. **Run the setup script**:
   ```bash
   python3 setup_stripe.py
   ```

2. **Follow the instructions** to create products and prices

### Option B: Manual Setup

1. **Go to Products** in Stripe Dashboard
2. **Create 3 products**:

#### Starter Plan ($49/month)
- **Name**: Starter Plan
- **Description**: Perfect for small businesses and startups
- **Price**: $49.00/month
- **Price ID**: `price_starter_monthly`

#### Professional Plan ($149/month)
- **Name**: Professional Plan
- **Description**: For growing businesses and teams
- **Price**: $149.00/month
- **Price ID**: `price_professional_monthly`

#### Enterprise Plan ($499/month)
- **Name**: Enterprise Plan
- **Description**: For large organizations with unlimited needs
- **Price**: $499.00/month
- **Price ID**: `price_enterprise_monthly`

## 🌐 Step 4: Create Webhook Endpoint

1. **Go to Webhooks** in Stripe Dashboard: https://dashboard.stripe.com/webhooks
2. **Click "Add endpoint"**
3. **Enter endpoint URL**: `https://outreachpilotpro.com/webhook/stripe`
4. **Select events to listen for**:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. **Copy the webhook signing secret**
6. **Add to your `.env` file**:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
   ```

## 🔄 Step 5: Update Your App Configuration

The app is already configured to use these environment variables. Make sure your `.env` file has:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

## 🧪 Step 6: Test the Integration

1. **Deploy your app** with the new environment variables
2. **Go to your app**: https://outreachpilotpro.com
3. **Navigate to Subscription page**
4. **Try upgrading to a paid plan**
5. **Use Stripe test card**: `4242 4242 4242 4242`

## 🔍 Step 7: Monitor Webhooks

1. **Check webhook logs** in Stripe Dashboard
2. **Monitor your app logs** for webhook processing
3. **Test subscription lifecycle**:
   - Create subscription
   - Update subscription
   - Cancel subscription

## 🚨 Troubleshooting

### Common Issues:

1. **"Invalid API key"**
   - Check your `STRIPE_SECRET_KEY` is correct
   - Make sure you're using the right environment (test/live)

2. **"Webhook signature verification failed"**
   - Verify `STRIPE_WEBHOOK_SECRET` is correct
   - Check webhook endpoint URL is accessible

3. **"Price not found"**
   - Ensure price IDs match between Stripe and your code
   - Check price IDs in `subscription_manager.py`

4. **"Domain not allowed"**
   - Add your domain to Stripe Dashboard → Settings → Checkout
   - For testing: add `localhost:8800` and your production domain

### Test Cards:

- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **Requires Authentication**: `4000 0025 0000 3155`

## 📊 Going Live

When ready to accept real payments:

1. **Switch to Live Mode** in Stripe Dashboard
2. **Update environment variables** with live keys
3. **Update webhook endpoint** to use live webhook secret
4. **Test with real payment methods**

## 🎯 Next Steps

After setup:

1. **Customize checkout pages** in Stripe Dashboard
2. **Set up email receipts**
3. **Configure tax rates** if needed
4. **Set up subscription management** for customers

## 📞 Support

- **Stripe Documentation**: https://stripe.com/docs
- **Stripe Support**: https://support.stripe.com
- **App Issues**: Check your app logs and webhook events 