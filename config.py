import os
from dotenv import load_dotenv

# Load variables from .env file (optional but recommended for production)
load_dotenv()

class Config:
    # Flask App Config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Database (currently using SQLite, upgrade later to Postgres)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth Config
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'your-google-client-id-here')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'your-google-client-secret-here')

    # Temporary callback URL using Render subdomain (until Google Cloud quota resets)
    OAUTH_CALLBACK_URL = "https://outreachpilotpro-app.onrender.com/login/google/authorize"

