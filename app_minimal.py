#!/usr/bin/env python3
"""
OutreachPilotPro - Minimal Flask App with Google OAuth
Working authentication system for production deployment
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from config import Config
import sqlite3
import os
from datetime import datetime
import json
import requests
import re
import time
import random

# Import OAuth dependencies
from authlib.integrations.flask_client import OAuth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
app.config.from_object(Config)

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

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('outreachpilot.db')
    conn.row_factory = sqlite3.Row
    return conn

# User management functions
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

# Placeholder user for templates that need user data
PLACEHOLDER_USER = {
    'id': 1,
    'name': 'Demo User',
    'email': 'demo@outreachpilotpro.com'
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    return render_template('dashboard.html', user=PLACEHOLDER_USER)

@app.route('/scrape')
def scrape():
    if 'user' in session:
        return render_template('scrape.html', user=session['user'])
    return render_template('scrape.html', user=PLACEHOLDER_USER)

@app.route('/scrape_page')
def scrape_page():
    if 'user' in session:
        return render_template('scrape.html', user=session['user'])
    return render_template('scrape.html', user=PLACEHOLDER_USER)

@app.route('/campaigns')
def campaigns():
    if 'user' in session:
        return render_template('campaigns.html', user=session['user'])
    return render_template('campaigns.html', user=PLACEHOLDER_USER)

@app.route('/campaigns_page')
def campaigns_page():
    if 'user' in session:
        return render_template('campaigns.html', user=session['user'])
    return render_template('campaigns.html', user=PLACEHOLDER_USER)

@app.route('/subscription')
def subscription():
    if 'user' in session:
        return render_template('subscription.html', user=session['user'])
    return render_template('subscription.html', user=PLACEHOLDER_USER)

@app.route('/subscription_page')
def subscription_page():
    if 'user' in session:
        return render_template('subscription.html', user=session['user'])
    return render_template('subscription.html', user=PLACEHOLDER_USER)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template("login.html")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if user exists and password matches
        c.execute("SELECT id, email, name, password_hash FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        
        if user and user['password_hash']:
            from werkzeug.security import check_password_hash
            if check_password_hash(user['password_hash'], password):
                session['user'] = {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name']
                }
                return redirect(url_for('dashboard'))
        
        flash('Invalid email or password', 'error')
    
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
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

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# Working Google OAuth routes
@app.route('/google_login')
def google_login():
    """Google OAuth login - redirects to Google"""
    if not app.config.get('GOOGLE_CLIENT_ID'):
        flash('Google OAuth not configured. Please contact support.', 'error')
        return redirect(url_for('login'))
    
    redirect_uri = url_for('google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def google_authorize():
    """Google OAuth callback - handles the response from Google"""
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token)
        
        user = get_or_create_user(user_info)
        session['user'] = user
        
        flash(f'Welcome back, {user["name"]}!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        print(f"Google OAuth error: {e}")
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/live-demo')
def live_demo():
    return render_template('live_demo.html')

@app.route('/gdpr')
def gdpr():
    return render_template('gdpr.html')

@app.route('/integrations')
def integrations():
    return render_template('integrations.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/careers')
def careers():
    return render_template('careers.html')

@app.route('/anti-spam')
def anti_spam():
    return render_template('anti_spam.html')

@app.route('/api')
def api_docs():
    return render_template('api_docs.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
