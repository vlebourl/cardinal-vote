# Project Requirements & Planning (PRP)

## Generalized Voting Platform Transformation

### Executive Summary

Transform the current ToVéCo Logo Voting Platform from a single-purpose application into a **generalized multi-tenant voting platform as a service**. Users will be able to register, create custom votes with text and/or image options, share voting links, and manage their own voting campaigns through dedicated admin panels.

### Project Vision

**From**: Single ToVéCo logo vote with 11 predefined options
**To**: Multi-tenant platform where any user can create unlimited custom votes

**Core Value Proposition**:

- Democratic decision-making tool accessible to everyone
- No-code vote creation with intuitive interface
- Professional results presentation and data export
- Scalable architecture supporting concurrent voting campaigns

### Current State Analysis

#### Existing Strengths ✅

- **Proven voting logic**: -2 to +2 value voting system works well
- **Mobile-first responsive design**: Excellent user experience on all devices
- **Robust backend architecture**: FastAPI + SQLite with comprehensive testing
- **Docker containerization**: Production-ready deployment
- **CI/CD pipeline**: Automated testing and deployment
- **Security fundamentals**: Input validation, CORS, rate limiting

#### Current Limitations ⚠️

- **Single-tenant**: Hard-coded for ToVéCo branding and specific logos
- **No user management**: No registration or authentication system
- **Static content**: Logo files are baked into the container
- **Single vote instance**: Cannot create multiple concurrent votes
- **No admin separation**: All admin functions are global

#### Technical Debt Assessment

- **Database schema**: Current tables are ToVéCo-specific, need generalization
- **File handling**: Static logo serving needs dynamic media management
- **Authentication**: No existing user/session management
- **Multi-tenancy**: No tenant isolation or data separation

### Target Architecture Overview

#### Platform Roles & Permissions

**1. Super Administrator (Platform Owner)**

- Full platform access and management
- User account management (view, suspend, delete)
- Global platform statistics and monitoring
- System configuration and maintenance
- Vote moderation and content management

**2. Registered Users (Vote Creators)**

- Account registration with email verification
- Create unlimited custom votes
- Upload and manage vote option media
- Access dedicated admin panel per vote
- Share vote links and manage voting campaigns
- Export vote results and analytics
- Close/reopen votes and manage lifecycle

**3. Voters (Anonymous Participants)**

- Access votes via unique unguessable links
- Participate without registration (first/last name only)
- CAPTCHA verification for spam prevention
- View results if enabled by vote creator

#### Core Platform Features

**User Management System**

- Email/password registration and authentication
- Email verification workflow
- Password reset functionality
- User profile management
- Session management and security

**Vote Creation & Management**

- Intuitive vote creation wizard
- Text and image option support (PNG/JPG, max 10MB per image)
- Vote configuration (title, description, options, settings)
- Unique unguessable URL generation
- Vote lifecycle management (draft, active, closed)
- Real-time vote monitoring and analytics

**Voting Experience**

- Mobile-optimized voting interface
- CAPTCHA protection against spam
- Progress tracking and vote review
- Responsive design across all devices
- Anonymous participation with name collection

**Results & Analytics**

- Real-time vote results and statistics
- Data visualization with charts and graphs
- CSV/PDF export functionality
- Vote history and audit trails
- Shareable results pages

### Detailed Functional Requirements

#### 1. User Registration & Authentication

**Registration Workflow**

- Email and password registration form
- Password strength validation (min 8 chars, mix of letters/numbers/symbols)
- Email verification via activation link
- Account activation and welcome flow
- Terms of service and privacy policy acceptance

**Authentication Features**

- Secure login with email/password
- "Remember me" functionality with secure cookies
- Password reset via email link
- Session timeout and security measures
- Account lockout after failed login attempts

**User Profile Management**

- Update email address (with re-verification)
- Change password with current password confirmation
- Account deletion with data export option
- Activity history and vote creation logs

#### 2. Vote Creation System

**Vote Creation Wizard**

_Step 1: Basic Information_

- Vote title (required, max 100 characters)
- Vote description (optional, max 500 characters, Markdown support)
- Vote category/tags (optional, for organization)

_Step 2: Voting Options_

- Add text options (required, max 100 characters each)
- Upload image options (PNG/JPG, max 10MB, auto-resize to standard dimensions)
- Mixed text/image options support
- Drag-and-drop reordering
- Option limit: 30 maximum per vote

_Step 3: Vote Settings_

- Voting scale: -2 to +2 (fixed for initial version)
- Results visibility: Show during vote or only after closure
- Vote duration: Manual close only (no time limits initially)
- Voter name requirement: First/last name mandatory
- CAPTCHA requirement: Enabled by default

_Step 4: Review & Launch_

- Preview vote as voters will see it
- Generate unique unguessable URL (UUID-based)
- Save as draft or publish immediately
- Share options (copy link, QR code generation)

**Vote Management Dashboard**

- List all user's votes with status (draft, active, closed)
- Quick stats: participant count, completion rate, creation date
- Bulk actions: duplicate, delete, export
- Search and filter votes by status, date, title

#### 3. Voting Experience Enhancement

**Vote Access & Security**

- Unique URL format: `/vote/{uuid}` (128-bit UUID)
- CAPTCHA challenge before vote access (hCaptcha integration)
- Browser fingerprinting for duplicate vote detection
- IP-based rate limiting (max 1 vote per IP per vote)

**Enhanced Voting Interface**

- Vote branding: Creator name and vote title prominently displayed
- Progress indicator: "Option X of Y" with completion percentage
- Option presentation: Randomized order per voter
- Image optimization: Lazy loading, responsive sizing, WebP support
- Vote validation: Ensure all options are rated before submission

**Vote Review & Submission**

- Summary page showing all options with assigned ratings
- Edit capability for any rating before final submission
- Confirmation dialog with vote summary
- Thank you page with optional results preview
- Social sharing options for completed vote

#### 4. Results & Analytics System

**Real-time Analytics Dashboard**

- Live participant count and completion rate
- Average rating per option with visual bars
- Vote distribution charts (histogram of ratings)
- Participation timeline (votes over time)
- Geographic distribution (if IP geolocation enabled)

**Advanced Results Features**

- Ranking by average score with confidence intervals
- Statistical significance indicators
- Voter demographics (anonymous aggregate data)
- Comment system (optional, for qualitative feedback)
- Results comparison tools (A/B testing between similar votes)

**Data Export Options**

- CSV export: Raw vote data with timestamps
- PDF report: Professional results presentation
- JSON API: Programmatic access to vote data
- Embeddable results widget for external websites

#### 5. Administrative Functions

**Vote Creator Admin Panel**

- Vote performance metrics and KPIs
- Voter management: view participants, detect anomalies
- Vote modification: update title/description (not options)
- Vote lifecycle: pause, resume, close, reopen, delete
- Communication tools: message to participants, announcement system

**Super Administrator Functions**

- User management: view all users, account status, activity logs
- Vote moderation: review flagged content, content policy enforcement
- Platform analytics: usage statistics, growth metrics
- System monitoring: performance metrics, error tracking
- Content management: manage reported votes, user disputes

### Technical Architecture Design

#### Architecture Pattern: Multi-Tenant with Shared Database

**Rationale**: For expected scale (few dozen concurrent votes), shared database with tenant isolation provides optimal balance of simplicity and performance.

**Database Design Strategy**:

```sql
-- Tenant isolation via user_id foreign keys
-- All vote-related data linked to creating user
-- Indexes on tenant columns for query performance
```

#### Technology Stack Evolution

**Backend Enhancements**

- **Framework**: FastAPI (maintain current choice)
- **Authentication**: FastAPI-Users with JWT tokens
- **Database**: PostgreSQL (upgrade from SQLite for concurrency)
- **File Storage**: Local filesystem with organized directory structure
- **Email**: SMTP integration for verification and notifications
- **CAPTCHA**: hCaptcha integration for spam prevention

**Frontend Architecture**

- **Approach**: Maintain vanilla JavaScript (no framework dependencies)
- **Structure**: Modular JavaScript with ES6 modules
- **State Management**: Simple state objects with localStorage persistence
- **API Client**: Fetch API with error handling and retries
- **UI Components**: Reusable component system for consistency

**Infrastructure Updates**

- **Database Migration**: SQLite to PostgreSQL with data preservation
- **File Management**: Organized media storage with cleanup routines
- **Caching**: Redis for session storage and rate limiting
- **Monitoring**: Basic logging and health checks
- **Backup**: Automated database and file backups

#### Database Schema Design

**Core Tables**

```sql
-- User Management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Vote Configuration
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft', -- draft, active, closed
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    slug VARCHAR(255) UNIQUE NOT NULL -- URL-safe unique identifier
);

-- Vote Options (text or image)
CREATE TABLE vote_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vote_id UUID NOT NULL REFERENCES votes(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL, -- 'text' or 'image'
    content TEXT NOT NULL, -- text content or image filename
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Voter Responses
CREATE TABLE voter_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vote_id UUID NOT NULL REFERENCES votes(id) ON DELETE CASCADE,
    voter_name VARCHAR(100) NOT NULL,
    voter_ip INET,
    responses JSONB NOT NULL, -- {option_id: rating}
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vote_id, voter_ip) -- Prevent duplicate votes from same IP
);

-- Audit and Analytics
CREATE TABLE vote_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vote_id UUID NOT NULL REFERENCES votes(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'view', 'start', 'complete', 'abandon'
    event_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes for Performance**

```sql
CREATE INDEX idx_votes_creator_id ON votes(creator_id);
CREATE INDEX idx_vote_options_vote_id ON vote_options(vote_id);
CREATE INDEX idx_voter_responses_vote_id ON voter_responses(vote_id);
CREATE INDEX idx_vote_analytics_vote_id ON vote_analytics(vote_id);
CREATE INDEX idx_votes_slug ON votes(slug);
CREATE INDEX idx_users_email ON users(email);
```

#### File Storage Strategy

**Directory Structure**

```
uploads/
├── votes/
│   └── {vote_id}/
│       ├── options/
│       │   ├── {option_id}_original.jpg
│       │   ├── {option_id}_thumbnail.jpg
│       │   └── {option_id}_display.jpg
│       └── exports/
│           ├── results.pdf
│           └── data.csv
└── temp/
    └── {upload_session_id}/
```

**Image Processing Pipeline**

- **Upload validation**: File type, size, image dimensions
- **Image processing**: Generate multiple sizes (thumbnail, display, original)
- **Optimization**: WebP conversion with fallback support
- **Cleanup**: Remove temporary files and orphaned uploads
- **Storage limits**: 100MB per user, 10MB per file

#### Security Implementation

**Authentication & Authorization**

- **JWT tokens**: Secure session management with refresh tokens
- **Password hashing**: bcrypt with appropriate work factor
- **Email verification**: Cryptographically secure tokens
- **Rate limiting**: Per-IP and per-user limits on sensitive operations
- **CORS configuration**: Proper headers for API access

**Input Validation & Sanitization**

- **Pydantic models**: Strict input validation on all endpoints
- **SQL injection prevention**: Parameterized queries only
- **XSS protection**: Content sanitization and CSP headers
- **File upload security**: MIME type validation, virus scanning
- **CAPTCHA integration**: Spam prevention for voter participation

**Data Protection**

- **Encryption at rest**: Database encryption for sensitive data
- **HTTPS enforcement**: TLS 1.3 for all communication
- **Privacy compliance**: GDPR-ready data handling
- **Data retention**: Configurable cleanup of old vote data
- **Audit logging**: Track all administrative actions

### Implementation Phases

#### Phase 1: Foundation (Weeks 1-3)

**Database & Authentication Infrastructure**

_Week 1: Database Migration_

- Migrate from SQLite to PostgreSQL
- Design and implement new multi-tenant schema
- Create database migration scripts and backup procedures
- Set up PostgreSQL in development and production environments

_Week 2: User Management System_

- Implement user registration with email verification
- Add authentication endpoints (login, logout, password reset)
- Create user profile management functionality
- Add session management with JWT tokens

_Week 3: Basic Vote Creation_

- Build vote creation API endpoints
- Implement basic vote storage and retrieval
- Create unique URL generation for votes
- Add basic vote status management (draft, active, closed)

**Deliverables:**

- ✅ PostgreSQL database with complete schema
- ✅ User registration and authentication system
- ✅ Basic vote creation and management API
- ✅ Database migration from current ToVéCo data

**Success Criteria:**

- Users can register and verify email accounts
- Users can log in and access authenticated endpoints
- Basic vote creation workflow functional
- All existing ToVéCo vote data preserved and accessible

#### Phase 2: Vote Creation & Management (Weeks 4-6)

**Complete Vote Creation Workflow**

_Week 4: Vote Creation Wizard_

- Build multi-step vote creation interface
- Implement text option management (add, edit, reorder)
- Add vote settings configuration (title, description, options)
- Create vote preview functionality

_Week 5: Media Upload System_

- Implement image upload with validation and processing
- Add thumbnail generation and image optimization
- Create file storage management and cleanup routines
- Build mixed text/image option support

_Week 6: Vote Management Dashboard_

- Create user dashboard listing all votes
- Add vote status management (draft, publish, close)
- Implement vote editing and configuration updates
- Build vote analytics basic tracking

**Deliverables:**

- ✅ Complete vote creation wizard with all option types
- ✅ Image upload and processing system
- ✅ User dashboard for vote management
- ✅ Vote lifecycle management tools

**Success Criteria:**

- Users can create votes with text and image options
- Image uploads work reliably with proper validation
- Vote creators can manage their vote lifecycle
- Dashboard provides clear overview of user's votes

#### Phase 3: Enhanced Voting Experience (Weeks 7-8)

**Voter Interface & Security**

_Week 7: Voting Interface Enhancement_

- Adapt current voting UI for dynamic vote content
- Implement option randomization per voter
- Add progress tracking and vote review functionality
- Create responsive design for all vote types

_Week 8: Security & Anti-Spam_

- Integrate CAPTCHA system for voter verification
- Implement IP-based duplicate vote prevention
- Add rate limiting for vote access and submissions
- Create voter analytics and tracking

**Deliverables:**

- ✅ Enhanced voting interface supporting all option types
- ✅ CAPTCHA integration and spam prevention
- ✅ Duplicate vote detection and prevention
- ✅ Voter analytics and tracking system

**Success Criteria:**

- Voting experience works seamlessly across devices
- CAPTCHA effectively prevents automated voting
- Duplicate votes are reliably detected and prevented
- Basic voter analytics provide useful insights

#### Phase 4: Results & Analytics (Weeks 9-10)

**Results Dashboard & Export**

_Week 9: Results Dashboard_

- Create real-time results visualization
- Build statistical analysis and ranking displays
- Add vote comparison and trend analysis
- Implement results sharing functionality

_Week 10: Data Export & Reporting_

- Build CSV export with comprehensive vote data
- Create PDF report generation with professional formatting
- Add embeddable results widgets
- Implement data archival and cleanup tools

**Deliverables:**

- ✅ Comprehensive results dashboard with visualizations
- ✅ Multiple export formats (CSV, PDF, JSON)
- ✅ Results sharing and embedding capabilities
- ✅ Data management and archival tools

**Success Criteria:**

- Results display updates in real-time during voting
- Export formats provide complete and accurate data
- Results can be easily shared and embedded
- Data management tools work reliably

#### Phase 5: Admin & Platform Management (Weeks 11-12)

**Administrative Tools & Platform Completion**

_Week 11: Super Admin Functions_

- Build admin panel for platform oversight
- Implement user management tools (view, suspend, delete)
- Add vote moderation and content management
- Create platform analytics and monitoring

_Week 12: Polish & Production Readiness_

- Comprehensive testing of all functionality
- Performance optimization and caching implementation
- Security audit and penetration testing
- Production deployment and monitoring setup

**Deliverables:**

- ✅ Complete super admin panel with all management tools
- ✅ Content moderation and platform oversight capabilities
- ✅ Production-ready platform with monitoring and backups
- ✅ Comprehensive documentation and user guides

**Success Criteria:**

- Super admin can effectively manage users and platform
- All platform functions work reliably under load
- Security measures protect against common threats
- Platform is ready for production use with real users

### Migration Strategy

#### Current Data Preservation

**Vote Data Migration**

- Export existing ToVéCo vote data from current SQLite database
- Create migration script to populate new PostgreSQL schema
- Preserve all voter responses and timestamps
- Maintain results and analytics continuity

**Image Asset Migration**

- Move existing logo files to new organized file structure
- Generate thumbnails and optimized versions for existing images
- Update database references to new file paths
- Implement fallback for any missing assets

#### Deployment Strategy

**Blue-Green Deployment Approach**

- Set up new platform infrastructure alongside current system
- Test migration with copy of production data
- Gradual cutover with ability to rollback if issues arise
- DNS switching for seamless transition

**Data Validation**

- Comprehensive comparison of migrated vs original data
- Functional testing of all existing vote functionality
- Performance testing with production-scale data
- User acceptance testing before final switchover

### Quality Assurance & Testing

#### Testing Strategy

**Unit Testing (Backend)**

- Test coverage >90% for all business logic
- Database operations and migration testing
- Authentication and authorization testing
- File upload and processing validation

**Integration Testing**

- API endpoint testing with real database
- Authentication flow testing across all features
- File storage and retrieval testing
- Email delivery and verification testing

**End-to-End Testing**

- Complete user registration and vote creation workflow
- Full voting experience from multiple voter perspectives
- Results calculation and export functionality
- Admin panel operations and user management

**Performance Testing**

- Load testing with multiple concurrent votes
- Database performance under expected load
- File upload performance and storage limits
- API response times under various conditions

#### Security Testing

**Vulnerability Assessment**

- SQL injection testing on all input endpoints
- XSS prevention validation in user-generated content
- Authentication bypass attempts
- File upload security (malware, size limits, type validation)
- Rate limiting effectiveness testing

**Privacy & Compliance**

- Data handling audit for privacy compliance
- User data export and deletion functionality
- Cookie and session management review
- Third-party integration security (CAPTCHA, email)

### Success Metrics & KPIs

#### Platform Adoption Metrics

**User Growth**

- Monthly active users (MAU)
- New user registrations per month
- User retention rate (30-day, 90-day)
- Email verification completion rate

**Platform Usage**

- Votes created per month
- Average options per vote
- Total voter participation across all votes
- Vote completion rate (started vs finished)

#### Technical Performance Metrics

**System Performance**

- API response times (95th percentile <500ms)
- Database query performance (all queries <100ms)
- File upload success rate (>99%)
- Platform uptime (>99.9%)

**User Experience Metrics**

- Vote creation completion rate (>85%)
- Voting experience satisfaction (survey-based)
- Mobile vs desktop usage patterns
- Most popular vote types and configurations

### Risk Assessment & Mitigation

#### High-Risk Areas

**Data Migration Risk**

- _Risk_: Data loss or corruption during SQLite to PostgreSQL migration
- _Mitigation_: Comprehensive backup strategy, phased migration, extensive validation
- _Contingency_: Ability to rollback to original system if migration fails

**User Adoption Risk**

- _Risk_: Current ToVéCo users unable to access historical data
- _Mitigation_: Preserve all existing URLs and functionality during transition
- _Contingency_: Maintain read-only access to legacy system during transition period

**Security Risk**

- _Risk_: New authentication system introduces vulnerabilities
- _Mitigation_: Security audit, penetration testing, gradual rollout
- _Contingency_: Rapid rollback capability and incident response plan

#### Medium-Risk Areas

**Performance Risk**

- _Risk_: New multi-tenant architecture performs worse than current system
- _Mitigation_: Load testing, performance monitoring, database optimization
- _Contingency_: Architecture adjustments and performance tuning plan

**File Storage Risk**

- _Risk_: Large file uploads impact system performance or storage costs
- _Mitigation_: File size limits, image compression, storage monitoring
- _Contingency_: Storage cleanup tools and usage limits enforcement

#### Low-Risk Areas

**Feature Complexity Risk**

- _Risk_: Advanced features delay core platform launch
- _Mitigation_: Phased development approach, MVP-first strategy
- _Contingency_: Feature removal or delay without impacting core functionality

### Resource Requirements

#### Development Resources

**Phase 1-2 (Weeks 1-6): Foundation & Core Features**

- Full-time development focus on backend architecture
- Database design and migration expertise
- User interface development for vote creation

**Phase 3-4 (Weeks 7-10): Enhancement & Analytics**

- Frontend development for enhanced voting experience
- Data visualization and reporting development
- Security implementation and testing

**Phase 5 (Weeks 11-12): Admin & Launch**

- Admin panel development
- Performance optimization and testing
- Production deployment and monitoring

#### Infrastructure Requirements

**Development Environment**

- PostgreSQL database server
- Redis for caching and session storage
- File storage system with backup capability
- Email service for user verification

**Production Environment**

- Scalable web server infrastructure
- Database hosting with backup and monitoring
- CDN for file serving and performance
- Monitoring and alerting systems

### Success Dependencies

#### Technical Dependencies

- Successful migration from SQLite to PostgreSQL
- Reliable email service integration for user verification
- CAPTCHA service integration for spam prevention
- File storage and processing pipeline stability

#### User Experience Dependencies

- Intuitive vote creation workflow that doesn't require training
- Mobile-first design that works across all devices
- Fast and reliable voting experience for participants
- Clear and professional results presentation

#### Business Dependencies

- Clear communication to existing users about platform evolution
- Documentation and support materials for new features
- Feedback collection and iteration based on user needs
- Long-term maintenance and feature development plan

### Post-Launch Evolution

#### Short-term Enhancements (Months 1-3)

- User feedback integration and UI improvements
- Performance optimization based on real usage patterns
- Additional export formats and integrations
- Mobile app considerations and PWA enhancements

#### Medium-term Features (Months 4-12)

- Alternative voting systems (ranked choice, approval voting)
- Advanced analytics and reporting features
- User collaboration features (shared vote creation)
- API for third-party integrations

#### Long-term Vision (Year 2+)

- Enterprise features for organizational use
- Advanced branding and customization options
- Integration with popular platforms (Slack, Teams, etc.)
- AI-powered insights and recommendations

---

**Document Status**: Draft for Review  
**Priority**: High - Strategic Platform Evolution  
**Estimated Effort**: 12 weeks full-time development  
**Dependencies**: Current platform stability, user communication plan  
**Next Action**: Technical architecture review and implementation planning  
**Success Measure**: Successful transformation to multi-tenant platform with user adoption >80% within 3 months of launch
