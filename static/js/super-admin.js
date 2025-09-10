/**
 * Super Admin JavaScript for Cardinal Vote Platform
 * Provides specialized functionality for super admin operations
 */

// Super Admin API utilities
window.SuperAdminAPI = {
  baseURL: '/api/admin',

  // Get JWT token from localStorage
  getAuthHeaders: function () {
    const token = localStorage.getItem('jwt_token')
    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token || ''}`
    }
  },

  // Generic API call wrapper
  async call (endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const config = {
      headers: this.getAuthHeaders(),
      ...options
    }

    const response = await fetch(url, config)

    // Handle authentication errors
    if (response.status === 401) {
      localStorage.removeItem('jwt_token')
      window.location.href = '/login'
      return null
    }

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`)
    }

    return response.json()
  },

  // System statistics
  async getStats () {
    return this.call('/stats')
  },

  async getComprehensiveStats () {
    return this.call('/comprehensive-stats')
  },

  // User management
  async getUsers (page = 1, limit = 20, search = '') {
    const params = new URLSearchParams({ page: page.toString(), limit: limit.toString() })
    if (search) params.append('search', search)
    return this.call(`/users?${params}`)
  },

  async getUserDetails (userId) {
    return this.call(`/users/${userId}`)
  },

  async updateUser (userId, data) {
    return this.call('/users/manage', {
      method: 'POST',
      body: JSON.stringify({
        operation: 'update_user',
        user_id: userId,
        ...data
      })
    })
  },

  async bulkUpdateUsers (userIds, operation, data = {}) {
    return this.call('/users/bulk-update', {
      method: 'POST',
      body: JSON.stringify({
        user_ids: userIds,
        operation,
        ...data
      })
    })
  },

  // Activity and monitoring
  async getRecentActivity (limit = 20) {
    return this.call(`/recent-activity?limit=${limit}`)
  },

  async getUserSummary () {
    return this.call('/user-summary')
  },

  async getAuditLog (limit = 50) {
    return this.call(`/audit-log?limit=${limit}`)
  },

  // Content moderation
  async getModerationStats () {
    return this.call('/moderation/dashboard')
  },

  async getPendingFlags (limit = 50, offset = 0) {
    const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() })
    return this.call(`/moderation/flags?${params}`)
  },

  async reviewFlag (flagId, status, reviewNotes) {
    return this.call(`/moderation/flags/${flagId}/review`, {
      method: 'POST',
      body: JSON.stringify({
        status,
        review_notes: reviewNotes
      })
    })
  },

  async getFlaggedVotes (limit = 20, offset = 0, flagStatus = null) {
    const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() })
    if (flagStatus) params.append('flag_status', flagStatus)
    return this.call(`/moderation/votes?${params}`)
  },

  async getVoteModerationSummary (voteId) {
    return this.call(`/moderation/votes/${voteId}`)
  },

  async takeModerationAction (voteId, actionType, reason, additionalData = {}) {
    return this.call(`/moderation/votes/${voteId}/action`, {
      method: 'POST',
      body: JSON.stringify({
        action_type: actionType,
        reason,
        additional_data: additionalData
      })
    })
  },

  async bulkModerationAction (voteIds, actionType, reason) {
    return this.call('/moderation/bulk-action', {
      method: 'POST',
      body: JSON.stringify({
        vote_ids: voteIds,
        action_type: actionType,
        reason
      })
    })
  }
}

// Super Admin utilities extending AdminUtils
window.SuperAdminUtils = {
  ...window.AdminUtils,

  // Enhanced user management functions
  async verifyUsers (userIds) {
    try {
      showLoading()
      const result = await SuperAdminAPI.bulkUpdateUsers(userIds, 'verify_users')
      if (result.success) {
        showMessage(result.message, 'success')
        return true
      } else {
        showMessage(result.message || 'Failed to verify users', 'error')
        return false
      }
    } catch (error) {
      console.error('Error verifying users:', error)
      showMessage('Error verifying users', 'error')
      return false
    } finally {
      hideLoading()
    }
  },

  async unverifyUsers (userIds) {
    try {
      showLoading()
      const result = await SuperAdminAPI.bulkUpdateUsers(userIds, 'unverify_users')
      if (result.success) {
        showMessage(result.message, 'success')
        return true
      } else {
        showMessage(result.message || 'Failed to unverify users', 'error')
        return false
      }
    } catch (error) {
      console.error('Error unverifying users:', error)
      showMessage('Error unverifying users', 'error')
      return false
    } finally {
      hideLoading()
    }
  },

  // Platform health monitoring
  updatePlatformHealth: function (health) {
    if (!health) return

    const indicator = document.getElementById('healthIndicator')
    if (indicator) {
      const statusClass =
        health.status === 'healthy'
          ? 'status-healthy'
          : health.status === 'warning'
            ? 'status-warning'
            : 'status-critical'

      indicator.innerHTML = `
                <span class="status-dot ${statusClass}"></span>
                <span class="status-text">${health.status}</span>
            `
    }
  },

  // Export system data
  exportData: function (data, filename, format = 'json') {
    let content, mimeType

    if (format === 'json') {
      content = JSON.stringify(data, null, 2)
      mimeType = 'application/json'
    } else if (format === 'csv') {
      content = this.convertToCSV(data)
      mimeType = 'text/csv'
    } else {
      console.error('Unsupported export format:', format)
      return
    }

    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    showMessage(`Data exported successfully as ${format.toUpperCase()}`, 'success')
  },

  // Convert data to CSV format
  convertToCSV: function (data) {
    if (!Array.isArray(data) || data.length === 0) {
      return ''
    }

    const headers = Object.keys(data[0])
    const csvRows = [headers.join(',')]

    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header]
        // Escape quotes and wrap in quotes if necessary
        if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
          return `"${value.replace(/"/g, '""')}"`
        }
        return value
      })
      csvRows.push(values.join(','))
    }

    return csvRows.join('\n')
  },

  // Format date/time for display
  formatDateTime: function (dateString) {
    if (!dateString) return 'Unknown'

    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'Invalid Date'

    const now = new Date()
    const diff = now - date

    // Less than 1 minute ago
    if (diff < 60000) {
      return 'Just now'
    }

    // Less than 1 hour ago
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000)
      return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`
    }

    // Less than 24 hours ago
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000)
      return `${hours} hour${hours !== 1 ? 's' : ''} ago`
    }

    // Less than 7 days ago
    if (diff < 604800000) {
      const days = Math.floor(diff / 86400000)
      return `${days} day${days !== 1 ? 's' : ''} ago`
    }

    // More than 7 days ago
    return date.toLocaleDateString()
  },

  // Format numbers with commas
  formatNumber: function (num) {
    return new Intl.NumberFormat().format(num)
  },

  // Validate email address
  isValidEmail: function (email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  },

  // Debounce function for search inputs
  debounce: function (func, wait) {
    let timeout
    return function executedFunction (...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  }
}

// Super Admin Dashboard Management
window.SuperAdminDashboard = {
  refreshInterval: null,

  // Initialize dashboard
  init: function () {
    this.loadInitialData()
    this.setupEventListeners()
    this.startAutoRefresh()
  },

  // Load all dashboard data
  loadInitialData: async function () {
    try {
      showLoading()

      await Promise.all([
        this.loadSystemStats(),
        this.loadPlatformHealth(),
        this.loadRecentActivity(),
        this.loadUserSummary()
      ])
    } catch (error) {
      console.error('Error loading dashboard data:', error)
      showMessage('Error loading dashboard data', 'error')
    } finally {
      hideLoading()
    }
  },

  // Load system statistics
  loadSystemStats: async function () {
    try {
      const stats = await SuperAdminAPI.getStats()
      this.updateStatsDisplay(stats)
    } catch (error) {
      console.error('Error loading system stats:', error)
    }
  },

  // Load platform health
  loadPlatformHealth: async function () {
    try {
      const data = await SuperAdminAPI.getComprehensiveStats()
      if (data.platform_health) {
        SuperAdminUtils.updatePlatformHealth(data.platform_health)
      }
    } catch (error) {
      console.error('Error loading platform health:', error)
    }
  },

  // Load recent activity
  loadRecentActivity: async function () {
    try {
      const activity = await SuperAdminAPI.getRecentActivity(10)
      this.updateActivityDisplay(activity)
    } catch (error) {
      console.error('Error loading recent activity:', error)
      this.showActivityError()
    }
  },

  // Load user summary
  loadUserSummary: async function () {
    try {
      const summary = await SuperAdminAPI.getUserSummary()
      this.updateUserSummaryDisplay(summary)
    } catch (error) {
      console.error('Error loading user summary:', error)
      this.showUserSummaryError()
    }
  },

  // Update statistics display
  updateStatsDisplay: function (stats) {
    const elements = {
      totalUsers: stats.total_users || 0,
      totalVotes: stats.total_votes || 0,
      totalResponses: stats.total_responses || 0,
      superAdmins: stats.super_admins || 0,
      verifiedUsers: `${stats.verified_users || 0} verified`,
      activeVotes: `${stats.active_votes || 0} active`,
      responsesToday: `${stats.responses_today || 0} today`,
      usersToday: `${stats.users_created_today || 0} new today`
    }

    Object.entries(elements).forEach(([id, value]) => {
      const element = document.getElementById(id)
      if (element) {
        element.textContent = value
      }
    })
  },

  // Update activity display
  updateActivityDisplay: function (activity) {
    const container = document.getElementById('recentActivity')
    if (!container) return

    if (activity && activity.length > 0) {
      container.innerHTML = activity
        .map(
          item => `
                <div class="activity-item">
                    <div class="activity-icon">
                        <i class="fas ${item.event_type === 'user_registration' ? 'fa-user-plus' : 'fa-vote-yea'}"></i>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">${item.details}</div>
                        <div class="activity-meta">
                            <span class="activity-user">${item.user_email}</span>
                            <span class="activity-time">${SuperAdminUtils.formatDateTime(item.timestamp)}</span>
                        </div>
                    </div>
                </div>
            `
        )
        .join('')
    } else {
      container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>No recent activity</p>
                </div>
            `
    }
  },

  // Update user summary display
  updateUserSummaryDisplay: function (summary) {
    const container = document.getElementById('userSummary')
    if (!container) return

    container.innerHTML = `
            <div class="summary-stats">
                <div class="summary-stat">
                    <div class="stat-value">${SuperAdminUtils.formatNumber(summary.verified_users_count || 0)}</div>
                    <div class="stat-label">Verified Users</div>
                </div>
                <div class="summary-stat">
                    <div class="stat-value">${SuperAdminUtils.formatNumber(summary.unverified_users_count || 0)}</div>
                    <div class="stat-label">Pending Verification</div>
                </div>
                <div class="summary-stat">
                    <div class="stat-value">${SuperAdminUtils.formatNumber(summary.super_admins_count || 0)}</div>
                    <div class="stat-label">Super Admins</div>
                </div>
            </div>

            ${
  summary.most_active_users && summary.most_active_users.length > 0
    ? `
                <div class="active-users">
                    <h4>Most Active Users</h4>
                    <div class="user-list">
                        ${summary.most_active_users
    .map(
      user => `
                            <div class="user-item">
                                <span class="user-name">${user.first_name} ${user.last_name}</span>
                                <span class="user-votes">${SuperAdminUtils.formatNumber(user.vote_count)} votes</span>
                            </div>
                        `
    )
    .join('')}
                    </div>
                </div>
            `
    : ''
}
        `
  },

  // Show error states
  showActivityError: function () {
    const container = document.getElementById('recentActivity')
    if (container) {
      container.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading recent activity</p>
                </div>
            `
    }
  },

  showUserSummaryError: function () {
    const container = document.getElementById('userSummary')
    if (container) {
      container.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading user summary</p>
                </div>
            `
    }
  },

  // Setup event listeners
  setupEventListeners: function () {
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.stopAutoRefresh()
      } else {
        this.startAutoRefresh()
      }
    })

    // Handle window unload
    window.addEventListener('beforeunload', () => {
      this.stopAutoRefresh()
    })
  },

  // Auto-refresh functionality
  startAutoRefresh: function () {
    this.stopAutoRefresh() // Clear any existing interval

    this.refreshInterval = setInterval(async () => {
      try {
        await this.loadSystemStats()
        await this.loadPlatformHealth()
      } catch (error) {
        console.error('Auto-refresh error:', error)
      }
    }, 30000) // 30 seconds
  },

  stopAutoRefresh: function () {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
      this.refreshInterval = null
    }
  }
}

// Global utility functions for templates
function showLoading () {
  SuperAdminUtils.showLoading()
}

function hideLoading () {
  SuperAdminUtils.hideLoading()
}

function showMessage (message, type, duration) {
  SuperAdminUtils.showMessage(message, type, duration)
}

// Moderation Dashboard Management
window.ModerationDashboard = {
  currentTab: 'pending-flags',
  currentPage: 1,
  itemsPerPage: 20,

  // Initialize moderation dashboard
  init: function () {
    this.loadInitialData()
    this.setupEventListeners()
  },

  // Load initial moderation data
  loadInitialData: async function () {
    try {
      showLoading()
      await Promise.all([this.loadModerationStats(), this.loadCurrentTabData()])
    } catch (error) {
      console.error('Error loading moderation data:', error)
      showMessage('Error loading moderation data', 'error')
    } finally {
      hideLoading()
    }
  },

  // Load moderation statistics
  loadModerationStats: async function () {
    try {
      const stats = await SuperAdminAPI.getModerationStats()
      this.updateStatsDisplay(stats)
    } catch (error) {
      console.error('Error loading moderation stats:', error)
    }
  },

  // Update statistics display
  updateStatsDisplay: function (stats) {
    const elements = {
      pendingFlags: stats.pending_flags || 0,
      moderatedVotes: stats.total_moderated_votes || 0,
      weeklyActions: Object.values(stats.recent_actions_by_type || {}).reduce((sum, count) => sum + count, 0),
      disabledCount: stats.moderated_votes_by_status?.disabled || 0,
      hiddenCount: stats.moderated_votes_by_status?.hidden || 0,
      closedCount: stats.moderated_votes_by_status?.closed || 0
    }

    Object.entries(elements).forEach(([id, value]) => {
      const element = document.getElementById(id)
      if (element) {
        element.textContent = value
      }
    })

    // Update status indicators
    const flagsStatus = document.getElementById('flagsStatus')
    if (flagsStatus) {
      const pendingCount = stats.pending_flags || 0
      flagsStatus.textContent =
        pendingCount > 10 ? 'High priority' : pendingCount > 0 ? 'Requires attention' : 'All clear'
      flagsStatus.className =
        pendingCount > 10 ? 'stat-status urgent' : pendingCount > 0 ? 'stat-status warning' : 'stat-status normal'
    }
  },

  // Load data for current tab
  loadCurrentTabData: async function () {
    switch (this.currentTab) {
    case 'pending-flags':
      await this.loadPendingFlags()
      break
    case 'flagged-votes':
      await this.loadFlaggedVotes()
      break
    case 'moderation-log':
      await this.loadModerationLog()
      break
    case 'bulk-actions':
      await this.loadBulkActions()
      break
    }
  },

  // Load pending flags
  loadPendingFlags: async function () {
    try {
      const flags = await SuperAdminAPI.getPendingFlags(this.itemsPerPage, (this.currentPage - 1) * this.itemsPerPage)
      this.renderPendingFlags(flags)
    } catch (error) {
      console.error('Error loading pending flags:', error)
      this.showTabError('Error loading pending flags')
    }
  },

  // Load flagged votes
  loadFlaggedVotes: async function () {
    try {
      const votes = await SuperAdminAPI.getFlaggedVotes(this.itemsPerPage, (this.currentPage - 1) * this.itemsPerPage)
      this.renderFlaggedVotes(votes)
    } catch (error) {
      console.error('Error loading flagged votes:', error)
      this.showTabError('Error loading flagged votes')
    }
  },

  // Load moderation log
  loadModerationLog: async function () {
    try {
      // This would need a new API endpoint for moderation history
      this.renderModerationLog([])
    } catch (error) {
      console.error('Error loading moderation log:', error)
      this.showTabError('Error loading moderation log')
    }
  },

  // Load bulk actions interface
  loadBulkActions: async function () {
    this.renderBulkActions()
  },

  // Render pending flags
  renderPendingFlags: function (flags) {
    const container = document.getElementById('tabContent')
    if (!container || !flags) return

    if (flags.length === 0) {
      container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <h3>No Pending Flags</h3>
                    <p>All flags have been reviewed</p>
                </div>
            `
      return
    }

    container.innerHTML = `
            <div class="flags-list">
                ${flags
    .map(
      flag => `
                    <div class="flag-item" data-flag-id="${flag.id}">
                        <div class="flag-header">
                            <div class="flag-info">
                                <span class="flag-type ${flag.flag_type}">${flag.flag_type}</span>
                                <span class="flag-vote-title">${flag.vote_title}</span>
                                <span class="flag-date">${SuperAdminUtils.formatDateTime(flag.created_at)}</span>
                            </div>
                            <div class="flag-actions">
                                <button class="btn-approve" onclick="ModerationDashboard.reviewFlag('${flag.id}', 'approved')">
                                    <i class="fas fa-check"></i> Approve
                                </button>
                                <button class="btn-reject" onclick="ModerationDashboard.reviewFlag('${flag.id}', 'rejected')">
                                    <i class="fas fa-times"></i> Reject
                                </button>
                                <button class="btn-details" onclick="ModerationDashboard.showFlagDetails('${flag.id}')">
                                    <i class="fas fa-eye"></i> Details
                                </button>
                            </div>
                        </div>
                        <div class="flag-details">
                            <p><strong>Reason:</strong> ${flag.reason}</p>
                            <p><strong>Vote:</strong> <a href="/vote/${flag.vote_slug}" target="_blank">${flag.vote_slug}</a></p>
                            <p><strong>Creator:</strong> ${flag.creator_email}</p>
                            <p><strong>Flagger:</strong> ${flag.flagger_email}</p>
                        </div>
                    </div>
                `
    )
    .join('')}
            </div>
        `
  },

  // Review flag
  reviewFlag: async function (flagId, status) {
    const reviewNotes = prompt(`Enter review notes for this ${status} action:`)
    if (reviewNotes === null) return

    try {
      showLoading()
      const result = await SuperAdminAPI.reviewFlag(flagId, status, reviewNotes)
      if (result.success) {
        showMessage(`Flag ${status} successfully`, 'success')
        await this.loadCurrentTabData()
        await this.loadModerationStats()
      } else {
        showMessage(result.message || `Failed to ${status} flag`, 'error')
      }
    } catch (error) {
      console.error('Error reviewing flag:', error)
      showMessage('Error reviewing flag', 'error')
    } finally {
      hideLoading()
    }
  },

  // Show tab error
  showTabError: function (message) {
    const container = document.getElementById('tabContent')
    if (container) {
      container.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error</h3>
                    <p>${message}</p>
                    <button onclick="ModerationDashboard.loadCurrentTabData()" class="btn-retry">
                        <i class="fas fa-refresh"></i> Retry
                    </button>
                </div>
            `
    }
  },

  // Render flagged votes
  renderFlaggedVotes: function (votes) {
    const container = document.getElementById('tabContent')
    if (!container || !votes) return

    if (votes.length === 0) {
      container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-shield-alt"></i>
                    <h3>No Flagged Votes</h3>
                    <p>No votes have been flagged for review</p>
                </div>
            `
      return
    }

    container.innerHTML = `
            <div class="votes-list">
                ${votes
    .map(
      vote => `
                    <div class="vote-item" data-vote-id="${vote.id}">
                        <div class="vote-header">
                            <div class="vote-info">
                                <h4>${vote.title}</h4>
                                <span class="vote-status status-${vote.status}">${vote.status}</span>
                                <span class="vote-flags">${vote.total_flags} flag(s)</span>
                            </div>
                            <div class="vote-actions">
                                <button class="btn-view" onclick="window.open('/vote/${vote.slug}', '_blank')">
                                    <i class="fas fa-external-link-alt"></i> View Vote
                                </button>
                                <button class="btn-moderate" onclick="ModerationDashboard.showModerationActions('${vote.id}')">
                                    <i class="fas fa-gavel"></i> Moderate
                                </button>
                            </div>
                        </div>
                        <div class="vote-details">
                            <p><strong>Creator:</strong> ${vote.creator_email}</p>
                            <p><strong>Created:</strong> ${SuperAdminUtils.formatDateTime(vote.created_at)}</p>
                            <p><strong>Options:</strong> ${vote.total_options} | <strong>Responses:</strong> ${vote.total_responses}</p>
                            <div class="flag-summary">
                                ${Object.entries(vote.flag_counts)
    .map(
      ([status, count]) =>
        `<span class="flag-count flag-${status}">${status}: ${count}</span>`
    )
    .join('')}
                            </div>
                        </div>
                    </div>
                `
    )
    .join('')}
            </div>
        `
  },

  // Render moderation log
  renderModerationLog: function (_actions) {
    const container = document.getElementById('tabContent')
    if (!container) return

    container.innerHTML = `
            <div class="moderation-log">
                <div class="log-header">
                    <h3>Recent Moderation Actions</h3>
                    <p>Track all moderation decisions and actions taken</p>
                </div>
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h3>Moderation Log</h3>
                    <p>Coming soon - Complete audit trail of all moderation actions</p>
                </div>
            </div>
        `
  },

  // Render bulk actions interface
  renderBulkActions: function () {
    const container = document.getElementById('tabContent')
    if (!container) return

    container.innerHTML = `
            <div class="bulk-actions">
                <div class="bulk-header">
                    <h3>Bulk Moderation Actions</h3>
                    <p>Perform actions on multiple votes at once</p>
                </div>

                <form id="bulkActionForm" class="bulk-form">
                    <div class="form-group">
                        <label for="vote_ids">Vote IDs (comma-separated):</label>
                        <textarea id="vote_ids" name="vote_ids" rows="3" placeholder="Enter vote IDs separated by commas..."></textarea>
                        <small>Example: abc123-def456, ghi789-jkl012</small>
                    </div>

                    <div class="form-group">
                        <label for="action_type">Action:</label>
                        <select id="action_type" name="action_type" required>
                            <option value="">Select action...</option>
                            <option value="close_vote">Close Votes</option>
                            <option value="disable_vote">Disable Votes</option>
                            <option value="hide_vote">Hide Votes</option>
                            <option value="restore_vote">Restore Votes</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="reason">Reason:</label>
                        <textarea id="reason" name="reason" rows="2" placeholder="Explain why this action is being taken..." required></textarea>
                    </div>

                    <div class="form-actions">
                        <button type="submit" class="btn-primary">
                            <i class="fas fa-play"></i> Execute Bulk Action
                        </button>
                        <button type="reset" class="btn-secondary">
                            <i class="fas fa-times"></i> Clear Form
                        </button>
                    </div>
                </form>

                <div class="bulk-help">
                    <h4>Bulk Action Guidelines:</h4>
                    <ul>
                        <li>Maximum 50 votes per bulk operation</li>
                        <li>Actions are permanent and logged for audit</li>
                        <li>Use "Close" for votes that should end naturally</li>
                        <li>Use "Disable" for policy violations</li>
                        <li>Use "Hide" for content that needs removal</li>
                        <li>Use "Restore" to reactivate disabled/hidden votes</li>
                    </ul>
                </div>
            </div>
        `
  },

  // Show moderation actions modal/interface (called from renderFlaggedVotes)
  showModerationActions: function (voteId) {
    // Simple implementation - could be enhanced with a modal
    const actions = ['close_vote', 'disable_vote', 'hide_vote', 'restore_vote']
    const actionType = prompt(`Choose action for vote ${voteId}:\n${actions.join(', ')}`)

    if (actionType && actions.includes(actionType)) {
      const reason = prompt(`Enter reason for ${actionType}:`)
      if (reason) {
        this.executeModerationAction(voteId, actionType, reason)
      }
    }
  },

  // Execute moderation action
  executeModerationAction: async function (voteId, actionType, reason) {
    try {
      showLoading()
      const result = await SuperAdminAPI.takeModerationAction(voteId, actionType, reason)
      if (result.success) {
        showMessage(`Action '${actionType}' applied successfully`, 'success')
        await this.loadCurrentTabData()
        await this.loadModerationStats()
      } else {
        showMessage(result.message || 'Action failed', 'error')
      }
    } catch (error) {
      console.error('Error executing moderation action:', error)
      showMessage('Error executing moderation action', 'error')
    } finally {
      hideLoading()
    }
  },

  // Setup event listeners
  setupEventListeners: function () {
    // Handle bulk action form if it exists
    const bulkForm = document.getElementById('bulkActionForm')
    if (bulkForm) {
      bulkForm.addEventListener('submit', this.handleBulkAction.bind(this))
    }
  },

  // Handle bulk action
  handleBulkAction: async function (event) {
    event.preventDefault()
    const formData = new FormData(event.target)
    const actionType = formData.get('action_type')
    const reason = formData.get('reason')
    const voteIds = formData
      .get('vote_ids')
      .split(',')
      .map(id => id.trim())
      .filter(id => id)

    if (!actionType || !reason || voteIds.length === 0) {
      showMessage('Please fill in all required fields', 'warning')
      return
    }

    try {
      showLoading()
      const result = await SuperAdminAPI.bulkModerationAction(voteIds, actionType, reason)
      if (result.success) {
        showMessage(
          `Bulk action completed: ${result.success_count} successful, ${result.error_count} failed`,
          'success'
        )
        event.target.reset()
      } else {
        showMessage(result.message || 'Bulk action failed', 'error')
      }
    } catch (error) {
      console.error('Error in bulk action:', error)
      showMessage('Error performing bulk action', 'error')
    } finally {
      hideLoading()
    }
  }
}

// Tab switching function (called by moderation template)
function switchTab (tabName) {
  // Update active tab button
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active')
  })
  document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active')

  // Update current tab and load data
  ModerationDashboard.currentTab = tabName
  ModerationDashboard.currentPage = 1
  ModerationDashboard.loadCurrentTabData()
}

// Export system statistics (used by dashboard template)
function exportSystemStats () {
  const data = window.dashboardData?.stats
  if (data) {
    SuperAdminUtils.exportData(data, 'system_stats', 'json')
  } else {
    showMessage('No data available to export', 'warning')
  }
}

// Open user management (used by dashboard template)
function openUserManagement () {
  window.location.href = '/api/admin/users'
}

// Bulk verify users (used by dashboard template)
function bulkVerifyUsers () {
  showMessage('Bulk verification feature coming soon', 'info')
}

// View audit log (used by dashboard template)
function viewAuditLog () {
  showMessage('Audit log feature coming soon', 'info')
}

// Initialize Super Admin Dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  // Only initialize if we're on a super admin page
  if (document.body.classList.contains('super-admin-body')) {
    SuperAdminDashboard.init()
  }

  // Initialize moderation dashboard if on moderation page
  if (document.body.classList.contains('moderation-page') || document.querySelector('.moderation-dashboard')) {
    ModerationDashboard.init()
  }
})

// Export for use in other modules
window.SuperAdminAPI = SuperAdminAPI
window.SuperAdminUtils = SuperAdminUtils
window.SuperAdminDashboard = SuperAdminDashboard
