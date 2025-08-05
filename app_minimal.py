#!/usr/bin/env python3
"""
Minimal Flask app for initial deployment
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Basic configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', '')
app.config['STRIPE_PUBLISHABLE_KEY'] = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect("outreachpilot.db", timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

# Initialize database tables
def init_database():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create users table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create subscriptions table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
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
    
    # Simple subscription page
    plans = {
        "free": {"name": "Free Trial", "price": 0, "features": ["100 emails/month", "Basic support"]},
        "starter": {"name": "Starter", "price": 29, "features": ["1,000 emails/month", "Priority support"]},
        "professional": {"name": "Professional", "price": 99, "features": ["10,000 emails/month", "Advanced features"]},
        "enterprise": {"name": "Enterprise", "price": 299, "features": ["Unlimited emails", "Dedicated support"]}
    }
    
    return render_template("subscription.html", 
                         user=session['user'],
                         subscription=None,
                         usage_stats={},
                         plans=plans)

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

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 