// Landing Page Material Design JavaScript
/* global grecaptcha, hcaptcha */

// Wait for DOM to be loaded
document.addEventListener('DOMContentLoaded', function () {
  // Navigation Drawer
  const navButton = document.querySelector('.md-top-app-bar-navigation-icon')
  const drawer = document.getElementById('navigationDrawer')
  const scrim = document.getElementById('navigationScrim')

  if (navButton && drawer && scrim) {
    navButton.addEventListener('click', () => {
      drawer.classList.toggle('md-navigation-drawer-open')
      scrim.classList.toggle('md-navigation-drawer-scrim-visible')
    })

    scrim.addEventListener('click', () => {
      drawer.classList.remove('md-navigation-drawer-open')
      scrim.classList.remove('md-navigation-drawer-scrim-visible')
    })
  }

  // Smooth scrolling for navigation links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault()
      const target = document.querySelector(this.getAttribute('href'))
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' })
        // Close drawer if open
        if (drawer && scrim) {
          drawer.classList.remove('md-navigation-drawer-open')
          scrim.classList.remove('md-navigation-drawer-scrim-visible')
        }
      }
    })
  })

  // Scroll to Top Button
  const scrollToTopBtn = document.getElementById('scrollToTop')

  if (scrollToTopBtn) {
    window.addEventListener('scroll', () => {
      if (window.pageYOffset > 300) {
        scrollToTopBtn.classList.add('visible')
      } else {
        scrollToTopBtn.classList.remove('visible')
      }
    })

    scrollToTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    })
  }

  // Ripple Effect
  function createRipple(event) {
    const button = event.currentTarget
    const ripple = document.createElement('span')
    const diameter = Math.max(button.clientWidth, button.clientHeight)
    const radius = diameter / 2

    ripple.style.width = ripple.style.height = `${diameter}px`
    ripple.style.left = `${event.clientX - button.offsetLeft - radius}px`
    ripple.style.top = `${event.clientY - button.offsetTop - radius}px`
    ripple.classList.add('md-ripple-effect')

    button.appendChild(ripple)

    setTimeout(() => {
      ripple.remove()
    }, 600)
  }

  // Add ripple effect to all buttons
  document.querySelectorAll('.md-button, .md-fab, .md-card').forEach(element => {
    element.classList.add('md-ripple')
    element.addEventListener('click', createRipple)
  })

  // Snackbar functionality
  function showSnackbar(message, action = null) {
    const snackbar = document.getElementById('snackbar')
    const snackbarMessage = document.getElementById('snackbar-message')
    const snackbarAction = document.getElementById('snackbar-action')

    if (snackbar && snackbarMessage && snackbarAction) {
      snackbarMessage.textContent = message

      if (action) {
        snackbarAction.style.display = 'block'
        snackbarAction.onclick = action
      } else {
        snackbarAction.style.display = 'none'
      }

      snackbar.classList.add('md-snackbar-visible')

      setTimeout(() => {
        snackbar.classList.remove('md-snackbar-visible')
      }, 4000)
    }
  }

  // Dismiss snackbar
  const snackbarAction = document.getElementById('snackbar-action')
  if (snackbarAction) {
    snackbarAction.addEventListener('click', () => {
      const snackbar = document.getElementById('snackbar')
      if (snackbar) {
        snackbar.classList.remove('md-snackbar-visible')
      }
    })
  }

  // Removed automatic welcome popup - was causing unwanted black popup on page load
  // Users can still see CTAs and welcome messages in the hero section

  // Intersection Observer for animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  }

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-fade-in-up')
        observer.unobserve(entry.target)
      }
    })
  }, observerOptions)

  // Observe feature cards and other elements
  document.querySelectorAll('.feature-card, .stat-item, .step-item').forEach(el => {
    observer.observe(el)
  })

  // Initialize authentication functionality
  AuthenticationManager.init()
})

// Authentication Manager Class
class AuthenticationManager {
  constructor() {
    this.API_BASE = '/api/auth'
    this.loginModal = null
    this.registerModal = null
    this.loginForm = null
    this.registerForm = null
    this.captchaWidgetId = null
    this.captchaResponse = null
    this.captchaConfig = window.captchaConfig || { backend: 'mock', enabled: false }
  }

  static init() {
    const auth = new AuthenticationManager()
    auth.initializeElements()
    auth.initializeEventListeners()
    auth.initializeCaptcha()
    auth.checkAuthStatus()
  }

  initializeElements() {
    this.loginModal = document.getElementById('loginModalScrim')
    this.registerModal = document.getElementById('registerModalScrim')
    this.loginForm = document.getElementById('loginForm')
    this.registerForm = document.getElementById('registerForm')
  }

  initializeEventListeners() {
    // Global click handler for data-action buttons
    document.addEventListener('click', e => {
      const action = e.target.closest('[data-action]')?.dataset.action
      if (action) {
        e.preventDefault()
        this.handleAction(action, e.target)
      }
    })

    // Form submissions
    if (this.loginForm) {
      this.loginForm.addEventListener('submit', e => this.handleLogin(e))
    }

    if (this.registerForm) {
      this.registerForm.addEventListener('submit', e => this.handleRegister(e))
    }

    // Close modals on escape key
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        this.closeAllModals()
      }
    })

    // Close modals when clicking on scrim
    if (this.loginModal) {
      this.loginModal.addEventListener('click', e => {
        if (e.target === this.loginModal) {
          this.closeModal('login')
        }
      })
    }

    if (this.registerModal) {
      this.registerModal.addEventListener('click', e => {
        if (e.target === this.registerModal) {
          this.closeModal('register')
        }
      })
    }
  }

  handleAction(action, element) {
    const modal = element.dataset.modal

    switch (action) {
      case 'show-login':
        this.showModal('login')
        break
      case 'show-register':
        this.showModal('register')
        break
      case 'close-modal':
        this.closeModal(modal)
        break
      case 'switch-to-login':
        this.switchToLogin()
        break
      case 'switch-to-register':
        this.switchToRegister()
        break
    }
  }

  showModal(type) {
    this.closeAllModals() // Close any open modals first

    const modal = type === 'login' ? this.loginModal : this.registerModal
    if (modal) {
      modal.classList.add('md-dialog-scrim-visible')
      modal.setAttribute('aria-hidden', 'false')

      // Focus first input
      const firstInput = modal.querySelector('input')
      if (firstInput) {
        setTimeout(() => firstInput.focus(), 100)
      }

      // Clear any previous errors
      this.clearErrors(type)
    }
  }

  closeModal(type) {
    const modal = type === 'login' ? this.loginModal : this.registerModal
    if (modal) {
      modal.classList.remove('md-dialog-scrim-visible')
      modal.setAttribute('aria-hidden', 'true')
      this.clearErrors(type)
    }
  }

  closeAllModals() {
    this.closeModal('login')
    this.closeModal('register')
  }

  switchToLogin() {
    this.closeModal('register')
    this.showModal('login')
  }

  switchToRegister() {
    this.closeModal('login')
    this.showModal('register')
  }

  async handleLogin(event) {
    event.preventDefault()

    const submitBtn = document.getElementById('loginSubmitBtn')
    const email = document.getElementById('loginEmail').value.trim()
    const password = document.getElementById('loginPassword').value

    // Basic validation
    if (!email || !password) {
      this.showError('login', 'Please fill in all required fields')
      return
    }

    // Set loading state
    this.setButtonLoading(submitBtn, true)
    this.clearErrors('login')

    try {
      const response = await fetch(`${this.API_BASE}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (response.ok) {
        // Store tokens
        this.storeTokens(data.access_token, data.refresh_token)

        // Show success and redirect
        this.showSnackbar('Welcome back! Redirecting to your dashboard...')
        this.closeModal('login')

        // Redirect to dashboard after short delay
        setTimeout(() => {
          window.location.href = '/dashboard'
        }, 1500)
      } else {
        this.showError('login', data.message || 'Invalid credentials. Please try again.')
      }
    } catch (error) {
      console.error('Login error:', error)
      this.showError('login', 'Network error. Please check your connection and try again.')
    } finally {
      this.setButtonLoading(submitBtn, false)
    }
  }

  async handleRegister(event) {
    event.preventDefault()

    const submitBtn = document.getElementById('registerSubmitBtn')
    const firstName = document.getElementById('registerFirstName').value.trim()
    const lastName = document.getElementById('registerLastName').value.trim()
    const username = document.getElementById('registerUsername').value.trim()
    const email = document.getElementById('registerEmail').value.trim()
    const password = document.getElementById('registerPassword').value

    // Basic validation
    if (!firstName || !lastName || !username || !email || !password) {
      this.showError('register', 'Please fill in all required fields')
      return
    }

    if (password.length < 8) {
      this.showError('register', 'Password must be at least 8 characters long')
      return
    }

    // CAPTCHA validation
    const captchaResponse = this.validateCaptcha()
    if (captchaResponse === null) {
      return // CAPTCHA validation failed, error already shown
    }

    // Set loading state
    this.setButtonLoading(submitBtn, true)
    this.clearErrors('register')
    this.clearCaptchaError()

    try {
      const response = await fetch(`${this.API_BASE}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          username,
          email,
          password,
          ...(this.captchaConfig.enabled && { captcha_response: captchaResponse })
        })
      })

      const data = await response.json()

      if (response.ok) {
        // Store tokens
        this.storeTokens(data.access_token, data.refresh_token)

        // Show success and redirect
        this.showSnackbar('Account created successfully! Welcome to the platform.')
        this.closeModal('register')

        // Redirect to dashboard after short delay
        setTimeout(() => {
          window.location.href = '/dashboard'
        }, 1500)
      } else {
        // Reset CAPTCHA on registration failure
        this.resetCaptcha()

        // Handle validation errors
        if (data.details && Array.isArray(data.details)) {
          const errorMessage = data.details.join(', ')
          this.showError('register', errorMessage)
        } else {
          const message = data.message || 'Registration failed. Please try again.'
          // Show specific CAPTCHA error if needed
          if (message.toLowerCase().includes('captcha')) {
            this.showCaptchaError(message)
          } else {
            this.showError('register', message)
          }
        }
      }
    } catch (error) {
      console.error('Registration error:', error)
      this.resetCaptcha()
      this.showError('register', 'Network error. Please check your connection and try again.')
    } finally {
      this.setButtonLoading(submitBtn, false)
    }
  }

  storeTokens(accessToken, refreshToken) {
    if (accessToken) {
      sessionStorage.setItem('access_token', accessToken)
    }
    if (refreshToken) {
      sessionStorage.setItem('refresh_token', refreshToken)
    }
  }

  getAccessToken() {
    return sessionStorage.getItem('access_token')
  }

  async checkAuthStatus() {
    const token = this.getAccessToken()
    if (token) {
      try {
        const response = await fetch(`${this.API_BASE}/me`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        })

        if (response.ok) {
          // User is already authenticated
          // Could show different UI or redirect to dashboard
          console.log('User is already authenticated')
        } else {
          // Token is invalid, clear it
          this.clearTokens()
        }
      } catch (error) {
        console.error('Auth check error:', error)
        this.clearTokens()
      }
    }
  }

  clearTokens() {
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')
  }

  // CAPTCHA Methods
  async initializeCaptcha() {
    if (!this.captchaConfig.enabled) return

    // Wait for CAPTCHA scripts to load
    const maxAttempts = 50
    let attempts = 0

    const waitForCaptcha = () => {
      attempts++

      if (this.captchaConfig.backend === 'recaptcha' && window.grecaptcha) {
        this.renderReCaptcha()
        return
      }

      if (this.captchaConfig.backend === 'hcaptcha' && window.hcaptcha) {
        this.renderHCaptcha()
        return
      }

      if (attempts < maxAttempts) {
        setTimeout(waitForCaptcha, 100)
      } else {
        console.warn('CAPTCHA service failed to load')
        this.showCaptchaError('CAPTCHA service unavailable. Please refresh the page.')
      }
    }

    setTimeout(waitForCaptcha, 100)
  }

  renderReCaptcha() {
    const container = document.getElementById('registerCaptcha')
    if (!container) return

    try {
      container.innerHTML = '<div class="captcha-loading">Loading verification...</div>'

      this.captchaWidgetId = grecaptcha.render(container, {
        sitekey: this.captchaConfig.siteKey,
        callback: response => {
          this.captchaResponse = response
          this.clearCaptchaError()
        },
        'expired-callback': () => {
          this.captchaResponse = null
          this.showCaptchaError('Verification expired. Please complete the CAPTCHA again.')
        },
        'error-callback': () => {
          this.captchaResponse = null
          this.showCaptchaError('Verification failed. Please try again.')
        }
      })
    } catch (error) {
      console.error('reCAPTCHA render error:', error)
      this.showCaptchaError('Failed to load verification. Please refresh the page.')
    }
  }

  renderHCaptcha() {
    const container = document.getElementById('registerCaptcha')
    if (!container) return

    try {
      container.innerHTML = '<div class="captcha-loading">Loading verification...</div>'

      this.captchaWidgetId = hcaptcha.render(container, {
        sitekey: this.captchaConfig.siteKey,
        callback: response => {
          this.captchaResponse = response
          this.clearCaptchaError()
        },
        'expired-callback': () => {
          this.captchaResponse = null
          this.showCaptchaError('Verification expired. Please complete the CAPTCHA again.')
        },
        'error-callback': () => {
          this.captchaResponse = null
          this.showCaptchaError('Verification failed. Please try again.')
        }
      })
    } catch (error) {
      console.error('hCAPTCHA render error:', error)
      this.showCaptchaError('Failed to load verification. Please refresh the page.')
    }
  }

  resetCaptcha() {
    if (!this.captchaConfig.enabled || !this.captchaWidgetId) return

    try {
      if (this.captchaConfig.backend === 'recaptcha' && window.grecaptcha) {
        grecaptcha.reset(this.captchaWidgetId)
      } else if (this.captchaConfig.backend === 'hcaptcha' && window.hcaptcha) {
        hcaptcha.reset(this.captchaWidgetId)
      }

      this.captchaResponse = null
      this.clearCaptchaError()
    } catch (error) {
      console.error('CAPTCHA reset error:', error)
    }
  }

  validateCaptcha() {
    if (!this.captchaConfig.enabled) {
      // For mock/development, always return a mock response
      return 'mock-captcha-response'
    }

    if (!this.captchaResponse) {
      this.showCaptchaError('Please complete the verification to continue.')
      return null
    }

    return this.captchaResponse
  }

  showCaptchaError(message) {
    const errorElement = document.getElementById('registerCaptchaError')
    const container = document.getElementById('registerCaptcha')

    if (errorElement) {
      errorElement.textContent = message
      errorElement.style.display = 'block'
    }

    if (container) {
      container.classList.add('error')
    }
  }

  clearCaptchaError() {
    const errorElement = document.getElementById('registerCaptchaError')
    const container = document.getElementById('registerCaptcha')

    if (errorElement) {
      errorElement.style.display = 'none'
    }

    if (container) {
      container.classList.remove('error')
    }
  }

  showError(type, message) {
    const errorElement = document.getElementById(`${type}Error`)
    const messageElement = document.getElementById(`${type}ErrorMessage`)

    if (errorElement && messageElement) {
      messageElement.textContent = message
      errorElement.style.display = 'flex'
    }
  }

  clearErrors(type) {
    const errorElement = document.getElementById(`${type}Error`)
    if (errorElement) {
      errorElement.style.display = 'none'
    }
  }

  setButtonLoading(button, loading) {
    const textElement = button.querySelector('.btn-text')
    const loadingElement = button.querySelector('.btn-loading')

    if (textElement && loadingElement) {
      if (loading) {
        button.disabled = true
        button.classList.add('loading')
        textElement.style.opacity = '0'
        loadingElement.style.display = 'inline-block'
      } else {
        button.disabled = false
        button.classList.remove('loading')
        textElement.style.opacity = '1'
        loadingElement.style.display = 'none'
      }
    }
  }

  showSnackbar(message) {
    // Use existing snackbar function from global scope
    if (typeof window.showSnackbar === 'function') {
      window.showSnackbar(message)
    } else {
      // Fallback implementation
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
  }
}
