/**
 * Admin JavaScript for Cardinal Vote Voting Platform
 * Provides common functionality for admin interface
 */

// Global admin utilities
window.AdminUtils = {
  // Message display system
  showMessage: function (message, type = 'info', duration = 5000) {
    const messageContainer = document.getElementById('messageContainer')
    if (!messageContainer) return

    const messageDiv = document.createElement('div')
    messageDiv.className = `message ${type}`

    let icon = 'fa-info-circle'
    if (type === 'success') icon = 'fa-check-circle'
    else if (type === 'error') icon = 'fa-exclamation-circle'

    messageDiv.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `

    messageContainer.appendChild(messageDiv)

    // Auto-remove message after duration
    setTimeout(() => {
      messageDiv.style.animation = 'slideOut 0.3s ease forwards'
      setTimeout(() => {
        if (messageDiv.parentNode) {
          messageDiv.parentNode.removeChild(messageDiv)
        }
      }, 300)
    }, duration)

    // Add click to dismiss
    messageDiv.addEventListener('click', () => {
      messageDiv.style.animation = 'slideOut 0.3s ease forwards'
      setTimeout(() => {
        if (messageDiv.parentNode) {
          messageDiv.parentNode.removeChild(messageDiv)
        }
      }, 300)
    })
  },

  // Loading overlay
  showLoading: function () {
    const overlay = document.getElementById('loadingOverlay')
    if (overlay) {
      overlay.classList.add('show')
    }
  },

  hideLoading: function () {
    const overlay = document.getElementById('loadingOverlay')
    if (overlay) {
      overlay.classList.remove('show')
    }
  },

  // Confirmation modal
  showConfirm: function (title, message, onConfirm, onCancel = null) {
    const modal = document.getElementById('confirmModal')
    const titleEl = document.getElementById('confirmTitle')
    const messageEl = document.getElementById('confirmMessage')
    const cancelBtn = document.getElementById('confirmCancel')
    const okBtn = document.getElementById('confirmOk')

    if (!modal) return

    titleEl.textContent = title
    messageEl.textContent = message

    modal.classList.add('show')

    // Event handlers
    const handleConfirm = () => {
      modal.classList.remove('show')
      if (onConfirm) onConfirm()
      cleanup()
    }

    const handleCancel = () => {
      modal.classList.remove('show')
      if (onCancel) onCancel()
      cleanup()
    }

    const cleanup = () => {
      okBtn.removeEventListener('click', handleConfirm)
      cancelBtn.removeEventListener('click', handleCancel)
      modal.removeEventListener('click', handleModalClick)
    }

    const handleModalClick = e => {
      if (e.target === modal) {
        handleCancel()
      }
    }

    okBtn.addEventListener('click', handleConfirm)
    cancelBtn.addEventListener('click', handleCancel)
    modal.addEventListener('click', handleModalClick)
  },

  // JWT helper
  getJwtToken: function () {
    return localStorage.getItem('jwt_token') || ''
  },

  // Fetch wrapper with JWT token
  fetchWithAuth: async function (url, options = {}) {
    const token = this.getJwtToken()
    const defaultOptions = {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    }

    const response = await fetch(url, { ...options, ...defaultOptions })

    // Handle authentication errors
    if (response.status === 401) {
      localStorage.removeItem('jwt_token')
      showMessage('Session expirée, redirection...', 'error')
      setTimeout(() => {
        window.location.href = '/login'
      }, 2000)
      return null
    }

    return response
  },

  // Format file size
  formatFileSize: function (bytes) {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  },

  // Format date
  formatDate: function (dateString) {
    const date = new Date(dateString)
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  },

  // Debounce function
  debounce: function (func, wait) {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  },

  // Form serialization
  serializeForm: function (form) {
    const formData = new FormData(form)
    const data = {}
    for (const [key, value] of formData.entries()) {
      if (data[key]) {
        if (Array.isArray(data[key])) {
          data[key].push(value)
        } else {
          data[key] = [data[key], value]
        }
      } else {
        data[key] = value
      }
    }
    return data
  },

  // URL parameter helpers
  getUrlParam: function (param) {
    const urlParams = new URLSearchParams(window.location.search)
    return urlParams.get(param)
  },

  setUrlParam: function (param, value) {
    const url = new URL(window.location)
    if (value) {
      url.searchParams.set(param, value)
    } else {
      url.searchParams.delete(param)
    }
    window.history.replaceState({}, '', url)
  }
}

// Make utilities available globally
window.showMessage = window.AdminUtils.showMessage
window.showLoading = window.AdminUtils.showLoading
window.hideLoading = window.AdminUtils.hideLoading
window.showConfirm = window.AdminUtils.showConfirm

// Vote Management Functions
window.VoteManager = {
  // Export votes - Updated to use generalized voting platform API
  exportVotes: async function (voteId, format = 'csv') {
    if (!voteId) {
      showMessage("Vote ID requis pour l'export", 'error')
      return
    }

    try {
      showLoading()

      // Get JWT token for authentication
      const token = localStorage.getItem('jwt_token')
      if (!token) {
        showMessage('Authentification requise', 'error')
        return
      }

      const response = await fetch(`/api/votes/${voteId}/export?format=${format}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        // Trigger download
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `vote_${voteId}_export_${new Date().toISOString().slice(0, 10)}.${format}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)

        showMessage('Export réussi', 'success')
      } else if (response.status === 401) {
        localStorage.removeItem('jwt_token')
        showMessage('Session expirée, redirection...', 'error')
        setTimeout(() => {
          window.location.href = '/login'
        }, 2000)
      } else {
        const result = await response.json()
        showMessage(result.message || "Erreur lors de l'export", 'error')
      }
    } catch (error) {
      console.error('Export error:', error)
      showMessage("Erreur lors de l'export", 'error')
    } finally {
      hideLoading()
    }
  },

  // Delete individual vote - Updated for generalized voting platform API
  deleteVote: async function (voteId) {
    if (!voteId) {
      showMessage('Vote ID requis', 'error')
      return
    }

    showConfirm(
      'Confirmer la suppression',
      'Cette action supprimera définitivement ce vote. Cette action est irréversible. Êtes-vous sûr ?',
      async () => {
        try {
          showLoading()

          // Get JWT token for authentication
          const token = localStorage.getItem('jwt_token')
          if (!token) {
            showMessage('Authentification requise', 'error')
            return
          }

          const response = await fetch(`/api/votes/${voteId}`, {
            method: 'DELETE',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })

          if (response.ok) {
            showMessage('Vote supprimé avec succès', 'success')
            setTimeout(() => {
              window.location.reload()
            }, 1500)
          } else if (response.status === 401) {
            localStorage.removeItem('jwt_token')
            showMessage('Session expirée, redirection...', 'error')
            setTimeout(() => {
              window.location.href = '/login'
            }, 2000)
          } else {
            const result = await response.json()
            showMessage(result.message || 'Erreur lors de la suppression', 'error')
          }
        } catch (error) {
          console.error('Delete vote error:', error)
          showMessage('Erreur lors de la suppression', 'error')
        } finally {
          hideLoading()
        }
      }
    )
  },

  // Get vote results - Updated for generalized voting platform API
  getVoteResults: async function (voteId) {
    if (!voteId) {
      showMessage('Vote ID requis', 'error')
      return null
    }

    try {
      showLoading()

      // Get JWT token for authentication
      const token = localStorage.getItem('jwt_token')
      if (!token) {
        showMessage('Authentification requise', 'error')
        return null
      }

      const response = await fetch(`/api/votes/${voteId}/results`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const results = await response.json()
        return results
      } else if (response.status === 401) {
        localStorage.removeItem('jwt_token')
        showMessage('Session expirée, redirection...', 'error')
        setTimeout(() => {
          window.location.href = '/login'
        }, 2000)
      } else {
        const result = await response.json()
        showMessage(result.message || 'Erreur lors de la récupération des résultats', 'error')
      }
      return null
    } catch (error) {
      console.error('Get vote results error:', error)
      showMessage('Erreur lors de la récupération des résultats', 'error')
      return null
    } finally {
      hideLoading()
    }
  }
}

// System Management Functions - Updated for generalized voting platform
window.SystemManager = {
  // Get system stats - Using correct API endpoint
  getSystemStats: async function () {
    try {
      showLoading()

      // Get JWT token for authentication
      const token = localStorage.getItem('jwt_token')
      if (!token) {
        showMessage('Authentification requise', 'error')
        return null
      }

      const response = await fetch('/api/admin/stats', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const stats = await response.json()
        return stats
      } else if (response.status === 401) {
        localStorage.removeItem('jwt_token')
        showMessage('Session expirée, redirection...', 'error')
        setTimeout(() => {
          window.location.href = '/login'
        }, 2000)
      } else {
        const result = await response.json()
        showMessage(result.message || 'Erreur lors de la récupération des statistiques', 'error')
      }
      return null
    } catch (error) {
      console.error('System stats error:', error)
      showMessage('Erreur lors de la récupération des statistiques', 'error')
      return null
    } finally {
      hideLoading()
    }
  }
}

// Initialize admin interface
document.addEventListener('DOMContentLoaded', function () {
  // Add slideOut animation to CSS if not present
  if (!document.querySelector('style[data-admin-animations]')) {
    const style = document.createElement('style')
    style.setAttribute('data-admin-animations', 'true')
    style.textContent = `
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `
    document.head.appendChild(style)
  }

  // Handle navigation active states
  const currentPath = window.location.pathname
  const navItems = document.querySelectorAll('.admin-nav-item')
  navItems.forEach(item => {
    if (item.getAttribute('href') === currentPath) {
      item.classList.add('active')
    }
  })

  // Auto-hide messages after 5 seconds
  const existingMessages = document.querySelectorAll('.message')
  existingMessages.forEach(message => {
    setTimeout(() => {
      if (message.parentNode) {
        message.style.animation = 'slideOut 0.3s ease forwards'
        setTimeout(() => {
          if (message.parentNode) {
            message.parentNode.removeChild(message)
          }
        }, 300)
      }
    }, 5000)
  })

  // Handle session timeout - Updated for JWT authentication
  let sessionWarningShown = false
  const checkSession = async () => {
    try {
      const token = localStorage.getItem('jwt_token')
      if (!token) {
        if (!sessionWarningShown) {
          sessionWarningShown = true
          showMessage('Session expirée. Redirection vers la page de connexion...', 'error')
          setTimeout(() => {
            window.location.href = '/login'
          }, 2000)
        }
        return
      }

      const response = await fetch('/api/admin/stats', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.status === 401) {
        localStorage.removeItem('jwt_token')
        if (!sessionWarningShown) {
          sessionWarningShown = true
          showMessage('Session expirée. Redirection vers la page de connexion...', 'error')
          setTimeout(() => {
            window.location.href = '/login'
          }, 2000)
        }
      }
    } catch (error) {
      // Silently handle errors - network issues shouldn't trigger redirects
    }
  }

  // Check session every 5 minutes
  setInterval(checkSession, 5 * 60 * 1000)

  console.log('Admin interface initialized')
})
