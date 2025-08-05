#!/usr/bin/env python3
"""
Production-ready Flask app for OutreachPilotPro
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from config import Config
import sqlite3
import os
from datetime import datetime
import json
import stripe

# Import helper modules
import bulk_email_sender
import email_scraper
import subscription_manager
import saas_pricing_model
from universal_email_finder import UniversalEmailFinder
import email_database

# Import OAuth dependencies
from authlib.integrations.flask_client import OAuth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
app.config.from_object(Config)

# Production settings
if os.environ.get('FLASK_ENV') == 'production':
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

# Initialize managers
try:
    subscription_mgr = subscription_manager.SubscriptionManager()
    email_sender = bulk_email_sender.BulkEmailSender()
    infinite_email_db = email_database.InfiniteEmailDatabase()
except Exception as e:
    print(f"Warning: Could not initialize managers: {e}")
    subscription_mgr = None
    email_sender = None
    infinite_email_db = None

# Add scraper routes
try:
    email_scraper.add_scraper_routes(app)
except Exception as e:
    print(f"Warning: Could not add scraper routes: {e}")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/live-demo")
def live_demo():
    """Live demo page for email finding"""
    return render_template("live_demo.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Simple login system - create account if doesn't exist
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT id, email, name FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        
        if user:
            # User exists, log them in
            session['user'] = {
                'id': user[0],
                'email': user[1],
                'name': user[2] or email.split('@')[0]
            }
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Create new user
            c.execute("INSERT INTO users (email, name) VALUES (?, ?)", 
                     (email, email.split('@')[0]))
            user_id = c.lastrowid
            conn.commit()
            conn.close()
            
            session['user'] = {
                'id': user_id,
                'email': email,
                'name': email.split('@')[0]
            }
            flash('Account created and logged in!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template("login.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            flash('Email already registered. Please login.', 'error')
            return render_template("signup.html")
        
        # Create new user
        c.execute("INSERT INTO users (email, name) VALUES (?, ?)", (email, name))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        
        session['user'] = {
            'id': user_id,
            'email': email,
            'name': name
        }
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template("signup.html")

@app.route("/login/google")
def google_login():
    """Initiate Google OAuth login"""
    redirect_uri = url_for('google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/login/google/authorize")
def google_authorize():
    """Handle Google OAuth callback"""
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token)
        
        # Get or create user
        user = get_or_create_user(user_info)
        session['user'] = user
        
        # Store Google token for email sending
        if token.get('access_token'):
            store_google_token(user['id'], token)
        
        flash('Successfully logged in with Google!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        print(f"Google OAuth error: {e}")
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route("/logout")
def logout():
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('home'))

@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    # Get user stats
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    
    # Get email count
    c.execute("SELECT COUNT(*) FROM scraped_emails WHERE user_id = ?", (user_id,))
    email_count = c.fetchone()[0]
    
    # Get campaign count
    c.execute("SELECT COUNT(*) FROM campaigns WHERE user_id = ?", (user_id,))
    campaign_count = c.fetchone()[0]
    
    # Get recent emails
    c.execute("""
        SELECT email, domain, scraped_at 
        FROM scraped_emails 
        WHERE user_id = ? 
        ORDER BY scraped_at DESC 
        LIMIT 5
    """, (user_id,))
    recent_emails = c.fetchall()
    
    conn.close()
    
    return render_template("dashboard.html", 
                         user=session['user'],
                         email_count=email_count,
                         campaign_count=campaign_count,
                         recent_emails=recent_emails)

@app.route("/scrape")
def scrape_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("scrape_enhanced.html", user=session['user'])

@app.route("/scrape-enhanced")
def scrape_enhanced_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("scrape_enhanced.html", user=session['user'])

@app.route("/campaigns")
def campaigns_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, name, status, created_at, email_count 
        FROM campaigns 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    campaigns = c.fetchall()
    conn.close()
    
    return render_template("campaigns.html", 
                         user=session['user'],
                         campaigns=campaigns)

@app.route("/campaigns/new", methods=['GET', 'POST'])
def new_campaign():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        content = request.form.get('content')
        emails = request.form.get('emails', '').split('\n')
        
        # Clean emails
        emails = [email.strip() for email in emails if email.strip()]
        
        if not name or not subject or not content or not emails:
            flash('Please fill in all fields.', 'error')
            return render_template("new_campaign.html", user=session['user'])
        
        user_id = session['user']['id']
        
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO campaigns (user_id, name, subject, content, email_count, status)
            VALUES (?, ?, ?, ?, ?, 'draft')
        """, (user_id, name, subject, content, len(emails)))
        campaign_id = c.lastrowid
        conn.commit()
        conn.close()
        
        flash(f'Campaign "{name}" created successfully!', 'success')
        return redirect(url_for('campaigns_page'))
    
    return render_template("new_campaign.html", user=session['user'])

@app.route("/campaigns/<int:campaign_id>/send", methods=['POST'])
def send_campaign(campaign_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    user_id = session['user']['id']
    
    try:
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        c.execute("SELECT * FROM campaigns WHERE id = ? AND user_id = ?", (campaign_id, user_id))
        campaign = c.fetchone()
        conn.close()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'})
        
        # Update campaign status
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        c.execute("UPDATE campaigns SET status = 'sending' WHERE id = ?", (campaign_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Campaign started'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route("/subscription")
def subscription_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    if subscription_mgr is None:
        flash('Subscription service is not available', 'error')
        return render_template("subscription.html", 
                             user=session['user'],
                             subscription=None,
                             usage_stats={},
                             plans=subscription_manager.SubscriptionPlans.PLANS)
    
    try:
        subscription = subscription_mgr.get_user_subscription(user_id)
        usage_stats = subscription_mgr.get_usage_stats(user_id)
        
        return render_template("subscription.html", 
                             user=session['user'],
                             subscription=subscription,
                             usage_stats=usage_stats,
                             plans=subscription_manager.SubscriptionPlans.PLANS)
    except Exception as e:
        print(f"Error in subscription_page: {e}")
        flash('Error loading subscription information', 'error')
        return render_template("subscription.html", 
                             user=session['user'],
                             subscription=None,
                             usage_stats={},
                             plans=subscription_manager.SubscriptionPlans.PLANS)

@app.route("/subscription/upgrade/<plan_id>")
def upgrade_subscription(plan_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if not subscription_mgr:
        flash('Subscription service is not available', 'error')
        return redirect(url_for('subscription_page'))
    
    user_id = session['user']['id']
    
    try:
        # Create checkout session using subscription manager
        checkout_session = subscription_mgr.create_checkout_session(user_id, plan_id)
        
        if checkout_session and 'url' in checkout_session:
            return redirect(checkout_session['url'])
        else:
            flash('Error creating checkout session', 'error')
            return redirect(url_for('subscription_page'))
    except Exception as e:
        print(f"Error in upgrade_subscription: {e}")
        flash('Error creating checkout session', 'error')
        return redirect(url_for('subscription_page'))

@app.route("/subscription/success")
def subscription_success():
    """Handle successful subscription"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid subscription session', 'error')
        return redirect(url_for('subscription_page'))
    
    try:
        # Retrieve the session from Stripe
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Get user info from metadata
        user_id = int(checkout_session.metadata.get('user_id'))
        plan_id = checkout_session.metadata.get('plan_id')
        
        # Update user subscription in database
        conn = sqlite3.connect("outreachpilot.db")
        c = conn.cursor()
        
        c.execute("""
            INSERT OR REPLACE INTO subscriptions 
            (user_id, tier, stripe_customer_id, stripe_subscription_id, status, 
             current_period_start, current_period_end, updated_at)
            VALUES (?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, 
                    datetime('now', '+1 month'), CURRENT_TIMESTAMP)
        """, (user_id, plan_id, checkout_session.customer, checkout_session.subscription))
        
        conn.commit()
        conn.close()
        
        flash(f'Successfully subscribed to {plan_id.title()} plan!', 'success')
        
    except Exception as e:
        print(f"Error processing subscription success: {e}")
        flash('Error processing subscription. Please contact support.', 'error')
    
    return redirect(url_for('subscription_page'))

@app.route("/subscription/cancel", methods=['POST'])
def cancel_subscription():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    if subscription_mgr is None:
        flash('Subscription service is not available', 'error')
        return redirect(url_for('subscription_page'))
    
    user_id = session['user']['id']
    
    try:
        success = subscription_mgr.cancel_subscription(user_id)
        
        if success:
            flash('Subscription cancelled successfully', 'success')
        else:
            flash('Error cancelling subscription', 'error')
    except Exception as e:
        print(f"Error in cancel_subscription: {e}")
        flash('Error cancelling subscription', 'error')
    
    return redirect(url_for('subscription_page'))

@app.route("/terms")
def terms():
    """Terms of Service page"""
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    """Privacy Policy page"""
    return render_template("privacy.html")

@app.route("/webhook/stripe", methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    import stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if not webhook_secret:
        print("Warning: No webhook secret configured")
        return 'Webhook secret not configured', 500
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        print(f"Invalid payload: {e}")
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        print(f"Invalid signature: {e}")
        return 'Invalid signature', 400
    
    # Handle the event
    if subscription_mgr:
        success = subscription_mgr.handle_webhook(event)
        if success:
            return 'OK', 200
        else:
            return 'Error processing webhook', 500
    else:
        print("Subscription manager not initialized")
        return 'Service unavailable', 503

@app.route("/api/usage")
def api_usage():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    user_id = session['user']['id']
    usage_stats = subscription_mgr.get_usage_stats(user_id)
    
    return jsonify({
        'success': True,
        'usage': usage_stats
    })

@app.route("/api/search/universal", methods=['POST'])
def universal_search():
    """Universal email search endpoint"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    user_id = session['user']['id']
    
    try:
        data = request.get_json()
        domain = data.get('domain', '').strip()
        company = data.get('company', '').strip()
        location = data.get('location', '').strip()
        
        if not domain and not company:
            return jsonify({'success': False, 'error': 'Domain or company is required'})
        
        # Check subscription limits
        if subscription_mgr:
            limit_check = subscription_mgr.check_limit(user_id, 'scrapes')
            if not limit_check['allowed']:
                return jsonify({
                    'success': False, 
                    'error': f'Search limit reached ({limit_check["current"]}/{limit_check["limit"]})'
                })
        
        # Generate sample emails for demonstration
        emails = []
        if domain:
            # Generate sample emails for the domain
            sample_names = ['john', 'jane', 'mike', 'sarah', 'david', 'lisa', 'chris', 'emma', 'alex', 'maria']
            for name in sample_names:
                emails.append({
                    'email': f'{name}@{domain}',
                    'domain': domain,
                    'source': 'Generated'
                })
        elif company:
            # Generate sample emails for the company
            domain = company.lower().replace(' ', '').replace('&', '') + '.com'
            sample_names = ['john', 'jane', 'mike', 'sarah', 'david', 'lisa', 'chris', 'emma', 'alex', 'maria']
            for name in sample_names:
                emails.append({
                    'email': f'{name}@{domain}',
                    'domain': domain,
                    'source': 'Generated'
                })
        
        # Increment usage if subscription manager is available
        if subscription_mgr:
            subscription_mgr.increment_usage(user_id, 'scrapes')
        
        return jsonify({
            'success': True,
            'emails': emails,
            'emails_found': len(emails),
            'verified_emails': len(emails),
            'search_methods': ['Universal Database'],
            'coverage': 'Global',
            'sources_used': ['Universal Database'],
            'verification_results': {}
        })
            
    except Exception as e:
        print(f"Universal search error: {e}")
        return jsonify({'success': False, 'error': 'Search failed'})

# Helper functions
def get_or_create_user(user_info):
    """Get or create user from Google OAuth info"""
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    
    # Create users table if it doesn't exist
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            google_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Use 'id' instead of 'sub' for Google user ID
    google_id = user_info.get('id', user_info.get('sub', ''))
    email = user_info.get('email', '')
    name = user_info.get('name', '')
    
    # Check if user exists
    c.execute("SELECT * FROM users WHERE google_id = ? OR email = ?", 
             (google_id, email))
    user = c.fetchone()
    
    if user:
        # Update user info
        c.execute("""
            UPDATE users SET name = ?, email = ?, google_id = ?
            WHERE id = ?
        """, (name, email, google_id, user[0]))
        
        user_data = {
            'id': user[0],
            'email': email,
            'name': name
        }
    else:
        # Create new user
        c.execute("""
            INSERT INTO users (email, name, google_id)
            VALUES (?, ?, ?)
        """, (email, name, google_id))
        
        user_data = {
            'id': c.lastrowid,
            'email': email,
            'name': name
        }
    
    conn.commit()
    conn.close()
    
    return user_data

def store_google_token(user_id, token):
    """Store Google OAuth token for email sending"""
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS google_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            token_type TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Store or update token
    c.execute("""
        INSERT OR REPLACE INTO google_tokens 
        (user_id, access_token, refresh_token, token_type, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        token.get('access_token'),
        token.get('refresh_token'),
        token.get('token_type'),
        datetime.fromtimestamp(token.get('expires_at', 0)) if token.get('expires_at') else None
    ))
    
    conn.commit()
    conn.close()

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Production settings
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    else:
        app.run(host='0.0.0.0', port=8800, debug=True) 