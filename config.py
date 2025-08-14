import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with all configuration options"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///outreachpilot.db'
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Microsoft OAuth Configuration
    MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET')
    
    # Stripe Configuration
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    
    # Universal Email Configuration (for SMTP)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Application Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    def __init__(self):
        """Initialize configuration and print verification"""
        self._verify_environment_variables()
    
    def _verify_environment_variables(self):
        """Print verification of environment variables for debugging"""
        print("🔍 Environment Variable Verification:")
        print(f"   SECRET_KEY: {'✅ Set' if self.SECRET_KEY and self.SECRET_KEY != 'dev-secret-key-change-in-production' else '❌ Not set or using default'}")
        print(f"   FLASK_ENV: {self.FLASK_ENV}")
        print(f"   STRIPE_SECRET_KEY: {'✅ Set' if self.STRIPE_SECRET_KEY else '❌ Not set'}")
        print(f"   STRIPE_PUBLISHABLE_KEY: {'✅ Set' if self.STRIPE_PUBLISHABLE_KEY else '❌ Not set'}")
        print(f"   GOOGLE_CLIENT_ID: {'✅ Set' if self.GOOGLE_CLIENT_ID else '❌ Not set'}")
        print(f"   MICROSOFT_CLIENT_ID: {'✅ Set' if self.MICROSOFT_CLIENT_ID else '❌ Not set'}")
        print(f"   DATABASE_URL: {self.DATABASE_URL}")
        print(f"   MAIL_SERVER: {self.MAIL_SERVER}")
        print(f"   MAIL_USERNAME: {'✅ Set' if self.MAIL_USERNAME else '❌ Not set'}")
        print("---")
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_DEBUG = False
    
    # Ensure production has proper secret key
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production security checks
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError('SECRET_KEY must be set in production')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Email Provider Presets
EMAIL_PROVIDERS = {
    'gmail': {
        'server': 'smtp.gmail.com',
        'port': 587,
        'use_tls': True,
        'use_ssl': False,
        'notes': 'Requires App Password for 2FA accounts'
    },
    'outlook': {
        'server': 'smtp-mail.outlook.com',
        'port': 587,
        'use_tls': True,
        'use_ssl': False,
        'notes': 'Standard Outlook/Hotmail configuration'
    },
    'yahoo': {
        'server': 'smtp.mail.yahoo.com',
        'port': 587,
        'use_tls': True,
        'use_ssl': False,
        'notes': 'Requires App Password'
    },
    'office365': {
        'server': 'smtp.office365.com',
        'port': 587,
        'use_tls': True,
        'use_ssl': False,
        'notes': 'Microsoft 365 Business accounts'
    },
    'protonmail': {
        'server': '127.0.0.1',
        'port': 1025,
        'use_tls': False,
        'use_ssl': False,
        'notes': 'Requires ProtonMail Bridge'
    },
    'custom': {
        'server': None,
        'port': None,
        'use_tls': None,
        'use_ssl': None,
        'notes': 'Custom SMTP configuration'
    }
}

def get_email_config(provider=None):
    """
    Get email configuration for a specific provider or current environment settings
    
    Args:
        provider (str): Email provider name (gmail, outlook, yahoo, office365, protonmail, custom)
    
    Returns:
        dict: Email configuration dictionary
    """
    if provider and provider in EMAIL_PROVIDERS:
        preset = EMAIL_PROVIDERS[provider]
        return {
            'server': preset['server'],
            'port': preset['port'],
            'use_tls': preset['use_tls'],
            'use_ssl': preset['use_ssl'],
            'username': os.environ.get('MAIL_USERNAME'),
            'password': os.environ.get('MAIL_PASSWORD'),
            'notes': preset['notes']
        }
    else:
        # Return current environment configuration
        return {
            'server': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
            'port': int(os.environ.get('MAIL_PORT', 587)),
            'use_tls': os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
            'use_ssl': os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true',
            'username': os.environ.get('MAIL_USERNAME'),
            'password': os.environ.get('MAIL_PASSWORD'),
            'notes': 'Custom configuration from environment variables'
        }

def get_smtp_connection_config(provider=None):
    """
    Get SMTP connection configuration for use with smtplib
    
    Args:
        provider (str): Email provider name
    
    Returns:
        dict: SMTP connection parameters
    """
    config = get_email_config(provider)
    return {
        'host': config['server'],
        'port': config['port'],
        'use_tls': config['use_tls'],
        'use_ssl': config['use_ssl'],
        'username': config['username'],
        'password': config['password']
    }

def get_smtp_config(provider=None):
    """Gets SMTP settings either from a provider preset or the environment variables."""
    if provider and provider in EMAIL_PROVIDERS:
        preset = EMAIL_PROVIDERS[provider]
        return {
            'server': preset['server'],
            'port': preset['port'],
            'use_tls': preset['use_tls'],
            'use_ssl': preset['use_ssl'],
            'username': os.environ.get('MAIL_USERNAME'),
            'password': os.environ.get('MAIL_PASSWORD'),
        }
    
    # Default to environment variables
    return {
        'server': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        'port': int(os.environ.get('MAIL_PORT', 587)),
        'use_tls': os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
        'use_ssl': os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true',
        'username': os.environ.get('MAIL_USERNAME'),
        'password': os.environ.get('MAIL_PASSWORD'),
    }

# Get current configuration based on environment
def get_config():
    """Get current configuration based on FLASK_ENV"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

