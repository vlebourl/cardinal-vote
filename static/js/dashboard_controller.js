/**
 * Dashboard Controller - Main controller for dashboard functionality
 * Handles navigation, data loading, and UI interactions
 */

class DashboardController {
  constructor() {
    this.API_BASE = '/api'
    this.currentSection = 'overview'
    this.currentUser = null
    this.dashboardData = {
      stats: null,
      votes: null,
      notifications: null,
      activity: null
    }

    // Configuration
    this.refreshInterval = null
    this.refreshIntervalTime = 30000 // 30 seconds

    // UI State
    this.isNavigationOpen = false
    this.currentView = 'grid' // 'grid' or 'list'
    this.currentFilter = 'all'
    this.currentSort = 'created_at_desc'
    this.pagination = {
      page: 1,
      limit: 12,
      total: 0,
      hasMore: false
    }

    // Event handlers storage for cleanup
    this.eventHandlers = new Map()

    // Initialize
    this.setupEventListeners()
  }

  /**
   * Initialize the dashboard
   */
  async init() {
    try {
      this.showLoadingState()

      // Load initial data
      await this.loadUserProfile()
      await this.loadDashboardData()

      // Setup UI
      this.updateNavigationState()
      this.startAutoRefresh()

      // Show welcome message
      this.showSnackbar('Dashboard loaded successfully!', 'success')
    } catch (error) {
      console.error('Dashboard initialization failed:', error)
      this.handleError(error, 'Failed to initialize dashboard')
    } finally {
      this.hideLoadingState()
    }
  }

  /**
   * Setup event listeners for dashboard interactions
   */
  setupEventListeners() {
    // Navigation toggle
    this.addEventHandler('navigationToggle', 'click', () => {
      this.toggleNavigation()
    })

    // Navigation items
    document.querySelectorAll('[data-section]').forEach(item => {
      this.addEventHandler(item, 'click', e => {
        e.preventDefault()
        const section = item.dataset.section
        this.showSection(section)
      })
    })

    // Top bar actions
    this.addEventHandler('refreshDashboard', 'click', () => {
      this.refreshDashboard()
    })

    this.addEventHandler('createVoteBtn', 'click', () => {
      this.showCreateVoteModal()
    })

    this.addEventHandler('userMenuBtn', 'click', () => {
      this.toggleUserMenu()
    })

    // User menu actions
    this.addEventHandler('profileBtn', 'click', () => {
      this.showProfileModal()
    })

    this.addEventHandler('settingsBtn', 'click', () => {
      this.showSettingsModal()
    })

    this.addEventHandler('logoutBtn', 'click', () => {
      this.handleLogout()
    })

    this.addEventHandler('menuLogoutBtn', 'click', () => {
      this.handleLogout()
    })

    // Navigation scrim (mobile)
    this.addEventHandler('navigationScrim', 'click', () => {
      this.closeNavigation()
    })

    // Notifications
    this.addEventHandler('notificationsBtn', 'click', () => {
      this.toggleNotificationsPanel()
    })

    this.addEventHandler('markAllReadBtn', 'click', () => {
      this.markAllNotificationsAsRead()
    })

    // Quick actions
    this.addEventHandler('createFirstVote', 'click', () => {
      this.showCreateVoteModal()
    })

    this.addEventHandler('helpBtn', 'click', () => {
      this.showHelpModal()
    })

    // Analytics controls
    this.addEventHandler('analyticsTimeframe', 'change', e => {
      this.loadAnalyticsData(e.target.value)
    })

    this.addEventHandler('exportAnalytics', 'click', () => {
      this.exportAnalyticsData()
    })

    // Snackbar dismiss
    this.addEventHandler('snackbar-action', 'click', () => {
      this.hideSnackbar()
    })

    // Window events
    window.addEventListener(
      'resize',
      this.debounce(() => {
        this.handleResize()
      }, 250)
    )

    window.addEventListener('beforeunload', () => {
      this.cleanup()
    })

    // Keyboard shortcuts
    document.addEventListener('keydown', e => {
      this.handleKeyboardShortcuts(e)
    })

    // Handle visibility change for auto-refresh
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.stopAutoRefresh()
      } else {
        this.startAutoRefresh()
        this.refreshDashboard()
      }
    })
  }

  /**
   * Add event handler with cleanup tracking
   */
  addEventHandler(elementOrId, event, handler) {
    const element = typeof elementOrId === 'string' ? document.getElementById(elementOrId) : elementOrId

    if (element) {
      element.addEventListener(event, handler)

      // Store for cleanup
      const key = `${elementOrId}-${event}`
      this.eventHandlers.set(key, { element, event, handler })
    }
  }

  /**
   * Load user profile data
   */
  async loadUserProfile() {
    try {
      const response = await this.apiRequest('/auth/me')
      this.currentUser = response

      // Update UI with user info
      this.updateUserProfile(response)

      // Check if user is admin and show admin sections
      if (response.role === 'admin' || response.is_super_admin) {
        this.showAdminSections()
      }
    } catch (error) {
      console.error('Failed to load user profile:', error)
      // Don't throw - dashboard can work without user profile
    }
  }

  /**
   * Load dashboard data
   */
  async loadDashboardData() {
    try {
      // Load data in parallel for better performance
      const [overview, notifications] = await Promise.all([this.loadDashboardOverview(), this.loadNotifications()])

      this.dashboardData = {
        ...overview,
        notifications
      }

      this.updateDashboardUI()
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      throw error
    }
  }

  /**
   * Load dashboard overview data
   */
  async loadDashboardOverview() {
    const response = await this.apiRequest('/dashboard/')
    return response
  }

  /**
   * Load notifications
   */
  async loadNotifications() {
    try {
      const response = await this.apiRequest('/dashboard/notifications?limit=10')
      return response.notifications || []
    } catch (error) {
      console.error('Failed to load notifications:', error)
      return []
    }
  }

  /**
   * Update dashboard UI with loaded data
   */
  updateDashboardUI() {
    const data = this.dashboardData

    if (data.quick_stats) {
      this.updateQuickStats(data.quick_stats)
    }

    if (data.recent_votes) {
      this.updateRecentVotes(data.recent_votes)
    }

    if (data.user_activity) {
      this.updateRecentActivity(data.user_activity)
    }

    if (data.notifications) {
      this.updateNotifications(data.notifications)
    }
  }

  /**
   * Update quick stats section
   */
  updateQuickStats(stats) {
    this.updateElement('totalVotes', stats.total_votes || 0)
    this.updateElement('activeVotes', stats.active_votes || 0)
    this.updateElement('totalResponses', stats.total_responses || 0)
    this.updateElement('participationRate', `${stats.participation_rate || 0}%`)

    // Update trend indicators
    this.updateTrendIndicator('votesTrend', stats.votes_trend)
    this.updateTrendIndicator('activeTrend', stats.active_trend)
    this.updateTrendIndicator('responsesTrend', stats.responses_trend)
    this.updateTrendIndicator('participationTrend', stats.participation_trend)
  }

  /**
   * Update trend indicator
   */
  updateTrendIndicator(elementId, trend) {
    const element = document.getElementById(elementId)
    if (!element || !trend) return

    const icon = element.querySelector('.trend-icon')
    const text = element.querySelector('.trend-text')

    if (icon && text) {
      icon.textContent =
        trend.direction === 'up' ? 'trending_up' : trend.direction === 'down' ? 'trending_down' : 'trending_flat'
      text.textContent = trend.text || 'No change'

      element.className = `stat-trend ${trend.direction}`
    }
  }

  /**
   * Update recent votes section
   */
  updateRecentVotes(votes) {
    const container = document.getElementById('recentActivityList')
    if (!container) return

    if (!votes || votes.length === 0) {
      container.innerHTML = this.createEmptyState(
        'schedule',
        'No recent activity',
        'Your recent votes and activities will appear here.'
      )
      return
    }

    const voteItems = votes.map(vote => this.createVoteActivityItem(vote)).join('')
    container.innerHTML = voteItems
  }

  /**
   * Create vote activity item HTML
   */
  createVoteActivityItem(vote) {
    const statusClass = this.getVoteStatusClass(vote.status)
    const timeAgo = this.formatTimeAgo(vote.created_at)

    return `
            <div class="activity-item vote-activity" data-vote-id="${vote.id}">
                <div class="activity-icon ${statusClass}">
                    <span class="material-icons">${this.getVoteStatusIcon(vote.status)}</span>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${this.escapeHtml(vote.title)}</div>
                    <div class="activity-description">
                        ${
                          vote.status === 'draft'
                            ? 'Draft created'
                            : vote.status === 'active'
                              ? `${vote.response_count || 0} responses`
                              : 'Vote completed'
                        }
                    </div>
                    <div class="activity-time">${timeAgo}</div>
                </div>
                <div class="activity-actions">
                    <button class="md-icon-button" onclick="dashboardController.viewVote('${vote.id}')" aria-label="View vote">
                        <span class="material-icons">visibility</span>
                    </button>
                </div>
            </div>
        `
  }

  /**
   * Update notifications
   */
  updateNotifications(notifications) {
    const badge = document.getElementById('notificationBadge')
    const container = document.getElementById('notificationsList')

    // Update badge
    const unreadCount = notifications.filter(n => !n.read).length
    if (badge) {
      if (unreadCount > 0) {
        badge.textContent = unreadCount
        badge.style.display = 'block'
      } else {
        badge.style.display = 'none'
      }
    }

    // Update notifications list
    if (container) {
      if (notifications.length === 0) {
        container.innerHTML = this.createEmptyState(
          'notifications',
          'No notifications',
          "You'll see notifications about your votes here."
        )
        return
      }

      const notificationItems = notifications.map(notification => this.createNotificationItem(notification)).join('')
      container.innerHTML = notificationItems
    }
  }

  /**
   * Create notification item HTML
   */
  createNotificationItem(notification) {
    const unreadClass = notification.read ? '' : 'unread'
    const timeAgo = this.formatTimeAgo(notification.created_at)

    return `
            <div class="notification-item ${unreadClass}" data-notification-id="${notification.id}">
                <div class="notification-icon">
                    <span class="material-icons">${this.getNotificationIcon(notification.type)}</span>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${this.escapeHtml(notification.title)}</div>
                    <div class="notification-message">${this.escapeHtml(notification.message)}</div>
                    <div class="notification-time">${timeAgo}</div>
                </div>
                ${
                  !notification.read
                    ? `
                    <button class="md-icon-button mark-read-btn" onclick="dashboardController.markNotificationAsRead('${notification.id}')" aria-label="Mark as read">
                        <span class="material-icons">done</span>
                    </button>
                `
                    : ''
                }
            </div>
        `
  }

  /**
   * Show/hide sections
   */
  showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.dashboard-section').forEach(section => {
      section.style.display = 'none'
    })

    // Update navigation
    document.querySelectorAll('.md-navigation-drawer-item').forEach(item => {
      item.classList.remove('md-navigation-drawer-item-selected')
    })

    // Show target section
    const targetSection = document.getElementById(`${sectionName}Section`)
    if (targetSection) {
      targetSection.style.display = 'block'
      this.currentSection = sectionName
    }

    // Update navigation item
    const navItem = document.querySelector(`[data-section="${sectionName}"]`)
    if (navItem) {
      navItem.classList.add('md-navigation-drawer-item-selected')
    }

    // Load section-specific data
    this.loadSectionData(sectionName)

    // Close navigation on mobile
    if (window.innerWidth < 1200) {
      this.closeNavigation()
    }

    // Update URL without page reload
    this.updateURL(sectionName)
  }

  /**
   * Load section-specific data
   */
  async loadSectionData(sectionName) {
    try {
      switch (sectionName) {
        case 'my-votes':
          await this.loadMyVotes()
          break
        case 'available-votes':
          await this.loadAvailableVotes()
          break
        case 'analytics':
          await this.loadAnalyticsData()
          break
        case 'user-management':
          if (this.currentUser?.is_super_admin) {
            await this.loadUserManagement()
          }
          break
        case 'system-votes':
          if (this.currentUser?.is_super_admin) {
            await this.loadSystemVotes()
          }
          break
        case 'system-stats':
          if (this.currentUser?.is_super_admin) {
            await this.loadSystemStats()
          }
          break
      }
    } catch (error) {
      console.error(`Failed to load section data for ${sectionName}:`, error)
      this.showSnackbar(`Failed to load ${sectionName} data`, 'error')
    }
  }

  /**
   * Load my votes data
   */
  async loadMyVotes() {
    try {
      const response = await this.apiRequest(
        `/dashboard/my-votes?limit=${this.pagination.limit}&offset=${(this.pagination.page - 1) * this.pagination.limit}&status=${this.currentFilter}`
      )

      if (window.voteManager) {
        window.voteManager.updateVotesList(response.votes, response.pagination)
      }
    } catch (error) {
      console.error('Failed to load my votes:', error)
    }
  }

  /**
   * Load available votes data
   */
  async loadAvailableVotes() {
    try {
      const response = await this.apiRequest(
        `/dashboard/available-votes?limit=${this.pagination.limit}&offset=${(this.pagination.page - 1) * this.pagination.limit}`
      )

      this.updateAvailableVotesList(response.votes, response.pagination)
    } catch (error) {
      console.error('Failed to load available votes:', error)
    }
  }

  /**
   * Load analytics data
   */
  async loadAnalyticsData(timeframe = '30d') {
    try {
      // This would load analytics data from the API
      // For now, we'll create mock data for demonstration
      this.updateAnalyticsCharts(timeframe)
    } catch (error) {
      console.error('Failed to load analytics data:', error)
    }
  }

  /**
   * Navigation methods
   */
  toggleNavigation() {
    this.isNavigationOpen = !this.isNavigationOpen
    this.updateNavigationState()
  }

  closeNavigation() {
    this.isNavigationOpen = false
    this.updateNavigationState()
  }

  updateNavigationState() {
    const drawer = document.getElementById('navigationDrawer')
    const scrim = document.getElementById('navigationScrim')

    if (this.isNavigationOpen) {
      drawer?.classList.add('md-navigation-drawer-open')
      scrim?.classList.add('md-navigation-drawer-scrim-visible')
      document.body.style.overflow = 'hidden'
    } else {
      drawer?.classList.remove('md-navigation-drawer-open')
      scrim?.classList.remove('md-navigation-drawer-scrim-visible')
      document.body.style.overflow = ''
    }
  }

  /**
   * User profile methods
   */
  updateUserProfile(user) {
    this.updateElement('userDisplayName', `${user.first_name} ${user.last_name}` || 'User')
    this.updateElement('userEmail', user.email || '')
  }

  showAdminSections() {
    const adminSection = document.getElementById('adminSection')
    if (adminSection) {
      adminSection.style.display = 'block'
    }

    // Update navigation badge for admin
    const totalUsersBadge = document.getElementById('totalUsersBadge')
    const totalVotesBadge = document.getElementById('totalVotesBadge')

    // These would be updated with real data
    if (totalUsersBadge) totalUsersBadge.textContent = '0'
    if (totalVotesBadge) totalVotesBadge.textContent = '0'
  }

  /**
   * Modal methods
   */
  showCreateVoteModal() {
    if (window.voteManager) {
      window.voteManager.showCreateModal()
    }
  }

  showProfileModal() {
    // Implementation for profile modal
    this.showSnackbar('Profile modal coming soon!', 'info')
  }

  showSettingsModal() {
    // Implementation for settings modal
    this.showSnackbar('Settings modal coming soon!', 'info')
  }

  showHelpModal() {
    // Implementation for help modal
    this.showSnackbar('Help documentation coming soon!', 'info')
  }

  /**
   * Notification methods
   */
  toggleNotificationsPanel() {
    const panel = document.getElementById('notificationsPanel')
    if (panel) {
      const isVisible = panel.style.display !== 'none'
      panel.style.display = isVisible ? 'none' : 'block'
    }
  }

  async markNotificationAsRead(notificationId) {
    try {
      await this.apiRequest('/dashboard/notifications', {
        method: 'PATCH',
        body: JSON.stringify({
          notification_ids: [notificationId]
        })
      })

      // Update UI
      const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`)
      if (notificationElement) {
        notificationElement.classList.remove('unread')
        const markReadBtn = notificationElement.querySelector('.mark-read-btn')
        if (markReadBtn) {
          markReadBtn.remove()
        }
      }

      // Update badge
      this.updateNotificationBadge()
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
      this.showSnackbar('Failed to mark notification as read', 'error')
    }
  }

  async markAllNotificationsAsRead() {
    try {
      await this.apiRequest('/dashboard/notifications', {
        method: 'PATCH',
        body: JSON.stringify({
          mark_all_read: true
        })
      })

      // Update UI
      document.querySelectorAll('.notification-item.unread').forEach(item => {
        item.classList.remove('unread')
        const markReadBtn = item.querySelector('.mark-read-btn')
        if (markReadBtn) {
          markReadBtn.remove()
        }
      })

      // Update badge
      this.updateNotificationBadge()
      this.showSnackbar('All notifications marked as read', 'success')
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error)
      this.showSnackbar('Failed to mark notifications as read', 'error')
    }
  }

  updateNotificationBadge() {
    const badge = document.getElementById('notificationBadge')
    const unreadCount = document.querySelectorAll('.notification-item.unread').length

    if (badge) {
      if (unreadCount > 0) {
        badge.textContent = unreadCount
        badge.style.display = 'block'
      } else {
        badge.style.display = 'none'
      }
    }
  }

  /**
   * User menu methods
   */
  toggleUserMenu() {
    const menu = document.getElementById('userMenu')
    if (menu) {
      const isVisible = menu.style.display !== 'none'
      menu.style.display = isVisible ? 'none' : 'block'
    }
  }

  /**
   * Logout handling
   */
  async handleLogout() {
    if (confirm('Are you sure you want to sign out?')) {
      try {
        // Clear local data
        this.cleanup()

        // Make logout request
        await fetch('/auth/logout', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${this.getToken()}`
          }
        })

        // Clear token and redirect
        localStorage.removeItem('access_token')
        sessionStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        sessionStorage.removeItem('refresh_token')

        window.location.href = '/'
      } catch (error) {
        console.error('Logout failed:', error)
        // Still redirect even if logout request fails
        localStorage.removeItem('access_token')
        sessionStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        sessionStorage.removeItem('refresh_token')
        window.location.href = '/'
      }
    }
  }

  /**
   * Refresh dashboard
   */
  async refreshDashboard() {
    try {
      this.showRefreshIndicator()
      await this.loadDashboardData()
      await this.loadSectionData(this.currentSection)
      this.showSnackbar('Dashboard refreshed', 'success')
    } catch (error) {
      console.error('Failed to refresh dashboard:', error)
      this.showSnackbar('Failed to refresh dashboard', 'error')
    } finally {
      this.hideRefreshIndicator()
    }
  }

  /**
   * Auto-refresh methods
   */
  startAutoRefresh() {
    this.stopAutoRefresh() // Clear any existing interval
    this.refreshInterval = setInterval(() => {
      this.loadDashboardData().catch(console.error)
    }, this.refreshIntervalTime)
  }

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
      this.refreshInterval = null
    }
  }

  /**
   * Keyboard shortcuts
   */
  handleKeyboardShortcuts(e) {
    // Ctrl/Cmd + R for refresh
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
      e.preventDefault()
      this.refreshDashboard()
    }

    // Escape to close modals/menus
    if (e.key === 'Escape') {
      this.closeAllModalsAndMenus()
    }

    // Ctrl/Cmd + N for new vote
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
      e.preventDefault()
      this.showCreateVoteModal()
    }
  }

  closeAllModalsAndMenus() {
    // Close user menu
    const userMenu = document.getElementById('userMenu')
    if (userMenu) userMenu.style.display = 'none'

    // Close notifications panel
    const notificationsPanel = document.getElementById('notificationsPanel')
    if (notificationsPanel) notificationsPanel.style.display = 'none'

    // Close navigation on mobile
    if (window.innerWidth < 1200) {
      this.closeNavigation()
    }
  }

  /**
   * Handle window resize
   */
  handleResize() {
    // Close navigation on mobile
    if (window.innerWidth < 1200 && this.isNavigationOpen) {
      this.closeNavigation()
    }

    // Auto-open navigation on desktop
    if (window.innerWidth >= 1200 && !this.isNavigationOpen) {
      this.isNavigationOpen = true
      this.updateNavigationState()
    }
  }

  /**
   * Utility methods
   */
  async apiRequest(endpoint, options = {}) {
    const token = this.getToken()

    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers
      }
    }

    const response = await fetch(`${this.API_BASE}${endpoint}`, {
      ...defaultOptions,
      ...options
    })

    if (!response.ok) {
      if (response.status === 401) {
        this.handleAuthError()
        throw new Error('Authentication failed')
      }
      throw new Error(`API request failed: ${response.status}`)
    }

    return await response.json()
  }

  getToken() {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  }

  handleAuthError() {
    localStorage.removeItem('access_token')
    sessionStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    sessionStorage.removeItem('refresh_token')
    this.showSnackbar('Session expired. Please sign in again.', 'error')
    setTimeout(() => {
      window.location.href = '/'
    }, 2000)
  }

  handleError(error, userMessage = 'An error occurred') {
    console.error('Dashboard error:', error)
    this.showSnackbar(userMessage, 'error')
  }

  updateElement(id, content) {
    const element = document.getElementById(id)
    if (element) {
      element.textContent = content
    }
  }

  escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
  }

  formatTimeAgo(dateString) {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now - date

    const minute = 60 * 1000
    const hour = 60 * minute
    const day = 24 * hour

    if (diff < minute) return 'just now'
    if (diff < hour) return `${Math.floor(diff / minute)}m ago`
    if (diff < day) return `${Math.floor(diff / hour)}h ago`
    return `${Math.floor(diff / day)}d ago`
  }

  getVoteStatusClass(status) {
    const statusMap = {
      draft: 'draft',
      active: 'active',
      closed: 'closed',
      completed: 'completed'
    }
    return statusMap[status] || 'unknown'
  }

  getVoteStatusIcon(status) {
    const iconMap = {
      draft: 'edit',
      active: 'trending_up',
      closed: 'archive',
      completed: 'check_circle'
    }
    return iconMap[status] || 'help'
  }

  getNotificationIcon(type) {
    const iconMap = {
      vote_created: 'how_to_vote',
      vote_closed: 'archive',
      new_response: 'person_add',
      system: 'info',
      warning: 'warning',
      error: 'error'
    }
    return iconMap[type] || 'notifications'
  }

  createEmptyState(icon, title, description) {
    return `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <span class="material-icons">${icon}</span>
                </div>
                <h3 class="md-headline-small">${title}</h3>
                <p class="md-body-medium md-on-surface-variant">${description}</p>
            </div>
        `
  }

  updateURL(section) {
    const url = new URL(window.location)
    url.hash = section
    window.history.replaceState({}, '', url)
  }

  debounce(func, wait) {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  }

  showLoadingState() {
    const overlay = document.getElementById('loadingOverlay')
    if (overlay) overlay.style.display = 'flex'
  }

  hideLoadingState() {
    const overlay = document.getElementById('loadingOverlay')
    if (overlay) overlay.style.display = 'none'
  }

  showRefreshIndicator() {
    const refreshBtn = document.getElementById('refreshDashboard')
    if (refreshBtn) {
      const icon = refreshBtn.querySelector('.material-icons')
      if (icon) {
        icon.classList.add('rotating')
      }
    }
  }

  hideRefreshIndicator() {
    const refreshBtn = document.getElementById('refreshDashboard')
    if (refreshBtn) {
      const icon = refreshBtn.querySelector('.material-icons')
      if (icon) {
        icon.classList.remove('rotating')
      }
    }
  }

  showSnackbar(message, type = 'info') {
    const snackbar = document.getElementById('snackbar')
    const messageElement = document.getElementById('snackbar-message')

    if (snackbar && messageElement) {
      messageElement.textContent = message
      snackbar.className = `md-snackbar ${type}`
      snackbar.classList.add('md-snackbar-open')

      // Auto-hide after 5 seconds
      setTimeout(() => {
        this.hideSnackbar()
      }, 5000)
    }
  }

  hideSnackbar() {
    const snackbar = document.getElementById('snackbar')
    if (snackbar) {
      snackbar.classList.remove('md-snackbar-open')
    }
  }

  /**
   * Cleanup method
   */
  cleanup() {
    this.stopAutoRefresh()

    // Remove event listeners
    this.eventHandlers.forEach(({ element, event, handler }) => {
      element.removeEventListener(event, handler)
    })
    this.eventHandlers.clear()
  }

  /**
   * View vote method (called from templates)
   */
  viewVote(voteId) {
    window.open(`/vote/${voteId}`, '_blank')
  }

  /**
   * Update recent activity section
   */
  updateRecentActivity(activityData) {
    console.log('Updating recent activity:', activityData)

    // This method handles updating the recent activity display
    // For now, just log the data - can be enhanced later
    if (activityData && Object.keys(activityData).length > 0) {
      console.log('Recent activity data received:', activityData)
    }
  }

  /**
   * Load user management section
   */
  async loadUserManagement() {
    console.log('Loading user management section...')

    try {
      const response = await this.apiRequest('/admin/users')
      console.log('User management data loaded:', response)

      // Update the main content area with user management interface
      const mainContent = document.querySelector('.dashboard-main-content')
      if (mainContent) {
        mainContent.innerHTML = `
                    <div class="user-management-section">
                        <h2>User Management</h2>
                        <p>User management functionality will be implemented here.</p>
                        <div class="user-list">
                            <!-- User list will be populated here -->
                        </div>
                    </div>
                `
      }
    } catch (error) {
      console.error('Error loading user management:', error)
      this.showSnackbar('Failed to load user management data', 'error')
    }
  }
}

// Export for use in other modules
window.DashboardController = DashboardController
