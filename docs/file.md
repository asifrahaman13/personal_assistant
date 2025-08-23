# Background Tasks Router API

Manages background tasks for organizations.

## Endpoints

### POST `/start`
- **Description:** Start a background task.
- **Request Body:** `BackgroundTaskRequest`
- **Auth:** Requires organization authentication
- **Response:** `BackgroundTaskResponse`

---

### DELETE `/stop`
- **Description:** Stop the current background task.
- **Auth:** Requires organization authentication
- **Response:** `BackgroundTaskResponse`

---

### GET `/status`
- **Description:** Get status of the current background task.
- **Auth:** Requires organization authentication
- **Response:** `BackgroundTaskStatusResponse`

---

### GET `/list`
- **Description:** List all background tasks.
- **Auth:** Requires organization authentication
- **Response:** `BackgroundTasksListResponse`

---

### DELETE `/stop-all`
- **Description:** Stop all background tasks.
- **Auth:** Requires organization authentication
- **Response:** None

---

### GET `/stats`
- **Description:** Get Telegram stats for background tasks.
- **Auth:** Requires organization authentication
- **Response:** None