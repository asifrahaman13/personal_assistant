# Organization Router API

Manages organizations.

## Endpoints

### POST `/organizations`
- **Description:** Create a new organization.
- **Request Body:** `OrganizationCreate`
- **Auth:** Requires organization authentication
- **Response:** `OrganizationResponse`

---

### GET `/organizations`
- **Description:** List all organizations.
- **Response:** List of `Organization`

---

### GET `/organizations/{org_id}`
- **Description:** Get details of a specific organization.
- **Path Params:** `org_id`
- **Response:** `Organization`

---

### PUT `/organizations/{org_id}`
- **Description:** Update an organization.
- **Path Params:** `org_id`
- **Request Body:** `OrganizationUpdate`
- **Response:** `OrganizationResponse`

---

### GET `/check`
- **Description:** Check organization setup.
- **Auth:** Requires organization authentication
- **Response:** None

---

### DELETE `/organizations/{org_id}`
- **Description:** Delete an organization.
- **Path Params:** `org_id`
- **Response:** `OrganizationResponse`