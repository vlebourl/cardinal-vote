/**
 * Real-time Client - Handles real-time updates using Server-Sent Events (SSE)
 * Provides live updates for dashboard data, notifications, and vote activity
 */

class RealtimeClient {
  constructor() {
    this.eventSource = null
    this.isConnected = false
    this.reconnectInterval = null
    this.reconnectDelay = 5000 // 5 seconds
    this.maxReconnectDelay = 30000 // 30 seconds
    this.currentReconnectDelay = this.reconnectDelay
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10

    // Event listeners storage
    this.eventListeners = new Map()

    // Connection state
    this.connectionState = 'disconnected' // 'disconnected', 'connecting', 'connected', 'error'

    // Heartbeat
    this.heartbeatInterval = null
    this.lastHeartbeat = null
    this.heartbeatTimeout = 30000 // 30 seconds

    // Statistics
    this.stats = {
      messagesReceived: 0,
      reconnectCount: 0,
      lastConnected: null,
      totalUptime: 0
    }

    this.setupConnectionHandlers()
  }

  /**
   * Initialize real-time connection
   */
  async init() {
    try {
      await this.connect()
      this.startHeartbeat()
      this.updateConnectionStatus()
      console.log('RealtimeClient initialized successfully')
    } catch (error) {
      console.error('Failed to initialize RealtimeClient:', error)
      this.scheduleReconnect()
    }
  }

  /**
   * Connect to SSE endpoint
   */
  async connect() {
    if (this.eventSource && this.eventSource.readyState !== EventSource.CLOSED) {
      this.disconnect()
    }

    this.connectionState = 'connecting'
    this.updateConnectionStatus()

    try {
      const token = this.getToken()
      if (!token) {
        throw new Error('No authentication token available')
      }

      // Create SSE connection with authentication
      const sseUrl = `/api/sse/dashboard?token=${encodeURIComponent(token)}`
      this.eventSource = new EventSource(sseUrl)

      this.setupEventSourceHandlers()

      // Wait for connection to be established
      await this.waitForConnection()

      this.isConnected = true
      this.connectionState = 'connected'
      this.reconnectAttempts = 0
      this.currentReconnectDelay = this.reconnectDelay
      this.stats.lastConnected = new Date()

      this.updateConnectionStatus()
      this.notifyListeners('connection', { status: 'connected' })

      console.log('Real-time connection established')
    } catch (error) {
      this.connectionState = 'error'
      this.updateConnectionStatus()
      console.error('Failed to connect to real-time service:', error)
      throw error
    }
  }

  /**
   * Setup EventSource event handlers
   */
  setupEventSourceHandlers() {
    if (!this.eventSource) return

    this.eventSource.onopen = _event => {
      console.log('SSE connection opened')
      this.isConnected = true
      this.connectionState = 'connected'
      this.updateConnectionStatus()
    }

    this.eventSource.onerror = event => {
      console.error('SSE connection error:', event)
      this.handleConnectionError()
    }

    this.eventSource.onmessage = event => {
      this.handleMessage(event)
    }

    // Specific event handlers
    this.eventSource.addEventListener('dashboard_update', event => {
      this.handleDashboardUpdate(event)
    })

    this.eventSource.addEventListener('vote_update', event => {
      this.handleVoteUpdate(event)
    })

    this.eventSource.addEventListener('notification', event => {
      this.handleNotification(event)
    })

    this.eventSource.addEventListener('user_activity', event => {
      this.handleUserActivity(event)
    })

    this.eventSource.addEventListener('system_alert', event => {
      this.handleSystemAlert(event)
    })

    this.eventSource.addEventListener('heartbeat', event => {
      this.handleHeartbeat(event)
    })
  }

  /**
   * Handle incoming messages
   */
  handleMessage(event) {
    try {
      this.stats.messagesReceived++
      const data = JSON.parse(event.data)

      console.log('Received real-time message:', data)

      // Route message to appropriate handler
      switch (data.type) {
        case 'dashboard_stats':
          this.handleDashboardStatsUpdate(data)
          break
        case 'vote_response':
          this.handleVoteResponseUpdate(data)
          break
        case 'user_notification':
          this.handleUserNotificationUpdate(data)
          break
        default:
          console.log('Unknown message type:', data.type)
      }
    } catch (error) {
      console.error('Failed to handle real-time message:', error)
    }
  }

  /**
   * Handle dashboard updates
   */
  handleDashboardUpdate(event) {
    try {
      const data = JSON.parse(event.data)
      console.log('Dashboard update received:', data)

      // Update dashboard controller if available
      if (window.dashboardController) {
        window.dashboardController.handleRealtimeUpdate('dashboard', data)
      }

      this.notifyListeners('dashboard_update', data)
    } catch (error) {
      console.error('Failed to handle dashboard update:', error)
    }
  }

  /**
   * Handle vote updates
   */
  handleVoteUpdate(event) {
    try {
      const data = JSON.parse(event.data)
      console.log('Vote update received:', data)

      // Update vote manager if available
      if (window.voteManager) {
        window.voteManager.handleRealtimeUpdate(data)
      }

      // Update dashboard if showing votes
      if (window.dashboardController) {
        window.dashboardController.handleRealtimeUpdate('vote', data)
      }

      this.notifyListeners('vote_update', data)

      // Show notification for important vote updates
      if (data.event_type === 'vote_closed' || data.event_type === 'vote_published') {
        this.showRealtimeNotification(data)
      }
    } catch (error) {
      console.error('Failed to handle vote update:', error)
    }
  }

  /**
   * Handle notifications
   */
  handleNotification(event) {
    try {
      const data = JSON.parse(event.data)
      console.log('Notification received:', data)

      // Update dashboard notification count
      if (window.dashboardController) {
        window.dashboardController.handleRealtimeUpdate('notification', data)
      }

      this.notifyListeners('notification', data)

      // Show browser notification if permission granted
      this.showBrowserNotification(data)
    } catch (error) {
      console.error('Failed to handle notification:', error)
    }
  }

  /**
   * Handle user activity updates
   */
  handleUserActivity(event) {
    try {
      const data = JSON.parse(event.data)
      console.log('User activity update received:', data)

      // Update activity feed if visible
      if (window.dashboardController) {
        window.dashboardController.handleRealtimeUpdate('activity', data)
      }

      this.notifyListeners('user_activity', data)
    } catch (error) {
      console.error('Failed to handle user activity update:', error)
    }
  }

  /**
   * Handle system alerts (admin only)
   */
  handleSystemAlert(event) {
    try {
      const data = JSON.parse(event.data)
      console.log('System alert received:', data)

      // Only handle if user is admin
      const currentUser = window.dashboardController?.currentUser
      if (currentUser?.is_super_admin) {
        if (window.adminDashboard) {
          window.adminDashboard.handleSystemAlert(data)
        }

        this.showSystemAlert(data)
      }

      this.notifyListeners('system_alert', data)
    } catch (error) {
      console.error('Failed to handle system alert:', error)
    }
  }

  /**
   * Handle heartbeat
   */
  handleHeartbeat(_event) {
    this.lastHeartbeat = new Date()
    this.stats.totalUptime = Date.now() - (this.stats.lastConnected?.getTime() || 0)

    // Optional: Update connection status indicator
    this.updateConnectionHeartbeat()
  }

  /**
   * Handle dashboard stats updates
   */
  handleDashboardStatsUpdate(data) {
    if (window.dashboardController && data.stats) {
      window.dashboardController.updateQuickStats(data.stats)
    }
  }

  /**
   * Handle vote response updates
   */
  handleVoteResponseUpdate(data) {
    if (data.vote_id && window.voteManager) {
      window.voteManager.updateVoteResponseCount(data.vote_id, data.response_count)
    }
  }

  /**
   * Handle user notification updates
   */
  handleUserNotificationUpdate(data) {
    if (window.dashboardController) {
      window.dashboardController.addNotification(data.notification)
    }
  }

  /**
   * Show real-time notification
   */
  showRealtimeNotification(data) {
    if (window.dashboardController) {
      const message = this.formatNotificationMessage(data)
      window.dashboardController.showSnackbar(message, 'info')
    }
  }

  /**
   * Show browser notification
   */
  showBrowserNotification(data) {
    if (!('Notification' in window)) return

    if (Notification.permission === 'granted') {
      const notification = new Notification(data.title || 'Cardinal Vote', {
        body: data.message || 'You have a new notification',
        icon: '/static/icons/notification-icon.png',
        tag: data.id || 'general',
        requireInteraction: false
      })

      // Auto-close after 5 seconds
      setTimeout(() => {
        notification.close()
      }, 5000)

      // Handle click
      notification.onclick = () => {
        window.focus()
        notification.close()

        // Navigate to relevant section if specified
        if (data.action_url && window.dashboardController) {
          window.location.href = data.action_url
        }
      }
    }
  }

  /**
   * Show system alert (admin only)
   */
  showSystemAlert(data) {
    if (window.dashboardController) {
      const message = `System Alert: ${data.message}`
      window.dashboardController.showSnackbar(message, data.severity || 'warning')
    }
  }

  /**
   * Format notification message
   */
  formatNotificationMessage(data) {
    switch (data.event_type) {
      case 'vote_closed':
        return `Vote "${data.vote_title}" has been closed`
      case 'vote_published':
        return `Vote "${data.vote_title}" is now live`
      case 'new_response':
        return `New response received for "${data.vote_title}"`
      default:
        return data.message || 'New update available'
    }
  }

  /**
   * Wait for connection to be established
   */
  waitForConnection(timeout = 10000) {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new Error('Connection timeout'))
      }, timeout)

      const checkConnection = () => {
        if (this.eventSource?.readyState === EventSource.OPEN) {
          clearTimeout(timeoutId)
          resolve()
        } else if (this.eventSource?.readyState === EventSource.CLOSED) {
          clearTimeout(timeoutId)
          reject(new Error('Connection failed'))
        } else {
          // Still connecting, check again
          setTimeout(checkConnection, 100)
        }
      }

      checkConnection()
    })
  }

  /**
   * Handle connection error
   */
  handleConnectionError() {
    this.isConnected = false
    this.connectionState = 'error'
    this.updateConnectionStatus()

    console.log('Real-time connection error, attempting to reconnect...')
    this.scheduleReconnect()
  }

  /**
   * Schedule reconnection
   */
  scheduleReconnect() {
    if (this.reconnectInterval) {
      clearTimeout(this.reconnectInterval)
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached, giving up')
      this.connectionState = 'failed'
      this.updateConnectionStatus()
      return
    }

    this.reconnectAttempts++
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${this.currentReconnectDelay}ms`)

    this.reconnectInterval = setTimeout(() => {
      this.reconnect()
    }, this.currentReconnectDelay)

    // Exponential backoff
    this.currentReconnectDelay = Math.min(this.currentReconnectDelay * 2, this.maxReconnectDelay)
  }

  /**
   * Reconnect to real-time service
   */
  async reconnect() {
    this.stats.reconnectCount++

    try {
      await this.connect()
      console.log('Real-time connection restored')
    } catch (error) {
      console.error('Reconnection failed:', error)
      this.scheduleReconnect()
    }
  }

  /**
   * Disconnect from real-time service
   */
  disconnect() {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }

    if (this.reconnectInterval) {
      clearTimeout(this.reconnectInterval)
      this.reconnectInterval = null
    }

    this.stopHeartbeat()

    this.isConnected = false
    this.connectionState = 'disconnected'
    this.updateConnectionStatus()

    this.notifyListeners('connection', { status: 'disconnected' })

    console.log('Real-time connection closed')
  }

  /**
   * Start heartbeat monitoring
   */
  startHeartbeat() {
    this.stopHeartbeat()

    this.heartbeatInterval = setInterval(() => {
      const now = new Date()
      const timeSinceLastHeartbeat = now - (this.lastHeartbeat || this.stats.lastConnected || now)

      if (timeSinceLastHeartbeat > this.heartbeatTimeout) {
        console.warn('Heartbeat timeout, reconnecting...')
        this.handleConnectionError()
      }
    }, 10000) // Check every 10 seconds
  }

  /**
   * Stop heartbeat monitoring
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  /**
   * Setup connection state handlers
   */
  setupConnectionHandlers() {
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // Page is hidden, we might want to reduce activity
        console.log('Page hidden, maintaining connection')
      } else {
        // Page is visible again, ensure connection is active
        console.log('Page visible, checking connection')
        if (!this.isConnected) {
          this.reconnect()
        }
      }
    })

    // Handle online/offline events
    window.addEventListener('online', () => {
      console.log('Network online, reconnecting...')
      if (!this.isConnected) {
        this.reconnect()
      }
    })

    window.addEventListener('offline', () => {
      console.log('Network offline')
      this.disconnect()
    })
  }

  /**
   * Update connection status in UI
   */
  updateConnectionStatus() {
    // Update connection indicator if it exists
    const indicator = document.getElementById('connectionIndicator')
    if (indicator) {
      indicator.className = `connection-indicator ${this.connectionState}`
      indicator.title = this.getConnectionStatusText()
    }

    // Update admin health indicator if available
    const healthDot = document.getElementById('navHealthDot')
    if (healthDot) {
      healthDot.className = `health-status-dot ${this.connectionState === 'connected' ? 'healthy' : 'warning'}`
    }
  }

  /**
   * Update connection heartbeat indicator
   */
  updateConnectionHeartbeat() {
    const indicator = document.getElementById('connectionIndicator')
    if (indicator) {
      indicator.classList.add('heartbeat')
      setTimeout(() => {
        indicator.classList.remove('heartbeat')
      }, 200)
    }
  }

  /**
   * Get connection status text
   */
  getConnectionStatusText() {
    switch (this.connectionState) {
      case 'connected':
        return 'Real-time updates active'
      case 'connecting':
        return 'Connecting to real-time updates...'
      case 'error':
        return 'Connection error, retrying...'
      case 'failed':
        return 'Real-time updates unavailable'
      default:
        return 'Real-time updates disconnected'
    }
  }

  /**
   * Event listener management
   */
  addEventListener(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, [])
    }
    this.eventListeners.get(event).push(callback)
  }

  removeEventListener(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event)
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  notifyListeners(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error)
        }
      })
    }
  }

  /**
   * Request browser notification permission
   */
  async requestNotificationPermission() {
    if (!('Notification' in window)) {
      console.warn('Browser notifications not supported')
      return false
    }

    if (Notification.permission === 'granted') {
      return true
    }

    if (Notification.permission === 'denied') {
      return false
    }

    const permission = await Notification.requestPermission()
    return permission === 'granted'
  }

  /**
   * Get authentication token
   */
  getToken() {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  }

  /**
   * Get connection statistics
   */
  getStats() {
    return {
      ...this.stats,
      isConnected: this.isConnected,
      connectionState: this.connectionState,
      reconnectAttempts: this.reconnectAttempts
    }
  }

  /**
   * Get connection health info
   */
  getHealthInfo() {
    return {
      connected: this.isConnected,
      state: this.connectionState,
      lastHeartbeat: this.lastHeartbeat,
      reconnectAttempts: this.reconnectAttempts,
      messagesReceived: this.stats.messagesReceived,
      uptime: this.stats.totalUptime
    }
  }

  /**
   * Force reconnection
   */
  forceReconnect() {
    console.log('Forcing reconnection...')
    this.disconnect()
    setTimeout(() => {
      this.connect()
    }, 1000)
  }

  /**
   * Cleanup method
   */
  cleanup() {
    this.disconnect()
    this.eventListeners.clear()

    // Remove document event listeners
    document.removeEventListener('visibilitychange', this.handleVisibilityChange)
    window.removeEventListener('online', this.handleOnline)
    window.removeEventListener('offline', this.handleOffline)
  }
}

// Export for use in other modules
window.RealtimeClient = RealtimeClient
