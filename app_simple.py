#!/usr/bin/env python3
"""
Simplified Flask app for initial deployment
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from config import Config
import sqlite3
import os
from datetime import datetime
import json
import stripe

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

# Initialize managers (simplified)
try:
    import subscription_manager
    subscription_mgr = subscription_manager.SubscriptionManager()
except Exception as e:
    print(f"Warning: Could not initialize subscription manager: {e}")
    subscription_mgr = None

# Fix database connection issues
def get_db_connection():
    conn = sqlite3.connect("outreachpilot.db", timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Simple login system - create account if doesn't exist
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT id, email, name FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        
        if user:
            # User exists, log them in
            session['user'] = {
                'id': user[0],
                'email': user[1],
                'name': user[2]
            }
            conn.close()
            return redirect(url_for('dashboard'))
        else:
            # Create new user
            c.execute("INSERT INTO users (email, name) VALUES (?, ?)", (email, email.split('@')[0]))
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

@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("dashboard.html", user=session['user'])

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
                             plans={})
    
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
                             plans={})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/terms")
def terms():
    """Terms of Service page"""
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    """Privacy Policy page"""
    return render_template("privacy.html")

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 