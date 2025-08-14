# Bulk Email Sender Microsoft Graph API Integration

## Overview
This document summarizes the updates made to `bulk_email_sender.py` to integrate Microsoft Graph API support alongside the existing Gmail API functionality. The implementation provides a unified email sending system that automatically detects and uses the appropriate OAuth provider for each user.

## Key Changes Made

### 1. Enhanced Imports
- **File**: `bulk_email_sender.py` (lines 1-15)
- **Added**:
  - `requests`: For making HTTP calls to Microsoft Graph API
  - `sqlite3`: For database operations (was missing)
  - `base64`: For Gmail API message encoding

### 2. Updated Email Sending Logic

#### `_send_single_email()` Method
- **File**: `bulk_email_sender.py` (lines 180-230)
- **Changes**:
  - Added `user_id` parameter to determine OAuth provider
  - Automatic provider detection from `user_oauth_tokens` table
  - Provider-specific email construction
  - Enhanced error handling for missing OAuth connections

#### Key Features:
- **Provider Detection**: Automatically checks which OAuth provider the user has connected
- **Dynamic Content**: Creates appropriate message format for each provider
- **Error Handling**: Clear error messages for missing or invalid OAuth tokens
- **Unified Interface**: Single method handles both Google and Microsoft providers

### 3. New Microsoft Graph API Function

#### `_send_via_microsoft_graph_api(payload, access_token)`
- **File**: `bulk_email_sender.py` (lines 250-270)
- **Purpose**: Send emails using Microsoft Graph API
- **Features**:
  - JSON payload construction for Microsoft Graph API
  - Proper HTTP headers with Bearer token authentication
  - Detailed error handling with API response parsing
  - Support for HTML content and recipient addressing

#### API Endpoint: `https://graph.microsoft.com/v1.0/me/sendMail`
- **Method**: POST
- **Headers**: Authorization Bearer token, Content-Type application/json
- **Payload**: Microsoft Graph API message format
- **Response**: 202 status code for successful sends

### 4. Enhanced Campaign Processing

#### `_process_campaign_queue()` Method
- **File**: `bulk_email_sender.py` (lines 140-180)
- **Changes**:
  - Updated to pass `user_id` to `_send_single_email()`
  - Maintains existing rate limiting and batch processing
  - Enhanced error tracking per email

### 5. Updated Database Queries

#### Campaign Details Query
- **File**: `bulk_email_sender.py` (lines 100-110)
- **Changes**:
  - Removed dependency on old `google_tokens` table
  - Simplified query to focus on campaign and user data
  - OAuth tokens now retrieved dynamically per email

### 6. New Utility Methods

#### `check_user_oauth_status(user_id)`
- **File**: `bulk_email_sender.py` (lines 320-340)
- **Purpose**: Check which OAuth providers a user has connected
- **Returns**:
  ```json
  {
    "google": true/false,
    "microsoft": true/false,
    "has_any": true/false
  }
  ```
- **Features**:
  - Token expiration checking
  - Database error handling
  - Provider-specific status reporting

#### `send_test_email(user_id, to_email, subject, body)`
- **File**: `bulk_email_sender.py` (lines 345-390)
- **Purpose**: Send test emails to verify OAuth connectivity
- **Features**:
  - Automatic provider selection
  - Test email templates
  - Connectivity verification
  - Error reporting for troubleshooting

## Provider-Specific Implementation

### Google (Gmail API)
- **Message Format**: MIME multipart with base64 encoding
- **API**: Gmail API v1
- **Authentication**: OAuth 2.0 Bearer token
- **Features**: HTML/Text alternative parts, tracking pixels, unsubscribe links

### Microsoft (Graph API)
- **Message Format**: JSON payload with HTML content
- **API**: Microsoft Graph API v1.0
- **Authentication**: OAuth 2.0 Bearer token
- **Features**: HTML content, recipient addressing, sent items saving

## Database Schema Requirements

### Required Table: `user_oauth_tokens`
```sql
CREATE TABLE user_oauth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL, -- 'google' or 'microsoft'
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, provider)
);
```

## Usage Examples

### 1. Check User OAuth Status
```python
sender = BulkEmailSender()
status = sender.check_user_oauth_status(user_id)
print(f"Google connected: {status['google']}")
print(f"Microsoft connected: {status['microsoft']}")
```

### 2. Send Test Email
```python
sender = BulkEmailSender()
result = sender.send_test_email(
    user_id=123,
    to_email="test@example.com",
    subject="OAuth Test",
    body="Testing OAuth connectivity"
)
print(f"Success: {result['success']}")
```

### 3. Send Campaign
```python
sender = BulkEmailSender()
result = sender.send_campaign(campaign_id=456)
print(f"Campaign started: {result['success']}")
```

## Error Handling

### Common Error Scenarios
1. **No OAuth Connection**: "No connected email account found for user."
2. **Expired Token**: Automatic detection and error reporting
3. **API Errors**: Detailed error messages from Microsoft Graph API
4. **Network Issues**: Connection timeout and retry handling

### Error Response Format
```json
{
    "success": false,
    "error": "Detailed error message"
}
```

## Security Considerations

### Token Management
- **Storage**: Tokens stored in database with expiration tracking
- **Access**: Tokens retrieved per email send operation
- **Expiration**: Automatic checking prevents use of expired tokens
- **Scope**: Minimal required scopes for each provider

### API Security
- **HTTPS**: All API calls use HTTPS
- **Authentication**: Bearer token authentication
- **Rate Limiting**: Built-in rate limiting for API calls
- **Error Handling**: Secure error messages without exposing sensitive data

## Performance Optimizations

### Batch Processing
- **Concurrent Sends**: ThreadPoolExecutor for parallel email sending
- **Rate Limiting**: Redis-based rate limiting (optional)
- **Connection Pooling**: SMTP connection reuse
- **Batch Sizes**: Configurable batch processing

### Database Optimization
- **Indexed Queries**: Efficient token retrieval
- **Connection Management**: Proper connection handling
- **Transaction Support**: Batch database operations

## Configuration

### Required Environment Variables
- `MICROSOFT_CLIENT_ID`: Microsoft OAuth client ID
- `MICROSOFT_CLIENT_SECRET`: Microsoft OAuth client secret
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret

### Optional Configuration
- `REDIS_URL`: For rate limiting (optional)
- SMTP settings for fallback email sending

## Testing

### Unit Tests
- OAuth status checking
- Provider detection
- Email sending for each provider
- Error handling scenarios

### Integration Tests
- End-to-end campaign sending
- OAuth token refresh
- Rate limiting functionality
- Database operations

### Manual Testing
- Test email sending
- Campaign creation and sending
- OAuth connection verification
- Error scenario testing

## Migration Guide

### For Existing Installations
1. **Database**: Ensure `user_oauth_tokens` table exists
2. **OAuth Setup**: Configure Microsoft and Google OAuth applications
3. **Environment**: Set required environment variables
4. **Testing**: Run test emails to verify connectivity

### Backward Compatibility
- Existing Gmail functionality preserved
- SMTP fallback still available
- Gradual migration to OAuth-based sending
- No breaking changes to existing APIs

## Monitoring and Logging

### Key Metrics
- Email send success/failure rates
- Provider usage statistics
- Token expiration tracking
- API response times

### Logging
- OAuth token operations
- Email send attempts and results
- Error conditions and resolutions
- Performance metrics

This implementation provides a robust, scalable email sending system that seamlessly supports both Google and Microsoft OAuth providers while maintaining backward compatibility and security best practices.
