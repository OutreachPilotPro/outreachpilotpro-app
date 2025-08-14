#!/usr/bin/env python3
"""
Email Configuration Test Utility
Tests SMTP connection for different email providers
"""

import os
import sys
from dotenv import load_dotenv
from config import get_email_config, EMAIL_PROVIDERS

# Load environment variables
load_dotenv()

def test_email_config(provider=None):
    """
    Test email configuration for a specific provider or current environment settings
    
    Args:
        provider (str): Email provider name (gmail, outlook, yahoo, office365, protonmail)
    """
    print(f"🔍 Testing Email Configuration for: {provider or 'Environment Settings'}")
    print("=" * 60)
    
    # Get configuration
    config = get_email_config(provider)
    
    # Display configuration
    print("📧 Email Configuration:")
    print(f"   Server: {config['server']}")
    print(f"   Port: {config['port']}")
    print(f"   TLS: {config['use_tls']}")
    print(f"   SSL: {config['use_ssl']}")
    print(f"   Username: {config['username'] or 'Not set'}")
    print(f"   Password: {'✅ Set' if config['password'] else '❌ Not set'}")
    print(f"   Notes: {config['notes']}")
    print()
    
    # Check if credentials are set
    if not config['username'] or not config['password']:
        print("❌ Error: MAIL_USERNAME and MAIL_PASSWORD must be set in environment variables")
        print("   Please check your .env file or environment variables")
        return False
    
    # Test SMTP connection
    print("🔌 Testing SMTP Connection...")
    try:
        import smtplib
        
        # Create SMTP connection
        if config['use_ssl']:
            print(f"   Connecting to {config['server']}:{config['port']} (SSL)...")
            server = smtplib.SMTP_SSL(config['server'], config['port'])
        else:
            print(f"   Connecting to {config['server']}:{config['port']}...")
            server = smtplib.SMTP(config['server'], config['port'])
        
        # Start TLS if required
        if config['use_tls'] and not config['use_ssl']:
            print("   Starting TLS...")
            server.starttls()
        
        # Login
        print("   Logging in...")
        server.login(config['username'], config['password'])
        
        print("✅ SMTP connection successful!")
        print("   Email configuration is working correctly")
        
        # Test sending a simple message
        print("\n📤 Testing email sending...")
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = config['username']
        msg['To'] = config['username']  # Send to self for testing
        msg['Subject'] = 'OutreachPilotPro Email Configuration Test'
        
        body = f"""
        This is a test email from OutreachPilotPro.
        
        Email Configuration:
        - Server: {config['server']}
        - Port: {config['port']}
        - TLS: {config['use_tls']}
        - SSL: {config['use_ssl']}
        - Provider: {provider or 'Environment Settings'}
        
        If you receive this email, your email configuration is working correctly!
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send test email
        server.send_message(msg)
        print("✅ Test email sent successfully!")
        print(f"   Check your inbox at {config['username']}")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Please check your username and password")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("   Please check your server and port settings")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_providers():
    """List all available email providers"""
    print("📧 Available Email Providers:")
    print("=" * 40)
    for provider, config in EMAIL_PROVIDERS.items():
        print(f"   {provider.upper()}:")
        print(f"     Server: {config['server']}")
        print(f"     Port: {config['port']}")
        print(f"     TLS: {config['use_tls']}")
        print(f"     SSL: {config['use_ssl']}")
        print(f"     Notes: {config['notes']}")
        print()

def main():
    """Main function"""
    if len(sys.argv) > 1:
        provider = sys.argv[1].lower()
        if provider in EMAIL_PROVIDERS:
            test_email_config(provider)
        elif provider == 'list':
            list_providers()
        else:
            print(f"❌ Unknown provider: {provider}")
            print("Available providers:", ', '.join(EMAIL_PROVIDERS.keys()))
            print("Use 'list' to see all providers")
    else:
        # Test current environment configuration
        test_email_config()

if __name__ == "__main__":
    main()
