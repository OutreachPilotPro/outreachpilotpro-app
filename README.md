# OutreachPilotPro 🚀

A comprehensive email scraping and bulk sending SaaS platform for business outreach automation.

## 🌟 Features

### Email Discovery
- **Website Scraping**: Automatically find emails from any website
- **Company Search**: Search for company emails using multiple sources
- **Email Verification**: Real-time DNS MX record verification
- **Pattern Recognition**: Generate potential emails based on common patterns

### Email Campaigns
- **Bulk Sending**: Send up to 500K emails/month on enterprise plan
- **Personalization**: Dynamic variables and smart templates
- **Scheduling**: Schedule campaigns for optimal delivery times
- **Tracking**: Monitor opens, clicks, and responses
- **Rate Limiting**: Prevent abuse and ensure deliverability

### Subscription Management
- **Multiple Tiers**: Free, Starter ($49), Professional ($149), Enterprise ($499)
- **Usage Tracking**: Monitor email sends, scrapes, and campaigns
- **Stripe Integration**: Secure payment processing
- **Automatic Billing**: Recurring subscriptions with webhooks

### User Experience
- **Google OAuth**: One-click login with Gmail integration
- **Modern UI**: Beautiful, responsive design
- **Real-time Analytics**: Live dashboard with usage statistics
- **API Access**: Full REST API for integrations

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Google OAuth 2.0
- **Email**: Gmail API + SMTP
- **Payments**: Stripe
- **Caching**: Redis
- **Web Scraping**: BeautifulSoup + Requests
- **Frontend**: HTML5, CSS3, JavaScript

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Redis (optional, for rate limiting)
- Google Cloud Console account
- Stripe account (for payments)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd outreachpilotpro
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```

3. **Configure environment variables**
   ```bash
   # Edit .env file with your credentials
   nano .env
   ```

4. **Start the application**
   ```bash
   python app.py
   ```

5. **Visit the application**
   ```
   http://localhost:5000
   ```

### Manual Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create database**
   ```bash
   python -c "from subscription_manager import SubscriptionManager; SubscriptionManager()._init_database()"
   ```

3. **Set up Google OAuth**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs:
     - `http://localhost:5000/login/google/authorize` (development)
     - `https://outreachpilotpro.com/login/google/authorize` (production)

4. **Set up Stripe** (optional)
   - Create a Stripe account
   - Get your API keys
   - Set up webhook endpoints
   - Create subscription products

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database Configuration
DATABASE_URL=sqlite:///outreachpilot.db

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Stripe Configuration
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

### Subscription Plans

The platform comes with 4 subscription tiers:

| Plan | Price | Emails/Month | Searches/Month | Campaigns | Features |
|------|-------|--------------|----------------|-----------|----------|
| Free | $0 | 100 | 50 | 1 | Basic features |
| Starter | $49 | 5,000 | 2,000 | 10 | Email verification |
| Professional | $149 | 50,000 | 20,000 | 50 | API access, A/B testing |
| Enterprise | $499 | 500,000 | 100,000 | Unlimited | Dedicated IP, white label |

## 🚀 Usage

### 1. Sign Up
- Visit the landing page
- Click "Start Free Trial"
- Sign in with Google OAuth

### 2. Find Emails
- Go to "Find Emails" page
- Enter a website URL or company name
- View and save found emails

### 3. Create Campaigns
- Go to "Campaigns" page
- Click "New Campaign"
- Write your email content
- Add recipients
- Schedule and send

### 4. Monitor Results
- Check dashboard for analytics
- View campaign performance
- Track email opens and clicks

## 🔧 API Endpoints

### Authentication
- `POST /login/google` - Google OAuth login
- `GET /logout` - Logout user

### Email Scraping
- `POST /api/scrape/website` - Scrape emails from website
- `POST /api/scrape/company` - Search company emails
- `GET /api/scraped-emails` - Get user's scraped emails

### Campaigns
- `GET /campaigns` - List user campaigns
- `POST /campaigns/new` - Create new campaign
- `POST /campaigns/{id}/send` - Send campaign

### Subscriptions
- `GET /subscription` - Get subscription info
- `GET /subscription/upgrade/{plan}` - Upgrade subscription
- `POST /subscription/cancel` - Cancel subscription

### Webhooks
- `POST /webhook/stripe` - Stripe webhook handler

## 🏗️ Project Structure

```
outreachpilotpro/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── setup.py             # Setup script
├── README.md            # This file
├── .env                 # Environment variables (create this)
├── outreachpilot.db     # SQLite database (created automatically)
├── email_scraper.py     # Email scraping functionality
├── bulk_email_sender.py # Email sending system
├── subscription_manager.py # Subscription management
├── saas_pricing_model.py  # Pricing and plans
└── templates/           # HTML templates
    ├── index.html       # Landing page
    ├── login.html       # Login page
    ├── signup.html      # Signup page
    ├── dashboard.html   # User dashboard
    └── scrape.html      # Email scraping page
```

## 🔒 Security & Compliance

### Email Compliance
- **CAN-SPAM Act**: Compliant with US email regulations
- **GDPR**: European data protection compliance
- **Unsubscribe Links**: Automatic unsubscribe functionality
- **Rate Limiting**: Prevents spam and abuse

### Data Protection
- **Encryption**: All sensitive data encrypted
- **OAuth**: Secure authentication via Google
- **HTTPS**: SSL/TLS encryption in production
- **Database Security**: SQL injection protection

### Best Practices
- **Rate Limiting**: Respects website robots.txt
- **User Consent**: Clear privacy policies
- **Opt-out**: Easy unsubscribe mechanisms
- **Monitoring**: Real-time abuse detection

## 🚀 Deployment

### Development
```bash
python app.py
```

### Production (using Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 📊 Monitoring & Analytics

### Built-in Analytics
- Email send rates
- Open and click tracking
- Campaign performance
- User engagement metrics

### Integration Options
- **Google Analytics**: Track website usage
- **Sentry**: Error monitoring
- **LogRocket**: User session recording
- **Custom Webhooks**: Real-time notifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README
- **Issues**: Create a GitHub issue
- **Email**: support@outreachpilotpro.com
- **Discord**: Join our community server

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Email scraping from websites
- ✅ Basic email campaigns
- ✅ Google OAuth integration
- ✅ Subscription management

### Phase 2 (Next)
- 🔄 Advanced email templates
- 🔄 A/B testing
- 🔄 Advanced analytics
- 🔄 API documentation

### Phase 3 (Future)
- 📋 Chrome extension
- 📋 Mobile app
- 📋 AI-powered content generation
- 📋 Advanced targeting

---

**Built with ❤️ for the outreach community** # Updated Thu Jul 31 09:23:26 EDT 2025
# Trigger new deployment Thu Jul 31 13:46:00 EDT 2025
