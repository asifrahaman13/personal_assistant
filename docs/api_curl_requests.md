# Backend API Curl Requests

This document provides curl requests for all available backend APIs.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require authentication. You'll need to:
1. Sign up or login to get an access token
2. Include the token in the Authorization header

## 1. Organization Authentication

### Sign Up
```bash
curl -X POST "http://localhost:8000/api/v1/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password",
    "name": "Your Organization",
    "api_id": "your-telegram-api-id",
    "api_hash": "your-telegram-api-hash",
    "phone": "+1234567890"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

## 2. Telegram Authentication

### Send Code Request
```bash
curl -X POST "http://localhost:8000/api/v1/telegram-login" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "phone": "+1234567890"
  }'
```

### Verify Code
```bash
curl -X POST "http://localhost:8000/api/v1/code" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "phone": "+1234567890",
    "code": "12345"
  }'
```

## 3. Telegram Data APIs

### Get Groups
```bash
curl -X POST "http://localhost:8000/api/v1/groups" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "phone": "+1234567890"
  }'
```

### Get Group Messages
```bash
curl -X POST "http://localhost:8000/api/v1/group-messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "phone": "+1234567890",
    "group_id": -1001234567890,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'
```

### Run Sentiment Analysis
```bash
curl -X POST "http://localhost:8000/api/v1/sentiment-analysis" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "phone": "+1234567890",
    "group_id": -1001234567890,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'
```

### Get Latest Sentiment Analysis
```bash
curl -X GET "http://localhost:8000/api/v1/latest-sentiment-analysis?group_id=-1001234567890" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Latest Detailed Analyses
```bash
# Get default 25 analyses
curl -X GET "http://localhost:8000/api/v1/latest-detailed-analyses" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get custom number of analyses (max 100)
curl -X GET "http://localhost:8000/api/v1/latest-detailed-analyses?limit=50" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get analyses for a specific group
curl -X GET "http://localhost:8000/api/v1/latest-detailed-analyses?group_id=4937795126" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get analyses for a specific group with custom limit
curl -X GET "http://localhost:8000/api/v1/latest-detailed-analyses?limit=10&group_id=4937795126" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 4. Organization Management

### Logout
```bash
curl -X GET "http://localhost:8000/api/v1/logout/{organization_id}/{phone}" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Example Workflow

### 1. Complete Authentication Flow
```bash
# Step 1: Sign up
curl -X POST "http://localhost:8000/api/v1/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test Organization",
    "api_id": "12345678",
    "api_hash": "abcdef1234567890abcdef1234567890",
    "phone": "+1234567890"
  }'

# Step 2: Login
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Step 3: Send Telegram code
curl -X POST "http://localhost:8000/api/v1/telegram-login" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "phone": "+1234567890"
  }'

# Step 4: Verify code
curl -X POST "http://localhost:8000/api/v1/code" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "phone": "+1234567890",
    "code": "12345"
  }'
```

### 2. Data Analysis Flow
```bash
# Step 1: Get groups
curl -X POST "http://localhost:8000/api/v1/groups" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "phone": "+1234567890"
  }'

# Step 2: Run sentiment analysis
curl -X POST "http://localhost:8000/api/v1/sentiment-analysis" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "phone": "+1234567890",
    "group_id": -1001234567890,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'

# Step 3: Get latest analysis
curl -X GET "http://localhost:8000/api/v1/latest-sentiment-analysis?group_id=-1001234567890" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Step 4: Get detailed analyses
curl -X GET "http://localhost:8000/api/v1/latest-detailed-analyses?limit=25" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Step 5: Get detailed analyses for specific group
curl -X GET "http://localhost:8000/api/v1/latest-detailed-analyses?limit=25&group_id=4937795126" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Response Examples

### Successful Group Response
```json
{
  "success": true,
  "message": "Groups fetched successfully",
  "groups": [
    {
      "id": -1001234567890,
      "title": "Test Group",
      "username": "testgroup",
      "participants_count": 150
    }
  ]
}
```

### Successful Sentiment Analysis Response
```json
{
  "success": true,
  "message": "Analysis complete",
  "analysis": {
    "total_messages": 1000,
    "unique_users": 50,
    "sentiment_distribution": {
      "positive": 400,
      "neutral": 300,
      "negative": 300
    },
    "average_sentiment": 0.05,
    "user_message_counts": {
      "123456789": 25,
      "987654321": 20
    },
    "top_users": [
      ["123456789", 25],
      ["987654321", 20]
    ]
  }
}
```

### Successful Detailed Analyses Response
```json
{
  "success": true,
  "message": "Found 5 detailed analyses",
  "analyses": [
    {
      "organization_id": "org-uuid",
      "group_id": -1001234567890,
      "group_title": "Test Group",
      "analysis_date": "2024-01-15T10:30:00Z",
      "time_period_days": 30,
      "summary": {
        "total_messages": 1000,
        "unique_users": 50,
        "average_sentiment": 0.05,
        "sentiment_distribution": {
          "positive": 400,
          "neutral": 300,
          "negative": 300
        }
      },
      "user_activity": {
        "user_message_counts": {
          "123456789": 25,
          "987654321": 20
        },
        "top_users": [
          ["123456789", 25],
          ["987654321", 20]
        ]
      },
      "messages_with_sentiment": [
        {
          "message_id": 123,
          "text": "Hello world!",
          "date": "2024-01-15T10:30:00Z",
          "sender_id": 123456789,
          "sender_name": "John Doe",
          "sentiment": "positive",
          "polarity": 0.8
        }
      ]
    }
  ]
}
```

## Error Responses

### Authentication Error
```json
{
  "detail": "Not authenticated"
}
```

### Validation Error
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "phone"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

### Server Error
```json
{
  "detail": "Failed to fetch groups: Connection timeout"
}
```

## Notes

1. **Replace `YOUR_ACCESS_TOKEN`** with the actual token received from login/signup
2. **Replace `+1234567890`** with your actual phone number
3. **Replace `-1001234567890`** with actual group IDs from your Telegram groups
4. **Replace API credentials** with your actual Telegram API ID and hash
5. **Date format**: Use ISO format (YYYY-MM-DD) for dates
6. **Group IDs**: Telegram group IDs are typically negative numbers
7. **Phone numbers**: Use international format with country code

## Testing with Environment Variables

You can use environment variables for easier testing:

```bash
export API_BASE_URL="http://localhost:8000/api/v1"
export ACCESS_TOKEN="your_token_here"
export PHONE="+1234567890"
export GROUP_ID="-1001234567890"

# Then use them in curl requests
curl -X POST "$API_BASE_URL/groups" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{\"phone\": \"$PHONE\"}"
``` 