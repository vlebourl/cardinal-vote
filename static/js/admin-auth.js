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

// Add authorization header to all fetch requests
const originalFetch = window.fetch
window.fetch = function (url, options = {}) {
  const token = localStorage.getItem('jwt_token')
  if (token && !options.headers?.Authorization) {
    options.headers = {
      ...options.headers,
      Authorization: `Bearer ${token}`
    }
  }
  return originalFetch(url, options)
}

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
          showMessage('Error during logout', 'error')
        }
      }
    })
  }
})
