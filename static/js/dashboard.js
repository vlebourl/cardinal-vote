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

  handleAction(action, _element) {
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
      case 'settings':
        this.showSettings()
        break
      case 'view-all-votes':
        this.viewAllVotes()
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
    }
  }

  async loadDashboardData() {
    const token = this.getAccessToken()
    if (!token) return

    try {
      // Load user's votes
      const votesResponse = await fetch(`${this.API_BASE}/votes/`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (votesResponse.ok) {
        const votesData = await votesResponse.json()
        this.updateStats(votesData)
        this.updateRecentVotes(votesData.votes)
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      // Don't show error for data loading - user can still use the interface
    }
  }

  updateStats(votesData) {
    const votes = votesData.votes || []

    // Update stat counters
    document.getElementById('totalVotes').textContent = votes.length
    document.getElementById('activeVotes').textContent = votes.filter(vote => vote.status === 'active').length

    // For now, set mock data for responses and recent activity
    document.getElementById('totalResponses').textContent = '0'
    document.getElementById('recentActivity').textContent = votes.length
  }

  updateRecentVotes(votes) {
    const recentVotesList = document.getElementById('recentVotesList')
    if (!recentVotesList) return

    if (votes.length === 0) {
      // Show empty state (already in HTML)
      return
    }

    // Show up to 5 recent votes
    const recentVotes = votes.slice(0, 5)
    const voteItems = recentVotes.map(vote => this.createVoteItem(vote)).join('')

    recentVotesList.innerHTML = voteItems
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
    // For now, show a placeholder message
    this.showSnackbar('Vote creation feature coming soon!')
  }

  viewAllVotes() {
    // For now, show a placeholder message
    this.showSnackbar('Vote management feature coming soon!')
  }

  showProfile() {
    this.closeUserMenu()
    this.showSnackbar('Profile settings coming soon!')
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
