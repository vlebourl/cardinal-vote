# Sprint 2: User Journey Restoration - Task Breakdown

**Sprint Goal**: Enable complete user journey from authentication to vote creation and sharing
**Duration**: 5 days
**Priority**: High
**Dependencies**: Sprint 1 (Authentication foundation) completed

---

## Task Overview

| Task ID | Component               | Effort   | Dependencies | Critical Path |
| ------- | ----------------------- | -------- | ------------ | ------------- |
| T-001   | Vote Creation Interface | 1.5 days | Sprint 1     | Yes           |
| T-002   | Enhanced Dashboard      | 1.5 days | Sprint 1     | Yes           |
| T-003   | API Extensions          | 1 day    | T-001        | Yes           |
| T-004   | Vote Preview & Sharing  | 1.5 days | T-001, T-003 | Yes           |
| T-005   | Testing & Validation    | 1 day    | All tasks    | Yes           |

---

## T-001: Vote Creation Interface Implementation

**Priority**: Critical
**Effort**: 1.5 days
**Owner**: Frontend Developer
**Dependencies**: Sprint 1 authentication foundation

### Description

Implement dynamic vote creation modal with Material Design 3 components, supporting up to 20 options with add/remove functionality and access control settings.

### Implementation Scope

- Create vote creation modal HTML template
- Implement VoteCreationManager JavaScript class
- Add dynamic option management (2-20 options)
- Integrate access control settings (public/auth/access codes)

### Acceptance Criteria

```gherkin
Scenario: User opens vote creation modal
  Given user is logged in and on dashboard
  When user clicks "Create Vote" button
  Then vote creation modal should open with Material Design 3 styling
  And form should display title field, description field, and 2 default option fields
  And modal should be responsive on mobile devices

Scenario: User adds vote options dynamically
  Given vote creation modal is open
  When user clicks "Add Option" button
  Then a new option field should appear with proper numbering
  And option counter should update to show current count
  And user should be able to add up to 20 options maximum

Scenario: User removes vote options
  Given vote creation modal has more than 2 options
  When user clicks remove button on an option
  Then that option should be removed with animation
  And remaining options should renumber correctly
  And minimum of 2 options should be enforced

Scenario: User configures access settings
  Given vote creation modal is open
  When user toggles "Require user account" setting
  Then setting should be reflected in form state
  And when user toggles "Protect with access code"
  Then access code field should appear/hide appropriately

Scenario: User submits valid vote
  Given user has filled required fields (title, 2+ options)
  When user clicks "Create Vote" button
  Then form should validate successfully
  And API call should be made to create vote
  And user should be redirected to vote preview page
```

### Technical Requirements

- **Files to Create**:
  - `static/css/vote-creation.css`
  - `static/js/vote-creation-manager.js`
  - Vote creation modal HTML in dashboard template
- **Integration**: Connect to existing dashboard.js `createVote()` method
- **Validation**: Client-side validation, API error handling, loading states

### Validation Commands

```bash
# Test modal functionality
npm run test:frontend
# Responsive design validation
npm run test:responsive
# Accessibility check
npm run test:a11y
```

---

## T-002: Enhanced Dashboard Implementation

**Priority**: Critical
**Effort**: 1.5 days
**Owner**: Frontend Developer
**Dependencies**: Sprint 1 dashboard foundation

### Description

Transform basic dashboard into comprehensive overview with 6 status cards and activity timeline following Material Design 3 patterns and industry best practices.

### Implementation Scope

- Replace basic stats section with 6 status cards grid
- Implement activity timeline with pagination
- Add real-time data loading and refresh functionality
- Ensure responsive design across all screen sizes

### Acceptance Criteria

```gherkin
Scenario: User views enhanced dashboard
  Given user is logged in
  When user navigates to dashboard
  Then 6 status cards should display in responsive grid
  And cards should show: Total Votes, Active Votes, Responses, Drafts, Weekly Activity, Quick Actions
  And activity timeline should appear below cards

Scenario: Dashboard loads user statistics
  Given user has existing votes in database
  When dashboard loads
  Then status cards should populate with real data from API
  And loading states should be shown while data loads
  And metrics should update correctly based on user's votes

Scenario: Activity timeline displays user actions
  Given user has recent activity
  When dashboard loads
  Then timeline should show recent actions in reverse chronological order
  And each timeline item should have appropriate icon and description
  And timeline should support pagination for more than 10 items

Scenario: Dashboard works on mobile devices
  Given user accesses dashboard on mobile
  When page loads
  Then status cards should stack vertically
  And timeline should remain readable and functional
  And all interactive elements should be touch-friendly
```

### Technical Requirements

- **Files to Modify**:
  - `templates/user_dashboard.html`
  - `static/css/dashboard.css`
  - `static/js/dashboard.js`
- **Integration**: Connect to new statistics API endpoint
- **Performance**: Lazy loading, caching, loading states

### Validation Commands

```bash
# Dashboard functionality
curl -H "Authorization: Bearer {token}" http://localhost:8000/api/votes/stats
# Mobile responsiveness
npm run test:mobile
# Performance check
npm run test:performance
```

---

## T-003: API Extensions Implementation

**Priority**: Critical
**Effort**: 1 day
**Owner**: Backend Developer
**Dependencies**: T-001 (for vote creation requirements)

### Description

Extend existing vote APIs with enhanced creation capabilities, dashboard statistics, and activity logging to support new frontend features.

### Implementation Scope

- Enhance vote creation endpoint with access controls
- Add dashboard statistics endpoint
- Implement activity logging system
- Add vote preview endpoint

### Acceptance Criteria

```gherkin
Scenario: Enhanced vote creation API
  Given authenticated user with valid JWT
  When POST request sent to /api/votes/ with access control fields
  Then vote should be created with access_code and require_auth fields
  And activity should be logged for timeline
  And response should include sharing URLs

Scenario: Dashboard statistics API
  Given authenticated user with existing votes
  When GET request sent to /api/votes/stats
  Then response should include vote counts by status
  And total responses across all user votes
  And weekly activity summary

Scenario: Activity timeline API
  Given user has recent activity
  When GET request sent to /api/votes/activity
  Then response should include paginated activity items
  And items should be in reverse chronological order
  And proper pagination metadata included
```

### Technical Requirements

- **Files to Modify**:
  - `src/cardinal_vote/vote_routes.py`
  - `src/cardinal_vote/models.py`
- **Database**: Add access_code and require_auth fields to votes table
- **Migration**: SQL migration for new fields and activity table

### Validation Commands

```bash
# API endpoint testing
curl -X POST http://localhost:8000/api/votes/ -H "Content-Type: application/json" -d '{test_data}'
curl http://localhost:8000/api/votes/stats -H "Authorization: Bearer {token}"
# Database migration
uv run alembic upgrade head
# Python validation
uv run ruff check src/ tests/
uv run pytest tests/test_vote_routes.py
```

---

## T-004: Vote Preview & Sharing Interface

**Priority**: Critical
**Effort**: 1.5 days
**Owner**: Full-stack Developer
**Dependencies**: T-001 (vote creation), T-003 (API endpoints)

### Description

Create vote preview interface that shows votes "as voters would see them" with comprehensive sharing controls supporting both public links and access codes.

### Implementation Scope

- Build vote preview template and route
- Implement sharing control panel with copy functionality
- Add access code management
- Create preview-specific styling

### Acceptance Criteria

```gherkin
Scenario: User accesses vote preview
  Given user has created a vote
  When user is redirected to preview page after creation
  Then page should show vote exactly as voters will see it
  And preview banner should indicate this is preview mode
  And sharing panel should be visible at bottom

Scenario: User copies sharing links
  Given user is on vote preview page
  When user clicks "Copy Link" button
  Then public voting URL should be copied to clipboard
  And success message should appear
  And link should work when pasted elsewhere

Scenario: User manages access codes
  Given vote has access code protection enabled
  When user views sharing options
  Then access code should be displayed
  And user should be able to copy the code
  And user should be able to regenerate the code

Scenario: Preview works on mobile
  Given user accesses preview on mobile device
  When page loads
  Then sharing panel should collapse appropriately
  And all copy buttons should work with touch
  And vote content should remain readable
```

### Technical Requirements

- **Files to Create**:
  - `templates/vote_preview.html`
  - `static/css/vote-preview.css`
  - `static/js/vote-preview.js`
- **Integration**: New `/vote-preview/{vote_id}` route in main.py
- **Features**: Copy-to-clipboard, responsive design, sharing options

### Validation Commands

```bash
# Preview page functionality
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/vote-preview/test-id
# Copy functionality (manual test)
# Mobile responsiveness
npm run test:responsive
```

---

## T-005: Comprehensive Testing & Validation

**Priority**: Critical
**Effort**: 1 day
**Owner**: QA/Development Team
**Dependencies**: T-001, T-002, T-003, T-004 completed

### Description

Comprehensive testing of complete user journey, cross-browser compatibility, and performance validation using both automated tools and manual testing procedures.

### Implementation Scope

- Playwright automated UI testing
- Cross-browser compatibility testing
- Mobile device testing
- Performance and accessibility validation
- Complete user journey testing

### Acceptance Criteria

```gherkin
Scenario: Complete user journey works end-to-end
  Given new user visits landing page
  When user registers, creates vote, and shares it
  Then entire workflow should complete without errors
  And each step should work as specified
  And performance should meet requirements (<2s page loads)

Scenario: Responsive design works across devices
  Given user accesses platform on different devices
  When user performs core actions (login, create, share)
  Then functionality should work on desktop, tablet, and mobile
  And UI should adapt appropriately to screen sizes
  And touch interactions should work properly

Scenario: Accessibility standards met
  Given user with assistive technology
  When user navigates platform with keyboard/screen reader
  Then all functionality should be accessible
  And WCAG guidelines should be followed
  And focus indicators should be visible and logical
```

### Technical Requirements

- **Playwright Tests**: Complete UI interaction testing
- **Manual Testing**: Cross-browser, mobile device testing
- **Performance**: Page load times, API response times
- **Accessibility**: Screen reader, keyboard navigation

### Validation Commands

```bash
# Complete test suite
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/
npm run test:playwright
npm run test:accessibility
# Performance testing
npm run test:performance
# Security check
uv run bandit -r src/
```

---

## Implementation Timeline

### Day 1: Vote Creation Foundation

- **Morning**: T-001 HTML template and CSS implementation
- **Afternoon**: T-001 JavaScript VoteCreationManager class
- **Evening**: T-003 API endpoint enhancement planning

### Day 2: Dashboard Enhancement

- **Morning**: T-002 Status cards implementation
- **Afternoon**: T-002 Activity timeline implementation
- **Evening**: T-003 API endpoints implementation

### Day 3: API Integration & Preview

- **Morning**: T-003 Complete API implementation and testing
- **Afternoon**: T-004 Vote preview template and routing
- **Evening**: T-004 Sharing panel implementation

### Day 4: Polish & Integration

- **Morning**: T-004 Complete sharing functionality
- **Afternoon**: End-to-end integration testing
- **Evening**: Cross-browser compatibility testing

### Day 5: Testing & Validation

- **Morning**: T-005 Comprehensive Playwright testing
- **Afternoon**: T-005 Mobile and accessibility testing
- **Evening**: Final validation and deployment preparation

---

## Risk Management

### High-Risk Items

- **Dynamic form complexity**: Extensive testing needed for add/remove options
- **Mobile responsiveness**: Multiple screen sizes to validate
- **API integration timing**: Frontend/backend coordination required

### Mitigation Strategies

- Daily standups for coordination
- Progressive testing throughout implementation
- Fallback plans for complex features

### Success Criteria

- [ ] Complete user journey functional
- [ ] All validation commands pass
- [ ] Responsive design works on all target devices
- [ ] Performance meets requirements (<2s page loads)
- [ ] No regression in existing functionality

---

## Definition of Done

### Technical Checklist

- [ ] All code follows existing patterns and conventions
- [ ] Material Design 3 consistency maintained
- [ ] API endpoints properly documented and tested
- [ ] Database migrations completed
- [ ] All validation commands pass without errors

### User Experience Checklist

- [ ] Complete user journey works without friction
- [ ] Mobile experience feels native and responsive
- [ ] Loading states provide clear feedback
- [ ] Error messages are helpful and clear
- [ ] Accessibility standards met (WCAG compliance)

### Quality Checklist

- [ ] Playwright tests cover critical user paths
- [ ] Cross-browser testing completed
- [ ] Performance requirements met
- [ ] Security considerations addressed
- [ ] Code review completed by team lead

---

_Task Breakdown Generated: January 13, 2025_
_Total Effort: 6.5 days across 5 tasks_
_Critical Path: T-001 → T-003 → T-004 → T-005_
