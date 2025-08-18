# Multi-Tenant Telegram Analyzer API

This document provides curl commands for testing the multi-tenant organization functionality.

## Base URL
```
http://localhost:8000/api/v1
```

## Organization Management

### 1. Create Organization
```bash
curl -X POST "http://localhost:8000/api/v1/organizations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "api_id": "12345678",
    "api_hash": "abcdef1234567890abcdef1234567890",
    "phone": "+1234567890"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Organization created successfully",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. List All Organizations
```bash
curl -X GET "http://localhost:8000/api/v1/organizations"
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Acme Corp",
    "api_id": "12345678",
    "api_hash": "abcdef1234567890abcdef1234567890",
    "phone": "+1234567890",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

### 3. Get Organization by ID
```bash
curl -X GET "http://localhost:8000/api/v1/organizations/550e8400-e29b-41d4-a716-446655440000"
```

### 4. Update Organization
```bash
curl -X PUT "http://localhost:8000/api/v1/organizations/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation Updated",
    "api_hash": "new_hash_1234567890abcdef1234567890"
  }'
```

### 5. Delete Organization
```bash
curl -X DELETE "http://localhost:8000/api/v1/organizations/550e8400-e29b-41d4-a716-446655440000"
```

## Authentication (Organization-Specific)

### 1. Send Login Code
```bash
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "phone": "+1234567890"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Verification code sent to your phone number",
  "requires_code": true
}
```

### 2. Verify Code
```bash
curl -X POST "http://localhost:8000/api/v1/code" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "phone": "+1234567890",
    "code": "12345"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully authenticated",
  "session_id": "1BQANOTEzOTU0NjU0NDUxMQG..."
}
```

### 3. Logout
```bash
curl -X GET "http://localhost:8000/api/v1/logout/550e8400-e29b-41d4-a716-446655440000/+1234567890"
```

## Complete Workflow Example

### Step 1: Create Organization
```bash
curl -X POST "http://localhost:8000/api/v1/organizations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "api_id": "12345678",
    "api_hash": "abcdef1234567890abcdef1234567890",
    "phone": "+1234567890"
  }'
```

### Step 2: Start Login Process
```bash
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "RETURNED_ORG_ID",
    "phone": "+1234567890"
  }'
```

### Step 3: Verify with Code
```bash
curl -X POST "http://localhost:8000/api/v1/code" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "RETURNED_ORG_ID",
    "phone": "+1234567890",
    "code": "RECEIVED_CODE"
  }'
```

## Environment Setup

Make sure your `.env` file contains:
```env
MONGODB_URI=mongodb://localhost:27017/telegram_analyzer
```

## Running the Server

```bash
# Start the server
uv run src/main.py

# Or with uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Database Collections

The multi-tenant system creates these collections:
- `organizations` - Organization credentials and metadata
- `sessions` - Organization-specific Telegram sessions
- `groups` - Organization-specific group data
- `messages` - Organization-specific message data
- `analyses` - Organization-specific analysis results
- `auth_sessions` - Pending authentication sessions