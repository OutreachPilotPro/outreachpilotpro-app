# Microsoft OAuth and Token Storage Implementation

## Overview
This document summarizes the implementation of Microsoft OAuth authentication and secure token storage in the OutreachPilotPro Flask application. The implementation allows users to authenticate with Microsoft accounts and securely store OAuth tokens for later use in sending emails via Microsoft Graph API.

## Key Changes Made

### 1. Enhanced Imports
- Added `base64` import for Microsoft Graph API operations
- Added `timedelta` import for token expiration calculations

### 2. Updated Microsoft OAuth Configuration
- **File**: `app.py` (lines 67-77)
- **Changes**: Updated Microsoft OAuth scope to include `Mail.Send` and `offline_access`
- **New Scope**: `'User.Read openid email profile Mail.Send offline_access'`
- **Purpose**: Enables email sending capabilities and refresh token access

### 3. Database Schema Updates
- **File**: `app.py` (lines 200-210 for PostgreSQL, 250-260 for SQLite)
- **New Table**: `user_oauth_tokens`
- **Columns**:
  - `id`: Primary key
  - `user_id`: Foreign key to users table
  - `provider`: OAuth provider ('google' or 'microsoft')
  - `access_token`: Encrypted access token
  - `refresh_token`: Encrypted refresh token
  - `expires_at`: Token expiration timestamp
  - `UNIQUE(user_id, provider)`: Ensures one token per user per provider

### 4. Token Management Functions

#### `store_oauth_token(user_id, provider, token)`
- **Purpose**: Securely store OAuth tokens in the database
- **Features**:
  - Database-compatible (PostgreSQL/SQLite)
  - Handles token expiration calculation
  - Uses UPSERT pattern for token updates
  - Supports both Google and Microsoft providers

#### `get_oauth_token(user_id, provider)`
- **Purpose**: Retrieve stored OAuth tokens
- **Features**:
  - Checks token expiration
  - Returns token data or None if expired/missing
  - Supports both providers

### 5. Updated OAuth Callback Routes

#### Microsoft OAuth (`/login/microsoft/authorize`)
- **Changes**: Now stores tokens using `store_oauth_token()`
- **Token Storage**: Automatically saves Microsoft tokens after successful authentication

#### Google OAuth (`/login/google/authorize`)
- **Changes**: Updated to use new generic `store_oauth_token()` function
- **Replacement**: Removed old `store_google_token()` function

### 6. Email Sending Functions

#### `send_email_with_microsoft_graph(user_id, to_email, subject, body, sender_email=None)`
- **Purpose**: Send emails using Microsoft Graph API
- **Features**:
  - Uses stored Microsoft OAuth tokens
  - Supports HTML email content
  - Handles sender email specification
  - Returns success/failure status

#### `send_email_with_gmail_api(user_id, to_email, subject, body, sender_email=None)`
- **Purpose**: Send emails using Gmail API
- **Features**:
  - Uses stored Google OAuth tokens
  - Base64 encoding for Gmail API compatibility
  - HTML email support
  - Returns success/failure status

### 7. New API Endpoints

#### `/api/send-email` (POST)
- **Purpose**: Send individual emails using stored OAuth tokens
- **Parameters**:
  - `to_email`: Recipient email address
  - `subject`: Email subject
  - `body`: Email content (HTML)
  - `provider`: 'microsoft' or 'google' (default: 'microsoft')
  - `sender_email`: Optional sender email address
- **Response**: Success/failure status with message

#### `/api/oauth-status` (GET)
- **Purpose**: Check OAuth token status for current user
- **Response**: Connection status and expiration times for both providers

### 8. Enhanced Campaign Sending
- **File**: `app.py` (lines 1050-1100)
- **Changes**: Updated campaign sending to use stored OAuth tokens
- **Features**:
  - Supports both Microsoft and Google providers
  - Configurable email subject and body
  - Tracks successful vs failed sends
  - Enhanced error handling

## Security Considerations

### Token Storage
- **Current**: Tokens stored in plain text (for development)
- **Production**: Should implement encryption before storage
- **Recommendation**: Use environment-based encryption keys

### Token Expiration
- **Handling**: Automatic expiration checking
- **Refresh**: Framework in place for token refresh (not yet implemented)
- **Security**: Expired tokens are not returned

### Database Security
- **Unique Constraints**: Prevents duplicate tokens per user/provider
- **Foreign Keys**: Ensures data integrity
- **Connection Management**: Proper connection handling with error recovery

## Usage Examples

### 1. Check OAuth Status
```bash
curl -X GET /api/oauth-status \
  -H "Cookie: session=your_session_cookie"
```

### 2. Send Individual Email
```bash
curl -X POST /api/send-email \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{
    "to_email": "recipient@example.com",
    "subject": "Test Email",
    "body": "<h1>Hello</h1><p>This is a test email.</p>",
    "provider": "microsoft",
    "sender_email": "your-email@yourdomain.com"
  }'
```

### 3. Send Campaign
```bash
curl -X POST /campaigns/123/send \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{
    "provider": "microsoft",
    "subject": "Campaign Subject",
    "body": "<h1>Campaign Email</h1><p>Campaign content here.</p>",
    "sender_email": "your-email@yourdomain.com"
  }'
```

## Database Migration

### For Existing Installations
The new `user_oauth_tokens` table will be automatically created when the application starts. No manual migration is required.

### Verification
```sql
-- Check if table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='user_oauth_tokens';

-- Check stored tokens (development only)
SELECT user_id, provider, expires_at FROM user_oauth_tokens;
```

## Next Steps

### 1. Token Encryption
- Implement encryption for stored tokens
- Use environment variables for encryption keys
- Add token rotation capabilities

### 2. Token Refresh
- Implement automatic token refresh logic
- Handle refresh token expiration
- Add user notification for re-authentication

### 3. Error Handling
- Enhanced error messages for token issues
- User-friendly authentication flow
- Retry mechanisms for failed sends

### 4. Monitoring
- Add logging for token operations
- Monitor token usage and expiration
- Alert on authentication failures

## Testing

### 1. OAuth Flow Testing
- Test Microsoft OAuth login
- Verify token storage
- Check token retrieval

### 2. Email Sending Testing
- Test individual email sending
- Test campaign sending
- Verify error handling

### 3. Token Management Testing
- Test token expiration
- Test provider switching
- Verify database constraints

## Configuration Requirements

### Environment Variables
Ensure these are set in your configuration:
- `MICROSOFT_CLIENT_ID`: Microsoft OAuth client ID
- `MICROSOFT_CLIENT_SECRET`: Microsoft OAuth client secret
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret

### Microsoft Azure Configuration
- Configure redirect URI: `https://yourdomain.com/login/microsoft/authorize`
- Enable required scopes: `User.Read`, `Mail.Send`, `offline_access`
- Set up proper permissions in Azure AD

This implementation provides a robust foundation for OAuth-based email sending capabilities while maintaining security and scalability for the OutreachPilotPro application.
