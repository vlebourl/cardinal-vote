/**
 * Landing Page JavaScript
 * Handles authentication modals, form submissions, and UI interactions
 */

// API endpoints
const API_BASE = '/api/auth'

// DOM elements
let loginModal, registerModal, successToast, errorToast

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  initializeElements()
  initializeEventListeners()
  checkAuthStatus()
})

/**
 * Initialize DOM element references
 */
function initializeElements() {
  loginModal = document.getElementById('loginModal')
  registerModal = document.getElementById('registerModal')
  successToast = document.getElementById('successToast')
  errorToast = document.getElementById('errorToast')
}

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
  // Form submissions
  const loginForm = document.getElementById('loginForm')
  const registerForm = document.getElementById('registerForm')

  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin)
  }

  if (registerForm) {
    registerForm.addEventListener('submit', handleRegister)
  }

  // Keyboard navigation
  document.addEventListener('keydown', handleKeyboardNavigation)

  // Close modals on escape
  document.addEventListener('keyup', function (e) {
    if (e.key === 'Escape') {
      closeAllModals()
    }
  })

  // Prevent modal content clicks from closing modal
  document.querySelectorAll('.modal-content').forEach(content => {
    content.addEventListener('click', function (e) {
      e.stopPropagation()
    })
  })
}

/**
 * Check if user is already authenticated
 */
async function checkAuthStatus() {
  try {
    const token = localStorage.getItem('authToken')
    if (!token) return

    const response = await fetch(`${API_BASE}/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const userData = await response.json()
      updateUIForAuthenticatedUser(userData)
    } else {
      // Token is invalid, remove it
      localStorage.removeItem('authToken')
    }
  } catch (error) {
    console.log('Auth check failed:', error)
    localStorage.removeItem('authToken')
  }
}

/**
 * Update UI when user is authenticated
 */
function updateUIForAuthenticatedUser(userData) {
  const authButtons = document.getElementById('authButtons')
  if (authButtons) {
    authButtons.innerHTML = `
            <div class="user-info">
                <span class="user-name">Hello, ${userData.first_name}!</span>
                <button class="btn-text" onclick="handleLogout()">
                    Sign Out
                </button>
                <button class="btn-primary" onclick="redirectToDashboard()">
                    Dashboard
                </button>
            </div>
        `
  }
}

/**
 * Show login modal
 */
function showLoginModal() {
  if (loginModal) {
    loginModal.classList.add('show')
    loginModal.setAttribute('aria-hidden', 'false')

    // Focus first input
    const firstInput = loginModal.querySelector('input')
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 100)
    }

    // Trap focus
    trapFocus(loginModal)
  }
}

/**
 * Show registration modal
 */
function showRegisterModal() {
  if (registerModal) {
    registerModal.classList.add('show')
    registerModal.setAttribute('aria-hidden', 'false')

    // Focus first input
    const firstInput = registerModal.querySelector('input')
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 100)
    }

    // Trap focus
    trapFocus(registerModal)
  }
}

/**
 * Close specific modal
 */
function closeModal(modalId) {
  const modal = document.getElementById(modalId)
  if (modal) {
    modal.classList.remove('show')
    modal.setAttribute('aria-hidden', 'true')
    releaseFocus()
  }
}

/**
 * Close all modals
 */
function closeAllModals() {
  ;[loginModal, registerModal].forEach(modal => {
    if (modal) {
      modal.classList.remove('show')
      modal.setAttribute('aria-hidden', 'true')
    }
  })
  releaseFocus()
}

/**
 * Switch from login to register modal
 */
function switchToRegister() {
  closeModal('loginModal')
  setTimeout(() => showRegisterModal(), 150)
}

/**
 * Switch from register to login modal
 */
function switchToLogin() {
  closeModal('registerModal')
  setTimeout(() => showLoginModal(), 150)
}

/**
 * Handle login form submission
 */
async function handleLogin(e) {
  e.preventDefault()

  const form = e.target
  const submitBtn = form.querySelector('button[type="submit"]')
  const email = form.querySelector('#loginEmail').value
  const password = form.querySelector('#loginPassword').value

  // Show loading state
  setButtonLoading(submitBtn, true)

  try {
    const response = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        password
      })
    })

    const data = await response.json()

    if (response.ok) {
      // Success
      localStorage.setItem('authToken', data.access_token)

      showToast('success', 'Welcome back!', 'You have been signed in successfully.')
      closeModal('loginModal')

      // Refresh page to update UI
      setTimeout(() => {
        window.location.reload()
      }, 1500)
    } else {
      // Error
      showToast('error', 'Sign In Failed', data.message || 'Please check your credentials and try again.')
    }
  } catch (error) {
    console.error('Login error:', error)
    showToast('error', 'Connection Error', 'Unable to connect to the server. Please try again.')
  } finally {
    setButtonLoading(submitBtn, false)
  }
}

/**
 * Handle registration form submission
 */
async function handleRegister(e) {
  e.preventDefault()

  const form = e.target
  const submitBtn = form.querySelector('button[type="submit"]')
  const firstName = form.querySelector('#registerFirstName').value
  const lastName = form.querySelector('#registerLastName').value
  const email = form.querySelector('#registerEmail').value
  const password = form.querySelector('#registerPassword').value

  // Basic validation
  if (password.length < 8) {
    showToast('error', 'Invalid Password', 'Password must be at least 8 characters long.')
    return
  }

  // Show loading state
  setButtonLoading(submitBtn, true)

  try {
    const response = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        email,
        password
      })
    })

    const data = await response.json()

    if (response.ok) {
      // Success
      localStorage.setItem('authToken', data.access_token)

      showToast('success', 'Account Created!', 'Welcome to the platform. You can now create your first vote.')
      closeModal('registerModal')

      // Refresh page to update UI
      setTimeout(() => {
        window.location.reload()
      }, 1500)
    } else {
      // Error
      showToast('error', 'Registration Failed', data.message || 'Please check your information and try again.')
    }
  } catch (error) {
    console.error('Registration error:', error)
    showToast('error', 'Connection Error', 'Unable to connect to the server. Please try again.')
  } finally {
    setButtonLoading(submitBtn, false)
  }
}

/**
 * Handle logout
 */
function handleLogout() {
  localStorage.removeItem('authToken')
  showToast('success', 'Signed Out', 'You have been signed out successfully.')

  setTimeout(() => {
    window.location.reload()
  }, 1500)
}

/**
 * Redirect to dashboard (placeholder)
 */
function redirectToDashboard() {
  showToast(
    'success',
    'Coming Soon',
    'Dashboard functionality is coming soon! For now, you can create votes through the platform.'
  )
}

/**
 * Show forgot password (placeholder)
 */
function showForgotPassword() {
  showToast('success', 'Coming Soon', 'Password reset functionality is coming soon! Please contact support if needed.')
}

/**
 * Scroll to features section
 */
function scrollToFeatures() {
  const featuresSection = document.getElementById('features')
  if (featuresSection) {
    featuresSection.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })
  }
}

/**
 * Show toast notification
 */
function showToast(type, title, message) {
  const toast = type === 'success' ? successToast : errorToast
  if (!toast) return

  const titleEl = toast.querySelector('.toast-title')
  const messageEl = toast.querySelector('.toast-message')

  if (titleEl) titleEl.textContent = title
  if (messageEl) messageEl.textContent = message

  toast.classList.add('show')

  // Auto-hide after 5 seconds
  setTimeout(() => {
    hideToast(toast.id)
  }, 5000)
}

/**
 * Hide toast notification
 */
function hideToast(toastId) {
  const toast = document.getElementById(toastId)
  if (toast) {
    toast.classList.remove('show')
  }
}

/**
 * Set button loading state
 */
function setButtonLoading(button, isLoading) {
  if (!button) return

  if (isLoading) {
    button.disabled = true
    button.classList.add('loading')
  } else {
    button.disabled = false
    button.classList.remove('loading')
  }
}

/**
 * Trap focus within modal
 */
function trapFocus(modal) {
  const focusableElements = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )

  const firstElement = focusableElements[0]
  const lastElement = focusableElements[focusableElements.length - 1]

  modal.addEventListener('keydown', function (e) {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus()
          e.preventDefault()
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus()
          e.preventDefault()
        }
      }
    }
  })
}

/**
 * Release focus trap
 */
function releaseFocus() {
  // Remove any existing focus trap listeners
  // This is handled by closing the modal and removing event listeners
}

/**
 * Handle keyboard navigation
 */
function handleKeyboardNavigation(e) {
  // Global keyboard shortcuts
  if (e.ctrlKey || e.metaKey) {
    switch (e.key) {
      case 'k':
        e.preventDefault()
        showLoginModal()
        break
    }
  }
}

/**
 * Utility: Debounce function
 */
function debounce(func, wait) {
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

/**
 * Utility: Format error message
 */
function formatErrorMessage(error) {
  if (typeof error === 'string') {
    return error
  }

  if (error.message) {
    return error.message
  }

  if (error.details && Array.isArray(error.details)) {
    return error.details.join(', ')
  }

  return 'An unexpected error occurred'
}

/**
 * Utility: Validate email format
 */
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Enhanced form validation
 */
function validateForm(form) {
  const errors = []
  const inputs = form.querySelectorAll('input[required]')

  inputs.forEach(input => {
    if (!input.value.trim()) {
      errors.push(`${input.labels[0].textContent} is required`)
    } else if (input.type === 'email' && !isValidEmail(input.value)) {
      errors.push('Please enter a valid email address')
    } else if (input.type === 'password' && input.value.length < 8) {
      errors.push('Password must be at least 8 characters long')
    }
  })

  return {
    isValid: errors.length === 0,
    errors
  }
}

// Export functions for global access
window.showLoginModal = showLoginModal
window.showRegisterModal = showRegisterModal
window.closeModal = closeModal
window.switchToLogin = switchToLogin
window.switchToRegister = switchToRegister
window.handleLogout = handleLogout
window.redirectToDashboard = redirectToDashboard
window.showForgotPassword = showForgotPassword
window.scrollToFeatures = scrollToFeatures
window.hideToast = hideToast
