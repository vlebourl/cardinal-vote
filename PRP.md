# Project Requirements & Planning (PRP) - LEGACY DOCUMENT

## Cardinal Vote Logo Voting Platform (Legacy)

> **⚠️ LEGACY DOCUMENT**: This document describes the original logo voting platform. For current generalized platform requirements, see [PRP-Generalized-Platform.md](PRP-Generalized-Platform.md).

### Executive Summary

Development of a web-based voting application for selecting the Cardinal Vote brand logo using the "vote de valeur" (value voting) methodology. The system will present 11 logo variants to voters who rate each on a scale from -2 to +2, with results aggregated across all participants.

### Project Objectives

1. **Primary Goal**: Facilitate democratic logo selection through structured value voting
2. **User Experience**: Create an intuitive, visually appealing voting interface
3. **Data Integrity**: Ensure accurate vote collection and storage
4. **Results Transparency**: Provide clear visualization of voting outcomes

### Functional Requirements

#### 1. Voter Registration

- **Name Input**: Mandatory field for voter identification
- **Validation**: Prevent empty submissions
- **Privacy**: No authentication required, name-based tracking only

#### 2. Voting Interface

- **Logo Presentation**:
  - Display logos one at a time in full resolution
  - Randomize presentation order per voter to eliminate position bias
  - Clear navigation between logos
- **Rating System**:
  - 5-point scale: -2 (Fortement rejeté), -1 (Rejeté), 0 (Neutre), +1 (Accepté), +2 (Fortement accepté)
  - Radio button implementation for single selection enforcement
  - Visual distinction between rating levels (colors/icons)
- **Progress Tracking**: Visual indicator showing completion status (e.g., "Logo 3 of 11")

#### 3. Vote Review & Confirmation

- **Summary Page**: Display all logos with assigned ratings
- **Edit Capability**: Allow voters to modify ratings before final submission
- **Confirmation Action**: Explicit submit button with confirmation dialog

#### 4. Data Management

- **Storage Solution**:
  - JSON file-based storage for simplicity
  - **Current Implementation**: PostgreSQL with async support for production deployment
- **Data Structure**:
  ```json
  {
    "votes": [
      {
        "voter_name": "string",
        "timestamp": "ISO 8601",
        "ratings": {
          "option-uuid-1": -2 to 2,
          "option-uuid-2": -2 to 2,
          ...
        }
      }
    ]
  }
  ```
- **Persistence**: Votes accumulate across sessions

#### 5. Results Dashboard (Admin View)

- **Aggregate Statistics**:
  - Average rating per logo
  - Vote distribution visualization
  - Total number of voters
- **Ranking Display**: Logos sorted by average score
- **Export Capability**: CSV download of raw voting data

### Non-Functional Requirements

#### 1. User Interface

- **Responsive Design**: Mobile-first approach, works on all devices
- **Accessibility**: WCAG 2.1 AA compliance
- **Visual Design**:
  - Clean, modern aesthetic aligned with Cardinal Vote eco-friendly brand
  - Green color palette with nature-inspired elements
  - Smooth transitions and micro-interactions

#### 2. Performance

- **Load Time**: < 3 seconds initial load
- **Image Optimization**: Lazy loading, appropriate compression
- **Client-Side Validation**: Instant feedback on user actions

#### 3. Security & Privacy

- **Input Sanitization**: Prevent XSS attacks
- **Rate Limiting**: Prevent vote spamming
- **Data Privacy**: No personal data beyond voter names
- **CORS Configuration**: Proper headers if API-based

### Technical Architecture

#### Selected Stack (Optimized for Ubuntu Deployment)

**Backend: FastAPI + Uvicorn**

- **Framework**: FastAPI (Python) - modern, fast, with automatic API documentation
- **Server**: Uvicorn ASGI server for production deployment
- **Storage**: PostgreSQL with async support (current implementation)
- **File Handling**: Static file serving for logo images

**Frontend: Vanilla JavaScript + Modern CSS**

- **Approach**: Single-page application without framework dependencies
- **Styling**: Modern CSS with CSS Grid and Flexbox for mobile-first responsive design
- **Optimization**: Minimal JavaScript, progressive enhancement
- **Mobile Priority**: Touch-friendly interface, optimized for mobile screens

**Deployment Architecture**

```
[Internet] → [Nginx/Apache Reverse Proxy + SSL]
            → [Uvicorn on localhost:8000]
            → [FastAPI Application]
            → [PostgreSQL Database (async)]
```

#### Alternative Deployment Options

**Option A: Docker Container**

- Dockerfile with multi-stage build
- Docker Compose for complete stack
- Easy deployment with single command
- Port mapping to local 8000

**Option B: Direct Python Deployment**

- Python virtual environment
- Systemd service for auto-restart
- Uvicorn running on localhost:8000
- Simple update process via Git pull

**Option C: Docker + Traefik**

- Traefik as reverse proxy with automatic SSL
- Docker Swarm or Docker Compose
- Auto-discovery of services
- Built-in load balancing

#### Development Workflow

1. **Version Control**: Git with feature branches
2. **Code Quality**: Black/Ruff for Python, Prettier for frontend
3. **Testing**: Pytest for backend, manual testing for frontend
4. **CI/CD**: Simple deployment scripts for Ubuntu server

### User Journey

1. **Landing Page**
   - Welcome message explaining the voting process
   - Name input field
   - "Commencer le vote" button

2. **Voting Flow**
   - Logo displayed prominently (centered, large)
   - Rating scale below with clear labels
   - "Suivant" button (disabled until rating selected)
   - Progress bar at top

3. **Review Page**
   - Grid view of all logos with ratings
   - Edit buttons on each card
   - "Confirmer mes votes" prominent CTA

4. **Confirmation**
   - Thank you message
   - Option to view current results (optional)
   - Share buttons for social media

### Implementation Phases

#### Phase 1: MVP (2-3 days)

- FastAPI backend with PostgreSQL database (async)
- Mobile-first responsive interface
- Core voting functionality
- Basic results display
- Docker containerization

#### Phase 2: Enhancement (1-2 days)

- Improved UI/UX with CSS animations
- Results visualization with charts
- Data export functionality (CSV)
- Admin dashboard

#### Phase 3: Deployment (1 day)

- Ubuntu server setup
- Systemd service configuration
- Reverse proxy configuration guide
- Deployment documentation
- Performance testing

### Success Metrics

- **Participation Rate**: Target 80%+ of invited voters
- **Completion Rate**: 95%+ of started votes completed
- **User Satisfaction**: Post-vote feedback score > 4.5/5
- **Technical Performance**: 99.9% uptime, <3s load time

### Risk Mitigation

- **Data Loss**: Regular backups, version control for vote data
- **Duplicate Voting**: Name-based tracking with optional IP logging
- **Browser Compatibility**: Progressive enhancement approach
- **Scalability**: Prepared for 100-1000 concurrent voters

### Deliverables

1. **Functional Voting Application** (FastAPI backend + frontend)
2. **Admin Dashboard for Results** (integrated into main app)
3. **Docker Compose Configuration** (for easy deployment)
4. **README with Deployment Instructions** (not server configuration)
5. **Source Code with Documentation**

### Non-Deliverables (User Responsibility)

- Ubuntu server setup and configuration
- Reverse proxy (Nginx/Apache) configuration
- SSL certificate management
- Server monitoring and maintenance
- Backup infrastructure

### Timeline

- **Day 1-2**: Frontend development and UI implementation
- **Day 3**: Backend integration and data persistence
- **Day 4**: Testing, bug fixes, and deployment
- **Day 5**: Buffer for refinements and documentation

### Deployment Requirements

#### Server Prerequisites

- **OS**: Ubuntu 20.04 LTS or newer
- **Python**: 3.9+
- **Resources**: Minimum 1GB RAM, 10GB storage
- **Network**: Open port for internal communication (8000)

#### Deployment Commands

```bash
# Option 1: Docker deployment
docker-compose up -d

# Option 2: Direct Python deployment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Option 3: Systemd service
sudo systemctl start cardinal-vote-voting
sudo systemctl enable cardinal-vote-voting
```

#### Reverse Proxy Configuration (Nginx example)

```nginx
location /voting/ {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Mobile-First Design Principles

#### Responsive Breakpoints

- **Mobile**: 320px - 768px (primary focus)
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+

#### Touch Optimization

- **Button Size**: Minimum 44x44px touch targets
- **Spacing**: Adequate padding between interactive elements
- **Gestures**: Swipe support for navigation between logos
- **Viewport**: Proper meta tags for mobile rendering

#### Performance for Mobile

- **Image Optimization**: WebP format with fallbacks
- **Lazy Loading**: Load images as needed
- **CSS**: Minimal, inlined critical CSS
- **JavaScript**: Minimal, async loading
- **Caching**: Aggressive caching headers for static assets

### Post-Launch Considerations

- Monitor voting patterns for anomalies
- Gather user feedback for future improvements
- Archive final results with timestamps
- Prepare presentation materials for stakeholder review
- Backup strategy for vote data
- Log rotation and monitoring setup
