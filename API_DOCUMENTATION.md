# ToVéCo Logo Voting Platform - API Documentation

## Overview

The ToVéCo Logo Voting Platform is a FastAPI-based web application that implements a "vote de valeur" methodology for logo selection. Users can rate logos on a scale from -2 to +2 and view aggregated results.

## Architecture

### Backend Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Lightweight database for vote storage
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment

### Frontend

- **Vanilla JavaScript**: Mobile-first responsive voting interface
- **CSS Grid/Flexbox**: Modern responsive design
- **Progressive Enhancement**: Works without JavaScript for basic functionality

## API Endpoints

### Frontend Routes

#### `GET /`

Serves the main voting page.

**Response**: HTML page with voting interface

#### `GET /results`

Serves the results visualization page.

**Response**: HTML page with voting results

### API Routes

#### `GET /api/logos`

Returns a randomized list of available logo files.

**Response**:

```json
{
  "logos": ["toveco3.png", "toveco1.png", "toveco7.png", ...],
  "total_count": 11
}
```

#### `POST /api/vote`

Submit a complete vote with ratings for all logos.

**Request Body**:

```json
{
  "voter_name": "John Doe",
  "ratings": {
    "toveco1.png": 2,
    "toveco2.png": -1,
    "toveco3.png": 0,
    ...
  }
}
```

**Response**:

```json
{
  "success": true,
  "message": "Vote enregistré avec succès!",
  "vote_id": 123
}
```

**Validation Rules**:

- `voter_name`: 1-100 characters, non-empty after trimming
- `ratings`: Must include all available logos
- Rating values: Must be integers between -2 and +2
- Logo names: Must match `toveco*.png` format

#### `GET /api/results`

Get aggregated voting results with rankings.

**Query Parameters**:

- `include_votes` (bool, optional): Include individual vote records (admin feature)

**Response**:

```json
{
  "summary": {
    "toveco1.png": {
      "average": 1.5,
      "total_votes": 10,
      "total_score": 15,
      "ranking": 1
    },
    ...
  },
  "total_voters": 10,
  "votes": [...] // Only if include_votes=true
}
```

#### `GET /api/stats`

Get basic voting statistics.

**Response**:

```json
{
  "total_votes": 25,
  "total_logos": 11,
  "voting_scale": {
    "min": -2,
    "max": 2
  }
}
```

#### `GET /api/health`

Health check endpoint for monitoring.

**Response**:

```json
{
  "status": "healthy",
  "database": "connected",
  "logos_available": 11,
  "version": "0.1.0"
}
```

## Database Schema

### Votes Table

```sql
CREATE TABLE votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_name TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ratings TEXT NOT NULL  -- JSON string of logo ratings
);
```

**Example Record**:

```json
{
  "id": 1,
  "voter_name": "John Doe",
  "timestamp": "2025-09-04T12:00:00.000000",
  "ratings": "{\"toveco1.png\": 2, \"toveco2.png\": -1, ...}"
}
```

## Vote Data Structure

### Vote Submission Format

```json
{
  "voter_name": "User Name",
  "ratings": {
    "toveco1.png": 2,    // Strongly accepted
    "toveco2.png": 1,    // Accepted
    "toveco3.png": 0,    // Neutral
    "toveco4.png": -1,   // Rejected
    "toveco5.png": -2,   // Strongly rejected
    ...
  }
}
```

### Voting Scale

- **+2**: Strongly accepted
- **+1**: Accepted
- **0**: Neutral
- **-1**: Rejected
- **-2**: Strongly rejected

## Error Handling

### HTTP Status Codes

- `200`: Success
- `400`: Client error (validation failed)
- `404`: Resource not found
- `422`: Unprocessable entity (validation error)
- `500`: Server error

### Error Response Format

```json
{
  "success": false,
  "message": "Error description in French",
  "details": ["field1: error detail", ...] // For validation errors
}
```

## Security Features

### Input Validation

- Voter names are sanitized and length-limited
- Rating values are strictly validated (-2 to +2)
- Logo filenames are validated against expected format
- Complete vote validation (all logos must be rated)

### CORS Configuration

- Configured for development (`localhost:3000`, `localhost:8000`)
- Easily configurable for production domains

### Rate Limiting

- Configurable via `MAX_VOTES_PER_IP_PER_HOUR` setting
- Currently set to 5 votes per IP per hour

## Configuration

### Environment Variables

- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DATABASE_PATH`: SQLite database file path (default: votes.db)

### Directory Structure

```
toveco/
├── src/toveco_voting/          # Python package
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Data models and validation
│   ├── database.py             # Database operations
│   └── config.py               # Configuration settings
├── logos/                      # Logo PNG files (toveco1.png - toveco11.png)
├── templates/                  # Jinja2 HTML templates
│   ├── index.html
│   └── results.html
├── static/                     # Static assets
│   ├── style.css
│   └── app.js
├── tests/                      # Test suite
└── scripts/                    # Utility scripts
    └── run.sh
```

## Deployment

### Development

```bash
./scripts/run.sh
```

### Production with Uvicorn

```bash
uvicorn src.toveco_voting.main:app --host 0.0.0.0 --port 8000
```

### Using uv (recommended)

```bash
uv run uvicorn src.toveco_voting.main:app --host 0.0.0.0 --port 8000
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.toveco_voting.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Performance Considerations

### Database

- SQLite with WAL mode for better concurrency
- Indexes on timestamp and voter_name for efficient queries
- Connection pooling with `pool_pre_ping`

### Caching

- Static file serving with appropriate cache headers
- Logo randomization per request (no caching)
- Database results can be cached at application level if needed

### Scaling

- Horizontal scaling via reverse proxy (nginx)
- Database can be migrated to PostgreSQL for high-load scenarios
- Redis can be added for session management and caching

## Testing

### Run Tests

```bash
uv run pytest tests/ -v
```

### Test Coverage

```bash
uv run pytest tests/ --cov=src/toveco_voting --cov-report=html
```

### API Testing with curl

**Get logos**:

```bash
curl -X GET http://localhost:8000/api/logos
```

**Submit vote**:

```bash
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{
    "voter_name": "Test User",
    "ratings": {
      "toveco1.png": 2, "toveco2.png": 1, "toveco3.png": 0,
      "toveco4.png": -1, "toveco5.png": -2, "toveco6.png": 1,
      "toveco7.png": 0, "toveco8.png": 2, "toveco9.png": -1,
      "toveco10.png": 1, "toveco11.png": 0
    }
  }'
```

**Get results**:

```bash
curl -X GET http://localhost:8000/api/results
```

## Monitoring

### Health Check

The `/api/health` endpoint provides:

- Application status
- Database connectivity
- Available logo count
- Version information

### Logging

- Structured logging with Python's logging module
- Configurable log levels
- Request/response logging for debugging

### Metrics

- Vote submission counts
- Response times
- Error rates
- Database connection health

## Mobile-First Design

### Responsive Breakpoints

- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

### Touch-Friendly Interface

- 44px minimum touch targets
- Swipe gestures for navigation
- Large, clear voting buttons
- Optimized for one-handed use

### Performance

- Minimal JavaScript dependencies
- CSS Grid for efficient layouts
- Optimized images and assets
- Progressive enhancement

This implementation provides a complete, production-ready logo voting platform with comprehensive error handling, security measures, and a mobile-first responsive design.
