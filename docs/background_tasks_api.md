# Background Tasks API

This document describes the new background task management APIs that allow you to start and stop real-time intelligence monitoring without using WebSockets.

## Overview

The background task system allows you to:
- Start real-time intelligence monitoring for specific groups or all groups
- Stop monitoring when needed
- Check the status of running tasks
- List all active tasks

## API Endpoints

### 1. Start Background Task

**POST** `/api/v1/background-tasks/start`

Start a background task for real-time intelligence monitoring.

**Request Body:**
```json
{
  "group_ids": [123456789, -987654321]  // Optional: specific group IDs to monitor
}
```

If `group_ids` is not provided, the system will monitor all groups.

**Response:**
```json
{
  "success": true,
  "message": "Background intelligence task started for organization org_123",
  "task_id": "org_123",
  "group_ids": [123456789, -987654321],
  "started_at": "2024-01-15T10:30:00Z"
}
```

### 2. Stop Background Task

**DELETE** `/api/v1/background-tasks/stop`

Stop the background task for the current organization.

**Response:**
```json
{
  "success": true,
  "message": "Background intelligence task stopped for organization org_123",
  "task_id": "org_123"
}
```

### 3. Get Task Status

**GET** `/api/v1/background-tasks/status`

Get the status of the background task for the current organization.

**Response:**
```json
{
  "success": true,
  "task_id": "org_123",
  "status": "running",
  "allowed_groups": [123456789, -987654321],
  "is_running": true,
  "started_at": "2024-01-15T10:30:00Z",
  "stopped_at": null
}
```

### 4. List All Tasks

**GET** `/api/v1/background-tasks/list`

Get information about all active background tasks.

**Response:**
```json
{
  "success": true,
  "active_tasks": {
    "org_123": {
      "task_id": "org_123",
      "status": "running",
      "allowed_groups": [123456789],
      "is_running": true
    }
  },
  "total_active": 1
}
```

### 5. Stop All Tasks

**DELETE** `/api/v1/background-tasks/stop-all`

Stop all active background tasks (admin only).

**Response:**
```json
{
  "success": true,
  "message": "Stopped 2 background tasks",
  "results": [
    {
      "success": true,
      "message": "Background intelligence task stopped for organization org_123",
      "task_id": "org_123"
    }
  ]
}
```

## Authentication

All endpoints require authentication using the same token-based system as other APIs. Include the token in the Authorization header:

```
Authorization: Bearer your_token_here
```

## Usage Examples

### Start monitoring specific groups:
```bash
curl -X POST "http://localhost:8000/api/v1/background-tasks/start" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"group_ids": [123456789, -987654321]}'
```

### Start monitoring all groups:
```bash
curl -X POST "http://localhost:8000/api/v1/background-tasks/start" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Check task status:
```bash
curl -X GET "http://localhost:8000/api/v1/background-tasks/status" \
  -H "Authorization: Bearer your_token"
```

### Stop monitoring:
```bash
curl -X DELETE "http://localhost:8000/api/v1/background-tasks/stop" \
  -H "Authorization: Bearer your_token"
```

## Benefits over WebSocket

1. **No connection management**: No need to maintain WebSocket connections
2. **Automatic recovery**: Tasks can be restarted automatically if they fail
3. **Better resource management**: More efficient than maintaining multiple WebSocket connections
4. **Simpler client code**: No need to handle WebSocket connection states
5. **Persistent monitoring**: Tasks continue running even if clients disconnect

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (e.g., task already running)
- `401`: Unauthorized (invalid token)
- `404`: Organization not found
- `500`: Internal server error

Error responses include a descriptive message:

```json
{
  "detail": "Background task already running for organization org_123"
}
```

## Database Storage

Background task information is stored in the `background_tasks` collection in MongoDB, including:

- Organization ID
- Group IDs being monitored
- Task status (running/stopped)
- Start and stop timestamps
- Last activity timestamp

This allows for task recovery and monitoring across application restarts. 