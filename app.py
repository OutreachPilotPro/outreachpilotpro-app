#!/usr/bin/env python3
"""
OutreachPilotPro - Consolidated Flask App
Single source of truth combining the best features from all app variants
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from config import Config
import psycopg2
from psycopg2.extras import DictCursor
import os
from datetime import datetime
import json
import stripe
import requests
import re
import csv
import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import random

# Import helper modules
import bulk_email_sender
from services.email_finder import EmailFinder
import subscription_manager
import email_database

# Import OAuth dependencies
from authlib.integrations.flask_client import OAuth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
print("🔧 Loading configuration...")
app.config.from_object(Config)
print("✅ Configuration loaded successfully")

# Production security settings
if app.config['FLASK_ENV'] == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Ensure session configuration is set
if not app.config.get('SECRET_KEY') or app.config['SECRET_KEY'] == 'dev-secret-key':
    import secrets
    app.config['SECRET_KEY'] = secrets.token_hex(32)

# Initialize OAuth
oauth = OAuth(app)
try:
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url='https://oauth2.googleapis.com/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v2/',
        client_kwargs={
            'scope': 'openid email profile https://www.googleapis.com/auth/gmail.send'
        }
    )
except Exception as e:
    print(f"Warning: Could not initialize OAuth: {e}")

# Initialize managers with better error handling
subscription_mgr = None
email_sender = None
infinite_email_db = None

try:
    subscription_mgr = subscription_manager.SubscriptionManager()
    print("✅ Subscription manager initialized")
except Exception as e:
    print(f"Warning: Could not initialize subscription manager: {e}")

try:
    email_sender = bulk_email_sender.BulkEmailSender()
    print("✅ Email sender initialized")
except Exception as e:
    print(f"Warning: Could not initialize email sender: {e}")

try:
    # Initialize email database with timeout protection
    infinite_email_db = email_database.InfiniteEmailDatabase()
    print("✅ Infinite email database initialized")
except Exception as e:
    print(f"Warning: Could not initialize infinite email database: {e}")
    infinite_email_db = None

# Enhanced database connection with better error handling
def get_db_connection():
    try:
        conn = psycopg2.connect(app.config['DATABASE_URL'])
        conn.cursor_factory = DictCursor
        return conn
    except Exception as e:
        print(f"FATAL: Database connection failed: {e}")
        raise

# Enhanced database initialization
def init_enhanced_database():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create enhanced users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            subscription_status VARCHAR(50) DEFAULT 'free'
        )
    ''')
    
    # Create enhanced subscriptions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            plan_id VARCHAR(100) NOT NULL,
            status VARCHAR(50) DEFAULT 'active',
            stripe_subscription_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create enhanced campaigns table
    c.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            emails TEXT,
            status VARCHAR(50) DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            open_rate DECIMAL(5,2) DEFAULT 0.0,
            click_rate DECIMAL(5,2) DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create email_usage table for tracking
    c.execute('''
        CREATE TABLE IF NOT EXISTS email_usage (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            emails_found INTEGER DEFAULT 0,
            emails_sent INTEGER DEFAULT 0,
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create email_verification table
    c.execute('''
        CREATE TABLE IF NOT EXISTS email_verification (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            is_valid BOOLEAN DEFAULT FALSE,
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verification_source VARCHAR(100)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize enhanced database
try:
    init_enhanced_database()
except Exception as e:
    print(f"Warning: Could not initialize enhanced database: {e}")

# Initialize consolidated email finder service
email_finder = EmailFinder()

@app.route("/")
def index():
    return render_template("index.html")

# Route aliases removed - using endpoint parameter instead for cleaner code

@app.route("/live-demo", endpoint='live_demo')
def live_demo():
    """Live demo page for email finding"""
    return render_template("live_demo.html")

@app.route("/about", endpoint='about')
def about():
    """About page"""
    return render_template("about.html")

@app.route("/blog", endpoint='blog')
def blog():
    """Blog page"""
    return render_template("blog.html")

@app.route("/careers", endpoint='careers')
def careers():
    """Careers page"""
    return render_template("careers.html")

@app.route("/contact", endpoint='contact')
def contact():
    """Contact page"""
    return render_template("contact.html")

@app.route("/api", endpoint='api_docs')
def api_docs():
    """API documentation page"""
    return render_template("api.html")

@app.route("/integrations", endpoint='integrations')
def integrations():
    """Integrations page"""
    return render_template("integrations.html")

@app.route("/features", endpoint='features')
def features():
    """Features page"""
    return render_template("features.html")

@app.route("/pricing", endpoint='pricing')
def pricing():
    """Pricing page"""
    return render_template("pricing.html")

@app.route("/gdpr", endpoint='gdpr')
def gdpr():
    """GDPR compliance page"""
    return render_template("gdpr.html")

@app.route("/anti-spam", endpoint='anti_spam')
def anti_spam():
    """Anti-spam policy page"""
    return render_template("anti_spam.html")

@app.route("/login", methods=['GET', 'POST'], endpoint='login')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Enhanced login system with password support
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT id, email, name, password_hash FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        
        if user:
            user_id, user_email, user_name, password_hash = user
            
            # If password_hash exists, verify password
            if password_hash:
                from werkzeug.security import check_password_hash
                if check_password_hash(password_hash, password):
                    session['user'] = {
                        'id': user_id,
                        'email': user_email,
                        'name': user_name
                    }
                    conn.close()
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid password', 'error')
                    conn.close()
                    return render_template("login.html")
            else:
                # Legacy user without password, log them in
                session['user'] = {
                    'id': user_id,
                    'email': user_email,
                    'name': user_name
                }
                conn.close()
                return redirect(url_for('dashboard'))
        else:
            # Create new user with password
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(password) if password else None
            
            c.execute("INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)", 
                     (email, email.split('@')[0], password_hash))
            user_id = c.lastrowid
            conn.commit()
            conn.close()
            
            session['user'] = {
                'id': user_id,
                'email': email,
                'name': email.split('@')[0]
            }
            return redirect(url_for('dashboard'))
    
    return render_template("login.html")

@app.route("/signup", methods=['GET', 'POST'], endpoint='signup')
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name', email.split('@')[0])
        
        if not password:
            flash('Password is required', 'error')
            return render_template("signup.html")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if user already exists
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            flash('User already exists', 'error')
            conn.close()
            return render_template("signup.html")
        
        # Create new user
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash(password)
        
        c.execute("INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)", 
                 (email, name, password_hash))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        
        session['user'] = {
            'id': user_id,
            'email': email,
            'name': name
        }
        return redirect(url_for('dashboard'))
    
    return render_template("signup.html")

@app.route("/login/google", endpoint='google_login')
def google_login():
    """Google OAuth login"""
    redirect_uri = url_for('google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/login/google/authorize", endpoint='google_authorize')
def google_authorize():
    """Google OAuth callback"""
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token)
        
        user = get_or_create_user(user_info)
        session['user'] = user
        
        # Store Google token for Gmail access
        if 'access_token' in token:
            store_google_token(user['id'], token['access_token'])
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Google OAuth error: {e}")
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route("/logout", endpoint='logout')
def logout():
    """Logout user"""
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route("/dashboard", endpoint='dashboard')
def dashboard():
    """User dashboard"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    # Get user subscription and usage stats
    subscription = subscription_mgr.get_user_subscription(user_id)
    usage_stats = subscription_mgr.get_usage_stats(user_id)  # THIS LINE IS CRUCIAL
    
    # Get user stats
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get campaigns count
    c.execute("SELECT COUNT(*) FROM campaigns WHERE user_id = ?", (user_id,))
    campaigns_count = c.fetchone()[0]
    
    # Get emails found today
    c.execute("SELECT SUM(emails_found) FROM email_usage WHERE user_id = ? AND date = DATE('now')", (user_id,))
    emails_today = c.fetchone()[0] or 0
    
    # Get total emails found
    c.execute("SELECT SUM(emails_found) FROM email_usage WHERE user_id = ?", (user_id,))
    total_emails = c.fetchone()[0] or 0
    
    # Get recent campaigns for display
    c.execute("SELECT id, name, status, created_at FROM campaigns WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (user_id,))
    recent_campaigns = c.fetchall()
    
    # Get recent email activity
    c.execute("SELECT date, emails_found FROM email_usage WHERE user_id = ? ORDER BY date DESC LIMIT 7", (user_id,))
    recent_emails = c.fetchall()
    
    conn.close()
    
    return render_template("dashboard.html", 
                         user=session['user'],
                         subscription=subscription,
                         usage_stats=usage_stats,  # MAKE SURE THIS IS PASSED
                         campaigns_count=campaigns_count,
                         emails_today=emails_today,
                         total_emails=total_emails,
                         recent_campaigns=recent_campaigns,
                         recent_emails=recent_emails)

@app.route("/scrape", endpoint='scrape_page')
def scrape_page():
    """Email scraping page"""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("scrape.html")

@app.route("/scrape-enhanced", endpoint='scrape_enhanced_page')
def scrape_enhanced_page():
    """Enhanced email scraping page"""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("scrape_enhanced.html")

@app.route("/campaigns", endpoint='campaigns_page')
def campaigns_page():
    """Campaigns management page"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT id, name, status, created_at, emails FROM campaigns WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    campaigns = c.fetchall()
    
    conn.close()
    
    return render_template("campaigns.html", campaigns=campaigns)

@app.route("/campaigns/new", methods=['GET', 'POST'], endpoint='new_campaign')
def new_campaign():
    """Create new campaign"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        emails = request.form.get('emails')
        
        if not name or not emails:
            flash('Campaign name and emails are required', 'error')
            return render_template("new_campaign.html")
        
        user_id = session['user']['id']
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("INSERT INTO campaigns (user_id, name, emails, status) VALUES (?, ?, ?, ?)", 
                 (user_id, name, emails, 'draft'))
        campaign_id = c.lastrowid
        
        # Update email usage
        email_count = len([e for e in emails.split('\n') if e.strip()])
        c.execute("INSERT OR REPLACE INTO email_usage (user_id, emails_found, date) VALUES (?, ?, DATE('now'))", 
                 (email_count, user_id))
        
        conn.commit()
        conn.close()
        
        flash('Campaign created successfully!', 'success')
        return redirect(url_for('campaigns_page'))
    
    return render_template("new_campaign.html")

@app.route("/campaigns/<int:campaign_id>/send", methods=['POST'], endpoint='send_campaign')
def send_campaign(campaign_id):
    """Send campaign emails"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    
    # Verify campaign ownership
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name, emails FROM campaigns WHERE id = ? AND user_id = ?", (campaign_id, user_id))
    campaign = c.fetchone()
    
    if not campaign:
        conn.close()
        return jsonify({'error': 'Campaign not found'}), 404
    
    campaign_name, emails_text = campaign
    
    # Update campaign status
    c.execute("UPDATE campaigns SET status = 'sent', sent_at = DATETIME('now') WHERE id = ?", (campaign_id,))
    conn.commit()
    conn.close()
    
    # Send emails (simplified - in production you'd use proper email service)
    email_list = [e.strip() for e in emails_text.split('\n') if e.strip()]
    
    # Update email usage
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE email_usage SET emails_sent = emails_sent + ? WHERE user_id = ? AND date = DATE('now')", 
             (len(email_list), user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'emails_sent': len(email_list)})

@app.route("/subscription", endpoint='subscription_page')
def subscription_page():
    """Subscription management page"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    # Get current subscription
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT s.plan_id, s.status, s.stripe_subscription_id FROM subscriptions s WHERE s.user_id = ? AND s.status = 'active' ORDER BY s.created_at DESC LIMIT 1", (user_id,))
    subscription = c.fetchone()
    
    # Get available plans
    plans = [
        {'id': 'free', 'name': 'Free', 'price': 0, 'emails_per_month': 100, 'features': ['Basic email scraping', 'Simple campaigns']},
        {'id': 'starter', 'name': 'Starter', 'price': 29, 'emails_per_month': 1000, 'features': ['Advanced scraping', 'Campaign management', 'Email verification']},
        {'id': 'professional', 'name': 'Professional', 'price': 99, 'emails_per_month': 10000, 'features': ['Unlimited scraping', 'Advanced analytics', 'Priority support']},
        {'id': 'enterprise', 'name': 'Enterprise', 'price': 299, 'emails_per_month': 100000, 'features': ['Custom integrations', 'Dedicated support', 'SLA guarantee']}
    ]
    
    conn.close()
    
    return render_template("subscription.html", 
                         subscription=subscription,
                         plans=plans,
                         stripe_public_key=app.config.get('STRIPE_PUBLISHABLE_KEY'))

@app.route("/subscription/upgrade/<plan_id>", endpoint='upgrade_subscription')
def upgrade_subscription(plan_id):
    """Upgrade subscription page"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get plan details
    plans = {
        'basic': {'name': 'Basic', 'price': 29, 'stripe_price_id': 'price_basic'},
        'pro': {'name': 'Pro', 'price': 79, 'stripe_price_id': 'price_pro'},
        'enterprise': {'name': 'Enterprise', 'price': 199, 'stripe_price_id': 'price_enterprise'}
    }
    
    if plan_id not in plans:
        return redirect(url_for('subscription_page'))
    
    plan = plans[plan_id]
    return render_template("subscription_upgrade.html", plan=plan)

@app.route("/subscription/create-checkout-session", methods=['POST'], endpoint='create_checkout_session')
def create_checkout_session():
    """Create Stripe checkout session"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    plan_id = data.get('plan_id')
    
    if not plan_id:
        return jsonify({'error': 'Plan ID required'}), 400
    
    # Get plan details
    plans = {
        'basic': {'name': 'Basic', 'price': 29, 'stripe_price_id': 'price_basic'},
        'pro': {'name': 'Pro', 'price': 79, 'stripe_price_id': 'price_pro'},
        'enterprise': {'name': 'Enterprise', 'price': 199, 'stripe_price_id': 'price_enterprise'}
    }
    
    if plan_id not in plans:
        return jsonify({'error': 'Invalid plan ID'}), 400
    
    plan = plans[plan_id]
    user_id = session['user']['id']
    
    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': plan['stripe_price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'subscription/success',
            cancel_url=request.host_url + 'subscription',
            client_reference_id=str(user_id),
            metadata={'plan_id': plan_id}
        )
        
        return jsonify({'session_id': checkout_session.id})
        
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return jsonify({'error': 'Error creating checkout session'}), 500

@app.route("/subscription/success", endpoint='subscription_success')
def subscription_success():
    """Subscription success page"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    return render_template("subscription_success.html")

@app.route("/subscription/cancel", methods=['POST'], endpoint='cancel_subscription')
def cancel_subscription():
    """Cancel subscription"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    
    try:
        # Get subscription ID
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT stripe_subscription_id FROM subscriptions WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1", (user_id,))
        subscription = c.fetchone()
        
        if subscription and subscription[0]:
            # Cancel in Stripe
            stripe.Subscription.modify(
                subscription[0],
                cancel_at_period_end=True
            )
            
            # Update local database
            c.execute("UPDATE subscriptions SET status = 'cancelled' WHERE user_id = ? AND status = 'active'", (user_id,))
            conn.commit()
            
            conn.close()
            return jsonify({'success': True, 'message': 'Subscription cancelled successfully'})
        else:
            conn.close()
            return jsonify({'error': 'No active subscription found'}), 404
            
    except Exception as e:
        print(f"Error cancelling subscription: {e}")
        return jsonify({'error': 'Error cancelling subscription'}), 500

@app.route("/terms", endpoint='terms')
def terms():
    """Terms of service page"""
    return render_template("terms.html")

@app.route("/privacy", endpoint='privacy')
def privacy():
    """Privacy policy page"""
    return render_template("privacy.html")

@app.route("/webhook/stripe", methods=['POST'], endpoint='stripe_webhook')
def stripe_webhook():
    """Stripe webhook handler"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, app.config.get('STRIPE_WEBHOOK_SECRET', '')
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = int(session['client_reference_id'])
        plan_id = session['metadata']['plan_id']
        
        # Create subscription record
        conn = get_db_connection()
        c = conn.cursor()
        
        # Cancel any existing active subscriptions
        c.execute("UPDATE subscriptions SET status = 'cancelled' WHERE user_id = ? AND status = 'active'", (user_id,))
        
        # Create new subscription
        c.execute("INSERT INTO subscriptions (user_id, plan_id, status, stripe_subscription_id) VALUES (?, ?, 'active', ?)", 
                 (user_id, plan_id, session['subscription']))
        
        conn.commit()
        conn.close()
        
        return 'Success', 200
    
    return 'Success', 200

@app.route("/api/usage", endpoint='api_usage')
def api_usage():
    """Get user usage statistics"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get today's usage
    c.execute("SELECT emails_found, emails_sent FROM email_usage WHERE user_id = ? AND date = DATE('now')", (user_id,))
    today_usage = c.fetchone() or (0, 0)
    
    # Get monthly usage
    c.execute("SELECT SUM(emails_found), SUM(emails_sent) FROM email_usage WHERE user_id = ? AND date >= DATE('now', 'start of month')", (user_id,))
    monthly_usage = c.fetchone() or (0, 0)
    
    # Get total usage
    c.execute("SELECT SUM(emails_found), SUM(emails_sent) FROM email_usage WHERE user_id = ?", (user_id,))
    total_usage = c.fetchone() or (0, 0)
    
    conn.close()
    
    return jsonify({
        'today': {'found': today_usage[0], 'sent': today_usage[1]},
        'month': {'found': monthly_usage[0], 'sent': monthly_usage[1]},
        'total': {'found': total_usage[0], 'sent': total_usage[1]}
    })

@app.route("/api/search/infinite", methods=['POST'], endpoint='search_infinite_emails')
def search_infinite_emails():
    """Infinite email search API"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    industry = data.get('industry')
    location = data.get('location')
    company_size = data.get('company_size')
    limit = data.get('limit', 1000)
    
    if not industry:
        return jsonify({'error': 'Industry is required for infinite search'}), 400
    
    try:
        # Ensure the infinite_email_db is initialized and use it
        if infinite_email_db:
            results = infinite_email_db.search_infinite_emails(
                industry=industry, 
                location=location, 
                company_size=company_size, 
                limit=limit
            )
        else:
            return jsonify({'error': 'Infinite email database not initialized'}), 500

        # Update usage stats
        user_id = session['user']['id']
        email_count = results.get('emails_returned', 0)
        
        if email_count > 0:
            conn = get_db_connection()
            c = conn.cursor()
            # Use INSERT OR IGNORE and UPDATE for safety
            c.execute("INSERT OR IGNORE INTO email_usage (user_id, emails_found, date) VALUES (?, 0, DATE('now'))", (user_id,))
            c.execute("UPDATE email_usage SET emails_found = emails_found + ? WHERE user_id = ? AND date = DATE('now')", 
                     (email_count, user_id))
            conn.commit()
            conn.close()
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error in infinite search: {e}")
        return jsonify({'error': 'Search failed due to a server error'}), 500

@app.route("/api/search/advanced", methods=['POST'], endpoint='advanced_search')
def advanced_search():
    """Advanced email search API"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    query = data.get('query', '')
    filters = data.get('filters', {})
    source = data.get('source', 'all')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        emails = []
        
        if source == 'all' or source == 'google':
            google_emails = email_finder._search_google_emails(query, filters)
            emails.extend(google_emails)
        
        if source == 'all' or source == 'linkedin':
            linkedin_emails = email_finder._search_linkedin_emails(query, filters)
            emails.extend(linkedin_emails)
        
        if source == 'all' or source == 'directories':
            directory_emails = email_finder._search_business_directories(query, filters)
            emails.extend(directory_emails)
        
        if source == 'all' or source == 'social':
            social_emails = email_finder._search_social_media_emails(query, filters)
            emails.extend(social_emails)
        
        if source == 'all' or source == 'github':
            github_emails = email_finder._search_github_emails(query, filters)
            emails.extend(github_emails)
        
        # Remove duplicates
        unique_emails = list(set(emails))
        
        # Update usage
        user_id = session['user']['id']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO email_usage (user_id, emails_found, date) VALUES (?, ?, DATE('now'))", 
                 (user_id, len(unique_emails)))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'emails': unique_emails,
            'count': len(unique_emails),
            'query': query,
            'source': source
        })
        
    except Exception as e:
        print(f"Error in advanced search: {e}")
        return jsonify({'error': 'Search failed'}), 500

@app.route("/api/search/universal", methods=['POST'], endpoint='universal_search')
def universal_search():
    """Universal email search API"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    query = data.get('query', '')
    filters = data.get('filters', {})
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        # Use universal email finder
        finder = EmailFinder()
        results = finder.find_emails_universal(query, filters)
        
        # Update usage
        user_id = session['user']['id']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO email_usage (user_id, emails_found, date) VALUES (?, ?, DATE('now'))", 
                 (user_id, len(results.get('emails', []))))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query
        })
        
    except Exception as e:
        print(f"Error in universal search: {e}")
        return jsonify({'error': 'Search failed'}), 500

@app.route("/api/scrape-website", methods=['POST'], endpoint='scrape_website')
def scrape_website():
    """Scrape emails from a specific website"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        # Use enhanced scraper
        emails = email_finder.scrape_website_emails(url)
        
        # Update usage
        user_id = session['user']['id']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO email_usage (user_id, emails_found, date) VALUES (?, ?, DATE('now'))", 
                 (user_id, len(emails)))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'emails': emails,
            'count': len(emails),
            'url': url
        })
        
    except Exception as e:
        print(f"Error scraping website: {e}")
        return jsonify({'error': 'Scraping failed'}), 500

@app.route("/api/export-emails", methods=['POST'], endpoint='export_emails')
def export_emails():
    """Export emails to CSV"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    emails = data.get('emails', [])
    format_type = data.get('format', 'csv')
    
    if not emails:
        return jsonify({'error': 'No emails to export'}), 400
    
    try:
        if format_type == 'csv':
            # Create CSV content
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Email', 'Source', 'Date'])
            
            for email in emails:
                writer.writerow([email, 'OutreachPilotPro', datetime.now().strftime('%Y-%m-%d')])
            
            csv_content = output.getvalue()
            output.close()
            
            response = make_response(csv_content)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=emails.csv'
            return response
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        print(f"Error exporting emails: {e}")
        return jsonify({'error': 'Export failed'}), 500

@app.route("/api/health", endpoint='api_health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.route("/api/email-search", methods=['POST'], endpoint='email_search')
def email_search():
    """Search for emails based on query and filters"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    query = data.get('query', '')
    search_type = data.get('search_type', 'niche')
    filters = data.get('filters', {})
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        # Use the consolidated email finder service
        email_finder = EmailFinder()
        
        if search_type == 'niche':
            emails = email_finder.search_niche_emails(query, filters)
        else:
            emails = email_finder.search_emails(query, filters)
        
        # Convert to list if it's a set
        if isinstance(emails, set):
            emails = list(emails)
        
        # Format response
        email_list = []
        for email in emails:
            if isinstance(email, str):
                email_list.append({
                    'email': email,
                    'source': 'search',
                    'verified': True
                })
            else:
                email_list.append(email)
        
        return jsonify({
            'success': True,
            'emails': email_list,
            'count': len(email_list),
            'query': query,
            'filters': filters
        })
        
    except Exception as e:
        print(f"Error in email search: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/campaigns/create", methods=['POST'], endpoint='create_campaign')
def create_campaign():
    """Create a new email campaign"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    campaign_name = data.get('name')
    subject_line = data.get('subject')
    email_content = data.get('content')
    sender_name = data.get('sender_name')
    send_delay = data.get('send_delay', 0)
    max_emails_per_hour = data.get('max_emails_per_hour', 100)
    emails = data.get('emails', [])
    
    if not all([campaign_name, subject_line, email_content, sender_name, emails]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Create campaign
        c.execute("""
            INSERT INTO campaigns (user_id, name, subject, content, sender_name, 
                                 send_delay, max_emails_per_hour, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now'))
        """, (session['user']['id'], campaign_name, subject_line, email_content, 
              sender_name, send_delay, max_emails_per_hour, 'draft'))
        
        campaign_id = c.lastrowid
        
        # Add emails to campaign
        for email in emails:
            c.execute("""
                INSERT INTO campaign_emails (campaign_id, email, status)
                VALUES (?, ?, 'pending')
            """, (campaign_id, email))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'message': 'Campaign created successfully'
        })
        
    except Exception as e:
        print(f"Error creating campaign: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/campaigns/<int:campaign_id>/start", methods=['POST'], endpoint='start_campaign')
def start_campaign(campaign_id):
    """Start a campaign"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if campaign belongs to user
        c.execute("SELECT id FROM campaigns WHERE id = ? AND user_id = ?", 
                 (campaign_id, session['user']['id']))
        campaign = c.fetchone()
        
        if not campaign:
            conn.close()
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Update campaign status
        c.execute("UPDATE campaigns SET status = 'active', started_at = DATETIME('now') WHERE id = ?", 
                 (campaign_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Campaign started'})
        
    except Exception as e:
        print(f"Error starting campaign: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/campaigns/<int:campaign_id>/pause", methods=['POST'], endpoint='pause_campaign')
def pause_campaign(campaign_id):
    """Pause a campaign"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if campaign belongs to user
        c.execute("SELECT id FROM campaigns WHERE id = ? AND user_id = ?", 
                 (campaign_id, session['user']['id']))
        campaign = c.fetchone()
        
        if not campaign:
            conn.close()
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Update campaign status
        c.execute("UPDATE campaigns SET status = 'paused' WHERE id = ?", (campaign_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Campaign paused'})
        
    except Exception as e:
        print(f"Error pausing campaign: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/campaigns/<int:campaign_id>/resume", methods=['POST'], endpoint='resume_campaign')
def resume_campaign(campaign_id):
    """Resume a campaign"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if campaign belongs to user
        c.execute("SELECT id FROM campaigns WHERE id = ? AND user_id = ?", 
                 (campaign_id, session['user']['id']))
        campaign = c.fetchone()
        
        if not campaign:
            conn.close()
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Update campaign status
        c.execute("UPDATE campaigns SET status = 'active' WHERE id = ?", (campaign_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Campaign resumed'})
        
    except Exception as e:
        print(f"Error resuming campaign: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/campaigns/<int:campaign_id>", methods=['DELETE'], endpoint='delete_campaign')
def delete_campaign(campaign_id):
    """Delete a campaign"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if campaign belongs to user
        c.execute("SELECT id FROM campaigns WHERE id = ? AND user_id = ?", 
                 (campaign_id, session['user']['id']))
        campaign = c.fetchone()
        
        if not campaign:
            conn.close()
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Delete campaign emails first
        c.execute("DELETE FROM campaign_emails WHERE campaign_id = ?", (campaign_id,))
        
        # Delete campaign
        c.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Campaign deleted'})
        
    except Exception as e:
        print(f"Error deleting campaign: {e}")
        return jsonify({'error': str(e)}), 500

def get_or_create_user(user_info):
    """Get or create user from Google OAuth info"""
    email = user_info.get('email')
    name = user_info.get('name', email.split('@')[0])
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if user exists
    c.execute("SELECT id, email, name FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    
    if user:
        # Update last login
        c.execute("UPDATE users SET last_login = DATETIME('now') WHERE id = ?", (user[0],))
        conn.commit()
        conn.close()
        
        return {
            'id': user[0],
            'email': user[1],
            'name': user[2]
        }
    else:
        # Create new user
        c.execute("INSERT INTO users (email, name) VALUES (?, ?)", (email, name))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'id': user_id,
            'email': email,
            'name': name
        }

def store_google_token(user_id, token):
    """Store Google OAuth token for Gmail access"""
    # In production, you'd want to encrypt this token
    # For now, we'll just store it in the session
    session['google_token'] = token

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("🚀 Starting OutreachPilotPro application...")
    app.run(debug=True)

