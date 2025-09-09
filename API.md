# 🔗 Cardinal Vote Logo Voting Platform - API Integration Guide

**Complete API reference for integration, troubleshooting, and advanced usage** of the Cardinal Vote logo voting platform.

![API Architecture](static/api-architecture.png)

## 🎯 API Overview

The Cardinal Vote API provides RESTful endpoints for:

- **Logo management**: Retrieve available logos
- **Vote submission**: Submit value-based votes (-2 to +2 scale)
- **Results aggregation**: Get voting statistics and rankings
- **System monitoring**: Health checks and application status

### Base URL Structure

```
https://voting.yourdomain.com/api/v1/
```

### Authentication

- **Public endpoints**: No authentication required for voting functionality
- **Admin endpoints**: Basic authentication for administrative features (future)

## 📋 Quick Start Integration

### 1. Check System Health

```bash
curl -X GET "https://voting.yourdomain.com/api/health" \
  -H "Accept: application/json"
```

### 2. Get Available Logos

```bash
curl -X GET "https://voting.yourdomain.com/api/logos" \
  -H "Accept: application/json"
```

### 3. Submit a Vote

```bash
curl -X POST "https://voting.yourdomain.com/api/vote" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "voter_name": "John Doe",
    "ratings": {
      "cardinal-vote1.png": 2,
      "cardinal-vote2.png": -1,
      "cardinal-vote3.png": 0,
      "cardinal-vote4.png": 1,
      "cardinal-vote5.png": -2,
      "cardinal-vote6.png": 1,
      "cardinal-vote7.png": 0,
      "cardinal-vote8.png": 2,
      "cardinal-vote9.png": -1,
      "cardinal-vote10.png": 1,
      "cardinal-vote11.png": 0
    }
  }'
```

### 4. Get Results

```bash
curl -X GET "https://voting.yourdomain.com/api/results" \
  -H "Accept: application/json"
```

## 🔍 Complete API Reference

### Frontend Endpoints

#### `GET /`

**Purpose**: Serve the main voting interface
**Response**: HTML page with mobile-first voting UI
**Content-Type**: `text/html`

**Example**:

```bash
curl -X GET "https://voting.yourdomain.com/" \
  -H "Accept: text/html"
```

#### `GET /results`

**Purpose**: Serve the results visualization page
**Response**: HTML page with charts and statistics
**Content-Type**: `text/html`

**Example**:

```bash
curl -X GET "https://voting.yourdomain.com/results" \
  -H "Accept: text/html"
```

### API Endpoints

#### `GET /api/logos`

**Purpose**: Get randomized list of available logo files
**Method**: `GET`
**Content-Type**: `application/json`
**Rate Limit**: 100 requests/minute

**Response Schema**:

```json
{
  "logos": ["string"],
  "total_count": "integer"
}
```

**Success Response (200)**:

```json
{
  "logos": [
    "cardinal-vote3.png",
    "cardinal-vote1.png",
    "cardinal-vote7.png",
    "cardinal-vote11.png",
    "cardinal-vote2.png",
    "cardinal-vote9.png",
    "cardinal-vote5.png",
    "cardinal-vote8.png",
    "cardinal-vote10.png",
    "cardinal-vote4.png",
    "cardinal-vote6.png"
  ],
  "total_count": 11
}
```

**Error Responses**:

- `404`: No logo files found
- `500`: Server error retrieving logos

#### `POST /api/vote`

**Purpose**: Submit a complete vote with ratings for all logos
**Method**: `POST`
**Content-Type**: `application/json`
**Rate Limit**: 5 requests/hour per IP

**Request Schema**:

```json
{
  "voter_name": "string (1-100 characters, required)",
  "ratings": {
    "logo_filename.png": "integer (-2 to +2, required for each logo)"
  }
}
```

**Request Validation Rules**:

- `voter_name`: 1-100 characters, non-empty after trimming
- `ratings`: Must include ALL available logos
- Rating values: Must be integers between -2 and +2 inclusive
- Logo names: Must match exactly the filenames from `/api/logos`

**Example Request**:

```json
{
  "voter_name": "Alice Johnson",
  "ratings": {
    "cardinal-vote1.png": 2,
    "cardinal-vote2.png": -1,
    "cardinal-vote3.png": 0,
    "cardinal-vote4.png": 1,
    "cardinal-vote5.png": -2,
    "cardinal-vote6.png": 1,
    "cardinal-vote7.png": 0,
    "cardinal-vote8.png": 2,
    "cardinal-vote9.png": -1,
    "cardinal-vote10.png": 1,
    "cardinal-vote11.png": 0
  }
}
```

**Success Response (200)**:

```json
{
  "success": true,
  "message": "Vote enregistré avec succès!",
  "vote_id": 123
}
```

**Error Responses**:

- `400`: Invalid request data (see details)
- `422`: Validation errors (missing logos, invalid ratings)
- `429`: Rate limit exceeded
- `500`: Server error during vote processing

**Detailed Error Response (422)**:

```json
{
  "success": false,
  "message": "Données invalides",
  "details": [
    "ratings.cardinal-vote5.png: Rating must be between -2 and +2",
    "Missing ratings for: cardinal-vote11.png"
  ]
}
```

#### `GET /api/results`

**Purpose**: Get aggregated voting results with rankings
**Method**: `GET`
**Content-Type**: `application/json`
**Rate Limit**: 60 requests/minute

**Query Parameters**:

- `include_votes` (boolean, optional): Include individual vote records (admin feature)
  - Default: `false`
  - Example: `?include_votes=true`

**Response Schema**:

```json
{
  "summary": {
    "logo_filename.png": {
      "average": "number",
      "total_votes": "integer",
      "total_score": "integer",
      "ranking": "integer"
    }
  },
  "total_voters": "integer",
  "votes": ["array"] // Optional, only if include_votes=true
}
```

**Success Response (200)**:

```json
{
  "summary": {
    "cardinal-vote3.png": {
      "average": 1.8,
      "total_votes": 25,
      "total_score": 45,
      "ranking": 1
    },
    "cardinal-vote7.png": {
      "average": 1.2,
      "total_votes": 25,
      "total_score": 30,
      "ranking": 2
    },
    "cardinal-vote1.png": {
      "average": 0.8,
      "total_votes": 25,
      "total_score": 20,
      "ranking": 3
    }
  },
  "total_voters": 25
}
```

**With Individual Votes** (`?include_votes=true`):

```json
{
  "summary": {
    /* ... same as above ... */
  },
  "total_voters": 25,
  "votes": [
    {
      "id": 1,
      "voter_name": "Alice Johnson",
      "timestamp": "2025-09-04T12:00:00.000000",
      "ratings": {
        "cardinal-vote1.png": 2,
        "cardinal-vote2.png": -1,
        "cardinal-vote3.png": 0
      }
    }
  ]
}
```

#### `GET /api/stats`

**Purpose**: Get basic voting statistics
**Method**: `GET`
**Content-Type**: `application/json`
**Rate Limit**: 100 requests/minute

**Success Response (200)**:

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

**Purpose**: Health check endpoint for monitoring and uptime checks
**Method**: `GET`
**Content-Type**: `application/json`
**Rate Limit**: No limit

**Success Response (200)**:

```json
{
  "status": "healthy",
  "database": "connected",
  "logos_available": 11,
  "version": "0.1.0"
}
```

**Unhealthy Response (200)** - Still returns 200 but indicates issues:

```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "logos_available": 0,
  "version": "0.1.0",
  "error": "Database connection failed"
}
```

## 🛡️ Security & Rate Limiting

### Rate Limiting Rules

| Endpoint           | Limit        | Window   | Scope  |
| ------------------ | ------------ | -------- | ------ |
| `POST /api/vote`   | 5 requests   | 1 hour   | Per IP |
| `GET /api/logos`   | 100 requests | 1 minute | Per IP |
| `GET /api/results` | 60 requests  | 1 minute | Per IP |
| `GET /api/stats`   | 100 requests | 1 minute | Per IP |
| `GET /api/health`  | No limit     | -        | -      |

### Rate Limit Headers

When rate limited, responses include:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1691234567
Retry-After: 3600

{
  "success": false,
  "message": "Rate limit exceeded. Try again in 1 hour."
}
```

### CORS Configuration

**Development Origins**:

- `http://localhost:3000`
- `http://localhost:8000`
- `http://127.0.0.1:8000`

**Production**: Configure via `ALLOWED_ORIGINS` environment variable

**Allowed Methods**: `GET`, `POST`, `OPTIONS`
**Allowed Headers**: `Content-Type`, `Accept`, `Authorization`

## 🔧 Integration Examples

### JavaScript/TypeScript Client

```typescript
class CardinalVoteAPI {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async getLogos(): Promise<{ logos: string[]; total_count: number }> {
    const response = await fetch(`${this.baseUrl}/api/logos`);
    if (!response.ok) {
      throw new Error(`Failed to get logos: ${response.status}`);
    }
    return response.json();
  }

  async submitVote(
    voterName: string,
    ratings: Record<string, number>,
  ): Promise<{ success: boolean; message: string; vote_id: number }> {
    const response = await fetch(`${this.baseUrl}/api/vote`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        voter_name: voterName,
        ratings: ratings,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `Vote submission failed: ${response.status}`);
    }

    return response.json();
  }

  async getResults(includeVotes: boolean = false): Promise<any> {
    const url = new URL(`${this.baseUrl}/api/results`);
    if (includeVotes) {
      url.searchParams.set("include_votes", "true");
    }

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`Failed to get results: ${response.status}`);
    }
    return response.json();
  }

  async checkHealth(): Promise<{
    status: string;
    database: string;
    logos_available: number;
    version: string;
  }> {
    const response = await fetch(`${this.baseUrl}/api/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return response.json();
  }
}

// Usage example
const api = new CardinalVoteAPI("https://voting.yourdomain.com");

async function submitSampleVote() {
  try {
    // Get available logos
    const { logos } = await api.getLogos();

    // Create ratings for all logos
    const ratings: Record<string, number> = {};
    logos.forEach((logo) => {
      ratings[logo] = Math.floor(Math.random() * 5) - 2; // Random rating -2 to +2
    });

    // Submit vote
    const result = await api.submitVote("Test User", ratings);
    console.log("Vote submitted:", result);

    // Get updated results
    const results = await api.getResults();
    console.log("Current results:", results);
  } catch (error) {
    console.error("Error:", error);
  }
}
```

### Python Client

```python
import requests
import json
from typing import Dict, List, Optional

class CardinalVoteAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def get_logos(self) -> Dict:
        """Get list of available logos."""
        response = self.session.get(f"{self.base_url}/api/logos")
        response.raise_for_status()
        return response.json()

    def submit_vote(self, voter_name: str, ratings: Dict[str, int]) -> Dict:
        """Submit a vote with ratings for all logos."""
        data = {
            'voter_name': voter_name,
            'ratings': ratings
        }
        response = self.session.post(f"{self.base_url}/api/vote", json=data)

        if not response.ok:
            error_data = response.json()
            raise requests.HTTPError(f"Vote submission failed: {error_data.get('message', 'Unknown error')}")

        return response.json()

    def get_results(self, include_votes: bool = False) -> Dict:
        """Get voting results."""
        params = {'include_votes': 'true'} if include_votes else {}
        response = self.session.get(f"{self.base_url}/api/results", params=params)
        response.raise_for_status()
        return response.json()

    def get_stats(self) -> Dict:
        """Get basic voting statistics."""
        response = self.session.get(f"{self.base_url}/api/stats")
        response.raise_for_status()
        return response.json()

    def check_health(self) -> Dict:
        """Check system health."""
        response = self.session.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()

# Usage example
def main():
    api = CardinalVoteAPI('https://voting.yourdomain.com')

    try:
        # Check system health
        health = api.check_health()
        print(f"System status: {health['status']}")

        # Get available logos
        logos_data = api.get_logos()
        logos = logos_data['logos']
        print(f"Available logos: {len(logos)}")

        # Create sample ratings
        ratings = {logo: 1 for logo in logos}  # Rate all logos as +1
        ratings[logos[0]] = 2  # Give first logo highest rating

        # Submit vote
        result = api.submit_vote('Python Test User', ratings)
        print(f"Vote submitted with ID: {result['vote_id']}")

        # Get results
        results = api.get_results()
        print(f"Total voters: {results['total_voters']}")

        # Print rankings
        summary = results['summary']
        sorted_logos = sorted(summary.items(), key=lambda x: x[1]['ranking'])
        for logo, data in sorted_logos[:3]:  # Top 3
            print(f"#{data['ranking']}: {logo} (avg: {data['average']:.2f})")

    except requests.RequestException as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    main()
```

### cURL Testing Scripts

Create `test-api.sh`:

```bash
#!/bin/bash
# Cardinal Vote API Test Script

API_BASE="https://voting.yourdomain.com/api"
VOTER_NAME="Test User $(date +%s)"

echo "🔍 Testing Cardinal Vote Voting API..."

# Test health check
echo "1. Health Check:"
curl -s "$API_BASE/health" | jq '.'
echo

# Test get logos
echo "2. Get Logos:"
LOGOS_RESPONSE=$(curl -s "$API_BASE/logos")
echo "$LOGOS_RESPONSE" | jq '.'
LOGOS=$(echo "$LOGOS_RESPONSE" | jq -r '.logos[]')
echo

# Create ratings for all logos
echo "3. Creating test vote..."
RATINGS="{"
FIRST=true
for logo in $LOGOS; do
    if [ "$FIRST" = true ]; then
        FIRST=false
    else
        RATINGS="$RATINGS,"
    fi
    # Random rating between -2 and +2
    RATING=$((RANDOM % 5 - 2))
    RATINGS="$RATINGS\"$logo\": $RATING"
done
RATINGS="$RATINGS}"

VOTE_DATA="{\"voter_name\": \"$VOTER_NAME\", \"ratings\": $RATINGS}"
echo "Vote data: $VOTE_DATA" | jq '.'

# Submit vote
echo "4. Submit Vote:"
curl -s -X POST "$API_BASE/vote" \
    -H "Content-Type: application/json" \
    -d "$VOTE_DATA" | jq '.'
echo

# Get results
echo "5. Get Results:"
curl -s "$API_BASE/results" | jq '.summary | to_entries | sort_by(.value.ranking) | .[0:3]'
echo

# Get stats
echo "6. Get Stats:"
curl -s "$API_BASE/stats" | jq '.'
echo

echo "✅ API test completed!"
```

Make executable and run:

```bash
chmod +x test-api.sh
./test-api.sh
```

## 🐛 Troubleshooting Guide

### Common Integration Issues

#### 1. CORS Errors

**Problem**: Browser requests blocked by CORS policy
**Symptoms**:

```
Access to fetch at 'https://voting.domain.com/api/logos' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**Solutions**:

```bash
# Add your domain to ALLOWED_ORIGINS in .env
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Restart containers
docker compose down && docker compose up -d
```

#### 2. Rate Limit Exceeded

**Problem**: Too many requests from same IP
**Symptoms**: `429 Too Many Requests` responses

**Solutions**:

```bash
# Check current rate limits
curl -I https://voting.yourdomain.com/api/vote

# Adjust rate limits in .env
MAX_VOTES_PER_IP_PER_HOUR=10

# Or disable rate limiting temporarily
ENABLE_RATE_LIMITING=false
```

#### 3. Validation Errors

**Problem**: Vote submission fails validation
**Symptoms**: `422 Unprocessable Entity` responses

**Common Issues**:

- Missing ratings for some logos
- Invalid rating values (not -2 to +2)
- Empty or too long voter names
- Logo filenames don't match exactly

**Debug Steps**:

```bash
# Get current logo list
curl -s https://voting.yourdomain.com/api/logos | jq '.logos'

# Validate your ratings object matches exactly
echo '{"voter_name": "Test", "ratings": {"cardinal-vote1.png": 2}}' | jq '.ratings | keys'
```

#### 4. Database Connection Issues

**Problem**: Database unavailable or corrupted
**Symptoms**: `500 Internal Server Error`, health check shows "disconnected"

**Solutions**:

```bash
# Check database file permissions
docker compose exec cardinal-vote-voting ls -la /app/data/

# Restart with database recreation
docker compose down
docker volume rm cardinal-vote_data
docker compose up -d

# Check application logs
docker compose logs cardinal-vote-voting
```

### Monitoring & Debugging

#### API Response Time Monitoring

```bash
# Monitor API response times
while true; do
  echo "$(date): $(curl -s -w '%{time_total}s\n' -o /dev/null https://voting.yourdomain.com/api/health)"
  sleep 30
done
```

#### Health Check Integration

```bash
# Simple health check for monitoring systems
#!/bin/bash
HEALTH_ENDPOINT="https://voting.yourdomain.com/api/health"

if curl -sf "$HEALTH_ENDPOINT" | grep -q '"status": "healthy"'; then
    echo "OK - Cardinal Vote API is healthy"
    exit 0
else
    echo "CRITICAL - Cardinal Vote API is unhealthy"
    exit 2
fi
```

#### Log Analysis

```bash
# Filter API logs for errors
docker compose logs cardinal-vote-voting 2>&1 | grep -E "(ERROR|WARNING|CRITICAL)"

# Monitor vote submissions
docker compose logs -f cardinal-vote-voting 2>&1 | grep "Vote submitted"

# Check database operations
docker compose logs cardinal-vote-voting 2>&1 | grep -i database
```

### Performance Optimization

#### Caching Strategies

```javascript
// Client-side logo caching
class CachedCardinalVoteAPI extends CardinalVoteAPI {
  private logoCache: {logos: string[], total_count: number} | null = null;
  private cacheTimestamp: number = 0;
  private cacheTimeout: number = 5 * 60 * 1000; // 5 minutes

  async getLogos(): Promise<{logos: string[], total_count: number}> {
    const now = Date.now();
    if (this.logoCache && (now - this.cacheTimestamp) < this.cacheTimeout) {
      return this.logoCache;
    }

    this.logoCache = await super.getLogos();
    this.cacheTimestamp = now;
    return this.logoCache;
  }
}
```

#### Batch Operations

```python
# Efficient batch vote processing
def submit_multiple_votes(api: CardinalVoteAPI, votes: List[Dict]):
    """Submit multiple votes with proper error handling and rate limiting."""
    results = []

    for i, vote in enumerate(votes):
        try:
            result = api.submit_vote(vote['voter_name'], vote['ratings'])
            results.append({'success': True, 'vote_id': result['vote_id']})

            # Respect rate limits (5 votes per hour)
            if i < len(votes) - 1:  # Don't wait after last vote
                time.sleep(720)  # 12 minutes between votes

        except Exception as e:
            results.append({'success': False, 'error': str(e)})

    return results
```

## 📊 API Analytics & Metrics

### Custom Metrics Collection

```python
import time
import statistics
from collections import defaultdict

class APIMetrics:
    def __init__(self):
        self.response_times = []
        self.endpoint_calls = defaultdict(int)
        self.error_counts = defaultdict(int)

    def record_request(self, endpoint: str, response_time: float, status_code: int):
        self.response_times.append(response_time)
        self.endpoint_calls[endpoint] += 1

        if status_code >= 400:
            self.error_counts[f"{endpoint}:{status_code}"] += 1

    def get_summary(self) -> dict:
        if not self.response_times:
            return {"message": "No data collected"}

        return {
            "total_requests": len(self.response_times),
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "95th_percentile": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times),
            "endpoint_usage": dict(self.endpoint_calls),
            "error_counts": dict(self.error_counts),
            "error_rate": sum(self.error_counts.values()) / len(self.response_times) * 100
        }

# Usage
metrics = APIMetrics()
api = CardinalVoteAPI('https://voting.yourdomain.com')

def timed_api_call(func, *args, **kwargs):
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        response_time = time.time() - start_time
        metrics.record_request(func.__name__, response_time, 200)
        return result
    except requests.HTTPError as e:
        response_time = time.time() - start_time
        metrics.record_request(func.__name__, response_time, e.response.status_code)
        raise

# Use timed calls
logos = timed_api_call(api.get_logos)
health = timed_api_call(api.check_health)

print(metrics.get_summary())
```

---

## 🎯 Integration Best Practices

### 1. **Error Handling**

- Always check HTTP status codes
- Parse error messages from response body
- Implement exponential backoff for rate limits
- Log failed requests for debugging

### 2. **Performance**

- Cache logo lists (change infrequently)
- Use appropriate timeouts (30s for votes, 5s for health checks)
- Implement request queuing for batch operations
- Monitor API response times

### 3. **Security**

- Validate all user inputs before sending to API
- Use HTTPS in production
- Implement proper CORS configuration
- Don't expose sensitive data in client-side code

### 4. **Reliability**

- Implement health checks in your monitoring
- Use circuit breakers for external dependencies
- Graceful degradation when API is unavailable
- Proper error messages for end users

---

_🔧 **Need help integrating?** This API guide provides everything needed to successfully integrate with the Cardinal Vote voting platform, from basic usage to advanced troubleshooting._
