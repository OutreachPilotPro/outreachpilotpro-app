# Stripe Integration Guide for OutreachPilotPro

This guide will help you set up and configure the Stripe payment integration for your OutreachPilotPro application.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.7+
- A Stripe account (get one at [stripe.com](https://stripe.com))
- Your Stripe API keys

### 2. Environment Setup

Create a `.env` file in your project root with the following variables:

```env
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret_here
```

### 3. Install Dependencies

```bash
pip install stripe python-dotenv
```

### 4. Run Setup Scripts

```bash
# Quick check
python3 setup_stripe_integration.py

# Complete setup (creates products, prices, and updates configuration)
python3 complete_stripe_setup.py

# Test the integration
python3 complete_stripe_setup.py test
```

## 📋 Detailed Setup Steps

### Step 1: Get Your Stripe API Keys

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Copy your **Secret key** (starts with `sk_test_` for test mode)
3. Add it to your `.env` file as `STRIPE_SECRET_KEY`

### Step 2: Create Products and Prices

The setup script will automatically create these subscription plans:

- **Starter Plan**: $49/month
  - 5,000 emails/month
  - 2,000 email searches
  - 10 campaigns
  - Email verification

- **Professional Plan**: $149/month
  - 50,000 emails/month
  - 20,000 email searches
  - 50 campaigns
  - API access
  - Priority support

- **Enterprise Plan**: $499/month
  - 500,000 emails/month
  - 100,000 email searches
  - Unlimited campaigns
  - Dedicated IP
  - White label option

### Step 3: Configure Webhooks

1. Go to [Stripe Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Set the endpoint URL:
   - **Development**: `http://localhost:8800/webhook/stripe`
   - **Production**: `https://yourdomain.com/webhook/stripe`
4. Select these events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the signing secret and add it to `.env` as `STRIPE_WEBHOOK_SECRET`

### Step 4: Test the Integration

```bash
# Test the complete setup
python3 complete_stripe_setup.py test

# Start your application
python3 app.py
```

Visit `http://localhost:8800/subscription` to see the subscription page.

## 🔧 Configuration Files

### subscription_manager.py
Contains the subscription logic and plan definitions. The setup script will automatically update the Stripe price IDs in this file.

### app.py
Contains the Flask routes for:
- `/subscription` - Subscription management page
- `/subscription/upgrade/<plan_id>` - Upgrade to a plan
- `/subscription/success` - Handle successful payments
- `/webhook/stripe` - Process Stripe webhooks

### templates/subscription.html
The subscription page template with:
- Current plan display
- Usage tracking
- Plan comparison
- Upgrade buttons

## 🧪 Testing

### Test Cards
Use these test card numbers in Stripe's test mode:

- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **Requires Authentication**: `4000 0025 0000 3155`

### Test Scenarios
1. **New Subscription**: Go to subscription page → Select a plan → Complete payment
2. **Upgrade**: Change from one plan to another
3. **Cancel**: Cancel an active subscription
4. **Webhook Testing**: Use Stripe CLI to test webhooks locally

## 🚨 Troubleshooting

### Common Issues

1. **"Invalid API key"**
   - Check your `STRIPE_SECRET_KEY` in `.env`
   - Ensure you're using the correct key (test vs live)

2. **"Webhook signature verification failed"**
   - Verify your `STRIPE_WEBHOOK_SECRET` is correct
   - Check that the webhook URL is accessible

3. **"No products found"**
   - Run `python3 complete_stripe_setup.py` to create products
   - Check your Stripe dashboard for products

4. **"Database error"**
   - Ensure the database file exists and is writable
   - Run the setup script to create required tables

### Debug Mode

Enable debug logging by adding to your `.env`:

```env
FLASK_DEBUG=1
STRIPE_LOG_LEVEL=debug
```

### Stripe CLI (Optional)

Install Stripe CLI for local webhook testing:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login to your account
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8800/webhook/stripe
```

## 📊 Monitoring

### Stripe Dashboard
Monitor your integration in the Stripe Dashboard:
- [Payments](https://dashboard.stripe.com/payments)
- [Subscriptions](https://dashboard.stripe.com/subscriptions)
- [Webhooks](https://dashboard.stripe.com/webhooks)
- [Logs](https://dashboard.stripe.com/logs)

### Application Logs
Check your application logs for:
- Webhook processing errors
- Subscription creation/updates
- Payment failures

## 🔒 Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for all sensitive data
3. **Verify webhook signatures** (already implemented)
4. **Use HTTPS** in production
5. **Test thoroughly** before going live

## 🚀 Production Deployment

1. **Switch to live keys** in your `.env`:
   ```env
   STRIPE_SECRET_KEY=sk_live_your_live_key
   STRIPE_WEBHOOK_SECRET=whsec_your_live_webhook_secret
   ```

2. **Update webhook URL** to your production domain

3. **Test with real cards** (small amounts)

4. **Monitor closely** for the first few days

## 📞 Support

If you encounter issues:

1. Check the [Stripe Documentation](https://stripe.com/docs)
2. Review the application logs
3. Test with Stripe's test mode first
4. Contact support with specific error messages

---

**Note**: This integration is designed for the OutreachPilotPro application. Make sure you have the latest version of all dependencies and follow the setup steps in order. 