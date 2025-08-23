# Email Tasks Router API

Manages email-related tasks for organizations.

## Endpoints

### POST `/start`
- **Description:** Start an email task.
- **Request Body:** `EmailTaskRequest`
- **Auth:** Requires organization authentication
- **Response:** `EmailTaskResponse`

---

### DELETE `/stop`
- **Description:** Stop the current email task.
- **Auth:** Requires organization authentication
- **Response:** `EmailTaskResponse`

---

### GET `/status`
- **Description:** Get status of the current email task.
- **Auth:** Requires organization authentication
- **Response:** `EmailTaskStatusResponse`

---

### GET `/list`
- **Description:** List all email tasks.
- **Auth:** Requires organization authentication
- **Response:** `EmailTasksListResponse`

---

### DELETE `/stop-all`
- **Description:** Stop all email tasks.
- **Auth:** Requires organization authentication
- **Response:** None

---

### GET `/stats`
- **Description:** Get stats for email tasks.
- **Auth:** Requires organization authentication
- **Response:** None