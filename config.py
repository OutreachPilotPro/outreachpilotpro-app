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
    
    # Stripe Configuration
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    
    # Email Configuration
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
        print(f"   DATABASE_URL: {self.DATABASE_URL}")
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

# Get current configuration based on environment
def get_config():
    """Get current configuration based on FLASK_ENV"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

