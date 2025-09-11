/**
 * Generalized Public Voting Platform - JavaScript
 * Mobile-first responsive voting application for any vote type
 */

class PublicVotingApp {
  constructor() {
    this.currentScreen = 'welcome'
    this.currentOptionIndex = 0
    this.voteData = null
    this.responses = {} // Store responses by option ID
    this.voterFirstName = ''
    this.voterLastName = ''
    this.liveRegion = document.getElementById('live-region')
    this.captchaConfig = null
    this.captchaResponse = null

    this.screens = {
      welcome: document.getElementById('welcome-screen'),
      voting: document.getElementById('voting-screen'),
      review: document.getElementById('review-screen'),
      success: document.getElementById('success-screen')
    }

    this.initializeVoteData()
    this.initializeCaptcha()
    this.initializeEventListeners()
    this.initializeKeyboardNavigation()
    this.initializeAccessibility()
  }

  /**
   * Initialize vote data from server
   */
  initializeVoteData() {
    try {
      const voteDataScript = document.getElementById('vote-data')
      if (voteDataScript) {
        this.voteData = JSON.parse(voteDataScript.textContent)
        console.log('Vote data loaded:', this.voteData)
      } else {
        throw new Error('Vote data not found')
      }
    } catch (error) {
      console.error('Failed to load vote data:', error)
      this.showError('Error loading vote data')
    }
  }

  /**
   * Initialize CAPTCHA configuration and setup
   */
  initializeCaptcha() {
    try {
      const captchaConfigScript = document.getElementById('captcha-config')
      if (captchaConfigScript) {
        this.captchaConfig = JSON.parse(captchaConfigScript.textContent)
        console.log('CAPTCHA config loaded:', this.captchaConfig)

        // Initialize CAPTCHA widget based on backend type
        if (this.captchaConfig.backend === 'recaptcha' && this.captchaConfig.site_key) {
          this.initializeRecaptcha()
        } else if (this.captchaConfig.backend === 'hcaptcha' && this.captchaConfig.site_key) {
          this.initializeHcaptcha()
        } else {
          // Mock CAPTCHA for development
          this.initializeMockCaptcha()
        }
      } else {
        console.warn('CAPTCHA config not found, using mock CAPTCHA')
        this.initializeMockCaptcha()
      }
    } catch (error) {
      console.error('Failed to load CAPTCHA config:', error)
      this.initializeMockCaptcha()
    }
  }

  /**
   * Initialize reCAPTCHA widget
   */
  initializeRecaptcha() {
    console.log('Initializing reCAPTCHA...')
    // reCAPTCHA initialization would go here
    // For now, fall back to mock for development
    this.initializeMockCaptcha()
  }

  /**
   * Initialize hCaptcha widget
   */
  initializeHcaptcha() {
    console.log('Initializing hCaptcha...')
    // hCaptcha initialization would go here
    // For now, fall back to mock for development
    this.initializeMockCaptcha()
  }

  /**
   * Initialize mock CAPTCHA for development
   */
  initializeMockCaptcha() {
    const captchaWidget = document.getElementById('captcha-widget')
    if (captchaWidget) {
      captchaWidget.innerHTML = `
        <div class="mock-captcha">
          <label class="mock-captcha-label">
            <input type="checkbox" id="mock-captcha-checkbox" class="mock-captcha-input">
            <span class="mock-captcha-text">I'm not a robot (Development Mode)</span>
          </label>
        </div>
      `

      // Add event listener for mock CAPTCHA
      const mockCheckbox = document.getElementById('mock-captcha-checkbox')
      if (mockCheckbox) {
        mockCheckbox.addEventListener('change', (e) => {
          if (e.target.checked) {
            this.captchaResponse = 'MOCK_SUCCESS_TOKEN'
            this.onCaptchaSuccess()
          } else {
            this.captchaResponse = null
            this.onCaptchaReset()
          }
        })
      }
    }
  }

  /**
   * Handle CAPTCHA success
   */
  onCaptchaSuccess() {
    const submitBtn = document.getElementById('submit-vote')
    const captchaError = document.getElementById('captcha-error')

    if (submitBtn) {
      submitBtn.disabled = false
      submitBtn.classList.remove('disabled')
    }

    if (captchaError) {
      captchaError.style.display = 'none'
    }

    this.announceToScreenReader('CAPTCHA completed successfully')
  }

  /**
   * Handle CAPTCHA reset/failure
   */
  onCaptchaReset() {
    const submitBtn = document.getElementById('submit-vote')

    if (submitBtn) {
      submitBtn.disabled = true
      submitBtn.classList.add('disabled')
    }

    this.captchaResponse = null
  }

  /**
   * Announce to screen readers
   */
  announceToScreenReader(message) {
    if (this.liveRegion) {
      this.liveRegion.textContent = message
    }
  }

  /**
   * Initialize accessibility features
   */
  initializeAccessibility() {
    this.updateProgressBarAria()

    // Add keyboard hints
    document.addEventListener('keydown', e => {
      if (e.ctrlKey && e.key === '?') {
        this.showKeyboardHelp()
      }
    })
  }

  /**
   * Initialize keyboard navigation
   */
  initializeKeyboardNavigation() {
    document.addEventListener('keydown', e => {
      if (this.currentScreen === 'voting') {
        switch (e.key) {
          case 'ArrowLeft':
            e.preventDefault()
            this.previousOption()
            break
          case 'ArrowRight':
            e.preventDefault()
            this.nextOption()
            break
          case '1':
            e.preventDefault()
            this.selectRating(-2)
            break
          case '2':
            e.preventDefault()
            this.selectRating(-1)
            break
          case '3':
            e.preventDefault()
            this.selectRating(0)
            break
          case '4':
            e.preventDefault()
            this.selectRating(1)
            break
          case '5':
            e.preventDefault()
            this.selectRating(2)
            break
          case 'Escape':
            if (this.currentOptionIndex > 0) {
              this.previousOption()
            } else {
              this.showWelcomeScreen()
            }
            break
        }
      } else if (this.currentScreen === 'review' && e.key === 'Escape') {
        this.showVotingScreen()
      }
    })
  }

  /**
   * Initialize all event listeners
   */
  initializeEventListeners() {
    // Voter form submission
    const voterForm = document.getElementById('voter-form')
    voterForm.addEventListener('submit', e => this.handleVoterSubmit(e))

    // Navigation buttons
    document.getElementById('prev-btn').addEventListener('click', () => this.previousOption())
    document.getElementById('next-btn').addEventListener('click', () => this.nextOption())

    // Rating selection
    const ratingInputs = document.querySelectorAll('input[name="rating"]')
    ratingInputs.forEach(input => {
      input.addEventListener('change', () => this.handleRatingChange())
    })

    // Review screen buttons
    document.getElementById('back-to-voting').addEventListener('click', () => this.showVotingScreen())
    document.getElementById('submit-vote').addEventListener('click', () => this.submitVote())

    // Handle review card clicks
    document.addEventListener('click', e => {
      if (e.target.closest('.review-card')) {
        this.editResponse(e.target.closest('.review-card'))
      }
    })
  }

  /**
   * Handle voter form submission
   */
  async handleVoterSubmit(event) {
    event.preventDefault()

    const firstNameInput = document.getElementById('voter-first-name')
    const lastNameInput = document.getElementById('voter-last-name')
    const firstName = firstNameInput.value.trim()
    const lastName = lastNameInput.value.trim()

    // Clear previous validation
    firstNameInput.setAttribute('aria-invalid', 'false')
    lastNameInput.setAttribute('aria-invalid', 'false')

    // Validate fields
    if (!firstName) {
      this.showError('Please enter your first name')
      firstNameInput.setAttribute('aria-invalid', 'true')
      firstNameInput.focus()
      this.announceToScreenReader('Error: first name is required')
      return
    }

    if (!lastName) {
      this.showError('Please enter your last name')
      lastNameInput.setAttribute('aria-invalid', 'true')
      lastNameInput.focus()
      this.announceToScreenReader('Error: last name is required')
      return
    }

    // Validate name formats
    if (!/^[a-zA-ZÀ-ÿ\s\-']{1,50}$/.test(firstName)) {
      this.showError('First name can only contain letters, spaces, hyphens, and apostrophes')
      firstNameInput.setAttribute('aria-invalid', 'true')
      firstNameInput.focus()
      return
    }

    if (!/^[a-zA-ZÀ-ÿ\s\-']{1,50}$/.test(lastName)) {
      this.showError('Last name can only contain letters, spaces, hyphens, and apostrophes')
      lastNameInput.setAttribute('aria-invalid', 'true')
      lastNameInput.focus()
      return
    }

    this.voterFirstName = firstName
    this.voterLastName = lastName
    this.announceToScreenReader(`Hello ${firstName} ${lastName}, starting vote...`)

    this.showVotingScreen()
  }

  /**
   * Show welcome screen
   */
  showWelcomeScreen() {
    this.currentScreen = 'welcome'
    this.updateScreen()
    const firstNameInput = document.getElementById('voter-first-name')
    if (firstNameInput) {
      firstNameInput.focus()
    }
  }

  /**
   * Show voting screen
   */
  showVotingScreen() {
    if (!this.voteData || !this.voteData.options) {
      this.showError('Vote data not available')
      return
    }

    this.currentScreen = 'voting'
    this.updateScreen()
    this.displayCurrentOption()
    this.updateProgress()
    this.updateNavigation()

    // Focus management for screen readers
    const votingTitle = document.getElementById('voting-title')
    if (votingTitle) {
      votingTitle.focus()
    }

    this.announceToScreenReader(
      `Voting screen. Option ${this.currentOptionIndex + 1} of ${this.voteData.options.length}`
    )
  }

  /**
   * Display current option
   */
  displayCurrentOption() {
    if (!this.voteData || !this.voteData.options || this.voteData.options.length === 0) {
      console.error('No options available')
      this.announceToScreenReader('Error: no options available')
      return
    }

    const option = this.voteData.options[this.currentOptionIndex]
    const container = document.getElementById('option-container')

    // Clear previous content
    container.innerHTML = ''

    // Create option display based on type
    const titleElement = document.createElement('div')
    titleElement.className = 'option-title'
    titleElement.textContent = option.title
    container.appendChild(titleElement)

    // Handle different option types
    if (option.option_type === 'image' && option.content && option.content.startsWith('/')) {
      // Image option
      const imageElement = document.createElement('img')
      imageElement.src = option.content
      imageElement.alt = `Option: ${option.title}`
      imageElement.className = 'option-image'
      imageElement.onerror = () => {
        this.showError(`Unable to load image for ${option.title}`)
      }
      container.appendChild(imageElement)
    } else if (option.content && option.content !== option.title) {
      // Text content (if different from title)
      const contentElement = document.createElement('div')
      contentElement.className = 'option-content'
      contentElement.textContent = option.content
      container.appendChild(contentElement)
    }

    // Restore previous rating if exists
    const previousRating = this.responses[option.id]
    const ratingInputs = document.querySelectorAll('input[name="rating"]')

    ratingInputs.forEach(input => {
      input.checked = parseInt(input.value) === previousRating
    })

    this.updateNavigation()
    this.updateProgressBarAria()

    // Announce option change to screen readers
    if (previousRating !== undefined) {
      this.announceToScreenReader(
        `Option ${this.currentOptionIndex + 1} of ${this.voteData.options.length}: ${option.title}. Current rating: ${this.getRatingLabel(previousRating)}`
      )
    } else {
      this.announceToScreenReader(
        `Option ${this.currentOptionIndex + 1} of ${this.voteData.options.length}: ${option.title}. No rating assigned`
      )
    }
  }

  /**
   * Handle rating selection
   */
  handleRatingChange() {
    const selectedRating = document.querySelector('input[name="rating"]:checked')
    if (selectedRating && this.voteData && this.voteData.options) {
      const option = this.voteData.options[this.currentOptionIndex]
      const rating = parseInt(selectedRating.value)
      this.responses[option.id] = rating

      console.log(`Rated option ${option.id} (${option.title}): ${rating}`)

      this.updateNavigation()
      this.announceToScreenReader(`Rating assigned: ${this.getRatingLabel(rating)}`)
    }
  }

  /**
   * Select a rating programmatically
   */
  selectRating(value) {
    const input = document.querySelector(`input[name="rating"][value="${value}"]`)
    if (input) {
      input.checked = true
      input.focus()
      this.handleRatingChange()
    }
  }

  /**
   * Update progress bar ARIA attributes
   */
  updateProgressBarAria() {
    const progressBar = document.querySelector('.progress-bar[role="progressbar"]')
    if (progressBar && this.voteData && this.voteData.options) {
      progressBar.setAttribute('aria-valuenow', this.currentOptionIndex + 1)
      progressBar.setAttribute('aria-valuemax', this.voteData.options.length)
      progressBar.setAttribute(
        'aria-valuetext',
        `Option ${this.currentOptionIndex + 1} of ${this.voteData.options.length}`
      )
    }
  }

  /**
   * Go to previous option
   */
  previousOption() {
    if (this.currentOptionIndex > 0) {
      this.currentOptionIndex--
      this.displayCurrentOption()
      this.updateProgress()

      // Focus on the current rating if one is selected
      const currentRating = document.querySelector('input[name="rating"]:checked')
      if (currentRating) {
        currentRating.focus()
      }
    } else {
      this.announceToScreenReader('Already at the first option')
    }
  }

  /**
   * Go to next option or finish voting
   */
  nextOption() {
    if (!this.voteData || !this.voteData.options) {
      this.showError('Vote data not available')
      return
    }

    const currentOption = this.voteData.options[this.currentOptionIndex]
    const hasRating = this.responses.hasOwnProperty(currentOption.id)

    if (!hasRating) {
      this.showError('Please assign a rating before continuing')
      this.announceToScreenReader('A rating is required for this option')
      // Focus on first rating option
      const firstRating = document.querySelector('input[name="rating"]')
      if (firstRating) {
        firstRating.focus()
      }
      return
    }

    if (this.currentOptionIndex < this.voteData.options.length - 1) {
      this.currentOptionIndex++
      this.displayCurrentOption()
      this.updateProgress()
    } else {
      this.showReviewScreen()
    }
  }

  /**
   * Update progress bar
   */
  updateProgress() {
    if (!this.voteData || !this.voteData.options) return

    const progress = ((this.currentOptionIndex + 1) / this.voteData.options.length) * 100
    document.getElementById('progress-fill').style.width = `${progress}%`
    document.getElementById('progress-text').textContent =
      `Option ${this.currentOptionIndex + 1} sur ${this.voteData.options.length}`
  }

  /**
   * Update navigation buttons state
   */
  updateNavigation() {
    const prevBtn = document.getElementById('prev-btn')
    const nextBtn = document.getElementById('next-btn')

    prevBtn.disabled = this.currentOptionIndex === 0

    if (!this.voteData || !this.voteData.options) {
      nextBtn.disabled = true
      return
    }

    const currentOption = this.voteData.options[this.currentOptionIndex]
    const hasRating = this.responses.hasOwnProperty(currentOption.id)
    nextBtn.disabled = !hasRating

    // Update button text for last option
    if (this.currentOptionIndex === this.voteData.options.length - 1) {
      nextBtn.textContent = 'Finish'
    } else {
      nextBtn.textContent = 'Next'
    }
  }

  /**
   * Show review screen
   */
  showReviewScreen() {
    if (!this.voteData || !this.voteData.options) {
      this.showError('Vote data not available')
      return
    }

    // Check if all options have been rated
    const unratedOptions = this.voteData.options.filter(option => !this.responses.hasOwnProperty(option.id))
    if (unratedOptions.length > 0) {
      this.showError(`Missing ratings for ${unratedOptions.length} option(s)`)
      this.announceToScreenReader(`${unratedOptions.length} option(s) without rating`)
      return
    }

    this.currentScreen = 'review'
    this.updateScreen()
    this.displayReview()

    // Focus management
    const reviewTitle = document.getElementById('review-title')
    if (reviewTitle) {
      reviewTitle.focus()
    }

    this.announceToScreenReader('Review page. Check your ratings before submitting')
  }

  /**
   * Display review grid
   */
  displayReview() {
    if (!this.voteData || !this.voteData.options) return

    const reviewGrid = document.getElementById('review-grid')
    reviewGrid.innerHTML = ''

    this.voteData.options.forEach((option, index) => {
      const rating = this.responses[option.id]
      const card = document.createElement('div')
      card.className = 'review-card'
      card.dataset.optionIndex = index
      card.setAttribute('role', 'gridcell')
      card.setAttribute('tabindex', '0')
      card.setAttribute('aria-label', `Option ${index + 1}: ${option.title}, rating: ${this.getRatingLabel(rating)}`)

      const ratingClass = this.getRatingClass(rating)
      const ratingText = rating > 0 ? `+${rating}` : rating.toString()

      card.innerHTML = `
                <div class="review-option-title">${option.title}</div>
                <div class="review-option-content">${option.content || ''}</div>
                <div class="review-rating">
                    <span class="review-rating-value ${ratingClass}">${ratingText}</span>
                    <span class="review-rating-label">${this.getRatingLabel(rating)}</span>
                </div>
            `

      // Add keyboard support
      card.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          this.editResponse(card)
        }
      })

      reviewGrid.appendChild(card)
    })
  }

  /**
   * Edit response from review screen
   */
  editResponse(card) {
    const optionIndex = parseInt(card.dataset.optionIndex)
    this.currentOptionIndex = optionIndex

    // Visual feedback
    card.classList.add('editing')

    // Announce to screen reader
    this.announceToScreenReader(`Modifying option ${optionIndex + 1}`)

    setTimeout(() => {
      this.showVotingScreen()
    }, 200)
  }

  /**
   * Submit the vote
   */
  async submitVote() {
    if (!this.voteData || !this.voteData.options) {
      this.showError('Vote data not available')
      return
    }

    try {
      // Validate all responses are present
      const missingOptions = this.voteData.options.filter(option => !this.responses.hasOwnProperty(option.id))
      if (missingOptions.length > 0) {
        this.showError(`Évaluations manquantes pour ${missingOptions.length} option(s)`)
        return
      }

      // Disable submit button to prevent double submission
      const submitBtn = document.getElementById('submit-vote')
      const originalText = submitBtn.textContent
      submitBtn.disabled = true
      submitBtn.setAttribute('aria-busy', 'true')
      submitBtn.innerHTML = '<span class="spinner"></span> Submitting...'

      this.announceToScreenReader('Submitting your vote...')

      // Validate CAPTCHA response
      if (!this.captchaResponse) {
        const captchaError = document.getElementById('captcha-error')
        if (captchaError) {
          captchaError.textContent = 'Please complete the security check'
          captchaError.style.display = 'block'
        }

        // Re-enable submit button
        submitBtn.disabled = false
        submitBtn.setAttribute('aria-busy', 'false')
        submitBtn.textContent = originalText

        this.announceToScreenReader('Error: Please complete the security check')
        return
      }

      const voteData = {
        voter_first_name: this.voterFirstName,
        voter_last_name: this.voterLastName,
        responses: this.responses, // Send responses by option ID
        captcha_response: this.captchaResponse
      }

      console.log('Submitting vote:', voteData)

      // Use the generalized API endpoint
      const response = await fetch(`/api/votes/public/${this.voteData.slug}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(voteData),
        signal: AbortSignal.timeout(15000) // 15 second timeout
      })

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage
        try {
          const errorData = JSON.parse(errorText)
          errorMessage = errorData.detail || errorData.message || 'Server error'
        } catch {
          errorMessage = `HTTP Error ${response.status}: ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      const result = await response.json()

      if (result.success) {
        this.showSuccessScreen(result.message)
      } else {
        throw new Error(result.message || "Error submitting vote")
      }
    } catch (error) {
      console.error('Error submitting vote:', error)

      let errorMessage
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        errorMessage = 'Timeout: request took too long. Please try again.'
      } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorMessage = 'Connection error. Check your internet connection and try again.'
      } else if (error.message.includes('already voted') || error.message.includes('already been submitted')) {
        errorMessage = "You have already voted. Each person can only vote once."
      } else {
        errorMessage = error.message || "Error submitting vote"
      }

      this.showError(errorMessage)
      this.announceToScreenReader(`Error: ${errorMessage}`)

      // Re-enable submit button
      const submitBtn = document.getElementById('submit-vote')
      submitBtn.disabled = false
      submitBtn.setAttribute('aria-busy', 'false')
      submitBtn.textContent = 'Confirm and Submit'
      submitBtn.focus()
    }
  }

  /**
   * Show success screen
   */
  showSuccessScreen(message = null) {
    this.currentScreen = 'success'
    this.updateScreen()

    if (message) {
      document.getElementById('success-message').textContent = message
    }

    // Focus management
    const successTitle = document.getElementById('success-title')
    if (successTitle) {
      successTitle.focus()
    }

    this.announceToScreenReader('Vote submitted successfully! Thank you for your participation.')
    console.log('Vote submitted successfully')
  }

  /**
   * Update visible screen
   */
  updateScreen() {
    Object.values(this.screens).forEach(screen => {
      screen.classList.remove('active')
    })

    this.screens[this.currentScreen].classList.add('active')
  }

  /**
   * Show error message
   */
  showError(message) {
    // Remove existing error messages
    const existingErrors = document.querySelectorAll('.error-message')
    existingErrors.forEach(error => error.remove())

    // Create new error message
    const errorDiv = document.createElement('div')
    errorDiv.className = 'error-message'
    errorDiv.setAttribute('role', 'alert')
    errorDiv.setAttribute('aria-live', 'assertive')
    errorDiv.textContent = message

    // Insert at the top of current screen
    const currentScreenEl = this.screens[this.currentScreen]
    currentScreenEl.insertBefore(errorDiv, currentScreenEl.firstChild)

    // Focus the error for screen readers
    errorDiv.setAttribute('tabindex', '-1')
    errorDiv.focus()

    // Auto-remove after 7 seconds
    setTimeout(() => {
      if (errorDiv.parentNode) {
        errorDiv.remove()
      }
    }, 7000)

    console.error('App Error:', message)
  }

  /**
   * Get rating label for display
   */
  getRatingLabel(rating) {
    const labels = {
      '-2': 'Strongly rejected',
      '-1': 'Rejected',
      0: 'Neutral',
      1: 'Accepted',
      2: 'Strongly accepted'
    }
    return labels[rating.toString()] || 'Unknown'
  }

  /**
   * Get rating CSS class
   */
  getRatingClass(rating) {
    if (rating === 2) return 'positive-strong'
    if (rating === 1) return 'positive'
    if (rating === 0) return 'neutral'
    if (rating === -1) return 'negative'
    if (rating === -2) return 'negative-strong'
    return 'neutral'
  }

  /**
   * Show keyboard help
   */
  showKeyboardHelp() {
    this.announceToScreenReader('Keyboard shortcuts: Arrow keys to navigate, 1-5 to rate, Enter to confirm')
  }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  try {
    new PublicVotingApp()
  } catch (error) {
    console.error('Failed to initialize public voting app:', error)

    // Show fallback error message
    const fallbackError = document.createElement('div')
    fallbackError.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #dc2626;">
                <h2>Initialization Error</h2>
                <p>An error occurred while loading the voting application.</p>
                <button onclick="window.location.reload()" style="margin: 1rem; padding: 0.5rem 1rem; border: none; background: #2D5820; color: white; border-radius: 4px; cursor: pointer;">
                    Reload page
                </button>
            </div>
        `
    document.body.appendChild(fallbackError)
  }
})

// Global error handling
window.addEventListener('error', event => {
  console.error('Global error:', event.error)
})

window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled promise rejection:', event.reason)
})
