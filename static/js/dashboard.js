// Dashboard JavaScript
// Handles dashboard functionality, navigation, and user interactions

// Dashboard Manager Class
class DashboardManager {
  constructor() {
    this.API_BASE = '/api'
    this.navigationDrawer = null
    this.navigationScrim = null
    this.userMenu = null
    this.user = null
  }

  static init() {
    const dashboard = new DashboardManager()
    dashboard.initializeElements()

    // Force drawer to be hidden immediately (before any CSS transitions)
    dashboard.forceCloseDrawer()

    dashboard.initializeEventListeners()
    dashboard.loadUserData()
    dashboard.loadDashboardData()
  }

  initializeElements() {
    this.navigationDrawer = document.getElementById('navigationDrawer')
    this.navigationScrim = document.getElementById('navigationScrim')
    this.userMenu = document.getElementById('userMenu')
  }

  initializeEventListeners() {
    // Navigation drawer toggle
    const navButton = document.querySelector('.md-top-app-bar-navigation-icon')
    if (navButton && this.navigationDrawer && this.navigationScrim) {
      navButton.addEventListener('click', () => {
        this.toggleNavigationDrawer()
      })

      this.navigationScrim.addEventListener('click', () => {
        this.closeNavigationDrawer()
      })
    }

    // Global click handler for data-action buttons
    document.addEventListener('click', e => {
      const action = e.target.closest('[data-action]')?.dataset.action
      if (action) {
        e.preventDefault()
        this.handleAction(action, e.target)
      }
    })

    // Close user menu when clicking outside
    document.addEventListener('click', e => {
      if (this.userMenu && !this.userMenu.contains(e.target) && !e.target.closest('[data-action="user-menu"]')) {
        this.closeUserMenu()
      }
    })

    // Keyboard shortcuts
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        this.closeNavigationDrawer()
        this.closeUserMenu()
      }
    })

    // Snackbar dismiss
    const snackbarAction = document.getElementById('snackbar-action')
    if (snackbarAction) {
      snackbarAction.addEventListener('click', () => {
        this.dismissSnackbar()
      })
    }
  }

  handleAction(action, element) {
    const voteId = element.dataset.voteId
    const modalType = element.dataset.modal

    switch (action) {
      case 'create-vote':
        this.createVote()
        break
      case 'user-menu':
        this.toggleUserMenu()
        break
      case 'logout':
        this.logout()
        break
      case 'profile':
        this.showProfile()
        break
      case 'switch-profile-tab':
        if (window.profileManager) {
          const tabName = element.dataset.tab
          window.profileManager.switchTab(tabName)
        }
        break
      case 'close-modal':
        if (modalType === 'profile' && window.profileManager) {
          window.profileManager.closeModal()
        } else if (window.voteManager && modalType) {
          window.voteManager.closeModal(modalType)
        }
        break
      case 'settings':
        this.showSettings()
        break
      case 'view-all-votes':
        this.viewAllVotes()
        break

      // Vote Management Actions
      case 'filter-votes':
        if (window.voteManager) {
          const filter = element.dataset.filter
          window.voteManager.filterVotes(filter)
        }
        break
      case 'sort-votes':
        if (window.voteManager) {
          window.voteManager.resetAndReload()
        }
        break
      case 'load-more-votes':
        if (window.voteManager) {
          window.voteManager.loadMoreVotes()
        }
        break
      case 'edit-vote':
        if (window.voteManager && voteId) {
          window.voteManager.openEditModal(voteId)
        }
        break
      case 'delete-vote':
        if (window.voteManager && voteId) {
          window.voteManager.openDeleteModal(voteId)
        }
        break
      case 'view-results':
        if (window.voteManager && voteId) {
          window.voteManager.openResultsModal(voteId)
        }
        break
      case 'confirm-delete-vote':
        if (window.voteManager) {
          window.voteManager.confirmDeleteVote()
        }
        break
      case 'export-csv':
        if (window.voteManager) {
          const resultsVoteId = document.getElementById('resultsVoteId')?.value
          if (resultsVoteId) {
            window.voteManager.exportVoteData(resultsVoteId, 'csv')
          }
        }
        break
      case 'export-json':
        if (window.voteManager) {
          const resultsVoteId = document.getElementById('resultsVoteId')?.value
          if (resultsVoteId) {
            window.voteManager.exportVoteData(resultsVoteId, 'json')
          }
        }
        break
      case 'refresh-results':
        if (window.voteManager) {
          const resultsVoteId = document.getElementById('resultsVoteId')?.value
          if (resultsVoteId) {
            window.voteManager.loadAndDisplayResults(resultsVoteId)
          }
        }
        break
      case 'view-vote':
        if (voteId) {
          // Open vote in new tab/window
          window.open(`/vote/${voteId}`, '_blank')
        }
        break
      case 'copy-link':
        if (voteId) {
          this.copyVoteLink(voteId)
        }
        break

      // Account Deletion Actions
      case 'show-delete-confirmation':
        if (window.profileManager) {
          window.profileManager.showDeleteConfirmation()
        }
        break
      case 'close-delete-modal':
        if (window.profileManager) {
          window.profileManager.closeDeleteModal()
        }
        break
      case 'confirm-account-deletion':
        if (window.profileManager) {
          window.profileManager.confirmAccountDeletion()
        }
        break

      // Draft vote management actions
      case 'edit-vote':
        if (voteId) {
          this.editVote(voteId)
        }
        break
      case 'publish-vote':
        if (voteId) {
          this.publishVote(voteId)
        }
        break
      case 'delete-vote':
        if (voteId) {
          this.deleteVote(voteId)
        }
        break

      default:
        console.log('Unhandled action:', action)
    }
  }

  toggleNavigationDrawer() {
    if (this.navigationDrawer && this.navigationScrim) {
      this.navigationDrawer.classList.toggle('md-navigation-drawer-open')
      this.navigationScrim.classList.toggle('md-navigation-drawer-scrim-visible')
    }
  }

  closeNavigationDrawer() {
    if (this.navigationDrawer && this.navigationScrim) {
      this.navigationDrawer.classList.remove('md-navigation-drawer-open')
      this.navigationScrim.classList.remove('md-navigation-drawer-scrim-visible')
    }
  }

  forceCloseDrawer() {
    // Immediately hide drawer without waiting for DOM ready
    const drawer = document.getElementById('navigationDrawer')
    const scrim = document.getElementById('navigationScrim')

    if (drawer) {
      drawer.classList.remove('md-navigation-drawer-open')
      drawer.style.transform = 'translateX(-100%)'
      drawer.style.pointerEvents = 'none'
    }

    if (scrim) {
      scrim.classList.remove('md-navigation-drawer-scrim-visible')
      scrim.style.opacity = '0'
      scrim.style.pointerEvents = 'none'
    }
  }

  toggleUserMenu() {
    if (this.userMenu) {
      const isVisible = this.userMenu.style.display === 'block'
      if (isVisible) {
        this.closeUserMenu()
      } else {
        this.showUserMenu()
      }
    }
  }

  showUserMenu() {
    if (this.userMenu) {
      this.userMenu.style.display = 'block'
      setTimeout(() => {
        this.userMenu.classList.add('visible')
      }, 10)
    }
  }

  closeUserMenu() {
    if (this.userMenu) {
      this.userMenu.classList.remove('visible')
      setTimeout(() => {
        this.userMenu.style.display = 'none'
      }, 200)
    }
  }

  async loadUserData() {
    const token = this.getAccessToken()
    if (!token) {
      this.redirectToLogin()
      return
    }

    try {
      const response = await fetch(`${this.API_BASE}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        this.user = await response.json()
        this.updateUserDisplay()
      } else {
        this.clearTokens()
        this.redirectToLogin()
      }
    } catch (error) {
      console.error('Failed to load user data:', error)
      this.showSnackbar('Failed to load user information')
    }
  }

  updateUserDisplay() {
    if (this.user) {
      const displayName = document.getElementById('userDisplayName')
      if (displayName) {
        displayName.textContent = `${this.user.first_name} ${this.user.last_name}`
      }

      // Show admin section for super admin users
      const adminSection = document.getElementById('adminSection')
      if (adminSection && this.user.is_super_admin) {
        adminSection.style.display = 'block'
      }
    }
  }

  async loadDashboardData() {
    const token = this.getAccessToken()
    if (!token) return

    try {
      // Load dashboard statistics from new API endpoint
      const statsResponse = await fetch(`${this.API_BASE}/dashboard/stats`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (statsResponse.ok) {
        const statsData = await statsResponse.json()
        this.updateDashboardStats(statsData)
      }

      // Load recent votes summary
      const voteSummaryResponse = await fetch(`${this.API_BASE}/dashboard/votes/summary?limit=10`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (voteSummaryResponse.ok) {
        const summaryData = await voteSummaryResponse.json()
        this.updateRecentVotes(summaryData.recent_votes)
      }

      // Load user's votes list
      const votesResponse = await fetch(`${this.API_BASE}/votes?limit=5&sort=created_at`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (votesResponse.ok) {
        const votesData = await votesResponse.json()
        this.updateVotesList(votesData.votes)
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      this.showErrorToast('Failed to load dashboard data. Please refresh the page.')
    }
  }

  updateDashboardStats(statsData) {
    // Update dashboard statistics with new API format
    const totalVotesEl = document.getElementById('totalVotes')
    const activeVotesEl = document.getElementById('activeVotes')
    const totalResponsesEl = document.getElementById('totalResponses')
    const recentActivityEl = document.getElementById('recentActivity')

    if (totalVotesEl) totalVotesEl.textContent = statsData.total_votes_created || 0
    if (activeVotesEl) activeVotesEl.textContent = statsData.active_votes_count || 0
    if (totalResponsesEl) totalResponsesEl.textContent = statsData.total_responses_received || 0
    if (recentActivityEl) recentActivityEl.textContent = statsData.recent_activity_count || 0

    // Additional status cards can be added as needed
    const draftVotesEl = document.getElementById('draftVotes')
    const closedVotesEl = document.getElementById('closedVotes')

    // Draft votes would be total_votes_created - active_votes_count (approximately)
    if (draftVotesEl) {
      const draftVotes = Math.max(0, (statsData.total_votes_created || 0) - (statsData.active_votes_count || 0))
      draftVotesEl.textContent = draftVotes
    }

    // Closed votes would need separate endpoint or calculation
    if (closedVotesEl) closedVotesEl.textContent = 0
  }

  updateRecentVotes(votes) {
    const recentVotesList = document.getElementById('recentVotesList')
    if (!recentVotesList) return

    if (!votes || votes.length === 0) {
      // Show empty state (already in HTML)
      return
    }

    // Show up to 5 recent votes
    const recentVotes = votes.slice(0, 5)
    const voteItems = recentVotes.map(vote => this.createVoteItem(vote)).join('')

    recentVotesList.innerHTML = voteItems
  }

  updateActivityTimeline(activityData) {
    const activityContainer = document.getElementById('activityTimeline')
    if (!activityContainer) {
      // Create activity timeline section if it doesn't exist
      this.createActivityTimelineSection()
      return this.updateActivityTimeline(activityData)
    }

    const activities = activityData.activities || []

    if (activities.length === 0) {
      activityContainer.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">
            <span class="material-icons">timeline</span>
          </div>
          <h3 class="md-headline-small">No recent activity</h3>
          <p class="md-body-medium md-on-surface-variant">
            Activity from the last 7 days will appear here.
          </p>
        </div>
      `
      return
    }

    const activityItems = activities.map(activity => this.createActivityItem(activity)).join('')
    activityContainer.innerHTML = `
      <div class="activity-list">
        ${activityItems}
      </div>
    `
  }

  createActivityTimelineSection() {
    const welcomeSection = document.querySelector('.welcome-section')
    if (!welcomeSection) return

    const activitySection = document.createElement('section')
    activitySection.className = 'activity-section'
    activitySection.innerHTML = `
      <div class="md-container">
        <div class="section-header">
          <h2 class="md-headline-medium">Recent Activity</h2>
          <span class="md-body-small md-on-surface-variant">Last 7 days</span>
        </div>
        <div class="activity-timeline-container md-card md-card-elevated">
          <div id="activityTimeline" class="activity-timeline">
            <!-- Activity items will be loaded here -->
          </div>
        </div>
      </div>
    `

    // Insert after the welcome section
    welcomeSection.parentNode.insertBefore(activitySection, welcomeSection.nextSibling)
  }

  createActivityItem(activity) {
    const timeAgo = this.formatTimeAgo(new Date(activity.timestamp))
    const colorClass = `activity-${activity.color || 'primary'}`

    return `
      <div class="activity-item ${colorClass}" data-activity-id="${activity.id}">
        <div class="activity-icon">
          <span class="material-icons">${activity.icon || 'circle'}</span>
        </div>
        <div class="activity-content">
          <h4 class="activity-title md-title-small">${this.escapeHtml(activity.title)}</h4>
          <p class="activity-description md-body-medium md-on-surface-variant">
            ${this.escapeHtml(activity.description)}
          </p>
          <span class="activity-time md-body-small md-on-surface-variant">${timeAgo}</span>
        </div>
      </div>
    `
  }

  formatTimeAgo(date) {
    const now = new Date()
    const diffInSeconds = Math.floor((now - date) / 1000)

    if (diffInSeconds < 60) return 'Just now'
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`

    return date.toLocaleDateString()
  }

  createVoteItem(vote) {
    const statusClass = vote.status || 'draft'
    const createdDate = new Date(vote.created_at).toLocaleDateString()

    return `
      <div class="vote-item" data-vote-id="${vote.id}">
        <div class="vote-status ${statusClass}"></div>
        <div class="vote-info">
          <h3 class="vote-title">${this.escapeHtml(vote.title)}</h3>
          <p class="vote-meta">Created ${createdDate} • ${vote.status}</p>
        </div>
        <div class="vote-actions">
          <button class="md-button md-button-icon" data-action="edit-vote" data-vote-id="${vote.id}">
            <span class="material-icons">edit</span>
          </button>
          <button class="md-button md-button-icon" data-action="view-vote" data-vote-id="${vote.id}">
            <span class="material-icons">visibility</span>
          </button>
        </div>
      </div>
    `
  }

  createVote() {
    // The VoteCreationManager handles this via data-action="create-vote"
    // This method is kept for compatibility but the modal is handled automatically
  }

  viewAllVotes() {
    // Scroll to vote management section
    const voteManagementSection = document.querySelector('.vote-management-section')
    if (voteManagementSection) {
      voteManagementSection.scrollIntoView({ behavior: 'smooth' })
    }
  }

  copyVoteLink(voteId) {
    const vote = window.voteManager?.votes.find(v => v.id === parseInt(voteId))
    if (vote && vote.slug) {
      const link = `${window.location.origin}/vote/${vote.slug}`
      navigator.clipboard
        .writeText(link)
        .then(() => {
          this.showSnackbar('Vote link copied to clipboard!')
        })
        .catch(() => {
          // Fallback for older browsers
          const textArea = document.createElement('textarea')
          textArea.value = link
          document.body.appendChild(textArea)
          textArea.select()
          document.execCommand('copy')
          document.body.removeChild(textArea)
          this.showSnackbar('Vote link copied to clipboard!')
        })
    } else {
      this.showSnackbar('Unable to copy vote link')
    }
  }

  showProfile() {
    this.closeUserMenu()
    if (window.profileManager) {
      window.profileManager.openModal()
    } else {
      this.showSnackbar('Profile manager not loaded')
    }
  }

  showSettings() {
    this.closeUserMenu()
    this.showSnackbar('Settings page coming soon!')
  }

  logout() {
    this.clearTokens()
    this.showSnackbar('Signed out successfully')
    setTimeout(() => {
      window.location.href = '/'
    }, 1000)
  }

  // Utility methods
  getAccessToken() {
    return sessionStorage.getItem('access_token')
  }

  clearTokens() {
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')
  }

  redirectToLogin() {
    window.location.href = '/'
  }

  showSnackbar(message) {
    const snackbar = document.getElementById('snackbar')
    const snackbarMessage = document.getElementById('snackbar-message')

    if (snackbar && snackbarMessage) {
      snackbarMessage.textContent = message
      snackbar.classList.add('md-snackbar-visible')

      setTimeout(() => {
        snackbar.classList.remove('md-snackbar-visible')
      }, 4000)
    }
  }

  dismissSnackbar() {
    const snackbar = document.getElementById('snackbar')
    if (snackbar) {
      snackbar.classList.remove('md-snackbar-visible')
    }
  }

  updateVotesList(votes) {
    const votesList = document.getElementById('voteList')
    if (!votesList) return

    if (!votes || votes.length === 0) {
      votesList.innerHTML = `
        <div class="empty-state">
          <span class="material-icons">ballot</span>
          <p class="md-body-large">No votes yet</p>
          <button class="md-button md-button-filled" data-action="create-vote">
            <span class="material-icons">add</span>
            Create Your First Vote
          </button>
        </div>
      `
      return
    }

    const votesHtml = votes
      .map(
        vote => `
      <div class="vote-card md-card md-card-outlined" data-vote-id="${vote.id}">
        <div class="vote-card-content">
          <h3 class="md-title-medium">${this.escapeHtml(vote.title)}</h3>
          <p class="md-body-medium md-on-surface-variant vote-description">
            ${vote.description ? this.escapeHtml(vote.description) : 'No description'}
          </p>
          <div class="vote-meta">
            <span class="vote-status ${vote.is_draft ? 'draft' : vote.is_active ? 'active' : 'closed'}">
              ${vote.is_draft ? 'Draft' : vote.is_active ? 'Active' : 'Closed'}
            </span>
            <span class="vote-choices">${vote.choice_count || 0} choices</span>
            <span class="vote-responses">${vote.response_count || 0} responses</span>
          </div>
          <div class="vote-actions">
            ${
              vote.is_draft
                ? `
              <button class="md-button md-button-text" data-action="edit-vote" data-vote-id="${vote.id}">
                <span class="material-icons">edit</span>
                Edit
              </button>
              <button class="md-button md-button-filled" data-action="publish-vote" data-vote-id="${vote.id}">
                <span class="material-icons">publish</span>
                Publish
              </button>
            `
                : `
              <button class="md-button md-button-text" data-action="view-results" data-vote-id="${vote.id}">
                <span class="material-icons">analytics</span>
                Results
              </button>
            `
            }
          </div>
        </div>
      </div>
    `
      )
      .join('')

    votesList.innerHTML = votesHtml
  }

  showErrorToast(message) {
    this.showSnackbar(message)
  }

  async editVote(voteId) {
    try {
      const token = this.getAccessToken()
      if (!token) {
        this.redirectToLogin()
        return
      }

      // For now, redirect to a vote editor or show a modal
      // This could be extended to use an edit modal
      this.showSnackbar('Edit functionality coming soon!')

      // In a full implementation, you might:
      // 1. Open a modal with vote edit form
      // 2. Load vote details via API
      // 3. Allow editing title, description, choices
      // 4. Save changes via PUT /api/votes/{vote_id}
    } catch (error) {
      console.error('Failed to edit vote:', error)
      this.showErrorToast('Failed to edit vote')
    }
  }

  async publishVote(voteId) {
    try {
      const token = this.getAccessToken()
      if (!token) {
        this.redirectToLogin()
        return
      }

      // Show confirmation dialog
      const confirmed = confirm(
        'Are you sure you want to publish this vote? Once published, you cannot edit it further.'
      )
      if (!confirmed) return

      const response = await fetch(`${this.API_BASE}/votes/${voteId}/publish`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        this.showSnackbar('Vote published successfully!')
        // Reload dashboard data to reflect changes
        this.loadDashboardData()
      } else {
        const errorData = await response.json()
        this.showErrorToast(errorData.message || 'Failed to publish vote')
      }
    } catch (error) {
      console.error('Failed to publish vote:', error)
      this.showErrorToast('Failed to publish vote')
    }
  }

  async deleteVote(voteId) {
    try {
      const token = this.getAccessToken()
      if (!token) {
        this.redirectToLogin()
        return
      }

      // Show confirmation dialog
      const confirmed = confirm('Are you sure you want to delete this vote? This action cannot be undone.')
      if (!confirmed) return

      const response = await fetch(`${this.API_BASE}/votes/${voteId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        this.showSnackbar('Vote deleted successfully!')
        // Reload dashboard data to reflect changes
        this.loadDashboardData()
      } else {
        const errorData = await response.json()
        this.showErrorToast(errorData.message || 'Failed to delete vote')
      }
    } catch (error) {
      console.error('Failed to delete vote:', error)
      this.showErrorToast('Failed to delete vote')
    }
  }

  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }
    return text.replace(/[&<>"']/g, function (m) {
      return map[m]
    })
  }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  DashboardManager.init()

  // Add fade-in animation to sections
  setTimeout(() => {
    document.querySelectorAll('.welcome-card, .stat-card').forEach((el, index) => {
      el.style.animationDelay = `${index * 0.1}s`
      el.classList.add('fade-in')
    })
  }, 100)
})
