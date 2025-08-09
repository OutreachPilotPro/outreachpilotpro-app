#!/usr/bin/env python3
"""
OutreachPilotPro - Minimal Production App
This is a streamlined version for production deployment on Render
"""

import os
from flask import Flask, render_template, jsonify, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    """Alias for index route to fix template errors"""
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/scrape')
def scrape():
    return render_template('scrape.html')

@app.route('/campaigns')
def campaigns():
    return render_template('campaigns.html')

@app.route('/subscription')
def subscription():
    return render_template('subscription.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Additional routes that templates expect
@app.route('/google_login')
def google_login():
    """Placeholder for Google OAuth login"""
    return redirect(url_for('login'))

@app.route('/live-demo')
def live_demo():
    """Placeholder for live demo page"""
    return render_template('live_demo.html')

@app.route('/gdpr')
def gdpr():
    """Placeholder for GDPR page"""
    return render_template('gdpr.html')

@app.route('/integrations')
def integrations():
    """Placeholder for integrations page"""
    return render_template('integrations.html')

@app.route('/blog')
def blog():
    """Placeholder for blog page"""
    return render_template('blog.html')

@app.route('/careers')
def careers():
    """Placeholder for careers page"""
    return render_template('careers.html')

@app.route('/anti-spam')
def anti_spam():
    """Placeholder for anti-spam page"""
    return render_template('anti_spam.html')

@app.route('/api')
def api():
    """Placeholder for API page"""
    return render_template('api_docs.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'app': 'OutreachPilotPro',
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
