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

    this.screens = {
      welcome: document.getElementById('welcome-screen'),
      voting: document.getElementById('voting-screen'),
      review: document.getElementById('review-screen'),
      success: document.getElementById('success-screen')
    }

    this.initializeVoteData()
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
      this.showError('Erreur lors du chargement des données du vote')
    }
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
      this.showError('Veuillez entrer votre prénom')
      firstNameInput.setAttribute('aria-invalid', 'true')
      firstNameInput.focus()
      this.announceToScreenReader('Erreur : le prénom est requis')
      return
    }

    if (!lastName) {
      this.showError('Veuillez entrer votre nom')
      lastNameInput.setAttribute('aria-invalid', 'true')
      lastNameInput.focus()
      this.announceToScreenReader('Erreur : le nom est requis')
      return
    }

    // Validate name formats
    if (!/^[a-zA-ZÀ-ÿ\s\-']{1,50}$/.test(firstName)) {
      this.showError('Le prénom ne peut contenir que des lettres, espaces, tirets et apostrophes')
      firstNameInput.setAttribute('aria-invalid', 'true')
      firstNameInput.focus()
      return
    }

    if (!/^[a-zA-ZÀ-ÿ\s\-']{1,50}$/.test(lastName)) {
      this.showError('Le nom ne peut contenir que des lettres, espaces, tirets et apostrophes')
      lastNameInput.setAttribute('aria-invalid', 'true')
      lastNameInput.focus()
      return
    }

    this.voterFirstName = firstName
    this.voterLastName = lastName
    this.announceToScreenReader(`Bonjour ${firstName} ${lastName}, début du vote...`)

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
      this.showError('Données du vote non disponibles')
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
      `Écran de vote. Option ${this.currentOptionIndex + 1} sur ${this.voteData.options.length}`
    )
  }

  /**
   * Display current option
   */
  displayCurrentOption() {
    if (!this.voteData || !this.voteData.options || this.voteData.options.length === 0) {
      console.error('No options available')
      this.announceToScreenReader('Erreur : aucune option disponible')
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
        this.showError(`Impossible de charger l'image pour ${option.title}`)
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
        `Option ${this.currentOptionIndex + 1} sur ${this.voteData.options.length}: ${option.title}. Note actuelle : ${this.getRatingLabel(previousRating)}`
      )
    } else {
      this.announceToScreenReader(
        `Option ${this.currentOptionIndex + 1} sur ${this.voteData.options.length}: ${option.title}. Aucune note attribuée`
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
      this.announceToScreenReader(`Note attribuée : ${this.getRatingLabel(rating)}`)
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
        `Option ${this.currentOptionIndex + 1} sur ${this.voteData.options.length}`
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
      this.announceToScreenReader('Déjà à la première option')
    }
  }

  /**
   * Go to next option or finish voting
   */
  nextOption() {
    if (!this.voteData || !this.voteData.options) {
      this.showError('Données du vote non disponibles')
      return
    }

    const currentOption = this.voteData.options[this.currentOptionIndex]
    const hasRating = this.responses.hasOwnProperty(currentOption.id)

    if (!hasRating) {
      this.showError('Veuillez attribuer une note avant de continuer')
      this.announceToScreenReader('Une note est requise pour cette option')
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
      nextBtn.textContent = 'Terminer'
    } else {
      nextBtn.textContent = 'Suivant'
    }
  }

  /**
   * Show review screen
   */
  showReviewScreen() {
    if (!this.voteData || !this.voteData.options) {
      this.showError('Données du vote non disponibles')
      return
    }

    // Check if all options have been rated
    const unratedOptions = this.voteData.options.filter(option => !this.responses.hasOwnProperty(option.id))
    if (unratedOptions.length > 0) {
      this.showError(`Évaluations manquantes pour ${unratedOptions.length} option(s)`)
      this.announceToScreenReader(`${unratedOptions.length} option(s) sans note`)
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

    this.announceToScreenReader('Page de révision. Vérifiez vos notes avant envoi')
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
      card.setAttribute('aria-label', `Option ${index + 1}: ${option.title}, note: ${this.getRatingLabel(rating)}`)

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
    this.announceToScreenReader(`Modification de l'option ${optionIndex + 1}`)

    setTimeout(() => {
      this.showVotingScreen()
    }, 200)
  }

  /**
   * Submit the vote
   */
  async submitVote() {
    if (!this.voteData || !this.voteData.options) {
      this.showError('Données du vote non disponibles')
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
      submitBtn.innerHTML = '<span class="spinner"></span> Envoi en cours...'

      this.announceToScreenReader('Envoi de votre vote en cours...')

      const voteData = {
        voter_first_name: this.voterFirstName,
        voter_last_name: this.voterLastName,
        responses: this.responses // Send responses by option ID
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
          errorMessage = errorData.detail || errorData.message || 'Erreur serveur'
        } catch {
          errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      const result = await response.json()

      if (result.success) {
        this.showSuccessScreen(result.message)
      } else {
        throw new Error(result.message || "Erreur lors de l'envoi du vote")
      }
    } catch (error) {
      console.error('Error submitting vote:', error)

      let errorMessage
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        errorMessage = 'Timeout: la requête a pris trop de temps. Veuillez réessayer.'
      } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorMessage = 'Erreur de connexion. Vérifiez votre connexion internet et réessayez.'
      } else if (error.message.includes('already voted') || error.message.includes('already been submitted')) {
        errorMessage = "Vous avez déjà voté. Chaque personne ne peut voter qu'une seule fois."
      } else {
        errorMessage = error.message || "Erreur lors de l'envoi du vote"
      }

      this.showError(errorMessage)
      this.announceToScreenReader(`Erreur: ${errorMessage}`)

      // Re-enable submit button
      const submitBtn = document.getElementById('submit-vote')
      submitBtn.disabled = false
      submitBtn.setAttribute('aria-busy', 'false')
      submitBtn.textContent = 'Confirmer et envoyer'
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

    this.announceToScreenReader('Vote envoyé avec succès! Merci pour votre participation.')
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
      '-2': 'Fortement rejeté',
      '-1': 'Rejeté',
      0: 'Neutre',
      1: 'Accepté',
      2: 'Fortement accepté'
    }
    return labels[rating.toString()] || 'Inconnu'
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
    this.announceToScreenReader('Raccourcis clavier : Flèches pour naviguer, 1-5 pour noter, Entrée pour confirmer')
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
                <h2>Erreur d'initialisation</h2>
                <p>Une erreur est survenue lors du chargement de l'application de vote.</p>
                <button onclick="window.location.reload()" style="margin: 1rem; padding: 0.5rem 1rem; border: none; background: #2D5820; color: white; border-radius: 4px; cursor: pointer;">
                    Recharger la page
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
