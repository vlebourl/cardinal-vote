# 🔗 Cardinal Vote Generalized Voting Platform - API Integration Guide

**Complete API reference for integration, troubleshooting, and advanced usage** of the Cardinal Vote generalized voting platform.

## 🎯 API Overview

The Cardinal Vote API provides RESTful endpoints for:

- **Vote Management**: Create, update, and manage votes with any content type
- **Authentication**: JWT-based user authentication and authorization
- **Public Voting**: Submit ratings on vote options using value voting (-2 to +2 scale)
- **Results & Analytics**: Get voting statistics, rankings, and export data
- **Super Admin**: User management, content moderation, and system oversight

### Base URL Structure

```
https://your-domain.com/api/
```

### Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

## 📋 Core API Endpoints

### 🗳️ Vote Management (`/api/votes/`)

#### `POST /api/votes/`

Create a new vote with custom options.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:

```json
{
  "title": "Choose our new design",
  "description": "Help us pick the best option",
  "slug": "design-vote-2024",
  "starts_at": "2024-02-01T10:00:00Z",
  "ends_at": "2024-02-15T23:59:59Z",
  "options": [
    {
      "title": "Modern Design",
      "option_type": "image",
      "content": "/uploads/design1.png",
      "display_order": 1
    },
    {
      "title": "Classic Style",
      "option_type": "text",
      "content": "Traditional approach with proven usability",
      "display_order": 2
    }
  ]
}
```

**Response**: `201 Created`

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "title": "Choose our new design",
    "slug": "design-vote-2024",
    "status": "active",
    "created_at": "2024-01-15T10:00:00Z",
    "options": [...]
  }
}
```

#### `GET /api/votes/`

List all votes (paginated).

**Query Parameters**:

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10, max: 100)
- `status`: Filter by status (`active`, `draft`, `closed`)
- `search`: Search in titles and descriptions

**Response**: `200 OK`

```json
{
  "success": true,
  "data": {
    "votes": [...],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 25,
      "pages": 3
    }
  }
}
```

#### `GET /api/votes/{vote_id}`

Get specific vote details.

**Response**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "title": "Choose our new design",
    "description": "Help us pick the best option",
    "slug": "design-vote-2024",
    "status": "active",
    "starts_at": "2024-02-01T10:00:00Z",
    "ends_at": "2024-02-15T23:59:59Z",
    "options": [
      {
        "id": "option-uuid",
        "title": "Modern Design",
        "option_type": "image",
        "content": "/uploads/design1.png",
        "display_order": 1
      }
    ],
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

### 🎯 Public Voting

#### `GET /api/votes/public/{slug}`

Get public vote by slug (no authentication required).

**Response**: Same as `/api/votes/{vote_id}` but only for active, public votes.

#### `POST /api/votes/public/{slug}/submit`

Submit vote responses (no authentication required).

**Request Body**:

```json
{
  "voter_first_name": "John",
  "voter_last_name": "Doe",
  "responses": {
    "option-uuid-1": 2,
    "option-uuid-2": -1,
    "option-uuid-3": 0
  }
}
```

**Response**: `200 OK`

```json
{
  "success": true,
  "message": "Vote submitted successfully",
  "submission_id": "submission-uuid"
}
```

#### `GET /api/votes/{vote_id}/results`

Get vote results and statistics.

**Response**: `200 OK`

```json
{
  "success": true,
  "data": {
    "vote_title": "Choose our new design",
    "total_participants": 150,
    "options": [
      {
        "id": "option-uuid-1",
        "title": "Modern Design",
        "total_ratings": 150,
        "average_rating": 1.2,
        "total_score": 180,
        "ranking": 1,
        "rating_distribution": {
          "-2": 5,
          "-1": 10,
          "0": 35,
          "1": 60,
          "2": 40
        }
      }
    ]
  }
}
```

### 🔐 Authentication (`/api/auth/`)

#### `POST /api/auth/register`

Register new user account.

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### `POST /api/auth/login`

Login and get JWT token.

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response**: `200 OK`

```json
{
  "success": true,
  "access_token": "jwt-token-string",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### `GET /api/auth/me`

Get current user information.

**Headers**: `Authorization: Bearer <token>`

**Response**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "user-uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "verified": true
  }
}
```

### 👑 Super Admin (`/api/admin/`)

#### `GET /api/admin/stats`

Get system statistics (super admin only).

**Headers**: `Authorization: Bearer <super_admin_token>`

**Response**: `200 OK`

```json
{
  "success": true,
  "data": {
    "total_votes": 45,
    "active_votes": 12,
    "total_users": 1250,
    "total_responses": 8500,
    "votes_created_today": 3
  }
}
```

#### `GET /api/admin/users`

List all users (super admin only).

**Query Parameters**:

- `page`: Page number
- `limit`: Items per page
- `search`: Search by name or email
- `role`: Filter by role
- `verified`: Filter by verification status

#### `GET /api/admin/moderation/dashboard`

Get content moderation dashboard (super admin only).

**Response**: Includes flagged content, moderation queue, and oversight statistics.

## 🔧 Integration Examples

### JavaScript/TypeScript

```javascript
class CardinalVoteAPI {
  constructor(baseURL, token = null) {
    this.baseURL = baseURL
    this.token = token
  }

  async createVote(voteData) {
    const response = await fetch(`${this.baseURL}/api/votes/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.token}`
      },
      body: JSON.stringify(voteData)
    })
    return await response.json()
  }

  async submitVote(slug, responses) {
    const response = await fetch(`${this.baseURL}/api/votes/public/${slug}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(responses)
    })
    return await response.json()
  }
}
```

### Python

```python
import requests

class CardinalVoteAPI:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url
        self.headers = {'Content-Type': 'application/json'}
        if token:
            self.headers['Authorization'] = f'Bearer {token}'

    def create_vote(self, vote_data: dict):
        response = requests.post(
            f'{self.base_url}/api/votes/',
            json=vote_data,
            headers=self.headers
        )
        return response.json()

    def get_vote_results(self, vote_id: str):
        response = requests.get(
            f'{self.base_url}/api/votes/{vote_id}/results',
            headers=self.headers
        )
        return response.json()
```

## 📊 Rate Limiting

| Endpoint                               | Limit         | Window     | Scope    |
| -------------------------------------- | ------------- | ---------- | -------- |
| `POST /api/votes/public/{slug}/submit` | 3 requests    | 1 hour     | Per IP   |
| `POST /api/auth/login`                 | 10 requests   | 15 minutes | Per IP   |
| `GET /api/*`                           | 1000 requests | 1 hour     | Per user |
| `POST /api/votes/`                     | 50 requests   | 1 hour     | Per user |

## 🛠️ Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": ["Field 'title' is required"]
  }
}
```

**Common HTTP Status Codes**:

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## 🚀 Getting Started

1. **Create a vote**: Use `POST /api/votes/` with your content
2. **Share the vote**: Give users the `/vote/{slug}` URL
3. **Collect responses**: Users submit via `POST /api/votes/public/{slug}/submit`
4. **View results**: Access real-time results via `GET /api/votes/{vote_id}/results`

This implementation provides a complete, production-ready generalized voting platform with comprehensive error handling, security measures, and flexible content support.
