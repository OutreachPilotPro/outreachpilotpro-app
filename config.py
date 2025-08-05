import os
from dotenv import load_dotenv

# Load variables from .env file (optional but recommended for production)
load_dotenv()

class Config:
    # Flask App Config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Database (currently using SQLite, upgrade later to Postgres)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///outreachpilot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth Config
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'your-google-client-id-here')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'your-google-client-secret-here')

    # Stripe Configuration
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # Production settings
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8800')
    
    # Security settings for production
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production callback URL for custom domain
    OAUTH_CALLBACK_URL = "https://outreachpilotpro.com/login/google/authorize"

