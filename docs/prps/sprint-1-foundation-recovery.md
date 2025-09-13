# PRP: Sprint 1 Foundation Recovery - Cardinal Vote Platform

**Document Version:** 1.0
**Created:** January 13, 2025
**Sprint:** 1 (Foundation Recovery)
**Estimated Duration:** 1 week
**Related Documents:**

- [Brainstorming Session: Web Interface Analysis](/docs/brainstorming/2025-01-13-web-interface-architecture-validation.md)
- [Architecture Documentation](/docs/ARCHITECTURE.md)

---

## Executive Summary

Sprint 1 focuses on restoring basic user functionality to the Cardinal Vote platform by fixing broken authentication flows and validating backend API infrastructure. Critical discovery revealed that while the platform has comprehensive Material Design 3 visual implementation and robust backend APIs, users cannot authenticate or access core functionality due to missing authentication modals and broken UI elements.

**Primary Objectives:**

1. **Backend API Validation** - Verify that 14 existing authentication and vote management endpoints function correctly
2. **Landing Page Authentication Fix** - Implement working login/register modals with Material Design 3 compliance
3. **Basic User Dashboard** - Create minimal post-login landing page for Sprint 2 foundation

**Success Criteria:**

- Users can successfully register and login through the landing page
- JWT tokens are properly generated, stored, and validated
- Users land on a functional dashboard after authentication
- All existing functionality remains intact

---

## Problem Statement

### Current Broken State

The Cardinal Vote platform architecture analysis revealed critical functionality gaps:

- **Landing Page**: Visually complete Material Design 3 implementation but non-functional interactive elements
- **Authentication Flow**: No working path for user registration or login despite comprehensive backend infrastructure
- **User Journey**: Complete breakdown at step 1 - users cannot access any platform functionality
- **Missing Components**: Authentication modals entirely absent from Material Design landing page

### Business Impact

- **User Acquisition**: New users cannot register or access the platform
- **User Retention**: Existing users cannot login to manage their votes
- **Platform Value**: Comprehensive backend infrastructure (14 API endpoints) is inaccessible to users
- **Development Velocity**: Frontend development blocked until basic authentication works

### Root Cause Analysis

1. **Material Design 3 Migration**: Authentication modals exist in legacy `landing.html` but are missing from active `landing_material.html`
2. **Broken UI Elements**: "Get Started" button, admin links, and navigation menu are non-functional
3. **Architectural Mismatch**: Admin links point to super-admin instead of user-admin flow
4. **Integration Gap**: Frontend lacks connection to working backend authentication APIs

---

## Discovery & Research

### Codebase Analysis Results

#### **CRITICAL FINDING: Missing Authentication Infrastructure**

The current `/templates/landing_material.html` lacks authentication modals entirely, while comprehensive Material Design 3 components and authentication APIs exist and are ready for integration.

#### **Existing Working Components**

✅ **Backend APIs** (Fully Functional):

- `POST /api/auth/register` - User registration with validation
- `POST /api/auth/login` - JWT authentication
- `POST /api/auth/token` - OAuth2-compatible token endpoint
- `GET /api/auth/me` - Current user information
- Complete JWT token generation and validation system

✅ **Material Design 3 System** (Ready for Use):

- Complete dialog components with animations and accessibility
- Form input patterns with floating labels and validation
- Button styles and interaction patterns
- Snackbar notification system for error handling
- CSP-compliant event handling architecture

✅ **Security Infrastructure**:

- Input sanitization with XSS prevention
- JWT token management patterns
- Content Security Policy compliance
- Accessibility (ARIA) requirements

#### **Missing Components Identified**

❌ **Authentication Modals**: No login/register dialogs in Material Design landing page
❌ **Modal Trigger Logic**: "Get Started" and menu buttons lack event handlers
❌ **Form Submission Logic**: No API integration for authentication forms
❌ **Post-Login Routing**: No destination after successful authentication
❌ **User Dashboard Template**: No basic landing page for authenticated users

### Technical Architecture

#### **Authentication Flow Pattern** (To Implement):

```
Landing Page → Modal Trigger → Authentication Modal → API Call → JWT Storage → Dashboard Redirect
```

#### **API Integration Pattern** (From codebase analysis):

```javascript
// JWT Token Storage (Session Storage - per requirement)
sessionStorage.setItem('jwt_token', response.access_token)
sessionStorage.setItem('refresh_token', response.refresh_token)

// API Request Headers
headers: {
  'Authorization': `Bearer ${sessionStorage.getItem('jwt_token')}`,
  'Content-Type': 'application/json'
}
```

#### **Material Design 3 Components** (Available):

```css
/* Dialog System - Ready for Use */
.md-dialog-scrim {
  /* Backdrop overlay */
}
.md-dialog {
  /* Modal container */
}
.md-dialog-visible {
  /* Show animation */
}

/* Form Components - Ready for Use */
.md-text-field {
  /* Input containers */
}
.md-text-field-label {
  /* Floating labels */
}
.md-button-filled {
  /* Primary actions */
}
.md-button-text {
  /* Secondary actions */
}

/* Notifications - Ready for Use */
.md-snackbar {
  /* Error/success messages */
}
```

---

## Technical Requirements

### Phase 1: Backend API Validation (Days 1-2)

#### **API Endpoint Testing**

Test all critical authentication and vote management endpoints to verify functionality:

**Authentication Endpoints:**

- `POST /api/auth/register` - User registration with input validation
- `POST /api/auth/login` - JWT authentication with error handling
- `POST /api/auth/token` - OAuth2 token endpoint (form-data format)
- `GET /api/auth/me` - Current user profile retrieval
- `POST /api/auth/refresh` - Token refresh mechanism

**Vote Management Endpoints (Validation Only):**

- `POST /api/votes/` - Vote creation endpoint
- `GET /api/votes/` - User vote listing
- `GET /api/votes/public/{slug}` - Public vote access

#### **JWT Token Functionality**

- Token generation and validation
- Access token expiration (30 minutes)
- Refresh token handling (7 days)
- Token invalidation on logout

#### **Database Operations**

- User creation and authentication
- Password hashing with bcrypt
- Email validation and sanitization
- Session context for Row-Level Security

### Phase 2: Landing Page Authentication Implementation (Days 3-5)

#### **Authentication Modal Development**

**Login Modal Requirements:**

```html
<!-- Material Design 3 Dialog Structure -->
<div class="md-dialog-scrim" id="loginDialogScrim">
  <div class="md-dialog" id="loginDialog" role="dialog" aria-labelledby="login-dialog-title">
    <div class="md-dialog-headline" id="login-dialog-title">Welcome Back</div>
    <form id="loginForm" class="md-dialog-supporting-text">
      <!-- Email input with floating label -->
      <!-- Password input with validation -->
      <!-- Error message display area -->
    </form>
    <div class="md-dialog-actions">
      <!-- Cancel and Sign In buttons -->
    </div>
  </div>
</div>
```

**Registration Modal Requirements:**

```html
<!-- Similar structure with additional fields -->
<!-- First Name, Last Name, Email, Password -->
<!-- Password strength validation -->
<!-- Terms acceptance checkbox -->
```

#### **Modal Functionality**

**Show/Hide Logic:**

```javascript
function showDialog(dialogId) {
  const scrim = document.getElementById(dialogId + 'Scrim')
  const dialog = document.getElementById(dialogId)

  // Add visibility classes
  scrim.classList.add('md-dialog-scrim-visible')
  dialog.classList.add('md-dialog-visible')

  // Accessibility requirements
  dialog.setAttribute('aria-hidden', 'false')

  // Focus management
  const firstInput = dialog.querySelector('input')
  if (firstInput) firstInput.focus()

  // Keyboard trap for accessibility
  trapFocus(dialog)
}
```

**Form Submission Logic:**

```javascript
async function handleLogin(formData) {
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    })

    if (response.ok) {
      const data = await response.json()
      // Store JWT tokens in session storage
      sessionStorage.setItem('jwt_token', data.access_token)
      sessionStorage.setItem('refresh_token', data.refresh_token)

      // Redirect to user dashboard
      window.location.href = '/dashboard'
    } else {
      // Show error message
      showErrorSnackbar('Invalid email or password')
    }
  } catch (error) {
    showErrorSnackbar('Connection error. Please try again.')
  }
}
```

#### **Error Handling Implementation**

**Snackbar Error Display:**

```javascript
function showErrorSnackbar(message) {
  const snackbar = document.createElement('div')
  snackbar.className = 'md-snackbar md-snackbar-visible'
  snackbar.textContent = message
  document.body.appendChild(snackbar)

  // Auto-hide after 4 seconds
  setTimeout(() => {
    snackbar.classList.remove('md-snackbar-visible')
    setTimeout(() => document.body.removeChild(snackbar), 300)
  }, 4000)
}
```

**Validation Error Patterns:**

- Invalid email format
- Password too short (minimum 8 characters)
- Required field validation
- Network connectivity errors
- Server error responses

#### **Landing Page Button Fixes**

**Current Broken Elements:**

```html
<!-- BEFORE: Non-functional button -->
<button class="md-button md-button-filled">
  <span class="material-icons">rocket_launch</span>
  Get Started
</button>

<!-- AFTER: Functional trigger -->
<button class="md-button md-button-filled" data-action="show-dialog" data-dialog="registerDialog">
  <span class="material-icons">rocket_launch</span>
  Get Started
</button>
```

**Navigation Menu Fixes:**

```html
<!-- BEFORE: Wrong admin link -->
<a href="/super-admin/login">Admin</a>

<!-- AFTER: Correct user authentication -->
<button data-action="show-dialog" data-dialog="loginDialog">Sign In</button>
```

### Phase 3: Basic User Dashboard (Days 4-5)

#### **Dashboard Template Creation**

**File Location:** `/templates/user_dashboard.html`

**Template Structure:**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Dashboard - {{ app_name }}</title>
    <link rel="stylesheet" href="/static/css/material-design.css" />
    <link rel="stylesheet" href="/static/css/user-dashboard.css" />
  </head>
  <body>
    <div class="dashboard-layout">
      <!-- Top App Bar -->
      <header class="md-top-app-bar">
        <div class="md-top-app-bar-headline">Welcome, {{ user.first_name }}</div>
        <div class="md-top-app-bar-actions">
          <button class="md-icon-button" id="logoutBtn">
            <span class="material-icons">logout</span>
          </button>
        </div>
      </header>

      <!-- Main Content -->
      <main class="dashboard-content">
        <div class="dashboard-welcome-card">
          <h2>Ready to create your first vote?</h2>
          <p>Vote creation interface will be available in Sprint 2</p>
          <button class="md-button md-button-filled" disabled>
            <span class="material-icons">add</span>
            Create Vote (Coming Soon)
          </button>
        </div>
      </main>
    </div>

    <script src="/static/js/user-dashboard.js"></script>
  </body>
</html>
```

#### **Dashboard Route Implementation**

**File Location:** `/src/cardinal_vote/user_routes.py` (New file)

```python
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .dependencies import get_current_user
from .models import User

user_router = APIRouter(tags=["User Dashboard"])
templates = Jinja2Templates(directory="templates")

@user_router.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """User dashboard page after authentication."""
    return templates.TemplateResponse(
        "user_dashboard.html",
        {
            "request": request,
            "user": current_user,
            "app_name": "Cardinal Vote"
        }
    )
```

**Router Integration** (Add to `/src/cardinal_vote/main.py`):

```python
from .user_routes import user_router

# Add after existing router inclusions
app.include_router(user_router)  # User dashboard
```

#### **Dashboard Styling**

**File Location:** `/static/css/user-dashboard.css`

```css
.dashboard-layout {
  min-height: 100vh;
  background-color: var(--md-sys-color-surface);
}

.dashboard-content {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-welcome-card {
  background-color: var(--md-sys-color-surface-container);
  border-radius: var(--md-sys-shape-corner-large);
  padding: 32px;
  text-align: center;
  box-shadow: var(--md-elevation-level1);
}

.dashboard-welcome-card h2 {
  color: var(--md-sys-color-on-surface);
  margin-bottom: 16px;
}

.dashboard-welcome-card p {
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 24px;
}
```

#### **Dashboard JavaScript**

**File Location:** `/static/js/user-dashboard.js`

```javascript
// JWT token validation and logout
document.addEventListener('DOMContentLoaded', function () {
  // Check authentication status
  const token = sessionStorage.getItem('jwt_token')
  if (!token) {
    window.location.href = '/'
    return
  }

  // Logout functionality
  const logoutBtn = document.getElementById('logoutBtn')
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function () {
      sessionStorage.removeItem('jwt_token')
      sessionStorage.removeItem('refresh_token')
      window.location.href = '/'
    })
  }

  // Validate token with server
  validateAuthToken()
})

async function validateAuthToken() {
  try {
    const token = sessionStorage.getItem('jwt_token')
    const response = await fetch('/api/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })

    if (!response.ok) {
      // Token invalid, redirect to login
      sessionStorage.clear()
      window.location.href = '/'
    }
  } catch (error) {
    console.error('Token validation failed:', error)
    // Optionally redirect on network error
  }
}
```

---

## Implementation Blueprint

### Pseudocode Implementation Approach

```
PHASE 1: API Validation
├── Test authentication endpoints with curl/Postman
├── Verify JWT token generation and validation
├── Confirm database user creation functionality
└── Document any API issues discovered

PHASE 2: Modal Implementation
├── Add authentication modal HTML to landing_material.html
├── Implement modal show/hide JavaScript functions
├── Add form submission handlers with API integration
├── Implement error handling and validation
└── Update button triggers to open modals

PHASE 3: Dashboard Creation
├── Create user dashboard template
├── Implement dashboard route with authentication
├── Add basic styling consistent with Material Design 3
├── Implement logout functionality
└── Add router to main application

PHASE 4: Integration Testing
├── Test complete authentication flow
├── Verify token storage and validation
├── Test dashboard access and logout
└── Validate all existing functionality remains intact
```

### File Modifications Required

**Template Updates:**

- `/templates/landing_material.html` - Add authentication modals
- `/templates/user_dashboard.html` - Create new dashboard template

**JavaScript Updates:**

- `/static/js/landing-material.js` - Add modal and form handling logic
- `/static/js/user-dashboard.js` - Create new dashboard functionality

**CSS Updates:**

- `/static/css/user-dashboard.css` - Create new dashboard styles

**Backend Updates:**

- `/src/cardinal_vote/user_routes.py` - Create new user dashboard routes
- `/src/cardinal_vote/main.py` - Add user router integration

### Error Handling Strategy

**Client-Side Error Patterns:**

- Form validation errors → Inline field error messages
- Authentication failures → Snackbar notifications
- Network errors → Retry mechanism with user feedback
- Token expiration → Automatic redirect to login

**Server-Side Error Handling:**

- Input validation → 400 Bad Request with specific error messages
- Authentication failures → 401 Unauthorized with clear messaging
- Rate limiting → 429 Too Many Requests with retry timing
- Server errors → 500 Internal Server Error with generic user message

**Accessibility Requirements:**

- All modals must have proper ARIA labels
- Focus management for keyboard navigation
- Screen reader announcements for form errors
- High contrast support for error states

---

## Testing & Validation

### Validation Gates (Executable Commands)

Based on project configuration analysis, the following validation commands must pass:

#### **Python Backend Validation:**

```bash
# Run all tests
uv run pytest tests/ -v

# Code quality and formatting
uv run ruff format src/ tests/     # Fix 58 identified linting errors
uv run ruff check src/ tests/      # Ensure no remaining lint issues
uv run mypy src/                   # Type checking compliance

# Security scanning
uv run bandit src/ -r              # Security vulnerability check
```

#### **JavaScript Frontend Validation:**

```bash
# JavaScript code quality
npm run lint                       # ESLint validation
npm run format:check              # Prettier formatting check
npm run test                      # Jest test suite

# Comprehensive validation
npm run validate                  # Combined linting and testing
```

#### **Docker Integration Testing:**

```bash
# Container build and health check
docker compose build --no-cache
docker compose up --detach
docker compose exec cardinal-vote python -c "import requests; print(requests.get('http://localhost:8000/api/health').json())"
```

### Test Cases for Authentication Flow

#### **Unit Tests Required:**

**Backend Authentication Tests:**

```python
# File: tests/test_auth_flow.py
def test_user_registration_success():
    """Test successful user registration with valid data"""

def test_user_registration_invalid_email():
    """Test registration rejection with invalid email format"""

def test_user_login_success():
    """Test successful login with valid credentials"""

def test_user_login_invalid_credentials():
    """Test login rejection with invalid credentials"""

def test_jwt_token_generation():
    """Test JWT token generation and validation"""

def test_jwt_token_expiration():
    """Test token expiration handling"""
```

**Frontend Modal Tests:**

```javascript
// File: tests/frontend/auth-modal.test.js
describe('Authentication Modals', () => {
  test('login modal opens when triggered')
  test('register modal opens when triggered')
  test('modals close on cancel button')
  test('modals close on backdrop click')
  test('form validation prevents submission with invalid data')
  test('successful login redirects to dashboard')
  test('failed login shows error message')
})
```

#### **Integration Tests Required:**

**End-to-End Authentication Flow:**

```javascript
// File: tests/e2e/auth-flow.test.js
describe('Complete Authentication Flow', () => {
  test('user can register, login, and access dashboard')
  test('user can logout and return to landing page')
  test('invalid tokens redirect to login')
  test('token refresh works correctly')
})
```

#### **Accessibility Testing:**

**ARIA Compliance:**

- Modal dialogs have proper `role="dialog"`
- Form inputs have associated labels
- Error messages are announced to screen readers
- Focus management works correctly

**Keyboard Navigation:**

- Tab order flows logically through modal elements
- Escape key closes modals
- Enter key submits forms
- Focus returns to trigger element on modal close

### Performance Requirements

**Page Load Performance:**

- Landing page with modals: < 2 seconds on 3G
- Modal show/hide animations: < 300ms
- Form submission response: < 1 second
- Dashboard load after authentication: < 1.5 seconds

**API Response Times:**

- Authentication endpoints: < 500ms
- Token validation: < 200ms
- User profile retrieval: < 300ms

---

## Risk Assessment & Mitigation

### High-Risk Areas

#### **Risk 1: Backend API Functionality Unknown**

**Impact:** If authentication APIs don't work as documented, entire Sprint 1 timeline at risk
**Probability:** Medium (30%)
**Mitigation Strategies:**

- Start with comprehensive API testing on Day 1
- Have backend developer available for immediate fixes
- Document any API issues for rapid resolution
- Fallback plan: Use mock authentication for frontend development

#### **Risk 2: Material Design 3 Component Integration**

**Impact:** Modal animations or styling may not work as expected
**Probability:** Low (15%)
**Mitigation Strategies:**

- Use existing working patterns from codebase
- Test modal functionality in isolation first
- Have CSS expert review component integration
- Fallback: Use simpler modal implementation if needed

#### **Risk 3: CSP Compliance Issues**

**Impact:** JavaScript functionality blocked by Content Security Policy
**Probability:** Medium (25%)
**Mitigation Strategies:**

- Follow existing CSP-compliant patterns in codebase
- Test all JavaScript functionality with CSP enabled
- Use event delegation instead of inline handlers
- Have security review before deployment

### Medium-Risk Areas

#### **Risk 4: Cross-Browser Compatibility**

**Impact:** Authentication may not work in all browsers
**Probability:** Low (10%)
**Mitigation Strategies:**

- Test in Chrome, Firefox, Safari, and Edge
- Use progressive enhancement approach
- Provide fallback for older browsers
- Focus on modern browser support initially

#### **Risk 5: Token Storage Security**

**Impact:** JWT tokens in session storage have security implications
**Probability:** Low (15%)
**Mitigation Strategies:**

- Session storage chosen for automatic cleanup on tab close
- Implement proper token validation
- Add token refresh mechanism
- Document security trade-offs for future improvement

### Mitigation Timeline

**Day 1:** Backend API validation and risk assessment
**Day 2:** Modal implementation with security compliance testing
**Day 3:** Integration testing and cross-browser validation
**Day 4:** Dashboard implementation and token security testing
**Day 5:** Comprehensive testing and risk mitigation validation

---

## Success Metrics & Acceptance Criteria

### Primary Success Criteria

#### **Functional Requirements:**

1. **User Registration Flow**
   - ✅ Users can open registration modal from "Get Started" button
   - ✅ Registration form validates input (email format, password length)
   - ✅ Valid registration creates user account and shows success message
   - ✅ Invalid registration shows specific error messages

2. **User Login Flow**
   - ✅ Users can open login modal from navigation menu
   - ✅ Login form validates credentials against backend
   - ✅ Valid login stores JWT tokens and redirects to dashboard
   - ✅ Invalid login shows clear error message

3. **Dashboard Access**
   - ✅ Authenticated users can access dashboard at `/dashboard`
   - ✅ Dashboard displays personalized welcome message
   - ✅ Logout functionality clears tokens and returns to landing page
   - ✅ Unauthenticated access to dashboard redirects to landing page

4. **Token Management**
   - ✅ JWT tokens stored securely in session storage
   - ✅ Tokens included in authenticated API requests
   - ✅ Token validation works with `/api/auth/me` endpoint
   - ✅ Token expiration handled gracefully

#### **Technical Requirements:**

1. **Code Quality**
   - ✅ All validation commands pass (pytest, ruff, mypy, eslint)
   - ✅ No new security vulnerabilities introduced
   - ✅ CSP compliance maintained
   - ✅ Accessibility standards met (ARIA, keyboard navigation)

2. **Performance**
   - ✅ Modal show/hide animations complete within 300ms
   - ✅ Form submission responses within 1 second
   - ✅ Dashboard loads within 1.5 seconds
   - ✅ No impact on existing page load times

#### **Integration Requirements:**

1. **Existing Functionality Preserved**
   - ✅ Super admin login still functions (at correct URL)
   - ✅ Public voting pages remain accessible
   - ✅ Landing page visual design unchanged
   - ✅ All existing API endpoints remain functional

### Quality Metrics

#### **User Experience Metrics:**

- Modal accessibility score: 100% (using axe-core testing)
- Form completion rate: > 95% for valid inputs
- Error message clarity: Users understand next steps
- Cross-browser compatibility: Works in 95% of modern browsers

#### **Technical Metrics:**

- Code coverage: > 80% for new authentication functionality
- API response time: < 500ms for authentication endpoints
- JavaScript error rate: < 1% in production monitoring
- CSP violation rate: 0% (strict compliance required)

#### **Security Metrics:**

- Input sanitization: 100% of user inputs processed through InputSanitizer
- XSS vulnerability scan: 0 vulnerabilities detected
- JWT token validation: 100% of authenticated requests verified
- HTTPS enforcement: All authentication traffic encrypted

### Acceptance Testing Procedure

#### **Manual Testing Checklist:**

**Authentication Flow Testing:**

- [ ] Click "Get Started" button opens registration modal
- [ ] Click "Sign In" in menu opens login modal
- [ ] Registration with valid data creates account
- [ ] Registration with invalid email shows error
- [ ] Registration with short password shows error
- [ ] Login with valid credentials succeeds
- [ ] Login with invalid credentials shows error
- [ ] Successful login redirects to dashboard
- [ ] Dashboard shows user's name
- [ ] Logout button clears session and returns to landing page

**Accessibility Testing:**

- [ ] Modal opens with keyboard (Enter key)
- [ ] Tab order flows logically through modal elements
- [ ] Escape key closes modal
- [ ] Screen reader announces modal content
- [ ] Form errors are announced to screen readers
- [ ] High contrast mode works correctly

**Error Handling Testing:**

- [ ] Network error during login shows appropriate message
- [ ] Server error during registration shows user-friendly message
- [ ] Invalid token on dashboard redirects to landing page
- [ ] Multiple rapid clicks on modal triggers don't cause issues

#### **Automated Testing Requirements:**

**Unit Test Coverage:**

- Authentication modal functionality
- Form validation logic
- JWT token management
- API integration functions
- Error handling scenarios

**Integration Test Coverage:**

- Complete registration → login → dashboard flow
- Token expiration and refresh
- Cross-browser compatibility
- Mobile responsiveness

**Security Test Coverage:**

- XSS prevention in form inputs
- CSRF protection on form submissions
- JWT token validation
- Input sanitization verification

---

## Timeline & Resource Allocation

### Sprint 1 Schedule (5 Working Days)

#### **Day 1-2: Backend Validation & Setup**

**Assigned:** Backend Developer + Frontend Developer (collaboration)
**Time Allocation:** 16 hours total

**Backend Developer Tasks (8 hours):**

- Test all authentication API endpoints with curl/Postman
- Verify JWT token generation and validation functionality
- Test user registration and login database operations
- Document any API issues or inconsistencies discovered
- Ensure input sanitization works correctly
- Validate password hashing and security measures

**Frontend Developer Tasks (8 hours):**

- Set up development environment for authentication work
- Analyze existing Material Design 3 modal components
- Study existing JavaScript patterns for API integration
- Prepare modal HTML structure based on design system
- Test existing landing page functionality to understand current state

#### **Day 3: Authentication Modal Implementation**

**Assigned:** Frontend Developer (primary) + Backend Developer (support)
**Time Allocation:** 8 hours

**Frontend Developer Tasks:**

- Add authentication modal HTML to `landing_material.html`
- Implement modal show/hide JavaScript functionality
- Add form validation logic for registration and login forms
- Implement API integration for authentication endpoints
- Add error handling and snackbar notifications
- Update button triggers to open appropriate modals

**Backend Developer Tasks:**

- Support frontend integration with API documentation
- Fix any API issues discovered during integration testing
- Assist with JWT token handling implementation

#### **Day 4: Dashboard Creation & Integration**

**Assigned:** Frontend Developer (primary) + Backend Developer (support)
**Time Allocation:** 8 hours

**Frontend Developer Tasks:**

- Create user dashboard template with Material Design 3 styling
- Implement dashboard JavaScript for token validation and logout
- Add dashboard CSS consistent with design system
- Test post-login routing and authentication flow

**Backend Developer Tasks:**

- Create user dashboard route with authentication middleware
- Integrate new user router with main application
- Test complete authentication flow from backend perspective

#### **Day 5: Testing & Validation**

**Assigned:** Full Team (Frontend + Backend + QA)
**Time Allocation:** 8 hours

**Comprehensive Testing:**

- Run all validation commands (pytest, ruff, mypy, eslint)
- Perform manual testing of complete authentication flow
- Test accessibility compliance with screen readers
- Validate cross-browser compatibility
- Test error scenarios and edge cases
- Perform integration testing with Docker containers
- Fix any issues discovered during testing

### Resource Requirements

#### **Human Resources:**

- **Frontend Developer:** 32 hours (experienced with vanilla JavaScript and CSS)
- **Backend Developer:** 24 hours (Python/FastAPI expertise)
- **QA/Testing:** 8 hours (accessibility and security testing)
- **Total:** 64 hours across 5 days

#### **Technical Resources:**

- Development environment with Docker and PostgreSQL
- Testing devices for cross-browser validation
- Accessibility testing tools (axe-core, screen readers)
- API testing tools (Postman, curl)

#### **Dependencies:**

- Material Design 3 CSS framework (already available)
- FastAPI authentication infrastructure (already available)
- PostgreSQL database with user schema (already available)
- JWT token management system (already available)

### Milestone Checkpoints

#### **End of Day 2: Backend Validation Complete**

**Deliverables:**

- All authentication API endpoints tested and documented
- Any API issues identified and resolved
- JWT token functionality verified
- Database operations confirmed working

**Success Criteria:**

- All API tests pass
- Authentication system ready for frontend integration
- No blocking issues discovered

#### **End of Day 3: Authentication Modals Functional**

**Deliverables:**

- Login and registration modals implemented
- Form validation working
- API integration complete
- Error handling implemented

**Success Criteria:**

- Users can register and login successfully
- Appropriate error messages shown for failures
- Modals follow Material Design 3 patterns

#### **End of Day 4: Dashboard Access Working**

**Deliverables:**

- User dashboard template created
- Post-login routing functional
- Token validation working
- Logout functionality implemented

**Success Criteria:**

- Complete authentication flow functional
- Users can access dashboard after login
- Logout returns users to landing page

#### **End of Day 5: Sprint 1 Complete**

**Deliverables:**

- All validation tests passing
- Complete documentation updated
- Cross-browser compatibility verified
- Accessibility compliance confirmed

**Success Criteria:**

- All acceptance criteria met
- No regression in existing functionality
- Ready for Sprint 2 development

---

## Post-Sprint Planning

### Sprint 2 Foundation Prepared

Sprint 1 success creates the foundation for Sprint 2 vote creation functionality:

**Sprint 2 Prerequisites Met:**

- ✅ User authentication working
- ✅ User dashboard template available
- ✅ Token management system functional
- ✅ Material Design 3 patterns established

**Sprint 2 Ready Components:**

- User dashboard can be extended with vote creation form
- JWT tokens available for authenticated API calls
- Material Design 3 system ready for vote interface components
- Error handling patterns established for reuse

### Architecture Document Updates Required

Based on Sprint 1 completion, update architecture documentation:

**Completion Status Updates:**

- Landing Page: 60% → 95% (authentication functional)
- Authentication Flow: "❌ Non-functional" → "✅ Fully Functional"
- User Dashboard: "❌ Missing" → "✅ Basic Implementation"

**New Documentation Needed:**

- Authentication modal patterns
- JWT token management approach
- User dashboard extension points for Sprint 2
- Error handling standard patterns

### Technical Debt Identified

**Immediate Technical Debt (Address in Sprint 2):**

- Dashboard functionality is minimal (only welcome message)
- No password reset flow implemented
- No email verification workflow
- Session storage security could be enhanced

**Future Technical Debt (Later Sprints):**

- Consider migration to HTTP-only cookies for token storage
- Implement refresh token rotation
- Add "Remember Me" functionality
- Enhanced error logging and monitoring

---

## Appendix

### Code Examples

#### **Complete Authentication Modal HTML**

```html
<!-- Login Modal Implementation -->
<div class="md-dialog-scrim" id="loginDialogScrim" aria-hidden="true">
  <div class="md-dialog" id="loginDialog" role="dialog" aria-labelledby="login-dialog-title">
    <div class="md-dialog-headline" id="login-dialog-title">Welcome Back</div>
    <form id="loginForm" class="md-dialog-supporting-text">
      <div class="md-text-field">
        <input
          type="email"
          id="loginEmail"
          class="md-text-field-input"
          placeholder=" "
          required
          aria-describedby="login-email-error"
        />
        <label for="loginEmail" class="md-text-field-label">Email Address</label>
        <div id="login-email-error" class="md-text-field-error" aria-live="polite"></div>
      </div>
      <div class="md-text-field">
        <input
          type="password"
          id="loginPassword"
          class="md-text-field-input"
          placeholder=" "
          required
          aria-describedby="login-password-error"
        />
        <label for="loginPassword" class="md-text-field-label">Password</label>
        <div id="login-password-error" class="md-text-field-error" aria-live="polite"></div>
      </div>
    </form>
    <div class="md-dialog-actions">
      <button
        type="button"
        class="md-button-text"
        data-action="close-dialog"
        data-dialog="loginDialog"
      >
        Cancel
      </button>
      <button type="submit" form="loginForm" class="md-button-filled">Sign In</button>
    </div>
  </div>
</div>

<!-- Registration Modal Implementation -->
<div class="md-dialog-scrim" id="registerDialogScrim" aria-hidden="true">
  <div class="md-dialog" id="registerDialog" role="dialog" aria-labelledby="register-dialog-title">
    <div class="md-dialog-headline" id="register-dialog-title">Create Account</div>
    <form id="registerForm" class="md-dialog-supporting-text">
      <div class="md-text-field">
        <input
          type="text"
          id="registerFirstName"
          class="md-text-field-input"
          placeholder=" "
          required
        />
        <label for="registerFirstName" class="md-text-field-label">First Name</label>
      </div>
      <div class="md-text-field">
        <input
          type="text"
          id="registerLastName"
          class="md-text-field-input"
          placeholder=" "
          required
        />
        <label for="registerLastName" class="md-text-field-label">Last Name</label>
      </div>
      <div class="md-text-field">
        <input
          type="email"
          id="registerEmail"
          class="md-text-field-input"
          placeholder=" "
          required
        />
        <label for="registerEmail" class="md-text-field-label">Email Address</label>
      </div>
      <div class="md-text-field">
        <input
          type="password"
          id="registerPassword"
          class="md-text-field-input"
          placeholder=" "
          required
          minlength="8"
        />
        <label for="registerPassword" class="md-text-field-label"
          >Password (minimum 8 characters)</label
        >
      </div>
    </form>
    <div class="md-dialog-actions">
      <button
        type="button"
        class="md-button-text"
        data-action="close-dialog"
        data-dialog="registerDialog"
      >
        Cancel
      </button>
      <button type="submit" form="registerForm" class="md-button-filled">Create Account</button>
    </div>
  </div>
</div>
```

#### **Complete JavaScript Implementation**

```javascript
// Authentication functionality for landing page
class AuthenticationManager {
  constructor() {
    this.initializeEventHandlers()
  }

  initializeEventHandlers() {
    document.addEventListener('click', this.handleClick.bind(this))
    document.addEventListener('submit', this.handleSubmit.bind(this))
    document.addEventListener('keydown', this.handleKeydown.bind(this))
  }

  handleClick(event) {
    const action = event.target.getAttribute('data-action')
    const dialogId = event.target.getAttribute('data-dialog')

    switch (action) {
      case 'show-dialog':
        if (dialogId) this.showDialog(dialogId)
        break
      case 'close-dialog':
        if (dialogId) this.closeDialog(dialogId)
        break
    }
  }

  handleSubmit(event) {
    const formId = event.target.id
    event.preventDefault()

    switch (formId) {
      case 'loginForm':
        this.handleLogin(event.target)
        break
      case 'registerForm':
        this.handleRegistration(event.target)
        break
    }
  }

  handleKeydown(event) {
    if (event.key === 'Escape') {
      const openDialog = document.querySelector('.md-dialog-scrim[aria-hidden="false"]')
      if (openDialog) {
        const dialogId = openDialog.querySelector('.md-dialog').id
        this.closeDialog(dialogId)
      }
    }
  }

  showDialog(dialogId) {
    const scrim = document.getElementById(dialogId + 'Scrim')
    const dialog = document.getElementById(dialogId)

    if (scrim && dialog) {
      scrim.setAttribute('aria-hidden', 'false')
      dialog.classList.add('md-dialog-visible')

      // Focus first input
      const firstInput = dialog.querySelector('input')
      if (firstInput) firstInput.focus()

      // Add backdrop click handler
      scrim.addEventListener('click', e => {
        if (e.target === scrim) this.closeDialog(dialogId)
      })
    }
  }

  closeDialog(dialogId) {
    const scrim = document.getElementById(dialogId + 'Scrim')
    const dialog = document.getElementById(dialogId)

    if (scrim && dialog) {
      scrim.setAttribute('aria-hidden', 'true')
      dialog.classList.remove('md-dialog-visible')

      // Clear form errors
      this.clearFormErrors(dialog)
    }
  }

  async handleLogin(form) {
    const formData = new FormData(form)
    const loginData = {
      email: formData.get('loginEmail'),
      password: formData.get('loginPassword')
    }

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData)
      })

      if (response.ok) {
        const data = await response.json()
        sessionStorage.setItem('jwt_token', data.access_token)
        sessionStorage.setItem('refresh_token', data.refresh_token)

        this.showSuccessSnackbar('Login successful!')
        setTimeout(() => (window.location.href = '/dashboard'), 1000)
      } else {
        const errorData = await response.json()
        this.showErrorSnackbar(errorData.detail || 'Login failed')
      }
    } catch (error) {
      this.showErrorSnackbar('Connection error. Please try again.')
    }
  }

  async handleRegistration(form) {
    const formData = new FormData(form)
    const registrationData = {
      email: formData.get('registerEmail'),
      password: formData.get('registerPassword'),
      first_name: formData.get('registerFirstName'),
      last_name: formData.get('registerLastName')
    }

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registrationData)
      })

      if (response.ok) {
        this.showSuccessSnackbar('Registration successful! Please login.')
        this.closeDialog('registerDialog')
        setTimeout(() => this.showDialog('loginDialog'), 500)
      } else {
        const errorData = await response.json()
        this.showErrorSnackbar(errorData.detail || 'Registration failed')
      }
    } catch (error) {
      this.showErrorSnackbar('Connection error. Please try again.')
    }
  }

  showSuccessSnackbar(message) {
    this.showSnackbar(message, 'success')
  }

  showErrorSnackbar(message) {
    this.showSnackbar(message, 'error')
  }

  showSnackbar(message, type = 'info') {
    const snackbar = document.createElement('div')
    snackbar.className = `md-snackbar md-snackbar-${type} md-snackbar-visible`
    snackbar.textContent = message
    snackbar.setAttribute('role', 'alert')
    snackbar.setAttribute('aria-live', 'assertive')

    document.body.appendChild(snackbar)

    setTimeout(() => {
      snackbar.classList.remove('md-snackbar-visible')
      setTimeout(() => {
        if (document.body.contains(snackbar)) {
          document.body.removeChild(snackbar)
        }
      }, 300)
    }, 4000)
  }

  clearFormErrors(dialog) {
    const errorElements = dialog.querySelectorAll('.md-text-field-error')
    errorElements.forEach(error => (error.textContent = ''))
  }
}

// Initialize authentication when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new AuthenticationManager()
})
```

### API Integration Examples

#### **Registration API Call**

```javascript
// Example API integration for user registration
const registrationData = {
  email: 'user@example.com',
  password: 'securepassword123',
  first_name: 'John',
  last_name: 'Doe'
}

const response = await fetch('/api/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(registrationData)
})

// Expected response structure
if (response.ok) {
  const result = await response.json()
  // result = { success: true, message: "User registered successfully", user_id: "uuid" }
} else {
  const error = await response.json()
  // error = { detail: "Email already registered" }
}
```

#### **Login API Call**

```javascript
// Example API integration for user login
const loginData = {
  email: 'user@example.com',
  password: 'securepassword123'
}

const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(loginData)
})

// Expected response structure
if (response.ok) {
  const result = await response.json()
  // result = {
  //   access_token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  //   refresh_token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  //   token_type: "bearer",
  //   expires_in: 1800
  // }

  sessionStorage.setItem('jwt_token', result.access_token)
  sessionStorage.setItem('refresh_token', result.refresh_token)
}
```

### Validation Commands Reference

```bash
# Complete validation suite for Sprint 1
# Run these commands before considering Sprint 1 complete

# Python backend validation
uv run pytest tests/ -v --cov=src --cov-report=html
uv run ruff format src/ tests/
uv run ruff check src/ tests/
uv run mypy src/
uv run bandit src/ -r

# JavaScript frontend validation
npm run lint
npm run format:check
npm run test
npm run validate

# Docker integration validation
docker compose build --no-cache
docker compose up --detach
docker compose exec cardinal-vote python -c "import requests; r = requests.get('http://localhost:8000/api/health'); print(f'Health: {r.status_code} - {r.json()}')"

# Manual accessibility validation
# Use browser dev tools accessibility scanner
# Test with screen reader (NVDA/JAWS/VoiceOver)
# Verify keyboard navigation works
```

---

**PRP Confidence Score: 9/10**

This PRP provides comprehensive implementation details with specific code examples, exact file locations, and executable validation steps. The high confidence score reflects:

✅ **Complete Requirements Analysis** - All authentication flow requirements defined
✅ **Detailed Technical Specifications** - Exact HTML, CSS, and JavaScript implementations provided
✅ **Existing Pattern Integration** - Leverages proven Material Design 3 and authentication patterns from codebase
✅ **Comprehensive Testing Strategy** - Both automated and manual testing procedures defined
✅ **Risk Mitigation Planning** - High and medium risks identified with specific mitigation strategies
✅ **Actionable Implementation Steps** - Clear day-by-day timeline with resource allocation

The only uncertainty (reducing confidence from 10/10) is the potential discovery of unexpected API issues during backend validation, but comprehensive mitigation strategies are in place.
