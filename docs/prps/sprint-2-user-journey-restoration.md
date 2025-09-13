# Sprint 2: User Journey Restoration - Product Requirements & Plans (PRP)

**Version**: 1.0
**Date**: January 13, 2025
**Sprint Duration**: Week 2
**Status**: Ready for Implementation

---

## Executive Summary

Sprint 2 focuses on restoring the complete user journey from authentication to vote creation and sharing. Building on Sprint 1's successful authentication foundation, this sprint implements the core voting functionality that transforms the Cardinal Vote platform from a landing page into a fully functional voting system.

**Key Deliverables:**

- Complete vote creation interface with dynamic option management
- Modern Material Design 3 dashboard with status cards and activity timeline
- Vote preview system showing "as voters would see it" view
- Comprehensive sharing controls with both public links and access codes
- End-to-end user journey: Login → Dashboard → Create → Preview → Share → Vote

**Business Impact:** Users can now complete their primary workflow - creating and sharing votes - addressing the critical gap identified in Sprint 1 where users had JWT tokens but no functional interface to use them.

---

## 1. Business Requirements

### 1.1 Primary User Journey

**Sprint 2 Success Criteria:**

```
As a vote creator, I want to:
1. ✅ Access the landing page (Sprint 1 Complete)
2. ✅ Register/login (Sprint 1 Complete)
3. ✅ Access my user-admin panel (Sprint 1 Basic Complete)
4. 🎯 Create votes with options (Sprint 2 Target)
5. 🎯 Share voting links (Sprint 2 Target)
6. 🎯 Preview votes as voters would see them (Sprint 2 Target)
7. ⏭️ Monitor vote progress (Sprint 3)
8. ⏭️ View and export results (Sprint 3)
```

### 1.2 Functional Requirements

#### Vote Creation Requirements

- **REQ-1**: When user clicks "Create Vote", the system shall display a dynamic form with title, description, and option fields
- **REQ-2**: While adding vote options, the system shall allow dynamic addition/removal up to 20 options maximum
- **REQ-3**: Where vote creation is completed, the system shall generate unique public URLs and optional access codes

#### Dashboard Requirements

- **REQ-4**: When user accesses dashboard, the system shall display status cards showing vote statistics
- **REQ-5**: While viewing dashboard, the system shall show activity timeline with recent actions
- **REQ-6**: Where votes exist, the system shall organize them by status (active, draft, closed)

#### Sharing & Access Requirements

- **REQ-7**: When vote is created, the system shall provide both public links and optional access code protection
- **REQ-8**: While sharing votes, the system shall allow mixed access (public + authenticated users)
- **REQ-9**: Where votes are accessed, the system shall enforce access controls appropriately

### 1.3 Non-Functional Requirements

- **Performance**: Dashboard loads within 2 seconds, form interactions feel responsive
- **Security**: Access codes properly enforced, JWT tokens validated for authenticated features
- **Accessibility**: Material Design 3 WCAG compliance, keyboard navigation, screen reader support
- **Compatibility**: Works on desktop (1280px+), tablet (600-1279px), mobile (320-599px)

---

## 2. Technical Architecture

### 2.1 System Integration Points

**Existing Infrastructure (Sprint 1 Foundation):**

```
✅ FastAPI backend with 14+ API endpoints
✅ JWT-based authentication system (/api/auth/*)
✅ Vote CRUD operations (/api/votes/*)
✅ Basic user dashboard template
✅ Material Design 3 UI framework
✅ PostgreSQL with UUID primary keys
✅ Image upload and processing pipeline
```

**Sprint 2 Extensions Required:**

```
🎯 Vote creation modal/form interface
🎯 Dynamic option management UI
🎯 Dashboard enhancement with status cards
🎯 Activity timeline implementation
🎯 Vote preview functionality
🎯 Sharing interface with access controls
🎯 Access code field addition to Vote model
```

### 2.2 Data Architecture

**Database Extensions:**

```sql
-- Add access code support to existing Vote table
ALTER TABLE votes ADD COLUMN access_code VARCHAR(50) NULL;
ALTER TABLE votes ADD COLUMN require_auth BOOLEAN DEFAULT FALSE;

-- Existing tables to leverage:
-- votes: id, title, description, slug, status, creator_email
-- vote_options: id, vote_id, content, content_type, display_order
-- voter_responses: id, vote_id, option_id, rating, voter_session_id
```

**API Endpoints to Implement:**

```python
# Extend existing vote creation
POST /api/votes/  # Enhanced with access_code field
GET /api/votes/stats/  # Dashboard statistics
GET /api/votes/recent/  # Activity timeline data

# New sharing endpoints
GET /api/votes/{vote_id}/sharing  # Get sharing options
POST /api/votes/{vote_id}/access-code  # Generate/update access code
GET /api/votes/preview/{vote_id}  # Preview vote as voters see it
```

### 2.3 Frontend Architecture

**Component Structure:**

```
src/
├── static/js/
│   ├── vote-creation-manager.js     # Vote creation logic
│   ├── dashboard-enhanced.js        # Dashboard with timeline
│   └── vote-preview.js              # Preview functionality
├── static/css/
│   ├── vote-creation.css            # Form styling
│   ├── dashboard-enhanced.css       # Cards + timeline
│   └── vote-preview.css             # Preview interface
└── templates/
    ├── vote-creation-modal.html     # Creation form template
    ├── vote-preview.html            # Preview template
    └── sharing-modal.html           # Sharing interface
```

---

## 3. Implementation Details

### 3.1 Vote Creation Interface

**Component Reference Pattern:**
Following `/mnt/cephfs/Shared/dropvault/toveco-dev/templates/landing_material.html:221-336` modal implementation:

```html
<!-- Vote Creation Modal -->
<div class="md-dialog-scrim" id="voteCreationModalScrim" role="dialog">
  <div class="md-dialog vote-creation-dialog">
    <div class="md-dialog-icon">
      <span class="material-icons">poll</span>
    </div>
    <h2 class="md-dialog-headline">Create New Vote</h2>
    <div class="md-dialog-supporting-text">
      <form id="voteCreationForm" class="vote-form">
        <!-- Title Field -->
        <div class="md-text-field md-text-field-outlined">
          <input
            type="text"
            id="voteTitle"
            class="md-text-field-input"
            placeholder=" "
            required
            maxlength="200"
          />
          <label for="voteTitle" class="md-text-field-label">Vote Title</label>
        </div>

        <!-- Description Field -->
        <div class="md-text-field md-text-field-outlined">
          <textarea
            id="voteDescription"
            class="md-text-field-input"
            placeholder=" "
            rows="3"
            maxlength="1000"
          ></textarea>
          <label for="voteDescription" class="md-text-field-label">Description (Optional)</label>
        </div>

        <!-- Dynamic Options Container -->
        <div class="vote-options-container">
          <h3 class="md-title-medium">Vote Options</h3>
          <div id="voteOptionsContainer" class="options-list">
            <!-- Dynamic option fields will be inserted here -->
          </div>
          <div class="option-controls">
            <button
              type="button"
              class="md-button md-button-outlined"
              id="addOptionBtn"
              data-action="add-option"
            >
              <span class="material-icons">add</span>
              Add Option
            </button>
            <span class="option-counter">2 of 20 options</span>
          </div>
        </div>

        <!-- Access Settings -->
        <div class="access-settings">
          <h3 class="md-title-medium">Access Settings</h3>
          <div class="setting-row">
            <label class="md-switch">
              <input type="checkbox" id="requireAuth" class="md-switch-input" />
              <div class="md-switch-track">
                <div class="md-switch-thumb"></div>
              </div>
            </label>
            <span>Require user account to vote</span>
          </div>
          <div class="setting-row">
            <label class="md-switch">
              <input type="checkbox" id="useAccessCode" class="md-switch-input" />
              <div class="md-switch-track">
                <div class="md-switch-thumb"></div>
              </div>
            </label>
            <span>Protect with access code</span>
          </div>
          <div
            class="md-text-field md-text-field-outlined access-code-field"
            id="accessCodeField"
            style="display: none;"
          >
            <input
              type="text"
              id="accessCode"
              class="md-text-field-input"
              placeholder=" "
              maxlength="50"
            />
            <label for="accessCode" class="md-text-field-label">Access Code</label>
          </div>
        </div>
      </form>
    </div>
    <div class="md-dialog-actions">
      <button type="button" class="md-button md-button-text" data-action="close-modal">
        Cancel
      </button>
      <button
        type="submit"
        form="voteCreationForm"
        class="md-button md-button-filled"
        id="createVoteBtn"
      >
        <span class="btn-text">Create Vote</span>
        <span class="material-icons btn-loading" style="display: none;">refresh</span>
      </button>
    </div>
  </div>
</div>
```

**Dynamic Options Management JavaScript:**
Following `/mnt/cephfs/Shared/dropvault/toveco-dev/static/js/landing-material.js:147-499` AuthenticationManager pattern:

```javascript
class VoteCreationManager {
  constructor() {
    this.API_BASE = '/api'
    this.maxOptions = 20
    this.minOptions = 2
    this.currentOptionCount = 2
    this.modal = null
    this.form = null
  }

  static init() {
    const manager = new VoteCreationManager()
    manager.initializeElements()
    manager.initializeEventListeners()
    manager.initializeDefaultOptions()
  }

  initializeElements() {
    this.modal = document.getElementById('voteCreationModalScrim')
    this.form = document.getElementById('voteCreationForm')
    this.optionsContainer = document.getElementById('voteOptionsContainer')
    this.addOptionBtn = document.getElementById('addOptionBtn')
    this.optionCounter = document.querySelector('.option-counter')
  }

  initializeDefaultOptions() {
    // Create initial 2 options
    this.addOptionField('Option 1', true)
    this.addOptionField('Option 2', true)
    this.updateOptionCounter()
  }

  addOptionField(placeholder = '', isDefault = false) {
    if (this.currentOptionCount >= this.maxOptions) {
      this.showSnackbar(`Maximum ${this.maxOptions} options allowed`)
      return
    }

    const optionId = `option-${Date.now()}`
    const optionHtml = `
            <div class="vote-option-field" data-option-id="${optionId}">
                <div class="md-text-field md-text-field-outlined">
                    <input type="text" id="${optionId}" class="md-text-field-input option-input"
                           placeholder=" " required maxlength="200" value="${placeholder}">
                    <label for="${optionId}" class="md-text-field-label">Option ${this.currentOptionCount + 1}</label>
                </div>
                ${
                  !isDefault
                    ? `
                <button type="button" class="md-button md-button-icon remove-option-btn"
                        data-action="remove-option" data-option-id="${optionId}">
                    <span class="material-icons">close</span>
                </button>
                `
                    : ''
                }
            </div>
        `

    this.optionsContainer.insertAdjacentHTML('beforeend', optionHtml)
    this.currentOptionCount++
    this.updateOptionCounter()
    this.updateAddButtonState()
  }

  removeOptionField(optionId) {
    if (this.currentOptionCount <= this.minOptions) {
      this.showSnackbar(`Minimum ${this.minOptions} options required`)
      return
    }

    const optionField = document.querySelector(`[data-option-id="${optionId}"]`)
    if (optionField) {
      optionField.remove()
      this.currentOptionCount--
      this.updateOptionCounter()
      this.updateAddButtonState()
      this.renumberOptions()
    }
  }

  async handleCreateVote(event) {
    event.preventDefault()

    const submitBtn = document.getElementById('createVoteBtn')
    const formData = this.collectFormData()

    if (!this.validateFormData(formData)) {
      return
    }

    this.setButtonLoading(submitBtn, true)

    try {
      const response = await fetch(`${this.API_BASE}/votes/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getAccessToken()}`
        },
        body: JSON.stringify(formData)
      })

      const data = await response.json()

      if (response.ok) {
        this.closeModal()
        // Redirect to vote preview with sharing options
        window.location.href = `/vote-preview/${data.id}?sharing=true`
      } else {
        this.showError(data.message || 'Failed to create vote')
      }
    } catch (error) {
      console.error('Vote creation error:', error)
      this.showError('Network error. Please try again.')
    } finally {
      this.setButtonLoading(submitBtn, false)
    }
  }

  collectFormData() {
    const title = document.getElementById('voteTitle').value.trim()
    const description = document.getElementById('voteDescription').value.trim()
    const requireAuth = document.getElementById('requireAuth').checked
    const useAccessCode = document.getElementById('useAccessCode').checked
    const accessCode = useAccessCode ? document.getElementById('accessCode').value.trim() : null

    const options = Array.from(document.querySelectorAll('.option-input'))
      .map((input, index) => ({
        content: input.value.trim(),
        content_type: 'text',
        display_order: index + 1
      }))
      .filter(option => option.content.length > 0)

    return {
      title,
      description: description || null,
      options,
      require_auth: requireAuth,
      access_code: accessCode,
      status: 'draft' // Start as draft, can be activated later
    }
  }
}
```

### 3.2 Enhanced Dashboard with Status Cards & Timeline

**Following Material Design 3 research findings** - maximum 6 status cards with integrated activity timeline:

```html
<!-- Enhanced Dashboard Template -->
<!-- Extend /mnt/cephfs/Shared/dropvault/toveco-dev/templates/user_dashboard.html -->

<!-- Status Cards Section (Replace existing stats-section) -->
<section class="dashboard-cards-section">
  <div class="md-container">
    <h2 class="md-headline-medium section-title">Your Voting Overview</h2>
    <div class="status-cards-grid">
      <!-- Card 1: Total Votes -->
      <div class="md-card md-card-elevated status-card vote-card">
        <div class="card-header">
          <div class="card-icon primary-icon">
            <span class="material-icons">poll</span>
          </div>
          <div class="card-actions">
            <button class="md-button md-button-icon" data-action="refresh-stats">
              <span class="material-icons">refresh</span>
            </button>
          </div>
        </div>
        <div class="card-content">
          <h3 class="md-title-large card-metric" id="totalVotesMetric">0</h3>
          <p class="md-body-medium card-label">Total Votes</p>
          <div class="card-trend">
            <span class="material-icons trend-icon">trending_up</span>
            <span class="trend-text" id="totalVotesTrend">+0 this week</span>
          </div>
        </div>
      </div>

      <!-- Card 2: Active Votes -->
      <div class="md-card md-card-elevated status-card active-card">
        <div class="card-header">
          <div class="card-icon success-icon">
            <span class="material-icons">play_circle</span>
          </div>
        </div>
        <div class="card-content">
          <h3 class="md-title-large card-metric" id="activeVotesMetric">0</h3>
          <p class="md-body-medium card-label">Active Votes</p>
          <div class="card-trend">
            <span class="material-icons trend-icon">schedule</span>
            <span class="trend-text" id="activeVotesTrend">Collecting responses</span>
          </div>
        </div>
      </div>

      <!-- Card 3: Total Responses -->
      <div class="md-card md-card-elevated status-card responses-card">
        <div class="card-header">
          <div class="card-icon tertiary-icon">
            <span class="material-icons">people</span>
          </div>
        </div>
        <div class="card-content">
          <h3 class="md-title-large card-metric" id="totalResponsesMetric">0</h3>
          <p class="md-body-medium card-label">Total Responses</p>
          <div class="card-trend">
            <span class="material-icons trend-icon">analytics</span>
            <span class="trend-text" id="responsesTrend">Across all votes</span>
          </div>
        </div>
      </div>

      <!-- Card 4: Draft Votes -->
      <div class="md-card md-card-elevated status-card draft-card">
        <div class="card-header">
          <div class="card-icon warning-icon">
            <span class="material-icons">edit</span>
          </div>
        </div>
        <div class="card-content">
          <h3 class="md-title-large card-metric" id="draftVotesMetric">0</h3>
          <p class="md-body-medium card-label">Draft Votes</p>
          <div class="card-trend">
            <span class="material-icons trend-icon">pending</span>
            <span class="trend-text" id="draftVotesTrend">Ready to publish</span>
          </div>
        </div>
      </div>

      <!-- Card 5: This Week Activity -->
      <div class="md-card md-card-elevated status-card activity-card">
        <div class="card-header">
          <div class="card-icon info-icon">
            <span class="material-icons">today</span>
          </div>
        </div>
        <div class="card-content">
          <h3 class="md-title-large card-metric" id="weeklyActivityMetric">0</h3>
          <p class="md-body-medium card-label">This Week</p>
          <div class="card-trend">
            <span class="material-icons trend-icon">timeline</span>
            <span class="trend-text" id="weeklyActivityTrend">Actions taken</span>
          </div>
        </div>
      </div>

      <!-- Card 6: Quick Actions -->
      <div class="md-card md-card-elevated status-card action-card">
        <div class="card-header">
          <div class="card-icon accent-icon">
            <span class="material-icons">rocket_launch</span>
          </div>
        </div>
        <div class="card-content quick-actions">
          <button class="md-button md-button-filled" data-action="create-vote">
            <span class="material-icons">add</span>
            New Vote
          </button>
          <button class="md-button md-button-outlined" data-action="view-analytics">
            <span class="material-icons">analytics</span>
            View Analytics
          </button>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Activity Timeline Section -->
<section class="activity-timeline-section">
  <div class="md-container">
    <div class="section-header">
      <h2 class="md-headline-medium">Recent Activity</h2>
      <div class="timeline-controls">
        <button class="md-button md-button-text" id="refreshTimeline">
          <span class="material-icons">refresh</span>
          Refresh
        </button>
        <button class="md-button md-button-text" data-action="view-all-activity">
          View All
          <span class="material-icons">arrow_forward</span>
        </button>
      </div>
    </div>

    <div class="activity-timeline" id="activityTimeline">
      <!-- Timeline items will be loaded here -->
      <div class="timeline-empty-state" id="timelineEmptyState">
        <div class="empty-state-icon">
          <span class="material-icons">timeline</span>
        </div>
        <h3 class="md-headline-small">No recent activity</h3>
        <p class="md-body-medium md-on-surface-variant">
          Your voting activity will appear here as you create and manage votes.
        </p>
      </div>
    </div>

    <div class="timeline-pagination" id="timelinePagination" style="display: none;">
      <button class="md-button md-button-outlined" id="loadMoreTimeline">
        <span class="material-icons">expand_more</span>
        Load More Activity
      </button>
    </div>
  </div>
</section>
```

**Activity Timeline JavaScript Implementation:**

```javascript
class ActivityTimelineManager {
  constructor() {
    this.API_BASE = '/api'
    this.timelineContainer = null
    this.maxItems = 30 // GitHub 2025 standard
    this.currentPage = 1
    this.itemsPerPage = 10
  }

  async loadTimelineData() {
    const token = this.getAccessToken()
    if (!token) return

    try {
      const response = await fetch(
        `${this.API_BASE}/votes/activity?page=${this.currentPage}&limit=${this.itemsPerPage}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      if (response.ok) {
        const data = await response.json()
        this.renderTimelineItems(data.activities)
        this.updatePagination(data.has_more)
      }
    } catch (error) {
      console.error('Failed to load timeline:', error)
    }
  }

  renderTimelineItems(activities) {
    const emptyState = document.getElementById('timelineEmptyState')

    if (activities.length === 0) {
      emptyState.style.display = 'block'
      return
    }

    emptyState.style.display = 'none'

    const timelineHtml = activities
      .map(
        activity => `
            <div class="timeline-item ${activity.type}" data-activity-id="${activity.id}">
                <div class="timeline-marker">
                    <div class="timeline-icon ${this.getActivityIconClass(activity.type)}">
                        <span class="material-icons">${this.getActivityIcon(activity.type)}</span>
                    </div>
                </div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <h4 class="md-body-large timeline-title">${activity.title}</h4>
                        <span class="md-body-small timeline-time" data-timestamp="${activity.created_at}">
                            ${this.formatTimeAgo(activity.created_at)}
                        </span>
                    </div>
                    <p class="md-body-medium timeline-description">${activity.description}</p>
                    ${
                      activity.vote_slug
                        ? `
                        <div class="timeline-actions">
                            <button class="md-button md-button-text" data-action="view-vote" data-slug="${activity.vote_slug}">
                                View Vote
                                <span class="material-icons">arrow_outward</span>
                            </button>
                        </div>
                    `
                        : ''
                    }
                </div>
            </div>
        `
      )
      .join('')

    if (this.currentPage === 1) {
      this.timelineContainer.innerHTML = timelineHtml
    } else {
      this.timelineContainer.insertAdjacentHTML('beforeend', timelineHtml)
    }
  }

  getActivityIcon(type) {
    const icons = {
      vote_created: 'add_circle',
      vote_published: 'publish',
      vote_closed: 'block',
      response_received: 'how_to_vote',
      vote_shared: 'share',
      vote_edited: 'edit'
    }
    return icons[type] || 'activity'
  }

  // Real-time updates via WebSocket (future enhancement)
  initializeRealTimeUpdates() {
    // WebSocket connection for live activity updates
    // Implementation follows existing auth pattern
  }
}
```

### 3.3 Vote Preview Interface

**Vote Preview Template** (New file: `/mnt/cephfs/Shared/dropvault/toveco-dev/templates/vote_preview.html`):

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Preview: {{ vote.title }} - {{ app_name }}</title>

    <!-- Same CSS framework as existing templates -->
    <link rel="stylesheet" href="/static/css/material-design.css" />
    <link rel="stylesheet" href="/static/css/vote-preview.css" />
    <link
      href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap"
      rel="stylesheet"
    />
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet" />
  </head>
  <body>
    <!-- Preview Mode Banner -->
    <div class="preview-banner">
      <div class="md-container">
        <div class="banner-content">
          <span class="material-icons">visibility</span>
          <span class="banner-text">Preview Mode - This is how voters will see your vote</span>
          <button class="md-button md-button-text" data-action="edit-vote">
            <span class="material-icons">edit</span>
            Edit Vote
          </button>
        </div>
      </div>
    </div>

    <!-- Vote Preview Content (Same as public_vote.html structure) -->
    <main class="vote-preview-content">
      <!-- Vote content rendered here using existing public vote template structure -->
      {% include 'public_vote_content.html' %}
    </main>

    <!-- Sharing Control Panel -->
    <div class="sharing-panel" id="sharingPanel">
      <div class="md-container">
        <div class="panel-header">
          <h2 class="md-headline-medium">Share Your Vote</h2>
          <button class="panel-toggle" id="panelToggle" data-action="toggle-sharing-panel">
            <span class="material-icons">expand_less</span>
          </button>
        </div>

        <div class="panel-content" id="panelContent">
          <div class="sharing-options">
            <!-- Public Link Section -->
            <div class="sharing-option">
              <div class="option-header">
                <div class="option-icon">
                  <span class="material-icons">link</span>
                </div>
                <div class="option-info">
                  <h3 class="md-title-medium">Public Link</h3>
                  <p class="md-body-medium">Anyone with this link can vote</p>
                </div>
              </div>
              <div class="option-controls">
                <div class="md-text-field md-text-field-outlined">
                  <input
                    type="text"
                    id="publicLink"
                    class="md-text-field-input"
                    value="{{ vote.public_url }}"
                    readonly
                  />
                  <label for="publicLink" class="md-text-field-label">Public Voting Link</label>
                </div>
                <button
                  class="md-button md-button-filled"
                  data-action="copy-link"
                  data-target="publicLink"
                >
                  <span class="material-icons">content_copy</span>
                  Copy Link
                </button>
              </div>
            </div>

            {% if vote.access_code %}
            <!-- Access Code Section -->
            <div class="sharing-option">
              <div class="option-header">
                <div class="option-icon">
                  <span class="material-icons">lock</span>
                </div>
                <div class="option-info">
                  <h3 class="md-title-medium">Access Code</h3>
                  <p class="md-body-medium">Voters need this code to access the vote</p>
                </div>
              </div>
              <div class="option-controls">
                <div class="md-text-field md-text-field-outlined">
                  <input
                    type="text"
                    id="accessCode"
                    class="md-text-field-input"
                    value="{{ vote.access_code }}"
                    readonly
                  />
                  <label for="accessCode" class="md-text-field-label">Access Code</label>
                </div>
                <button class="md-button md-button-outlined" data-action="copy-code">
                  <span class="material-icons">content_copy</span>
                  Copy Code
                </button>
                <button class="md-button md-button-text" data-action="regenerate-code">
                  <span class="material-icons">refresh</span>
                  Regenerate
                </button>
              </div>
            </div>
            {% endif %}

            <!-- Additional Sharing Options -->
            <div class="sharing-option">
              <div class="option-header">
                <div class="option-info">
                  <h3 class="md-title-medium">More Sharing Options</h3>
                </div>
              </div>
              <div class="option-controls sharing-buttons">
                <button class="md-button md-button-outlined" data-action="share-email">
                  <span class="material-icons">email</span>
                  Email
                </button>
                <button class="md-button md-button-outlined" data-action="share-social">
                  <span class="material-icons">share</span>
                  Social Media
                </button>
                <button class="md-button md-button-outlined" data-action="embed-code">
                  <span class="material-icons">code</span>
                  Embed Code
                </button>
              </div>
            </div>
          </div>

          <!-- Vote Actions -->
          <div class="vote-actions">
            <button class="md-button md-button-text" data-action="back-to-dashboard">
              <span class="material-icons">arrow_back</span>
              Back to Dashboard
            </button>
            <button class="md-button md-button-outlined" data-action="edit-vote">
              <span class="material-icons">edit</span>
              Edit Vote
            </button>
            <button
              class="md-button md-button-filled"
              data-action="publish-vote"
              id="publishVoteBtn"
            >
              <span class="material-icons">publish</span>
              Publish Vote
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Snackbar for notifications -->
    <div class="md-snackbar" id="snackbar">
      <span id="snackbar-message"></span>
      <button class="md-snackbar-action" id="snackbar-action">DISMISS</button>
    </div>

    <script src="/static/js/vote-preview.js"></script>
  </body>
</html>
```

---

## 4. API Implementation

### 4.1 Enhanced Vote Creation Endpoint

**Extend existing endpoint** `/mnt/cephfs/Shared/dropvault/toveco-dev/src/cardinal_vote/vote_routes.py:85-195`:

```python
# Add to existing VoteCreate Pydantic model (models.py)
class VoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    options: List[VoteOptionCreate] = Field(..., min_items=2, max_items=20)
    require_auth: bool = Field(default=False)
    access_code: Optional[str] = Field(None, max_length=50)
    status: VoteStatus = Field(default=VoteStatus.DRAFT)

# Enhanced vote creation endpoint
@vote_router.post("/", response_model=VoteResponse)
async def create_vote_enhanced(
    vote_data: VoteCreate,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
    image_service: ImageServiceDep = Depends(get_image_service),
) -> VoteResponse:
    """Create a new vote with enhanced options and access controls."""

    try:
        # Validate access code if provided
        if vote_data.access_code:
            if len(vote_data.access_code.strip()) < 4:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Access code must be at least 4 characters"
                )
            vote_data.access_code = vote_data.access_code.strip()

        # Generate unique slug
        slug = await generate_unique_slug(session, vote_data.title)

        # Create vote record
        vote = Vote(
            title=vote_data.title.strip(),
            description=vote_data.description.strip() if vote_data.description else None,
            slug=slug,
            status=vote_data.status,
            creator_email=current_user.email,
            require_auth=vote_data.require_auth,
            access_code=vote_data.access_code,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        session.add(vote)
        await session.flush()  # Get vote ID

        # Create vote options
        for i, option_data in enumerate(vote_data.options):
            option = VoteOption(
                vote_id=vote.id,
                content=option_data.content.strip(),
                content_type=option_data.content_type,
                display_order=i + 1
            )
            session.add(option)

        await session.commit()

        # Log activity for timeline
        await log_activity(
            session,
            user_id=current_user.id,
            activity_type="vote_created",
            title=f"Created vote: {vote.title}",
            vote_slug=vote.slug
        )

        # Prepare response with sharing URLs
        vote_response = VoteResponse.model_validate(vote)
        vote_response.public_url = f"{settings.BASE_URL}/vote/{vote.slug}"

        return vote_response

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to create vote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vote"
        ) from e

# New activity logging endpoint
@vote_router.get("/activity", response_model=ActivityResponse)
async def get_user_activity(
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50)
) -> ActivityResponse:
    """Get user's recent activity for dashboard timeline."""

    offset = (page - 1) * limit

    query = (
        select(Activity)
        .where(Activity.user_id == current_user.id)
        .order_by(Activity.created_at.desc())
        .offset(offset)
        .limit(limit + 1)  # Get one extra to check if there are more
    )

    result = await session.execute(query)
    activities = result.scalars().all()

    has_more = len(activities) > limit
    if has_more:
        activities = activities[:limit]

    return ActivityResponse(
        activities=[ActivityItem.model_validate(activity) for activity in activities],
        total=len(activities),
        page=page,
        has_more=has_more
    )

# New vote preview endpoint
@vote_router.get("/preview/{vote_id}", response_class=HTMLResponse)
async def vote_preview(
    request: Request,
    vote_id: str,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
) -> HTMLResponse:
    """Serve vote preview page with sharing controls."""

    # Get vote with options
    query = (
        select(Vote)
        .options(selectinload(Vote.options))
        .where(Vote.id == vote_id, Vote.creator_email == current_user.email)
    )

    result = await session.execute(query)
    vote = result.scalar_one_or_none()

    if not vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vote not found"
        )

    # Prepare template context
    vote_context = {
        "request": request,
        "vote": vote,
        "app_name": settings.APP_NAME,
        "show_sharing": True
    }

    return templates.TemplateResponse("vote_preview.html", vote_context)
```

### 4.2 Dashboard Statistics API

```python
# New dashboard stats endpoint
@vote_router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
) -> DashboardStats:
    """Get dashboard statistics for status cards."""

    # Get user's vote counts by status
    vote_stats_query = (
        select(
            Vote.status,
            func.count(Vote.id).label('count')
        )
        .where(Vote.creator_email == current_user.email)
        .group_by(Vote.status)
    )

    vote_stats_result = await session.execute(vote_stats_query)
    vote_stats = {row.status: row.count for row in vote_stats_result}

    # Get total responses across all user votes
    responses_query = (
        select(func.count(VoterResponse.id))
        .join(Vote, VoterResponse.vote_id == Vote.id)
        .where(Vote.creator_email == current_user.email)
    )

    responses_result = await session.execute(responses_query)
    total_responses = responses_result.scalar() or 0

    # Get this week's activity count
    week_start = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_activity_query = (
        select(func.count(Activity.id))
        .where(
            Activity.user_id == current_user.id,
            Activity.created_at >= week_start
        )
    )

    weekly_result = await session.execute(weekly_activity_query)
    weekly_activity = weekly_result.scalar() or 0

    return DashboardStats(
        total_votes=sum(vote_stats.values()),
        active_votes=vote_stats.get('active', 0),
        draft_votes=vote_stats.get('draft', 0),
        closed_votes=vote_stats.get('closed', 0),
        total_responses=total_responses,
        weekly_activity=weekly_activity,
        trends={
            'votes_this_week': weekly_activity,  # Simplified for MVP
            'responses_this_week': 0  # Future enhancement
        }
    )

# Add to models.py
class DashboardStats(BaseModel):
    total_votes: int
    active_votes: int
    draft_votes: int
    closed_votes: int
    total_responses: int
    weekly_activity: int
    trends: Dict[str, int]

class ActivityItem(BaseModel):
    id: str
    type: str
    title: str
    description: str
    created_at: datetime
    vote_slug: Optional[str] = None

class ActivityResponse(BaseModel):
    activities: List[ActivityItem]
    total: int
    page: int
    has_more: bool
```

---

## 5. CSS Styling Implementation

### 5.1 Vote Creation Modal Styles

**New file**: `/mnt/cephfs/Shared/dropvault/toveco-dev/static/css/vote-creation.css`:

```css
/* Vote Creation Modal Styles - Material Design 3 */

/* Extend existing modal styles from landing-material.css */
.vote-creation-dialog {
  max-width: 800px; /* Larger for form content */
  max-height: 90vh;
  overflow-y: auto;
}

/* Vote Form Layout */
.vote-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin: 16px 0;
}

.vote-form .md-text-field {
  margin-bottom: 8px;
}

.vote-form textarea.md-text-field-input {
  min-height: 80px;
  resize: vertical;
}

/* Dynamic Options Container */
.vote-options-container {
  margin: 24px 0;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 16px 0;
}

.vote-option-field {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  position: relative;
}

.vote-option-field .md-text-field {
  flex: 1;
  margin-bottom: 0;
}

.remove-option-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--md-sys-shape-corner-full);
  background-color: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  margin-top: 8px; /* Align with input field */
  flex-shrink: 0;
}

.remove-option-btn:hover {
  background-color: var(--md-sys-color-error);
  color: var(--md-sys-color-on-error);
}

/* Option Controls */
.option-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding: 16px 0;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.option-counter {
  font-size: var(--md-sys-typescale-body-small-size);
  color: var(--md-sys-color-on-surface-variant);
}

/* Access Settings */
.access-settings {
  margin: 24px 0;
  padding: 16px;
  background-color: var(--md-sys-color-surface-container-low);
  border-radius: var(--md-sys-shape-corner-medium);
}

.setting-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 12px 0;
}

.access-code-field {
  margin-left: 36px; /* Align with switch content */
  margin-top: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.access-code-field.show {
  opacity: 1;
  max-height: 100px;
}

.access-code-field.hide {
  opacity: 0;
  max-height: 0;
  margin: 0;
  padding: 0;
}

/* Responsive Design */
@media (max-width: 640px) {
  .vote-creation-dialog {
    width: calc(100vw - 32px);
    max-width: none;
    margin: 16px;
    max-height: calc(100vh - 32px);
  }

  .vote-option-field {
    flex-direction: column;
    align-items: stretch;
  }

  .remove-option-btn {
    align-self: flex-end;
    margin-top: -8px;
    margin-bottom: 8px;
  }

  .option-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}

/* Animation for adding/removing options */
.vote-option-field {
  animation: slideInUp 0.3s ease-out;
}

.vote-option-field.removing {
  animation: slideOutUp 0.3s ease-in forwards;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideOutUp {
  to {
    opacity: 0;
    transform: translateY(-20px);
    height: 0;
    margin: 0;
    padding: 0;
  }
}
```

### 5.2 Enhanced Dashboard Styles

**Extend** `/mnt/cephfs/Shared/dropvault/toveco-dev/static/css/dashboard.css`:

```css
/* Enhanced Dashboard Styles - Status Cards + Timeline */

/* Status Cards Grid */
.dashboard-cards-section {
  padding: 32px 0;
  background: linear-gradient(
    135deg,
    var(--md-sys-color-primary-container) 0%,
    var(--md-sys-color-surface) 100%
  );
}

.status-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* Status Card Base Styles */
.status-card {
  padding: 24px;
  background-color: var(--md-sys-color-surface);
  border-radius: var(--md-sys-shape-corner-large);
  box-shadow: var(--md-elevation-level2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.status-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--md-elevation-level4);
}

.status-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--md-sys-color-primary), var(--md-sys-color-tertiary));
}

/* Card Header */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--md-sys-shape-corner-medium);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-icon.primary-icon {
  background-color: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.card-icon.success-icon {
  background-color: #e8f5e8;
  color: #2e7d2e;
}

.card-icon.tertiary-icon {
  background-color: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.card-icon.warning-icon {
  background-color: #fff4e6;
  color: #f57c00;
}

.card-icon.info-icon {
  background-color: #e3f2fd;
  color: #1976d2;
}

.card-icon.accent-icon {
  background-color: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

/* Card Content */
.card-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-metric {
  font-size: 2.5rem;
  font-weight: 500;
  line-height: 1.2;
  color: var(--md-sys-color-on-surface);
  margin: 0;
}

.card-label {
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

.card-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
}

.trend-icon {
  font-size: 18px;
  color: var(--md-sys-color-primary);
}

.trend-text {
  font-size: var(--md-sys-typescale-body-small-size);
  color: var(--md-sys-color-on-surface-variant);
}

/* Quick Actions Card */
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.quick-actions .md-button {
  justify-content: flex-start;
  width: 100%;
}

/* Activity Timeline Styles */
.activity-timeline-section {
  padding: 32px 0 48px;
  background-color: var(--md-sys-color-surface);
}

.activity-timeline {
  max-width: 800px;
  margin: 0 auto;
}

.timeline-item {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  position: relative;
}

.timeline-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 20px;
  top: 48px;
  bottom: -24px;
  width: 2px;
  background-color: var(--md-sys-color-outline-variant);
}

.timeline-marker {
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.timeline-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--md-sys-shape-corner-full);
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  box-shadow: 0 0 0 4px var(--md-sys-color-surface);
}

.timeline-content {
  flex: 1;
  padding: 8px 0;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 8px;
}

.timeline-title {
  margin: 0;
  color: var(--md-sys-color-on-surface);
  flex: 1;
}

.timeline-time {
  color: var(--md-sys-color-on-surface-variant);
  white-space: nowrap;
}

.timeline-description {
  margin: 0 0 12px 0;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.5;
}

.timeline-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* Timeline Empty State */
.timeline-empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--md-sys-color-on-surface-variant);
}

.timeline-empty-state .empty-state-icon {
  margin-bottom: 16px;
}

.timeline-empty-state .material-icons {
  font-size: 48px;
  opacity: 0.6;
}

/* Timeline Pagination */
.timeline-pagination {
  text-align: center;
  margin-top: 32px;
}

/* Responsive Design */
@media (max-width: 640px) {
  .status-cards-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .status-card {
    padding: 20px;
  }

  .card-header {
    margin-bottom: 12px;
  }

  .card-metric {
    font-size: 2rem;
  }

  .timeline-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .timeline-actions {
    margin-top: 8px;
  }
}

@media (max-width: 480px) {
  .quick-actions {
    gap: 8px;
  }

  .timeline-item {
    gap: 12px;
  }

  .timeline-icon {
    width: 32px;
    height: 32px;
  }

  .timeline-item:not(:last-child)::after {
    left: 16px;
  }
}

/* Loading States */
.card-loading .card-metric {
  background: linear-gradient(
    90deg,
    var(--md-sys-color-surface-variant) 25%,
    var(--md-sys-color-surface-container) 50%,
    var(--md-sys-color-surface-variant) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  color: transparent;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* Real-time Updates */
.timeline-item.new-item {
  animation: slideInLeft 0.5s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
```

### 5.3 Vote Preview Styles

**New file**: `/mnt/cephfs/Shared/dropvault/toveco-dev/static/css/vote-preview.css`:

```css
/* Vote Preview Styles - Material Design 3 */

/* Preview Banner */
.preview-banner {
  position: sticky;
  top: 0;
  background-color: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  padding: 12px 0;
  z-index: 100;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: var(--md-sys-typescale-body-medium-size);
}

.banner-text {
  flex: 1;
}

/* Preview Content */
.vote-preview-content {
  min-height: 60vh;
  padding: 32px 0;
}

/* Sharing Panel */
.sharing-panel {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: var(--md-sys-color-surface-container-high);
  border-top: 1px solid var(--md-sys-color-outline-variant);
  box-shadow: var(--md-elevation-level3);
  z-index: 50;
  transform: translateY(0);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sharing-panel.collapsed {
  transform: translateY(calc(100% - 64px)); /* Show only header */
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: var(--md-sys-color-surface-container);
  cursor: pointer;
}

.panel-toggle {
  background: none;
  border: none;
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
  padding: 8px;
  border-radius: var(--md-sys-shape-corner-full);
  transition: all 0.2s ease;
}

.panel-toggle:hover {
  background-color: var(--md-sys-color-secondary-container);
}

.panel-content {
  max-height: 70vh;
  overflow-y: auto;
  padding: 24px;
}

/* Sharing Options */
.sharing-options {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sharing-option {
  padding: 20px;
  background-color: var(--md-sys-color-surface-container-low);
  border-radius: var(--md-sys-shape-corner-medium);
  border: 1px solid var(--md-sys-color-outline-variant);
}

.option-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.option-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--md-sys-shape-corner-medium);
  background-color: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.option-info {
  flex: 1;
}

.option-info h3 {
  margin: 0 0 4px 0;
  color: var(--md-sys-color-on-surface);
}

.option-info p {
  margin: 0;
  color: var(--md-sys-color-on-surface-variant);
}

.option-controls {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.option-controls .md-text-field {
  flex: 1;
  min-width: 300px;
  margin-bottom: 0;
}

.sharing-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* Vote Actions */
.vote-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

/* Copy Feedback */
.copy-success {
  position: relative;
}

.copy-success::after {
  content: 'Copied!';
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%);
  background-color: var(--md-sys-color-inverse-surface);
  color: var(--md-sys-color-inverse-on-surface);
  padding: 8px 12px;
  border-radius: var(--md-sys-shape-corner-small);
  font-size: var(--md-sys-typescale-body-small-size);
  white-space: nowrap;
  opacity: 1;
  animation: fadeInOut 2s ease;
  pointer-events: none;
}

@keyframes fadeInOut {
  0%,
  100% {
    opacity: 0;
  }
  20%,
  80% {
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .sharing-panel {
    position: relative;
    transform: none;
  }

  .sharing-panel.collapsed {
    transform: none;
  }

  .panel-content {
    max-height: none;
    padding: 16px;
  }

  .option-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .option-controls .md-text-field {
    min-width: auto;
    margin-bottom: 12px;
  }

  .vote-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .sharing-buttons {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .banner-content {
    font-size: var(--md-sys-typescale-body-small-size);
    gap: 8px;
  }

  .panel-header {
    padding: 12px 16px;
  }

  .sharing-option {
    padding: 16px;
  }

  .option-header {
    gap: 12px;
  }

  .option-icon {
    width: 32px;
    height: 32px;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .sharing-panel,
  .panel-toggle,
  .copy-success::after {
    transition: none;
    animation: none;
  }
}

/* High Contrast Mode */
@media (prefers-contrast: high) {
  .sharing-option {
    border-width: 2px;
  }

  .preview-banner {
    border-bottom-width: 2px;
  }
}
```

---

## 6. Validation & Quality Gates

### 6.1 Backend Validation Commands

```bash
# Python code quality (existing tools)
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/
uv run pytest --cov=src --cov-report=html
uv run bandit -r src/
```

### 6.2 Frontend Validation Commands

```bash
# Frontend linting (if configured)
npm run lint
npm run format:check

# Manual testing checklist
curl -X POST http://localhost:8000/api/votes/ -H "Content-Type: application/json" -H "Authorization: Bearer {token}" -d '{test_data}'
curl http://localhost:8000/api/votes/stats -H "Authorization: Bearer {token}"
curl http://localhost:8000/api/votes/activity -H "Authorization: Bearer {token}"
```

### 6.3 UI Validation with Playwright

**Critical UI Testing Steps:**

```javascript
// Playwright validation script for Sprint 2
const { test, expect } = require('@playwright/test')

test.describe('Sprint 2: Vote Creation & Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login setup
    await page.goto('/')
    // Perform login via existing auth flow
  })

  test('Vote creation modal opens and works', async ({ page }) => {
    await page.click('[data-action="create-vote"]')
    await expect(page.locator('#voteCreationModalScrim')).toBeVisible()

    // Fill form
    await page.fill('#voteTitle', 'Test Vote Title')
    await page.fill('#voteDescription', 'Test description')

    // Test dynamic option management
    await page.click('#addOptionBtn')
    const optionFields = page.locator('.vote-option-field')
    await expect(optionFields).toHaveCount(3) // 2 default + 1 added

    // Test form submission
    await page.fill('.option-input', 'Option 1')
    await page.click('#createVoteBtn')

    // Should redirect to preview page
    await expect(page).toHaveURL(/\/vote-preview\/.+/)
  })

  test('Dashboard status cards load and display correctly', async ({ page }) => {
    await page.goto('/dashboard')

    // Check all 6 status cards are present
    const statusCards = page.locator('.status-card')
    await expect(statusCards).toHaveCount(6)

    // Check metrics load (allow time for API call)
    await expect(page.locator('#totalVotesMetric')).not.toHaveText('0')

    // Test responsive behavior
    await page.setViewportSize({ width: 480, height: 800 })
    await expect(statusCards.first()).toBeVisible()
  })

  test('Activity timeline loads and functions', async ({ page }) => {
    await page.goto('/dashboard')

    // Check timeline section exists
    await expect(page.locator('.activity-timeline')).toBeVisible()

    // Test pagination if items exist
    const loadMoreBtn = page.locator('#loadMoreTimeline')
    if (await loadMoreBtn.isVisible()) {
      await loadMoreBtn.click()
      // Should load more items
    }
  })

  test('Vote preview and sharing works', async ({ page }) => {
    // Assume we have a vote to preview
    await page.goto('/vote-preview/test-vote-id?sharing=true')

    // Check preview banner
    await expect(page.locator('.preview-banner')).toBeVisible()

    // Check sharing panel
    await expect(page.locator('.sharing-panel')).toBeVisible()

    // Test copy link functionality
    await page.click('[data-action="copy-link"]')
    await expect(page.locator('.copy-success')).toBeVisible()

    // Test panel toggle
    await page.click('#panelToggle')
    await expect(page.locator('.sharing-panel')).toHaveClass(/collapsed/)
  })
})
```

### 6.4 Manual Testing Checklist

**User Journey Testing:**

- [ ] Can login and access dashboard
- [ ] Dashboard loads within 2 seconds
- [ ] All 6 status cards display correct data
- [ ] Activity timeline shows recent actions
- [ ] Can open vote creation modal
- [ ] Can add/remove options dynamically (up to 20)
- [ ] Access settings toggle correctly
- [ ] Form validation prevents invalid submissions
- [ ] Vote creation redirects to preview page
- [ ] Preview shows vote as voters would see it
- [ ] Sharing controls work (copy link, access code)
- [ ] Can return to dashboard from preview

**Responsive Testing:**

- [ ] Desktop (1280px+): 6 cards in grid, sidebar navigation
- [ ] Tablet (600-1279px): 2-column cards, drawer navigation
- [ ] Mobile (320-599px): Single column, drawer navigation

**Accessibility Testing:**

- [ ] Keyboard navigation works throughout
- [ ] Screen reader announces all interactive elements
- [ ] Focus indicators visible and logical
- [ ] Color contrast meets WCAG standards

---

## 7. Risk Assessment & Mitigation

### 7.1 Technical Risks

**HIGH RISK: Complex Dynamic Form Management**

- _Risk_: Adding/removing vote options may cause UI state issues
- _Mitigation_: Implement robust state management with proper cleanup, extensive testing
- _Fallback_: Provide fixed number of option fields if dynamic approach fails

**MEDIUM RISK: Material Design 3 Consistency**

- _Risk_: New components may not match existing design system
- _Mitigation_: Use existing CSS variables and component patterns, validate with Playwright
- _Fallback_: Simplify designs to match existing components exactly

**MEDIUM RISK: Dashboard Performance with Large Datasets**

- _Risk_: Timeline and statistics may load slowly for users with many votes
- _Mitigation_: Implement pagination, caching, and loading states
- _Fallback_: Limit timeline to last 30 days, paginate beyond that

### 7.2 User Experience Risks

**HIGH RISK: Preview Interface Complexity**

- _Risk_: Sharing panel may overwhelm users or not work on mobile
- _Mitigation_: Implement collapsible panel, extensive mobile testing
- _Fallback_: Simplify to basic copy-link functionality only

**MEDIUM RISK: Vote Creation Form Length**

- _Risk_: Long form may cause abandonment, especially on mobile
- _Mitigation_: Progressive disclosure, clear progress indication, auto-save drafts
- _Fallback_: Implement multi-step wizard if single form proves too long

### 7.3 Integration Risks

**LOW RISK: API Endpoint Compatibility**

- _Risk_: New API endpoints may conflict with existing functionality
- _Mitigation_: Thorough testing of existing endpoints after changes
- _Confidence_: High - building on validated Sprint 1 foundation

---

## 8. Implementation Timeline

### 8.1 Development Phase (Days 1-5)

**Day 1: Vote Creation Interface**

- [ ] Create vote creation modal HTML template
- [ ] Implement VoteCreationManager JavaScript class
- [ ] Add dynamic option management functionality
- [ ] Test form validation and submission

**Day 2: Enhanced API Endpoints**

- [ ] Extend vote creation endpoint with access controls
- [ ] Implement dashboard statistics endpoint
- [ ] Add activity logging and retrieval endpoints
- [ ] Test API endpoints with curl/Postman

**Day 3: Dashboard Enhancement**

- [ ] Implement status cards grid layout
- [ ] Add activity timeline component
- [ ] Connect dashboard to statistics API
- [ ] Test responsive behavior across devices

**Day 4: Vote Preview & Sharing**

- [ ] Create vote preview template
- [ ] Implement sharing control panel
- [ ] Add copy-to-clipboard functionality
- [ ] Test preview accuracy vs public vote page

**Day 5: Integration & Polish**

- [ ] Connect all components end-to-end
- [ ] Implement error handling and loading states
- [ ] Add animations and micro-interactions
- [ ] Comprehensive testing with Playwright

### 8.2 Validation Phase (Days 6-7)

**Day 6: Automated Testing**

- [ ] Run full Playwright test suite
- [ ] Execute all validation commands
- [ ] Performance testing with realistic data
- [ ] Accessibility audit with screen readers

**Day 7: User Acceptance Testing**

- [ ] Manual testing of complete user journey
- [ ] Mobile device testing (iOS/Android)
- [ ] Cross-browser compatibility verification
- [ ] Security testing (access controls, JWT validation)

---

## 9. Success Metrics

### 9.1 Technical Success Criteria

- [ ] All validation commands pass without errors
- [ ] Dashboard loads in under 2 seconds with sample data
- [ ] Vote creation form supports 20 options without performance issues
- [ ] Responsive design works on all target screen sizes
- [ ] No console errors in browser developer tools

### 9.2 User Experience Success Criteria

- [ ] Complete user journey: Login → Dashboard → Create → Preview → Share
- [ ] Users can create vote and access sharing link in under 2 minutes
- [ ] Dashboard provides clear overview of vote statistics
- [ ] Mobile experience feels native and responsive
- [ ] Preview accurately represents voter experience

### 9.3 Business Success Criteria

- [ ] Users can successfully complete primary workflow without support
- [ ] Platform provides value beyond landing page (core voting functionality)
- [ ] Foundation established for Sprint 3 features (analytics, management)
- [ ] No regression in existing authentication functionality

---

## 10. Handoff & Documentation

## Task Breakdown Reference

**Detailed Implementation Tasks**: See `/docs/tasks/sprint-2-user-journey-restoration.md` for comprehensive task breakdown with:

- 5 detailed tasks (T-001 through T-005) with effort estimates
- Clear dependencies and critical path analysis
- Given-When-Then acceptance criteria for each task
- Implementation timeline across 5-day sprint
- Risk management and mitigation strategies

### 10.1 Developer Handoff Package

**Implementation Files Created:**

- `/mnt/cephfs/Shared/dropvault/toveco-dev/templates/vote_preview.html`
- `/mnt/cephfs/Shared/dropvault/toveco-dev/static/css/vote-creation.css`
- `/mnt/cephfs/Shared/dropvault/toveco-dev/static/css/vote-preview.css`
- `/mnt/cephfs/Shared/dropvault/toveco-dev/static/js/vote-creation-manager.js`
- `/mnt/cephfs/Shared/dropvault/toveco-dev/static/js/vote-preview.js`

**Files Modified:**

- `/mnt/cephfs/Shared/dropvault/toveco-dev/src/cardinal_vote/vote_routes.py` (API extensions)
- `/mnt/cephfs/Shared/dropvault/toveco-dev/src/cardinal_vote/models.py` (new models)
- `/mnt/cephfs/Shared/dropvault/toveco-dev/templates/user_dashboard.html` (enhanced dashboard)
- `/mnt/cephfs/Shared/dropvault/toveco-dev/static/css/dashboard.css` (status cards + timeline)
- `/mnt/cephfs/Shared/dropvault/toveco-dev/static/js/dashboard.js` (enhanced functionality)

### 10.2 Testing Documentation

**Automated Testing:**

- Playwright test suite for UI interactions
- Python unit tests for API endpoints
- Integration tests for complete user journey

**Manual Testing Guide:**

- Cross-browser compatibility checklist
- Mobile device testing procedures
- Accessibility validation steps

### 10.3 Deployment Notes

**Database Migrations Required:**

```sql
-- Add access control fields to votes table
ALTER TABLE votes ADD COLUMN access_code VARCHAR(50) NULL;
ALTER TABLE votes ADD COLUMN require_auth BOOLEAN DEFAULT FALSE;

-- Create activity table for timeline
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    vote_slug VARCHAR(255) NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX idx_activities_user_created ON activities(user_id, created_at DESC);
CREATE INDEX idx_votes_creator_status ON votes(creator_email, status);
```

**Configuration Updates:**

```bash
# No new environment variables required
# All configuration uses existing settings
```

---

## 11. Future Enhancement Opportunities

### 11.1 Sprint 3 Preparation

**Vote Management Features:**

- Bulk operations (delete multiple votes)
- Vote duplication/templates
- Advanced sharing options (email invitations)
- Vote scheduling (start/end times)

**Analytics & Reporting:**

- Real-time vote monitoring
- Export capabilities (CSV, PDF, JSON)
- Response analytics and insights
- Participant demographics

### 11.2 Technical Improvements

**Performance Optimizations:**

- Real-time updates via WebSocket
- Client-side caching for dashboard data
- Progressive loading for large vote lists
- Image optimization for vote options

**User Experience Enhancements:**

- Drag-and-drop option reordering
- Vote templates and themes
- Collaboration features (multi-user vote management)
- Advanced accessibility features

---

## PRP Quality Score: 9/10

**Confidence Level for One-Pass Implementation: Very High**

**Strengths:**

- ✅ Complete business requirements with user clarifications
- ✅ Comprehensive codebase analysis with specific file references
- ✅ Detailed implementation examples following existing patterns
- ✅ Material Design 3 research integrated from external sources
- ✅ Executable validation gates with project-specific commands
- ✅ Risk mitigation strategies with fallback plans
- ✅ Clear handoff documentation and deployment instructions

**Minor Improvement Areas:**

- Activity logging implementation could be more detailed
- WebSocket integration deferred to future sprints
- Some edge cases in dynamic form management may require iteration

**Recommendation:** Proceed with implementation. The PRP provides sufficient context and detailed guidance for successful completion within the 1-week sprint timeline.

---

_PRP Document Generated: January 13, 2025_
_Next Steps: Generate detailed task breakdown using team-lead-task-breakdown agent_
