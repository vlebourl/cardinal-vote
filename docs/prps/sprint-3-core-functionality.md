# PRP: Sprint 3 - Core Functionality

**Feature**: Vote Management Interface & Results Analytics
**Sprint**: 3
**Priority**: High
**Status**: Ready for Implementation
**Confidence Score**: 9/10

## Executive Summary

Sprint 3 focuses on exposing existing backend functionality through a comprehensive vote management interface and results visualization system. The backend APIs are already complete (vote CRUD, results calculation, export), making this primarily a frontend integration sprint. This PRP builds upon the 98% complete Sprint 2 foundation to deliver core management capabilities to vote creators.

## Problem Statement

### Current State

- Users can create votes through Sprint 2's interface (98% complete)
- 14 comprehensive backend APIs exist for vote management
- No UI exists for users to manage, edit, or delete their votes
- Results data is available via API but not visualized
- Export functionality exists but isn't accessible to users

### Desired State

- Complete vote lifecycle management through intuitive UI
- Real-time results visualization with interactive charts
- One-click export of vote data in multiple formats
- Seamless integration with existing dashboard

### Success Metrics

- 100% of vote management APIs exposed through UI
- <2 second load time for results visualization
- Zero data loss during edit/delete operations
- 90%+ user task completion rate for management operations

## User Requirements

### User Stories

#### Story 1: Vote Management

**As a** vote creator
**I want to** view and manage all my votes in one place
**So that I** can track active votes and maintain control over my content

**Acceptance Criteria:**

- List shows all user's votes with status indicators
- Filtering by status (draft/active/closed)
- Sorting by date, name, or response count
- Quick actions for status changes

#### Story 2: Edit Capabilities

**As a** vote creator
**I want to** edit my vote details
**So that I** can correct mistakes or update information

**Acceptance Criteria:**

- Edit vote title and description for any status
- Edit options only for draft votes
- Clear warnings when editing active votes
- Validation prevents breaking changes

#### Story 3: Results Visualization

**As a** vote creator
**I want to** see real-time voting results
**So that I** can monitor engagement and make informed decisions

**Acceptance Criteria:**

- Interactive charts showing vote distribution
- Real-time updates without page refresh
- Statistical summary (average, total votes, participation)
- Mobile-responsive visualization

#### Story 4: Data Export

**As a** vote creator
**I want to** export vote data
**So that I** can analyze results offline or share with stakeholders

**Acceptance Criteria:**

- Export in CSV and JSON formats
- Include all responses and metadata
- One-click download functionality
- Filename includes vote title and date

### Business Rules

1. **Edit Restrictions**:
   - Draft votes: Full editing allowed
   - Active votes: Only metadata (title/description) editable
   - Closed votes: No editing allowed

2. **Delete Policy**:
   - Soft delete implementation (data preserved)
   - Confirmation modal required
   - Cannot delete votes with >100 responses without admin override

3. **Status Transitions**:
   - Draft → Active → Closed (forward only)
   - Closed votes can be archived but not reactivated
   - Status changes logged for audit trail

4. **Export Limitations**:
   - Maximum 10,000 responses per export
   - Rate limited to 5 exports per minute
   - Includes anonymized voter data only

## Technical Specifications

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
├─────────────────────────────────────────────────┤
│  Dashboard UI  │  Vote Manager  │  Results View  │
├────────────────┴────────────────┴────────────────┤
│              JavaScript Managers                  │
│   VoteManagementManager │ ResultsVisualization   │
├─────────────────────────────────────────────────┤
│                  API Layer                       │
│     Existing Vote Routes (CRUD, Results)         │
├─────────────────────────────────────────────────┤
│                  Backend                         │
│    FastAPI │ SQLAlchemy │ PostgreSQL            │
└─────────────────────────────────────────────────┘
```

### Component Specifications

#### 1. Vote Management Interface

**Location**: Extend `/templates/user_dashboard.html`

**Components**:

```html
<!-- Vote Management Section -->
<div class="vote-management-section">
  <!-- Filter Bar -->
  <div class="filter-bar">
    <button data-filter="all">All</button>
    <button data-filter="draft">Draft</button>
    <button data-filter="active">Active</button>
    <button data-filter="closed">Closed</button>
  </div>

  <!-- Vote List -->
  <div class="vote-list" id="voteList">
    <!-- Populated by JavaScript -->
  </div>
</div>
```

**JavaScript Manager**: `VoteManagementManager` class

- Extends existing pattern from `DashboardManager`
- Handles CRUD operations via existing APIs
- Implements infinite scroll for large lists

#### 2. Edit Vote Modal

**Pattern Reference**: `/templates/user_dashboard.html` lines 197-280 (vote creation modal)

```javascript
class VoteEditManager {
  constructor() {
    this.modal = document.getElementById('editVoteModal')
    this.form = document.getElementById('editVoteForm')
  }

  async loadVote(voteId) {
    const response = await fetch(`/api/votes/${voteId}`, {
      headers: { Authorization: `Bearer ${this.getToken()}` }
    })
    // Populate form with existing data
  }

  async saveChanges() {
    // Validate based on vote status
    // Call PUT /api/votes/{vote_id}
  }
}
```

#### 3. Results Visualization

**Library**: Chart.js (maintain consistency with existing patterns)

**Implementation**:

```javascript
class ResultsVisualization {
  async renderChart(voteId) {
    const data = await this.fetchResults(voteId)

    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.options.map(o => o.text),
        datasets: [
          {
            label: 'Votes',
            data: data.options.map(o => o.averageRating)
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    })
  }
}
```

#### 4. Export Functionality

**Integration Point**: `/api/votes/{vote_id}/export` (existing endpoint)

```javascript
async exportData(voteId, format) {
  const response = await fetch(
    `/api/votes/${voteId}/export?format=${format}`,
    { headers: { 'Authorization': `Bearer ${token}` }}
  );

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `vote-${voteId}-${Date.now()}.${format}`;
  a.click();
}
```

### API Endpoints (Existing - No Changes Needed)

| Method | Endpoint                  | Purpose           | Status    |
| ------ | ------------------------- | ----------------- | --------- |
| GET    | `/api/votes/`             | List user's votes | ✅ Exists |
| PUT    | `/api/votes/{id}`         | Update vote       | ✅ Exists |
| DELETE | `/api/votes/{id}`         | Delete vote       | ✅ Exists |
| PUT    | `/api/votes/{id}/status`  | Change status     | ✅ Exists |
| GET    | `/api/votes/{id}/results` | Get results       | ✅ Exists |
| GET    | `/api/votes/{id}/export`  | Export data       | ✅ Exists |

### Database Schema (Existing)

```python
# Already defined in models.py
class Vote(Base):
    id: int
    title: str
    description: str
    status: VoteStatus  # draft, active, closed
    created_by_id: int
    options: List[VoteOption]

class VoteOption(Base):
    id: int
    vote_id: int
    text: str
    image_url: Optional[str]

class VoterResponse(Base):
    id: int
    vote_id: int
    ratings: JSONB  # {"option_id": rating}
```

### Security Considerations

1. **Authorization**: All operations check JWT token and user ownership
2. **Input Sanitization**: Use existing `InputSanitizer` class
3. **XSS Prevention**: Template escaping and CSP headers
4. **Rate Limiting**: Existing decorators on sensitive endpoints
5. **CSRF Protection**: Token validation on state-changing operations

## Implementation Plan

### Phase 1: Vote Management UI (Day 1-2)

```javascript
// Pseudocode for vote list implementation
class VoteListManager {
  init() {
    this.loadVotes()
    this.attachEventListeners()
  }

  async loadVotes(status = 'all') {
    const votes = await api.get('/api/votes/', { status })
    this.renderVoteCards(votes)
  }

  renderVoteCards(votes) {
    votes.forEach(vote => {
      const card = this.createVoteCard(vote)
      container.appendChild(card)
    })
  }

  handleAction(action, voteId) {
    switch (action) {
      case 'edit':
        this.openEditModal(voteId)
      case 'delete':
        this.confirmDelete(voteId)
      case 'view-results':
        this.navigateToResults(voteId)
    }
  }
}
```

**Playwright MCP Validation for Phase 1**:

```javascript
// Test vote list filtering and display
test('Phase 1: Vote Management UI Validation', async ({ page }) => {
  await page.goto('/dashboard')

  // Test filter functionality
  await page.click('[data-filter="active"]')
  await expect(page.locator('.vote-card[data-status="draft"]')).toHaveCount(0)
  await expect(page.locator('.vote-card[data-status="active"]')).toBeVisible()

  // Test pagination
  await page.click('[data-action="load-more"]')
  await expect(page.locator('.vote-card')).toHaveCount({ min: 20 })

  // Test quick actions
  await page.hover('.vote-card:first-child')
  await expect(page.locator('[data-action="edit"]')).toBeVisible()
  await expect(page.locator('[data-action="delete"]')).toBeVisible()
})
```

### Phase 2: Edit/Delete Functionality (Day 3-4)

```javascript
// Edit modal pattern from existing vote creation
async function setupEditModal() {
  // Reuse Material Design 3 modal structure
  // Adapt form validation from VoteCreationManager
  // Add status-based field disabling
}

async function handleDelete(voteId) {
  // Show confirmation modal
  // Call DELETE endpoint
  // Update UI without refresh
  // Show success snackbar
}
```

**Playwright MCP Validation for Phase 2**:

```javascript
// Test edit/delete functionality with business rules
test('Phase 2: Edit/Delete Operations', async ({ page }) => {
  await page.goto('/dashboard')

  // Test edit draft vote (full editing)
  await page.click('[data-vote-id="draft-vote"] [data-action="edit"]')
  await expect(page.locator('#editVoteTitle')).toBeEnabled()
  await expect(page.locator('#editVoteOptions')).toBeEnabled()

  // Test edit active vote (limited editing)
  await page.click('[data-vote-id="active-vote"] [data-action="edit"]')
  await expect(page.locator('#editVoteTitle')).toBeEnabled()
  await expect(page.locator('#editVoteOptions')).toBeDisabled()

  // Test delete confirmation
  await page.click('[data-vote-id="test-vote"] [data-action="delete"]')
  await expect(page.locator('.delete-confirmation-modal')).toBeVisible()
  await page.click('[data-action="confirm-delete"]')

  // Verify vote removed from list
  await expect(page.locator('[data-vote-id="test-vote"]')).not.toBeVisible()
})
```

### Phase 3: Results Visualization (Day 5-6)

```javascript
// Results dashboard implementation
class ResultsDashboard {
  async init(voteId) {
    const results = await this.fetchResults(voteId)
    this.renderCharts(results)
    this.startPolling() // Real-time updates
  }

  renderCharts(data) {
    this.renderBarChart(data)
    this.renderPieChart(data)
    this.renderStatistics(data)
  }

  startPolling() {
    setInterval(() => this.updateResults(), 5000)
  }
}
```

**Playwright MCP Validation for Phase 3**:

```javascript
// Test results visualization and real-time updates
test('Phase 3: Results Visualization', async ({ page }) => {
  await page.goto('/dashboard')

  // Navigate to results view
  await page.click('[data-vote-id="active-vote"] [data-action="view-results"]')

  // Verify chart components load
  await expect(page.locator('.results-chart canvas')).toBeVisible()
  await expect(page.locator('.statistics-panel')).toBeVisible()

  // Test chart interaction
  await page.hover('.chart-bar:first-child')
  await expect(page.locator('.chart-tooltip')).toBeVisible()

  // Test real-time updates (mock new vote)
  await page.evaluate(() => {
    // Simulate new vote response via polling
    window.mockNewVoteResponse()
  })

  await page.waitForTimeout(6000) // Wait for next poll
  await expect(page.locator('.total-votes')).toHaveText(/Updated: \d+ votes/)

  // Test mobile chart responsiveness
  await page.setViewportSize({ width: 375, height: 667 })
  await expect(page.locator('.results-chart')).toBeVisible()
})
```

### Phase 4: Export Integration (Day 7)

```javascript
// Simple export handler
function addExportButtons() {
  const exportCSV = document.getElementById('exportCSV')
  const exportJSON = document.getElementById('exportJSON')

  exportCSV.onclick = () => exportData(voteId, 'csv')
  exportJSON.onclick = () => exportData(voteId, 'json')
}
```

**Playwright MCP Validation for Phase 4**:

```javascript
// Test export functionality and file downloads
test('Phase 4: Export Integration', async ({ page }) => {
  await page.goto('/dashboard')

  // Setup download handling
  const [download1] = await Promise.all([
    page.waitForEvent('download'),
    page.click('[data-vote-id="active-vote"] [data-action="export-csv"]')
  ])

  // Verify CSV download
  expect(download1.suggestedFilename()).toMatch(/vote-.*\.csv$/)

  const [download2] = await Promise.all([
    page.waitForEvent('download'),
    page.click('[data-vote-id="active-vote"] [data-action="export-json"]')
  ])

  // Verify JSON download
  expect(download2.suggestedFilename()).toMatch(/vote-.*\.json$/)

  // Test export button states during download
  await page.click('[data-action="export-csv"]')
  await expect(page.locator('[data-action="export-csv"]')).toBeDisabled()
  await page.waitForTimeout(2000) // Wait for export completion
  await expect(page.locator('[data-action="export-csv"]')).toBeEnabled()
})
```

## Playwright MCP Development Workflow

### Continuous UI Validation Strategy

**Integration Points**:

- Run Playwright MCP tests after each component implementation
- Use browser automation to validate Material Design 3 consistency
- Test real user interactions across different viewport sizes
- Verify API integration through UI actions

**Test Development Approach**:

1. **Component-First Testing**: Write Playwright tests alongside each UI component
2. **User Journey Validation**: Test complete workflows from login to export
3. **Cross-Browser Verification**: Validate on Chrome, Firefox, and Safari
4. **Mobile-First Testing**: Ensure responsive behavior on mobile devices

### Playwright MCP Test Scenarios

#### Core Functionality Tests

```javascript
// Comprehensive Sprint 3 test suite
describe('Sprint 3: Vote Management & Analytics', () => {
  test('Complete vote management workflow', async ({ page }) => {
    // 1. Navigation and authentication
    await page.goto('/dashboard')
    await expect(page.locator('.dashboard-header')).toBeVisible()

    // 2. Vote list operations
    await page.click('[data-filter="all"]')
    await expect(page.locator('.vote-card')).toHaveCount({ min: 1 })

    // 3. Edit workflow
    const firstVote = page.locator('.vote-card').first()
    await firstVote.hover()
    await firstVote.locator('[data-action="edit"]').click()

    await page.fill('#editVoteTitle', 'Updated by Playwright')
    await page.click('[data-action="save-changes"]')

    await expect(page.locator('.success-notification')).toBeVisible()

    // 4. Results viewing
    await firstVote.locator('[data-action="view-results"]').click()
    await expect(page.locator('.results-dashboard')).toBeVisible()
    await expect(page.locator('canvas')).toBeVisible() // Chart.js canvas

    // 5. Export functionality
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-action="export-csv"]')
    ])

    expect(download.suggestedFilename()).toContain('.csv')
  })

  test('Mobile responsiveness validation', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/dashboard')

    // Mobile navigation
    await expect(page.locator('.mobile-menu-toggle')).toBeVisible()
    await page.click('.mobile-menu-toggle')
    await expect(page.locator('.navigation-drawer')).toBeVisible()

    // Mobile vote cards
    await expect(page.locator('.vote-card')).toHaveCSS('flex-direction', 'column')

    // Mobile chart responsiveness
    await page.click('[data-vote-id] [data-action="view-results"]')
    const chart = page.locator('.results-chart')
    await expect(chart).toBeVisible()

    const chartBox = await chart.boundingBox()
    expect(chartBox.width).toBeLessThan(400) // Mobile width constraint
  })
})
```

#### Performance and Error Handling Tests

```javascript
test('Performance and error handling', async ({ page }) => {
  // Test loading states
  await page.goto('/dashboard')
  await expect(page.locator('.loading-skeleton')).toBeVisible()
  await page.waitForSelector('.vote-card', { timeout: 3000 })

  // Test error states
  await page.route('/api/votes/**', route => route.abort())
  await page.reload()
  await expect(page.locator('.error-state')).toBeVisible()

  // Test retry mechanism
  await page.unroute('/api/votes/**')
  await page.click('[data-action="retry"]')
  await expect(page.locator('.vote-card')).toBeVisible()
})
```

### Development Integration Commands

**Playwright MCP Integration in Development Workflow**:

```bash
# Run during development
npm run dev                      # Start development server
npx playwright test --ui         # Interactive test runner
npx playwright test --headed     # Run with browser visible

# Component testing as you build
npx playwright test --grep "Phase 1"  # Test specific phase
npx playwright test --project=mobile  # Test mobile only

# Continuous integration
npm run test:playwright          # Full test suite
npm run test:visual              # Visual regression tests
```

## Validation Gates

### Development Validation

```bash
# After each component completion
npm run lint                     # JavaScript linting
npm run format:check             # Code formatting
npm test                         # Component tests

# Playwright MCP validation after UI components
npx playwright test --grep "Phase 1"  # Test Phase 1 components
npx playwright test --grep "Phase 2"  # Test Phase 2 components
npx playwright test --grep "Phase 3"  # Test Phase 3 components
npx playwright test --grep "Phase 4"  # Test Phase 4 components
```

### Playwright MCP Validation Gates

```bash
# Component-level validation
npx playwright test --headed tests/sprint3-vote-management.spec.js
npx playwright test --headed tests/sprint3-results-visualization.spec.js

# Cross-browser validation
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Mobile validation
npx playwright test --project=mobile-chrome
npx playwright test --project=mobile-safari

# Visual regression testing
npx playwright test --update-snapshots  # Update baselines
npx playwright test --reporter=html     # Generate test report
```

### Python Backend Validation

```bash
# Verify API integration
uv run pytest tests/test_vote_routes.py
uv run pytest --cov=src/cardinal_vote
uv run ruff check src/
uv run mypy src/
```

### Full Stack Validation

```bash
# Integration testing
npm run validate                 # Full frontend validation
uv run pytest tests/integration/
docker-compose up --build        # Full stack test
```

### Playwright MCP Testing Strategy

**Integration Approach**: Use Playwright MCP throughout development for continuous UI validation

```javascript
// Example Playwright MCP test for vote management
test('should manage vote lifecycle completely', async ({ page }) => {
  // Navigate to dashboard
  await page.goto('/dashboard')

  // Create test vote for management
  await page.click('[data-action="create-vote"]')
  await page.fill('#voteTitle', 'Test Management Vote')
  await page.click('[data-action="save-vote"]')

  // Test edit functionality
  await page.click('[data-vote-id="123"] [data-action="edit"]')
  await page.fill('#editVoteTitle', 'Updated Vote Title')
  await page.click('[data-action="save-changes"]')

  // Verify update
  await expect(page.locator('[data-vote-id="123"] .vote-title')).toHaveText('Updated Vote Title')

  // Test results visualization
  await page.click('[data-vote-id="123"] [data-action="view-results"]')
  await expect(page.locator('.results-chart')).toBeVisible()

  // Test export functionality
  await page.click('[data-action="export-csv"]')
  // Verify download initiated
})
```

### Manual Testing Checklist

- [ ] Create 10+ votes to test pagination (validate with Playwright MCP)
- [ ] Edit draft, active, and closed votes (automated via Playwright scenarios)
- [ ] Delete vote with and without responses (Playwright confirmation modal tests)
- [ ] Export data in both formats (Playwright download validation)
- [ ] Test on mobile devices (Playwright mobile viewport testing)
- [ ] Verify real-time result updates (Playwright polling verification)

## Dependencies

### External Libraries

- **Chart.js**: Already available in project
- **Material Design 3**: Existing implementation

### Internal Dependencies

- `InputSanitizer` class for XSS prevention
- `DashboardManager` patterns for consistency
- JWT authentication utilities
- Existing vote API endpoints

## Error Handling Strategy

### Frontend Errors

```javascript
try {
  const result = await api.updateVote(voteId, data)
  showSuccess('Vote updated successfully')
} catch (error) {
  if (error.status === 403) {
    showError('You do not have permission to edit this vote')
  } else if (error.status === 422) {
    showValidationErrors(error.details)
  } else {
    showError('An unexpected error occurred. Please try again.')
  }
}
```

### Backend Validation

- Pydantic models ensure data integrity
- HTTP status codes for clear error communication
- Detailed error messages in development mode

## Performance Optimizations

1. **Lazy Loading**: Load vote details on demand
2. **Pagination**: 20 votes per page with infinite scroll
3. **Caching**: Cache results for 30 seconds
4. **Debouncing**: Search/filter with 300ms delay
5. **Virtual Scrolling**: For lists >100 items

## Accessibility Requirements

- ARIA labels on all interactive elements
- Keyboard navigation support
- Screen reader announcements for actions
- High contrast mode support
- Focus management in modals

## Risk Mitigation

| Risk                        | Impact | Mitigation                        |
| --------------------------- | ------ | --------------------------------- |
| Data loss during edit       | High   | Soft delete, audit logs           |
| Performance with many votes | Medium | Pagination, virtual scroll        |
| Concurrent edits            | Medium | Optimistic locking                |
| Export timeout              | Low    | Async job queue for large exports |

## Success Criteria

- [ ] All 6 user stories implemented and tested
- [ ] 100% of existing APIs integrated
- [ ] Page load time <2 seconds
- [ ] Mobile responsive design
- [ ] Accessibility score >90
- [ ] Zero critical security vulnerabilities
- [ ] Code coverage >80%

## Task Breakdown Reference

**Implementation Tasks**: See detailed breakdown in `/docs/tasks/sprint-3-core-functionality.md`

The task breakdown includes 10 detailed, actionable tasks organized in 4 phases:

- **Phase 1**: Vote Management UI Foundation (T-301, T-302, T-303)
- **Phase 2**: Edit/Delete Operations (T-304, T-305)
- **Phase 3**: Results Visualization (T-306, T-307)
- **Phase 4**: Testing & Quality (T-308, T-309, T-310)

Each task includes Playwright MCP validation steps and acceptance criteria.

## Playwright MCP Benefits Summary

**Why Playwright MCP is Critical for Sprint 3**:

1. **Real User Validation**: Tests actual user interactions, not just code functionality
2. **Cross-Browser Consistency**: Ensures Material Design 3 works across Chrome, Firefox, Safari
3. **Mobile-First Validation**: Guarantees responsive behavior on mobile devices
4. **Performance Verification**: Validates <2 second load time requirements
5. **Integration Testing**: Tests complete workflows from UI to backend APIs
6. **Regression Prevention**: Catches UI breaks during development iterations
7. **Accessibility Compliance**: Validates keyboard navigation and screen reader support

**Development Confidence Boost**:

- Eliminates "works on my machine" issues
- Provides immediate feedback on UI changes
- Validates complex interactions like drag-and-drop, real-time updates
- Tests error handling and edge cases automatically
- Ensures consistent user experience across different environments

## References

### Internal Documentation

- `/src/cardinal_vote/vote_routes.py` - Vote API implementation
- `/templates/user_dashboard.html` - Dashboard template
- `/static/js/dashboard.js` - Dashboard JavaScript patterns
- `/CLAUDE.md` - Development guidelines
- `/docs/prps/sprint-2-user-journey-restoration.md` - Previous sprint

### Code Patterns to Follow

- Modal implementation: lines 197-280 in `user_dashboard.html`
- API integration: `DashboardManager` class in `dashboard.js`
- Material Design 3 components throughout templates
- Input sanitization via `InputSanitizer` class

---

**Confidence Score**: 9.5/10
_Rationale_: Exceptional confidence due to complete backend implementation, established patterns, clear integration path, and comprehensive Playwright MCP testing strategy. The Playwright MCP integration provides continuous UI validation throughout development, eliminating most UI-related uncertainties. The only minor uncertainty is exact user interaction patterns, but existing code provides strong guidance.

**Estimated Timeline**: 7-8 days
**Team Size**: 1-2 developers
**Dependencies**: Sprint 2 completion (98% done)
