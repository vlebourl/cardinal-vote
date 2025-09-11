# Cardinal Vote Generalized Voting Platform - API Documentation

## Overview

The Cardinal Vote Generalized Voting Platform is a FastAPI-based web application that implements value voting methodology for any type of content. Organizers can create votes with custom options (text, images, videos, etc.) and users can rate options on a scale from -2 to +2.

## Architecture

### Backend Stack

- **FastAPI**: Modern, fast web framework for building APIs with automatic OpenAPI documentation
- **SQLAlchemy**: Async ORM for database operations with PostgreSQL
- **PostgreSQL**: Production-grade database with async support (asyncpg driver)
- **Pydantic**: Data validation and serialization with type safety
- **Uvicorn**: ASGI server for production deployment
- **JWT Authentication**: Secure token-based authentication for organizers and super admins

### Frontend

- **Server-Side Rendered**: Jinja2 templates with progressive enhancement
- **Vanilla JavaScript**: Modern ES6+ with async/await patterns
- **CSS Grid/Flexbox**: Mobile-first responsive design
- **Progressive Enhancement**: Core functionality works without JavaScript

## API Endpoints

### Authentication (`/api/auth/`)

#### `POST /api/auth/register`

Register a new user account.

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response**: `201 Created`

```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": "uuid-string"
}
```

#### `POST /api/auth/login`

Authenticate user and receive JWT token.

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

Get current authenticated user information.

**Headers**: `Authorization: Bearer <jwt_token>`

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

### Vote Management (`/api/votes/`)

#### `POST /api/votes/`

Create a new vote with custom options.

**Headers**: `Authorization: Bearer <jwt_token>`

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

List all votes (paginated, authenticated users only).

**Headers**: `Authorization: Bearer <jwt_token>`

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

Get specific vote details (authenticated users only).

**Headers**: `Authorization: Bearer <jwt_token>`

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

### Public Voting (No Authentication Required)

#### `GET /api/votes/public/{slug}`

Get public vote by slug for voting interface.

**Response**: Same as `/api/votes/{vote_id}` but only for active, public votes.

#### `POST /api/votes/public/{slug}/submit`

Submit vote responses (public endpoint).

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

**Validation Rules**:

- `voter_first_name` & `voter_last_name`: 1-100 characters, non-empty after trimming
- `responses`: Must include all available option UUIDs
- Rating values: Must be integers between -2 and +2
- Rate limiting: 3 votes per IP per hour

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

### Super Admin (`/api/admin/`)

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

List all users with pagination (super admin only).

**Headers**: `Authorization: Bearer <super_admin_token>`

**Query Parameters**:

- `page`: Page number
- `limit`: Items per page
- `search`: Search by name or email
- `role`: Filter by role
- `verified`: Filter by verification status

#### `GET /api/admin/moderation/dashboard`

Get content moderation dashboard (super admin only).

**Headers**: `Authorization: Bearer <super_admin_token>`

**Response**: Includes flagged content, moderation queue, and oversight statistics.

#### `GET /api/health`

Health check endpoint for monitoring.

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "total_votes": 45
}
```

## Database Schema

### PostgreSQL Models

#### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Votes Table

```sql
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    slug VARCHAR(200) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    starts_at TIMESTAMP WITH TIME ZONE,
    ends_at TIMESTAMP WITH TIME ZONE,
    creator_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Vote Options Table

```sql
CREATE TABLE vote_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vote_id UUID REFERENCES votes(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    option_type VARCHAR(50) NOT NULL,
    content TEXT,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Vote Responses Table

```sql
CREATE TABLE vote_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vote_id UUID REFERENCES votes(id) ON DELETE CASCADE,
    voter_first_name VARCHAR(100) NOT NULL,
    voter_last_name VARCHAR(100) NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET
);
```

#### Option Ratings Table

```sql
CREATE TABLE option_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID REFERENCES vote_responses(id) ON DELETE CASCADE,
    option_id UUID REFERENCES vote_options(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= -2 AND rating <= 2)
);
```

## Voting Scale

- **+2**: Strongly accepted
- **+1**: Accepted
- **0**: Neutral
- **-1**: Rejected
- **-2**: Strongly rejected

## Error Handling

### HTTP Status Codes

- `200`: Success
- `201`: Created
- `400`: Client error (validation failed)
- `401`: Unauthorized (invalid/missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Resource not found
- `422`: Unprocessable entity (validation error)
- `429`: Rate limit exceeded
- `500`: Server error

### Error Response Format

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

## Security Features

### Authentication & Authorization

- JWT token-based authentication
- Role-based access control (user, super_admin)
- Secure password hashing with bcrypt
- Token expiration and refresh

### Input Validation

- Comprehensive Pydantic model validation
- SQL injection prevention through SQLAlchemy ORM
- XSS prevention with proper template escaping
- File upload validation and sanitization

### Rate Limiting

- Vote submission: 3 requests per IP per hour
- Authentication: 10 login attempts per IP per 15 minutes
- API requests: 1000 requests per authenticated user per hour

### Security Headers

- Content Security Policy (CSP)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff

## Configuration

### Environment Variables

#### Required

- `DATABASE_URL`: PostgreSQL connection URL
- `SESSION_SECRET_KEY`: JWT signing key (use secrets.token_urlsafe(32))
- `ADMIN_USERNAME`: Super admin username
- `ADMIN_PASSWORD`: Super admin password

#### Optional

- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

### Directory Structure

```
cardinal-vote/
├── src/cardinal_vote/              # Python package
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point
│   ├── config.py                   # Configuration settings
│   ├── database.py                 # Database models and connection
│   ├── models.py                   # Pydantic models
│   ├── auth.py                     # Authentication utilities
│   ├── admin_routes.py             # Admin interface
│   └── super_admin_routes.py       # Super admin functionality
├── uploads/                        # User-uploaded content
├── templates/                      # Jinja2 HTML templates
│   ├── vote/
│   ├── results/
│   └── super_admin/
├── static/                         # Static assets
│   ├── css/
│   ├── js/
│   └── images/
├── tests/                          # Test suite
└── scripts/                        # Deployment scripts
    └── deploy.sh
```

## Deployment

### Docker Deployment (Recommended)

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - '8000:8000'
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@postgres:5432/cardinal_vote
      SESSION_SECRET_KEY: your-secret-key
      ADMIN_USERNAME: admin
      ADMIN_PASSWORD: secure-password
    depends_on:
      - postgres
    volumes:
      - ./uploads:/app/uploads

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cardinal_vote
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Development

```bash
# Install dependencies
uv sync --dev

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/cardinal_vote"
export SESSION_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=secure-password

# Run application
uv run python src/cardinal_vote/main.py
```

### Production with uv

```bash
uv run uvicorn src.cardinal_vote.main:app --host 0.0.0.0 --port 8000
```

## Testing

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=html

# Specific test categories
uv run pytest tests/test_api.py -v
uv run pytest -k "integration" -v
```

### API Testing with curl

**Register user**:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Login**:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Create vote**:

```bash
curl -X POST http://localhost:8000/api/votes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{
    "title": "Choose our new design",
    "description": "Help us pick the best option",
    "slug": "design-vote-2024",
    "options": [
      {
        "title": "Option A",
        "option_type": "text",
        "content": "First choice",
        "display_order": 1
      }
    ]
  }'
```

**Submit vote**:

```bash
curl -X POST http://localhost:8000/api/votes/public/design-vote-2024/submit \
  -H "Content-Type: application/json" \
  -d '{
    "voter_first_name": "John",
    "voter_last_name": "Doe",
    "responses": {
      "option-uuid": 2
    }
  }'
```

## Monitoring

### Health Checks

- `/api/health`: Application and database status
- Database connection pooling with health checks
- Graceful shutdown handling

### Logging

- Structured logging with JSON format in production
- Request/response logging for debugging
- Error tracking with stack traces
- Performance metrics logging

### Metrics

- Vote submission rates
- Authentication success/failure rates
- Database query performance
- Response time monitoring
- Error rate tracking

## Performance Considerations

### Database Optimization

- PostgreSQL with async driver (asyncpg)
- Connection pooling with SQLAlchemy
- Proper indexing on frequently queried columns
- Query optimization with EXPLAIN ANALYZE

### Caching Strategy

- Static file caching with appropriate headers
- Database result caching for expensive queries
- Redis integration for session storage (optional)

### Scaling

- Horizontal scaling via load balancer
- Database read replicas for high-load scenarios
- CDN for static asset delivery
- Container orchestration with Kubernetes

This implementation provides a complete, production-ready generalized voting platform with comprehensive authentication, content moderation, and scalable architecture.
