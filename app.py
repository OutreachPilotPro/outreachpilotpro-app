from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from config import Config
import sqlite3
import os
from datetime import datetime
import json

# Import helper modules
import bulk_email_sender
import email_scraper
import subscription_manager
import saas_pricing_model
import email_database

# Import OAuth dependencies
from authlib.integrations.flask_client import OAuth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
app.config.from_object(Config)

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

@app.route("/login")
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template("login.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle signup form submission
        email = request.form.get('email')
        password = request.form.get('password')
        
        # For now, just redirect to Google OAuth
        flash('Please use Google OAuth to sign up.', 'info')
        return redirect(url_for('google_login'))
    
    return render_template("signup.html")

@app.route("/login/google")
def google_login():
    redirect_uri = app.config['OAUTH_CALLBACK_URL']
    print(f"Redirecting to Google OAuth with URI: {redirect_uri}")
    # Clear any existing session data
    session.clear()
    return oauth.google.authorize_redirect(redirect_uri, prompt='consent')

@app.route("/login/google/authorize")
def google_authorize():
    try:
        print(f"OAuth callback received. Request args: {request.args}")
        
        # Get the authorization code from the request
        code = request.args.get('code')
        if not code:
            raise Exception("No authorization code received")
        
        # Exchange code for token manually
        import requests
        
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': app.config['GOOGLE_CLIENT_ID'],
            'client_secret': app.config['GOOGLE_CLIENT_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': app.config['OAUTH_CALLBACK_URL']
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token = token_response.json()
        
        print(f"Token received successfully")
        
        # Get user info using the access token
        userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f"Bearer {token['access_token']}"}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()
        
        print(f"User info: {user_info}")
        
        # Get or create user
        user = get_or_create_user(user_info)
        
        # Store user in session
        session['user'] = {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'google_id': user['google_id']
        }
        
        # Store Google token for email sending
        store_google_token(user['id'], token)
        
        flash('Successfully logged in with Google!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        print(f"OAuth error: {str(e)}")
        print(f"Error type: {type(e)}")
        flash(f'Login failed: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route("/logout")
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    # Get user subscription and usage stats
    subscription = subscription_mgr.get_user_subscription(user_id)
    usage_stats = subscription_mgr.get_usage_stats(user_id)
    
    # Get recent scraped emails
    scraper = email_scraper.EmailScraper()
    recent_emails = scraper.get_user_scraped_emails(user_id, limit=10)
    
    # Get recent campaigns
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, name, status, created_at, 
               (SELECT COUNT(*) FROM email_queue WHERE campaign_id = campaigns.id) as recipient_count
        FROM campaigns 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 5
    """, (user_id,))
    recent_campaigns = c.fetchall()
    conn.close()
    
    return render_template("dashboard.html", 
                         user=session['user'],
                         subscription=subscription,
                         usage_stats=usage_stats,
                         recent_emails=recent_emails,
                         recent_campaigns=recent_campaigns)

@app.route("/scrape")
def scrape_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    return render_template("scrape.html", user=session['user'])

@app.route("/campaigns")
def campaigns_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    # Get all campaigns
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, name, subject, status, created_at, scheduled_time,
               (SELECT COUNT(*) FROM email_queue WHERE campaign_id = campaigns.id) as recipient_count,
               (SELECT COUNT(*) FROM email_queue WHERE campaign_id = campaigns.id AND status = 'sent') as sent_count
        FROM campaigns 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    campaigns = c.fetchall()
    conn.close()
    
    return render_template("campaigns.html", user=session['user'], campaigns=campaigns)

@app.route("/campaigns/new", methods=['GET', 'POST'])
def new_campaign():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = session['user']['id']
        
        # Check campaign limits
        limit_check = subscription_mgr.check_limit(user_id, 'campaigns')
        if not limit_check['allowed']:
            flash(f'Campaign limit reached ({limit_check["current"]}/{limit_check["limit"]})', 'error')
            return redirect(url_for('campaigns_page'))
        
        # Create campaign
        campaign_data = {
            'name': request.form['name'],
            'subject': request.form['subject'],
            'body': request.form['body'],
            'from_name': request.form.get('from_name', session['user']['name']),
            'reply_to': request.form.get('reply_to', session['user']['email']),
            'recipients': request.form['recipients'].split('\n') if request.form['recipients'] else [],
            'scheduled_time': request.form.get('scheduled_time')
        }
        
        result = email_sender.create_campaign(user_id, campaign_data)
        
        if result['success']:
            flash('Campaign created successfully!', 'success')
            return redirect(url_for('campaigns_page'))
        else:
            flash(f'Error creating campaign: {result["error"]}', 'error')
    
    return render_template("new_campaign.html", user=session['user'])

@app.route("/campaigns/<int:campaign_id>/send", methods=['POST'])
def send_campaign(campaign_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    user_id = session['user']['id']
    
    # Verify campaign belongs to user
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM campaigns WHERE id = ?", (campaign_id,))
    result = c.fetchone()
    conn.close()
    
    if not result or result[0] != user_id:
        return jsonify({'success': False, 'error': 'Campaign not found'})
    
    # Send campaign
    result = email_sender.send_campaign(campaign_id)
    return jsonify(result)

@app.route("/subscription")
def subscription_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    subscription = subscription_mgr.get_user_subscription(user_id)
    usage_stats = subscription_mgr.get_usage_stats(user_id)
    
    return render_template("subscription.html", 
                         user=session['user'],
                         subscription=subscription,
                         usage_stats=usage_stats,
                         plans=subscription_manager.SubscriptionPlans.PLANS)

@app.route("/subscription/upgrade/<plan_id>")
def upgrade_subscription(plan_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    # Create checkout session
    checkout_session = subscription_mgr.create_checkout_session(user_id, plan_id)
    
    if checkout_session:
        return redirect(checkout_session['url'])
    else:
        flash('Error creating checkout session', 'error')
        return redirect(url_for('subscription_page'))

@app.route("/subscription/cancel", methods=['POST'])
def cancel_subscription():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    user_id = session['user']['id']
    success = subscription_mgr.cancel_subscription(user_id)
    
    if success:
        flash('Subscription cancelled successfully', 'success')
    else:
        flash('Error cancelling subscription', 'error')
    
    return redirect(url_for('subscription_page'))

@app.route("/webhook/stripe", methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400
    
    # Handle the event
    success = subscription_mgr.handle_webhook(event)
    
    if success:
        return 'OK', 200
    else:
        return 'Error processing webhook', 500

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

@app.route("/api/search/infinite", methods=['POST'])
def search_infinite_emails():
    """API endpoint for infinite email search"""
    print("Infinite search API called")
    
    if 'user' not in session:
        print("User not authenticated")
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    user_id = session['user']['id']
    print(f"User ID: {user_id}")
    
    try:
        data = request.get_json()
        print(f"Request data: {data}")
        
        industry = data.get('industry')
        location = data.get('location')
        company_size = data.get('company_size')
        limit = data.get('limit', 1000)
        
        print(f"Search params: industry={industry}, location={location}, size={company_size}, limit={limit}")
        
        # Check subscription limits
        limit_check = subscription_mgr.check_limit(user_id, 'scrapes')
        print(f"Limit check: {limit_check}")
        
        if not limit_check['allowed']:
            return jsonify({
                'success': False, 
                'error': f'Search limit reached ({limit_check["current"]}/{limit_check["limit"]})'
            })
        
        # Perform infinite email search
        result = infinite_email_db.search_infinite_emails(
            industry=industry,
            location=location,
            company_size=company_size,
            limit=limit
        )
        
        print(f"Search result: {result}")
        
        if result['success']:
            # Increment usage
            subscription_mgr.increment_usage(user_id, 'scrapes')
            
            # Save emails to database
            for email in result['emails']:
                infinite_email_db.add_email_to_database(
                    email=email,
                    industry=industry,
                    source='infinite_search'
                )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in infinite search: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

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
            'name': name,
            'google_id': google_id
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
            'name': name,
            'google_id': google_id
        }
    
    conn.commit()
    conn.close()
    return user_data

def store_google_token(user_id, token):
    """Store Google OAuth token for email sending"""
    conn = sqlite3.connect("outreachpilot.db")
    c = conn.cursor()
    
    # Create google_tokens table if it doesn't exist
    c.execute("""
        CREATE TABLE IF NOT EXISTS google_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Store or update token
    expires_at = datetime.fromtimestamp(token['expires_at']) if 'expires_at' in token else None
    
    c.execute("""
        INSERT OR REPLACE INTO google_tokens 
        (user_id, access_token, refresh_token, expires_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, token['access_token'], token.get('refresh_token'), expires_at))
    
    conn.commit()
    conn.close()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == "__main__":
    try:
        # Initialize database tables
        subscription_mgr._init_database()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=8800)

