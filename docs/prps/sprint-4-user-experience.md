# PRP: Sprint 4 - User Experience

**Feature**: Account Management & Enhanced User Features
**Sprint**: 4
**Priority**: High
**Status**: Ready for Implementation
**Confidence Score**: 9/10

## Executive Summary

Sprint 4 focuses on delivering comprehensive user account management capabilities and enhanced user experience features to complete the user journey restoration. Building upon the solid authentication infrastructure already in place, this sprint will implement user profile management, account deletion, email verification flow with CAPTCHA, enhanced image upload interface, and improved mobile responsiveness. All major backend services (authentication, email, CAPTCHA, image processing) are already implemented and tested, making this primarily a frontend integration sprint with strategic backend extensions.

## Problem Statement

### Current State

- Complete JWT authentication system with refresh tokens exists
- User registration and login APIs are fully functional (14 auth endpoints)
- Email service with verification capabilities is implemented
- CAPTCHA service with multiple backends (reCAPTCHA, hCAPTCHA, mock) is ready
- Image upload service with optimization and validation is complete
- Material Design 3 UI system is established across all interfaces
- Mobile responsive breakpoints are partially implemented

### Desired State

- Complete user account lifecycle management through intuitive web interface
- Seamless email verification flow with CAPTCHA protection during registration
- Enhanced image upload experience for vote options with reasonable constraints
- Simple URL sharing capabilities for vote distribution
- Consistent mobile-first responsive design across all user interfaces
- Complete data deletion compliance with warning system for account removal

### Success Metrics

- 100% user account management functionality accessible via web interface
- <3 second account registration and verification flow completion
- Zero security vulnerabilities in account deletion and data handling
- 95%+ mobile usability score across all new interfaces
- CAPTCHA protection successfully prevents bot registrations and vote spam

## User Requirements

### User Stories

#### Story 1: Account Registration with Verification

**As a** new user
**I want to** register with email verification and CAPTCHA protection
**So that I** can create a secure account and access the voting platform

**Acceptance Criteria:**

- Registration form with first name, last name, email, password fields
- CAPTCHA verification required during registration process
- Email verification sent immediately after registration
- Clear indication of verification status in user interface
- Resend verification email functionality available
- Account restricted until email is verified

#### Story 2: User Profile Management

**As a** registered user
**I want to** view and update my profile information
**So that I** can keep my account details current and accurate

**Acceptance Criteria:**

- View current profile with first name, last name, email, verification status
- Edit first name and last name with form validation
- Change email address with re-verification requirement
- View account creation date and last login timestamp
- Change password with current password confirmation
- All changes require form validation and input sanitization

#### Story 3: Account Deletion with Data Removal

**As a** registered user
**I want to** permanently delete my account and all associated data
**So that I** can completely remove my presence from the platform

**Acceptance Criteria:**

- Clear warning about permanent data deletion before confirmation
- All user data must be completely removed (GDPR compliance)
- All created votes and responses must be permanently deleted
- Uploaded images associated with account must be removed
- No possibility of data recovery after deletion
- Immediate logout and session termination after deletion

#### Story 4: Enhanced Image Upload for Vote Options

**As a** vote creator
**I want to** easily upload and manage images for vote options
**So that I** can create visually engaging votes

**Acceptance Criteria:**

- Drag-and-drop image upload interface
- Support for PNG, JPG, JPEG, GIF, WebP formats
- Maximum file size of 10MB per image
- Automatic image optimization and resizing (max 2048px)
- Preview uploaded images before saving vote
- Delete uploaded images with confirmation
- Progress indicator during upload process

#### Story 5: Simple Vote Sharing

**As a** vote creator
**I want to** easily share my vote via URL
**So that I** can distribute it to participants

**Acceptance Criteria:**

- Copy-to-clipboard functionality for vote URLs
- One-click URL copying with success feedback
- Clean, readable URLs using vote slugs
- Social sharing hints for future enhancement readiness
- Public vote access without authentication required
- CAPTCHA protection for anonymous vote submissions

#### Story 6: Mobile-First Responsive Experience

**As a** user on mobile devices
**I want to** have a consistent and touch-friendly experience
**So that I** can use the platform effectively on any device

**Acceptance Criteria:**

- All new interfaces adapt to mobile screen sizes (320px+)
- Touch-friendly tap targets (minimum 44px)
- Readable typography at mobile scales
- Optimized form inputs for mobile keyboards
- Swipe gestures where appropriate
- Fast loading on mobile networks

### Business Rules

1. **Account Deletion Rules**:
   - All user data must be permanently deleted (hard delete)
   - Deletion includes: user record, votes, responses, uploaded images
   - Warning message must clearly explain permanent nature
   - No grace period or recovery option after confirmation

2. **Email Verification Rules**:
   - Required for all new registrations
   - Verification token expires after 24 hours
   - Unverified users cannot create votes
   - Verification status visible in user profile

3. **Image Upload Rules**:
   - Maximum 10MB per file
   - Supported formats: PNG, JPG, JPEG, GIF, WebP
   - Automatic optimization to max 2048px width/height
   - JPEG quality compression at 85%
   - Unique UUID-based filenames for security

4. **CAPTCHA Protection Rules**:
   - Required for user registration
   - Required for anonymous vote submissions
   - Support for reCAPTCHA v2, hCAPTCHA, or mock (development)
   - Failed CAPTCHA blocks form submission

## Solution Architecture

### Technical Approach

#### Frontend Architecture

**Template Extensions**: Extend existing Material Design 3 templates

- User profile management section in dashboard
- Account settings modal with tabbed interface
- Enhanced image upload component with drag-and-drop
- Mobile-optimized responsive layouts

**JavaScript Components**: Build on existing patterns

- Profile management JavaScript class following DashboardManager pattern
- Image upload manager with progress tracking
- CAPTCHA integration for registration forms
- Mobile touch interaction handlers

#### Backend Extensions

**New Endpoints Required**:

```python
# User profile management
PUT /api/auth/profile - Update user profile
DELETE /api/auth/account - Delete user account

# Enhanced image management
GET /api/votes/images - List user's uploaded images
POST /api/votes/images/batch - Batch upload multiple images
```

**Service Enhancements**:

- Email verification integration during registration flow
- Account deletion service with cascade data cleanup
- Enhanced image upload with batch processing capability

### Component Specifications

#### 1. Account Registration Enhancement

**Location**: Extend `/templates/landing.html` authentication modals

**Components**:

```html
<!-- Enhanced Registration Modal -->
<div class="md-dialog-container">
  <form id="registrationForm" class="md-dialog-form">
    <!-- Name fields -->
    <div class="md-text-field-group">
      <input type="text" id="firstName" name="first_name" required />
      <input type="text" id="lastName" name="last_name" required />
    </div>

    <!-- Email and password -->
    <input type="email" id="email" name="email" required />
    <input type="password" id="password" name="password" required />

    <!-- CAPTCHA integration -->
    <div class="captcha-container" id="registrationCaptcha"></div>

    <!-- Email verification notice -->
    <div class="verification-notice">
      <p>You'll receive an email to verify your account</p>
    </div>
  </form>
</div>
```

**JavaScript Manager**: `RegistrationManager` class

```javascript
class RegistrationManager {
  constructor() {
    this.captchaService = new CaptchaService()
    this.emailService = new EmailService()
  }

  async handleRegistration(formData) {
    // Validate form data using existing patterns
    const validation = this.validateRegistrationData(formData)
    if (!validation.isValid) return this.showErrors(validation.errors)

    // Verify CAPTCHA
    const captchaResult = await this.captchaService.verify()
    if (!captchaResult.success) return this.showError('CAPTCHA verification failed')

    // Submit registration
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...formData, captcha_response: captchaResult.token })
    })

    if (response.ok) {
      this.showEmailVerificationMessage()
    }
  }
}
```

#### 2. User Profile Management Interface

**Location**: Extend `/templates/user_dashboard.html` with profile section

**Component Structure**:

```html
<!-- User Profile Section -->
<div class="profile-section">
  <div class="profile-header">
    <div class="user-avatar">
      <span class="material-icons">account_circle</span>
    </div>
    <div class="user-info">
      <h3 class="user-name">{{ user.first_name }} {{ user.last_name }}</h3>
      <p class="user-email">{{ user.email }}</p>
      <div class="verification-badge {{ 'verified' if user.is_verified else 'unverified' }}">
        <span class="material-icons">{{ 'verified' if user.is_verified else 'pending' }}</span>
        {{ 'Verified' if user.is_verified else 'Pending Verification' }}
      </div>
    </div>
  </div>

  <div class="profile-actions">
    <button class="md-button" data-action="edit-profile">
      <span class="material-icons">edit</span>
      Edit Profile
    </button>
    <button class="md-button md-button-outlined" data-action="account-settings">
      <span class="material-icons">settings</span>
      Account Settings
    </button>
  </div>
</div>
```

**Profile Management Service**:

```javascript
class ProfileManager {
  async updateProfile(profileData) {
    // Use existing input sanitization patterns
    const sanitizedData = InputSanitizer.sanitizeFormData(profileData)

    const response = await fetch('/api/auth/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.getAccessToken()}`
      },
      body: JSON.stringify(sanitizedData)
    })

    if (response.ok) {
      this.showSuccess('Profile updated successfully')
      this.refreshUserData()
    }
  }
}
```

#### 3. Account Deletion Interface

**Modal Component**:

```html
<!-- Account Deletion Warning Modal -->
<div class="md-dialog-scrim" id="deleteAccountModal">
  <div class="md-dialog danger-dialog">
    <div class="md-dialog-header">
      <span class="material-icons">warning</span>
      <h2>Delete Account</h2>
    </div>

    <div class="md-dialog-content">
      <div class="warning-content">
        <h3>This action cannot be undone</h3>
        <p>Deleting your account will permanently remove:</p>
        <ul>
          <li>All your votes and voting data</li>
          <li>All responses you've submitted</li>
          <li>All uploaded images</li>
          <li>Your profile information</li>
          <li>Your account access</li>
        </ul>
        <p><strong>There is no way to recover this data after deletion.</strong></p>
      </div>

      <div class="confirmation-input">
        <label for="deleteConfirmation">Type "DELETE" to confirm:</label>
        <input type="text" id="deleteConfirmation" placeholder="DELETE" />
      </div>
    </div>

    <div class="md-dialog-actions">
      <button class="md-button" data-action="cancel-delete">Cancel</button>
      <button class="md-button md-button-danger" data-action="confirm-delete" disabled>
        Delete Account
      </button>
    </div>
  </div>
</div>
```

#### 4. Enhanced Image Upload Component

**Pattern Reference**: Extend existing image service `/src/cardinal_vote/image_service.py`

**Enhanced Upload Interface**:

```html
<!-- Image Upload Component -->
<div class="image-upload-component">
  <div class="upload-zone" id="imageUploadZone">
    <div class="upload-prompt">
      <span class="material-icons">cloud_upload</span>
      <h4>Upload Images</h4>
      <p>Drag and drop images here, or click to browse</p>
      <p class="upload-limits">Max 10MB per image • PNG, JPG, GIF, WebP</p>
    </div>
    <input type="file" id="imageFileInput" multiple accept="image/*" hidden />
  </div>

  <div class="upload-progress" id="uploadProgress" hidden>
    <div class="progress-bar">
      <div class="progress-fill"></div>
    </div>
    <p class="progress-text">Uploading...</p>
  </div>

  <div class="uploaded-images" id="uploadedImages">
    <!-- Dynamically populated with uploaded images -->
  </div>
</div>
```

**Upload Manager**:

```javascript
class ImageUploadManager {
  constructor() {
    this.maxFileSize = 10 * 1024 * 1024 // 10MB
    this.allowedTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
  }

  async uploadImages(files) {
    const validFiles = this.validateFiles(files)
    if (validFiles.length === 0) return

    for (const file of validFiles) {
      await this.uploadSingleImage(file)
    }
  }

  validateFiles(files) {
    return Array.from(files).filter(file => {
      if (file.size > this.maxFileSize) {
        this.showError(`${file.name} is too large (max 10MB)`)
        return false
      }
      if (!this.allowedTypes.includes(file.type)) {
        this.showError(`${file.name} is not a supported image type`)
        return false
      }
      return true
    })
  }
}
```

### API Endpoints (Extensions to Existing System)

#### User Profile Management

| Method | Endpoint                        | Purpose                   | Authentication |
| ------ | ------------------------------- | ------------------------- | -------------- |
| PUT    | `/api/auth/profile`             | Update user profile       | Required       |
| DELETE | `/api/auth/account`             | Delete user account       | Required       |
| POST   | `/api/auth/resend-verification` | Resend verification email | Optional       |

#### Enhanced Image Management

| Method | Endpoint                  | Purpose             | Authentication |
| ------ | ------------------------- | ------------------- | -------------- |
| GET    | `/api/votes/images`       | List user's images  | Required       |
| POST   | `/api/votes/images/batch` | Batch upload images | Required       |
| DELETE | `/api/votes/images/batch` | Batch delete images | Required       |

### Database Schema Extensions

**User Profile Enhancement** (extending existing User model):

```python
# No schema changes needed - existing User model already contains all required fields:
# - first_name, last_name (profile data)
# - email, is_verified (verification status)
# - created_at, last_login (account metadata)
# - is_super_admin (role management)
```

**Audit Trail for Account Deletion**:

```python
class AccountDeletionLog(Base):
    __tablename__ = "account_deletion_logs"

    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(PostgreSQL_UUID(as_uuid=True), nullable=False)  # Deleted user's ID
    email = Column(String(255), nullable=False)  # Email of deleted account
    deletion_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    votes_deleted_count = Column(Integer, nullable=False)
    responses_deleted_count = Column(Integer, nullable=False)
    images_deleted_count = Column(Integer, nullable=False)
```

## Implementation Plan

### Phase 1: Account Management Foundation (Days 1-2)

**Backend Extensions**:

```python
# New account management endpoints
@auth_router.put("/profile")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: CurrentUser,
    session: AsyncDatabaseSession
):
    # Update user profile with input sanitization
    sanitized_data = InputSanitizer.sanitize_form_data(profile_data.dict())

    # Handle email change with re-verification
    if sanitized_data.get("email") != current_user.email:
        current_user.is_verified = False
        await send_verification_email(current_user.email)

    # Update user fields
    for field, value in sanitized_data.items():
        setattr(current_user, field, value)

    await session.commit()
    return {"message": "Profile updated successfully"}

@auth_router.delete("/account")
async def delete_user_account(
    current_user: CurrentUser,
    session: AsyncDatabaseSession
):
    # Count related data for audit log
    votes_count = await session.scalar(select(func.count(Vote.id)).where(Vote.creator_id == current_user.id))
    responses_count = await session.scalar(select(func.count(VoterResponse.id)).where(VoterResponse.voter_email == current_user.email))

    # Create audit log before deletion
    deletion_log = AccountDeletionLog(
        user_id=current_user.id,
        email=current_user.email,
        votes_deleted_count=votes_count,
        responses_deleted_count=responses_count,
        images_deleted_count=0  # Will be calculated during image cleanup
    )
    session.add(deletion_log)

    # Delete user (cascade will handle related data)
    await session.delete(current_user)
    await session.commit()

    return {"message": "Account deleted successfully"}
```

**Frontend Profile Interface**:

```javascript
// Extend DashboardManager with profile functionality
class ProfileManager extends DashboardManager {
  initializeProfile() {
    this.profileModal = document.getElementById('profileModal')
    this.profileForm = document.getElementById('profileForm')
    this.deleteAccountBtn = document.querySelector('[data-action="delete-account"]')

    this.attachProfileEventListeners()
  }

  attachProfileEventListeners() {
    // Profile edit handlers
    document.addEventListener('click', e => {
      if (e.target.dataset.action === 'edit-profile') {
        this.openProfileModal()
      }
      if (e.target.dataset.action === 'delete-account') {
        this.showDeleteWarning()
      }
    })
  }
}
```

### Phase 2: Registration Enhancement with CAPTCHA (Days 3-4)

**CAPTCHA Integration in Registration**:

```javascript
// Extend existing AuthenticationManager from landing-material.js
class EnhancedAuthManager extends AuthenticationManager {
  async initializeCaptcha() {
    // Use existing CAPTCHA service patterns
    if (window.grecaptcha) {
      this.captchaSiteKey = window.captchaConfig.siteKey
      grecaptcha.render('registration-captcha', {
        sitekey: this.captchaSiteKey,
        callback: this.handleCaptchaSuccess.bind(this)
      })
    }
  }

  async handleRegistration(formData) {
    // Extend existing registration with CAPTCHA verification
    const captchaResponse = grecaptcha.getResponse()
    if (!captchaResponse) {
      this.showError('Please complete the CAPTCHA verification')
      return
    }

    // Add CAPTCHA to registration request
    const registrationData = {
      ...formData,
      captcha_response: captchaResponse
    }

    // Use existing registration flow with CAPTCHA
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(registrationData)
    })

    if (response.ok) {
      this.showEmailVerificationNotice()
    }
  }
}
```

**Email Verification Status Integration**:

```html
<!-- Extend user dashboard with verification status -->
<div class="verification-status-banner" id="verificationBanner">
  <div class="banner-content">
    <span class="material-icons">mail_outline</span>
    <div class="banner-text">
      <h4>Please verify your email</h4>
      <p>Check your inbox and click the verification link to activate your account.</p>
    </div>
    <button class="md-button md-button-outlined" data-action="resend-verification">
      Resend Email
    </button>
  </div>
  <button class="banner-close" data-action="close-banner">
    <span class="material-icons">close</span>
  </button>
</div>
```

### Phase 3: Enhanced Image Upload (Days 5-6)

**Drag-and-Drop Image Upload**:

```javascript
class EnhancedImageUploadManager {
  constructor() {
    this.uploadZone = document.getElementById('imageUploadZone')
    this.fileInput = document.getElementById('imageFileInput')
    this.progressContainer = document.getElementById('uploadProgress')

    this.initializeDragAndDrop()
  }

  initializeDragAndDrop() {
    ;['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      this.uploadZone.addEventListener(eventName, this.preventDefaults)
    })
    ;['dragenter', 'dragover'].forEach(eventName => {
      this.uploadZone.addEventListener(eventName, () => {
        this.uploadZone.classList.add('drag-active')
      })
    })

    this.uploadZone.addEventListener('drop', this.handleDrop.bind(this))
  }

  async handleDrop(e) {
    const files = e.dataTransfer.files
    await this.processFiles(files)
  }

  async processFiles(files) {
    this.showProgress()
    const validFiles = this.validateFiles(files)

    for (let i = 0; i < validFiles.length; i++) {
      const file = validFiles[i]
      await this.uploadFile(file, i + 1, validFiles.length)
    }

    this.hideProgress()
  }

  async uploadFile(file, current, total) {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/votes/images/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.getAccessToken()}`
        },
        body: formData
      })

      if (response.ok) {
        const result = await response.json()
        this.addImageToGallery(result)
      }
    } catch (error) {
      this.showError(`Failed to upload ${file.name}`)
    }

    this.updateProgress(current, total)
  }
}
```

### Phase 4: Mobile Responsiveness & Polish (Days 7-8)

**Mobile-First Responsive Enhancements**:

```css
/* Extend existing Material Design breakpoints */

/* Profile management mobile optimization */
@media (max-width: 640px) {
  .profile-section {
    padding: 1rem;
  }

  .profile-header {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }

  .profile-actions {
    flex-direction: column;
    gap: 0.5rem;
  }

  .profile-actions .md-button {
    width: 100%;
    justify-content: center;
  }
}

/* Image upload mobile optimization */
@media (max-width: 640px) {
  .image-upload-component {
    margin: 0.5rem;
  }

  .upload-zone {
    min-height: 120px;
    padding: 1rem;
  }

  .upload-limits {
    font-size: 0.8rem;
  }

  .uploaded-images {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }
}

/* Account deletion warning mobile optimization */
@media (max-width: 640px) {
  .danger-dialog {
    margin: 1rem;
    max-width: calc(100% - 2rem);
  }

  .warning-content ul {
    padding-left: 1.5rem;
  }

  .md-dialog-actions {
    flex-direction: column-reverse;
    gap: 0.5rem;
  }

  .md-dialog-actions .md-button {
    width: 100%;
  }
}
```

**Touch Interaction Enhancements**:

```javascript
class MobileInteractionManager {
  constructor() {
    this.initializeTouchHandlers()
  }

  initializeTouchHandlers() {
    // Touch-friendly image gallery
    document.querySelectorAll('.uploaded-image').forEach(image => {
      image.addEventListener('touchstart', this.handleImageTouch.bind(this))
    })

    // Swipe gestures for image carousel (future enhancement)
    let startX = 0
    let startY = 0

    document.addEventListener('touchstart', e => {
      startX = e.touches[0].clientX
      startY = e.touches[0].clientY
    })

    document.addEventListener('touchend', e => {
      if (!startX || !startY) return

      let endX = e.changedTouches[0].clientX
      let endY = e.changedTouches[0].clientY

      let diffX = startX - endX
      let diffY = startY - endY

      // Basic swipe detection for future features
      if (Math.abs(diffX) > Math.abs(diffY)) {
        if (diffX > 50) {
          // Swipe left - next image
        } else if (diffX < -50) {
          // Swipe right - previous image
        }
      }
    })
  }
}
```

## Validation Gates

### Development Validation

```bash
# Python code quality and security
uv run ruff check src/ tests/      # Code linting
uv run mypy src/                   # Type checking
uv run bandit -r src/              # Security scanning
uv run pytest tests/               # Unit and integration tests

# Frontend code quality
npm run lint                       # JavaScript linting
npm run format:check               # Code formatting
npm test                          # JavaScript unit tests

# Database migrations
uv run alembic check               # Migration validation
uv run alembic upgrade head        # Apply migrations

# Docker build validation
docker-compose build               # Container build test
docker-compose up -d postgres      # Database startup
```

### Manual Testing Checklist

- [ ] **Registration Flow**: Complete registration with CAPTCHA and email verification
- [ ] **Profile Management**: Update all profile fields and verify persistence
- [ ] **Account Deletion**: Test deletion warning and complete data removal
- [ ] **Image Upload**: Upload multiple images with drag-and-drop and file picker
- [ ] **Mobile Experience**: Test all interfaces on mobile devices (320px+)
- [ ] **CAPTCHA Integration**: Verify CAPTCHA works in registration and voting
- [ ] **Email Services**: Test verification emails, resend functionality
- [ ] **Error Handling**: Test all error scenarios and validation messages

### Automated Testing Strategy

```python
# New test files to create
tests/test_profile_management.py      # Profile CRUD operations
tests/test_account_deletion.py        # Data deletion validation
tests/test_enhanced_registration.py   # CAPTCHA and verification flow
tests/test_image_upload_enhanced.py   # Enhanced upload functionality
tests/test_mobile_responsiveness.py   # Responsive layout validation
```

## Dependencies

### External Libraries

- **Google reCAPTCHA v2**: Already integrated in captcha service
- **PIL/Pillow**: Already available for image processing
- **Material Design 3**: Already implemented across the platform

### Internal Dependencies

- `AuthManager` class for JWT token management
- `CaptchaService` class for CAPTCHA verification
- `EmailService` class for verification emails
- `ImageService` class for file upload and optimization
- `InputSanitizer` class for security validation
- `DashboardManager` patterns for JavaScript architecture

## Error Handling Strategy

### Frontend Error Handling

```javascript
// Profile management error handling
class ProfileErrorHandler {
  handleProfileError(error) {
    if (error.status === 400) {
      // Validation errors
      this.showValidationErrors(error.details)
    } else if (error.status === 401) {
      // Authentication expired
      this.redirectToLogin()
    } else if (error.status === 413) {
      // File too large
      this.showError('File size exceeds 10MB limit')
    } else {
      // Generic error
      this.showError('An unexpected error occurred. Please try again.')
    }
  }
}
```

### Backend Error Handling

```python
# Account deletion error handling
@auth_router.delete("/account")
async def delete_user_account(current_user: CurrentUser, session: AsyncDatabaseSession):
    try:
        # Validate user can be deleted
        if current_user.is_super_admin:
            raise HTTPException(
                status_code=400,
                detail="Super admin accounts cannot be deleted"
            )

        # Begin transaction for atomic deletion
        async with session.begin():
            # Delete cascade will handle related data
            await session.delete(current_user)

        return {"message": "Account deleted successfully"}

    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete account due to data constraints"
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Account deletion failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Account deletion failed. Please try again."
        )
```

## Performance Optimizations

1. **Image Upload Optimization**: Use existing image service optimization (max 2048px, 85% JPEG quality)
2. **Lazy Loading**: Load profile data and images on demand
3. **Caching**: Cache user profile data in session storage
4. **Progressive Enhancement**: Core functionality works without JavaScript
5. **Mobile Performance**: Optimize touch interactions and reduce layout shifts

## Accessibility Standards

- **Keyboard Navigation**: All interactive elements accessible via keyboard
- **Screen Reader Support**: Proper ARIA labels and semantic HTML structure
- **High Contrast Mode**: Ensure visibility in high contrast settings
- **Focus Management**: Clear focus indicators and logical tab order
- **Form Labels**: All form inputs properly labeled and associated
- **Error Announcements**: Screen reader announcements for errors and success messages

## Risk Mitigation

| Risk                     | Impact | Mitigation                                                       |
| ------------------------ | ------ | ---------------------------------------------------------------- |
| CAPTCHA service failures | High   | Fallback to mock CAPTCHA in development, clear error messages    |
| Email delivery issues    | Medium | Resend functionality, clear status indicators                    |
| Image upload performance | Medium | Progress indicators, file size validation, chunked uploads       |
| Mobile compatibility     | High   | Progressive enhancement, extensive mobile testing                |
| Data deletion compliance | High   | Comprehensive audit logging, thorough testing of cascade deletes |

## Success Criteria

- [ ] All 6 user stories implemented and tested
- [ ] 100% CAPTCHA protection for registration and anonymous voting
- [ ] Complete account lifecycle management via web interface
- [ ] Mobile-first responsive design across all new interfaces
- [ ] GDPR-compliant account deletion with complete data removal
- [ ] Email verification flow with clear status indicators
- [ ] Enhanced image upload with drag-and-drop and batch processing
- [ ] Zero security vulnerabilities in new code
- [ ] <3 second page load times for all new interfaces

## Task Breakdown Reference

**Implementation Tasks**: See detailed breakdown in `/docs/tasks/sprint-4-user-experience.md`

The task breakdown includes 10 detailed, actionable development tasks organized in 4 phases:

- **Phase 1**: Account Management Foundation (T-001 through T-004)
  - User profile management backend API and UI interface
  - Account deletion with complete data cleanup and warning UI
- **Phase 2**: Registration Enhancement (T-005 through T-006)
  - CAPTCHA integration in registration flow
  - Email verification status indicators and resend functionality
- **Phase 3**: Enhanced Features (T-007 through T-008)
  - Drag-and-drop image upload with batch processing
  - Simple URL sharing with copy-to-clipboard functionality
- **Phase 4**: Mobile Experience (T-009 through T-010)
  - Mobile-first responsive design across all new interfaces
  - Touch interaction enhancements and mobile optimization

Each task includes Given-When-Then acceptance criteria, manual testing steps, file modification lists, validation gates, and clear integration points with existing backend services (JWT auth, email service, CAPTCHA service, image processing service).

---

**Confidence Score**: 9/10
_Rationale_: Exceptional confidence due to complete backend infrastructure already in place (authentication, email, CAPTCHA, image processing), established Material Design 3 patterns, clear integration path, and comprehensive existing validation. The only minor uncertainty is specific mobile interaction patterns, but existing responsive framework provides strong guidance.

**Estimated Timeline**: 7-8 days
**Team Size**: 2-3 developers
**Dependencies**: Sprint 3 completion, existing authentication system validation
