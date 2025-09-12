/**
 * Admin Authentication and JWT Management
 * Handles JWT token management and logout functionality for super admin interface
 */

// JWT token management for API calls
window.apiConfig = {
  baseURL: '/api/admin',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${localStorage.getItem('jwt_token') || ''}`
  }
}

// Create authenticated fetch wrapper instead of overriding global fetch
function authenticatedFetch(url, options = {}) {
  const token = localStorage.getItem('jwt_token')
  if (token && !options.headers?.Authorization) {
    options.headers = {
      ...options.headers,
      Authorization: `Bearer ${token}`
    }
  }
  return fetch(url, options)
}

// Make authenticated fetch available globally
window.authenticatedFetch = authenticatedFetch

// Handle authentication errors
// Used by admin templates (e.g., moderation.html) - ignore ESLint unused warning
// eslint-disable-next-line no-unused-vars
function handleAuthError(response) {
  if (response.status === 401) {
    localStorage.removeItem('jwt_token')
    window.location.href = '/login'
    return true
  }
  return false
}

// Logout functionality (only attach if logout button exists)
document.addEventListener('DOMContentLoaded', function () {
  const logoutBtn = document.getElementById('logoutBtn')
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async function () {
      if (confirm('Are you sure you want to logout?')) {
        try {
          // Clear JWT token
          localStorage.removeItem('jwt_token')

          // Redirect to login
          window.location.href = '/login'
        } catch (error) {
          console.error('Logout error:', error)
          // Use safe message creation instead of showMessage function
          if (window.AdminUtils && window.AdminUtils.showMessage) {
            window.AdminUtils.showMessage('Error during logout', 'error')
          } else {
            // Fallback: create message element safely
            const messageContainer = document.getElementById('messageContainer')
            if (messageContainer) {
              const messageElement = window.HTMLSanitizer.createMessageElement('Error during logout', 'error')
              messageContainer.appendChild(messageElement)
            }
          }
        }
      }
    })
  }
})
