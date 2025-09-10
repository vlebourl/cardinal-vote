/**
 * ToV'éCo Logo Voting Platform - Frontend JavaScript
 * Mobile-first responsive voting application with accessibility support
 */

class VotingApp {
  constructor() {
    this.currentScreen = 'welcome'
    this.currentLogoIndex = 0
    this.logos = []
    this.votes = {}
    this.voterName = ''
    this.liveRegion = document.getElementById('live-region')

    this.screens = {
      welcome: document.getElementById('welcome-screen'),
      voting: document.getElementById('voting-screen'),
      review: document.getElementById('review-screen'),
      success: document.getElementById('success-screen')
    }

    this.initializeEventListeners()
    this.initializeKeyboardNavigation()
    this.initializeAccessibility()
    this.loadVoterCounter()
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
    // Set initial ARIA states
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
            this.previousLogo()
            break
          case 'ArrowRight':
            e.preventDefault()
            this.nextLogo()
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
            if (this.currentLogoIndex > 0) {
              this.previousLogo()
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
   * Select a rating programmatically
   */
  selectRating(value) {
    const input = document.querySelector(`input[name="rating"][value="${value}"]`)
    if (input) {
      input.checked = true
      input.focus()
      this.handleRatingChange()
      this.announceToScreenReader(`Note sélectionnée : ${this.getRatingLabel(value)}`)
    }
  }

  /**
   * Show keyboard help
   */
  showKeyboardHelp() {
    const helpDialog = document.getElementById('keyboard-help')
    if (helpDialog) {
      helpDialog.style.display = 'block'
      helpDialog.setAttribute('aria-hidden', 'false')
    }
  }

  /**
   * Initialize all event listeners
   */
  initializeEventListeners() {
    // Name form submission
    const nameForm = document.getElementById('name-form')
    nameForm.addEventListener('submit', e => this.handleNameSubmit(e))

    // Navigation buttons
    document.getElementById('prev-btn').addEventListener('click', () => this.previousLogo())
    document.getElementById('next-btn').addEventListener('click', () => this.nextLogo())

    // Rating selection
    const ratingInputs = document.querySelectorAll('input[name="rating"]')
    ratingInputs.forEach(input => {
      input.addEventListener('change', () => this.handleRatingChange())
    })

    // Review screen buttons
    document.getElementById('back-to-voting').addEventListener('click', () => this.showVotingScreen())
    document.getElementById('submit-votes').addEventListener('click', () => this.submitVotes())

    // Handle review card clicks
    document.addEventListener('click', e => {
      if (e.target.closest('.review-card')) {
        this.editVote(e.target.closest('.review-card'))
      }
    })
  }

  /**
   * Handle name form submission
   */
  async handleNameSubmit(event) {
    event.preventDefault()

    const firstNameInput = document.getElementById('voter-first-name')
    const lastNameInput = document.getElementById('voter-last-name')
    const firstName = firstNameInput.value.trim()
    const lastName = lastNameInput.value.trim()

    // Clear previous validation
    firstNameInput.setAttribute('aria-invalid', 'false')
    lastNameInput.setAttribute('aria-invalid', 'false')

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

    if (firstName.length > 50) {
      this.showError('Le prénom ne peut pas dépasser 50 caractères')
      firstNameInput.setAttribute('aria-invalid', 'true')
      firstNameInput.focus()
      this.announceToScreenReader('Erreur : prénom trop long')
      return
    }

    if (lastName.length > 50) {
      this.showError('Le nom ne peut pas dépasser 50 caractères')
      lastNameInput.setAttribute('aria-invalid', 'true')
      lastNameInput.focus()
      this.announceToScreenReader('Erreur : nom trop long')
      return
    }

    if (!/^[a-zA-ZÀ-ſ\s\-']{1,50}$/.test(firstName)) {
      this.showError('Le prénom ne peut contenir que des lettres, espaces, tirets et apostrophes')
      firstNameInput.setAttribute('aria-invalid', 'true')
      firstNameInput.focus()
      this.announceToScreenReader('Erreur : caractères invalides dans le prénom')
      return
    }

    if (!/^[a-zA-ZÀ-ſ\s\-']{1,50}$/.test(lastName)) {
      this.showError('Le nom ne peut contenir que des lettres, espaces, tirets et apostrophes')
      lastNameInput.setAttribute('aria-invalid', 'true')
      lastNameInput.focus()
      this.announceToScreenReader('Erreur : caractères invalides dans le nom')
      return
    }

    this.voterFirstName = firstName
    this.voterLastName = lastName
    this.voterName = `${firstName} ${lastName}` // Keep for compatibility
    this.announceToScreenReader(`Bonjour ${firstName} ${lastName}, chargement des logos...`)

    try {
      await this.loadLogos()
      this.showVotingScreen()
    } catch (error) {
      this.showError('Impossible de charger les logos. Veuillez réessayer.')
      this.announceToScreenReader('Erreur de chargement des logos')
      console.error('Failed to load logos:', error)
    }
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
   * Load logos from API
   */
  async loadLogos() {
    try {
      const response = await fetch('/api/logos')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      this.logos = data.logos

      if (!this.logos || this.logos.length === 0) {
        throw new Error('No logos received from server')
      }

      console.log(`Loaded ${this.logos.length} logos:`, this.logos)
    } catch (error) {
      console.error('Error loading logos:', error)
      throw error
    }
  }

  /**
   * Show voting screen and display first logo
   */
  showVotingScreen() {
    this.currentScreen = 'voting'
    this.updateScreen()
    this.displayCurrentLogo()
    this.updateProgress()
    this.updateNavigation()

    // Focus management for screen readers
    const votingTitle = document.getElementById('voting-title')
    if (votingTitle) {
      votingTitle.focus()
    }

    this.announceToScreenReader(`Écran de vote. Logo ${this.currentLogoIndex + 1} sur ${this.logos.length}`)
  }

  /**
   * Display current logo
   */
  displayCurrentLogo() {
    if (!this.logos || this.logos.length === 0) {
      console.error('No logos available')
      this.announceToScreenReader('Erreur : aucun logo disponible')
      return
    }

    const logo = this.logos[this.currentLogoIndex]
    const logoImg = document.getElementById('current-logo')
    const logoDescription = document.getElementById('logo-description')

    logoImg.src = `/logos/${logo}`
    logoImg.alt = `Logo ToV'éCo numéro ${this.currentLogoIndex + 1}`

    if (logoDescription) {
      logoDescription.textContent = `Logo ToV'éCo numéro ${this.currentLogoIndex + 1} sur ${this.logos.length} en cours d'évaluation`
    }

    // Handle image load errors
    logoImg.onerror = () => {
      this.showError(`Impossible de charger le logo ${logo}`)
      this.announceToScreenReader(`Erreur de chargement du logo ${this.currentLogoIndex + 1}`)
    }

    // Restore previous rating if exists
    const previousRating = this.votes[logo]
    const ratingInputs = document.querySelectorAll('input[name="rating"]')

    ratingInputs.forEach(input => {
      input.checked = parseInt(input.value) === previousRating
    })

    this.updateNavigation()
    this.updateProgressBarAria()

    // Announce logo change to screen readers
    if (previousRating !== undefined) {
      this.announceToScreenReader(
        `Logo ${this.currentLogoIndex + 1} sur ${this.logos.length}. Note actuelle : ${this.getRatingLabel(previousRating)}`
      )
    } else {
      this.announceToScreenReader(`Logo ${this.currentLogoIndex + 1} sur ${this.logos.length}. Aucune note attribuée`)
    }
  }

  /**
   * Handle rating selection
   */
  handleRatingChange() {
    const selectedRating = document.querySelector('input[name="rating"]:checked')
    if (selectedRating) {
      const logo = this.logos[this.currentLogoIndex]
      const rating = parseInt(selectedRating.value)
      this.votes[logo] = rating
      console.log(`Rated ${logo}: ${rating}`)

      // Update ARIA attributes
      const ratingContainer = document.querySelector('.rating-container[role="radiogroup"]')
      if (ratingContainer) {
        ratingContainer.setAttribute('aria-describedby', `rating-selected-${rating}`)
      }

      this.updateNavigation()
      this.announceToScreenReader(`Note attribuée : ${this.getRatingLabel(rating)}`)
    }
  }

  /**
   * Update progress bar ARIA attributes
   */
  updateProgressBarAria() {
    const progressBar = document.querySelector('.progress-bar[role="progressbar"]')
    if (progressBar) {
      progressBar.setAttribute('aria-valuenow', this.currentLogoIndex + 1)
      progressBar.setAttribute('aria-valuemax', this.logos.length)
      progressBar.setAttribute('aria-valuetext', `Logo ${this.currentLogoIndex + 1} sur ${this.logos.length}`)
    }
  }

  /**
   * Go to previous logo
   */
  previousLogo() {
    if (this.currentLogoIndex > 0) {
      this.currentLogoIndex--
      this.displayCurrentLogo()
      this.updateProgress()

      // Focus on the current rating if one is selected
      const currentRating = document.querySelector('input[name="rating"]:checked')
      if (currentRating) {
        currentRating.focus()
      }
    } else {
      this.announceToScreenReader('Déjà au premier logo')
    }
  }

  /**
   * Go to next logo or finish voting
   */
  nextLogo() {
    const currentLogo = this.logos[this.currentLogoIndex]
    const hasRating = this.votes.hasOwnProperty(currentLogo)

    if (!hasRating) {
      this.showError('Veuillez attribuer une note avant de continuer')
      this.announceToScreenReader('Une note est requise pour ce logo')
      // Focus on first rating option
      const firstRating = document.querySelector('input[name="rating"]')
      if (firstRating) {
        firstRating.focus()
      }
      return
    }

    if (this.currentLogoIndex < this.logos.length - 1) {
      this.currentLogoIndex++
      this.displayCurrentLogo()
      this.updateProgress()
    } else {
      this.showReviewScreen()
    }
  }

  /**
   * Update progress bar
   */
  updateProgress() {
    const progress = ((this.currentLogoIndex + 1) / this.logos.length) * 100
    document.getElementById('progress-fill').style.width = `${progress}%`
    document.getElementById('progress-text').textContent = `Logo ${this.currentLogoIndex + 1} sur ${this.logos.length}`
  }

  /**
   * Update navigation buttons state
   */
  updateNavigation() {
    const prevBtn = document.getElementById('prev-btn')
    const nextBtn = document.getElementById('next-btn')

    prevBtn.disabled = this.currentLogoIndex === 0

    const currentLogo = this.logos[this.currentLogoIndex]
    const hasRating = this.votes.hasOwnProperty(currentLogo)
    nextBtn.disabled = !hasRating

    // Update button text for last logo
    if (this.currentLogoIndex === this.logos.length - 1) {
      nextBtn.textContent = 'Terminer'
    } else {
      nextBtn.textContent = 'Suivant'
    }
  }

  /**
   * Show review screen
   */
  showReviewScreen() {
    // Check if all logos have been rated
    const unratedLogos = this.logos.filter(logo => !this.votes.hasOwnProperty(logo))
    if (unratedLogos.length > 0) {
      this.showError(`Évaluations manquantes pour: ${unratedLogos.join(', ')}`)
      this.announceToScreenReader(`${unratedLogos.length} logo(s) sans note`)
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
    const reviewGrid = document.getElementById('review-grid')
    reviewGrid.innerHTML = ''

    this.logos.forEach((logo, index) => {
      const rating = this.votes[logo]
      const card = document.createElement('div')
      card.className = 'review-card'
      card.dataset.logoIndex = index
      card.setAttribute('role', 'gridcell')
      card.setAttribute('tabindex', '0')
      card.setAttribute('aria-label', `Logo ${index + 1}, note: ${this.getRatingLabel(rating)}`)

      const ratingClass = rating > 0 ? 'positive' : rating < 0 ? 'negative' : 'neutral'
      const ratingText = rating > 0 ? `+${rating}` : rating.toString()

      card.innerHTML = `
                <img src="/logos/${logo}" alt="Logo ${index + 1}" class="review-logo">
                <div class="review-rating">
                    <span class="review-rating-value ${ratingClass}">${ratingText}</span>
                    <span class="review-rating-label">${this.getRatingLabel(rating)}</span>
                </div>
            `

      // Add keyboard support
      card.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          this.editVote(card)
        }
      })

      reviewGrid.appendChild(card)
    })

    // Focus first card for keyboard navigation
    const firstCard = reviewGrid.querySelector('.review-card')
    if (firstCard) {
      firstCard.focus()
    }
  }

  /**
   * Edit vote from review screen
   */
  editVote(card) {
    const logoIndex = parseInt(card.dataset.logoIndex)
    this.currentLogoIndex = logoIndex

    // Visual feedback
    card.classList.add('editing')

    // Announce to screen reader
    this.announceToScreenReader(`Modification du logo ${logoIndex + 1}`)

    setTimeout(() => {
      this.showVotingScreen()
    }, 200)
  }

  /**
   * Submit all votes
   */
  async submitVotes() {
    try {
      // Validate all votes are present
      const missingVotes = this.logos.filter(logo => !this.votes.hasOwnProperty(logo))
      if (missingVotes.length > 0) {
        this.showError(`Évaluations manquantes: ${missingVotes.join(', ')}`)
        this.announceToScreenReader(`Erreur: ${missingVotes.length} évaluations manquantes`)
        return
      }

      // Disable submit button to prevent double submission
      const submitBtn = document.getElementById('submit-votes')
      const originalText = submitBtn.textContent
      submitBtn.disabled = true
      submitBtn.setAttribute('aria-busy', 'true')
      submitBtn.innerHTML = '<span class="spinner" aria-hidden="true"></span> Envoi en cours...'

      this.announceToScreenReader('Envoi de vos votes en cours...')

      const voteData = {
        voter_first_name: this.voterFirstName,
        voter_last_name: this.voterLastName,
        ratings: this.votes
      }

      console.log('Submitting votes:', voteData)

      const response = await fetch('/api/vote', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(voteData),
        signal: AbortSignal.timeout(10000) // 10 second timeout
      })

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage
        try {
          const errorData = JSON.parse(errorText)
          errorMessage = errorData.message || errorData.detail || 'Erreur serveur'
        } catch {
          errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      const result = await response.json()

      if (result.success) {
        this.showSuccessScreen()
      } else {
        throw new Error(result.message || "Erreur lors de l'envoi du vote")
      }
    } catch (error) {
      console.error('Error submitting votes:', error)

      let errorMessage
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        errorMessage = 'Timeout: la requête a pris trop de temps. Veuillez réessayer.'
      } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorMessage = 'Erreur de connexion. Vérifiez votre connexion internet et réessayez.'
      } else {
        errorMessage = error.message || "Erreur lors de l'envoi du vote"
      }

      this.showError(errorMessage)
      this.announceToScreenReader(`Erreur: ${errorMessage}`)

      // Re-enable submit button
      const submitBtn = document.getElementById('submit-votes')
      submitBtn.disabled = false
      submitBtn.setAttribute('aria-busy', 'false')
      submitBtn.textContent = 'Confirmer et envoyer'
      submitBtn.focus()
    }
  }

  /**
   * Show success screen
   */
  showSuccessScreen() {
    this.currentScreen = 'success'
    this.updateScreen()
    console.log('Votes submitted successfully')

    // Focus management
    const successTitle = document.getElementById('success-title')
    if (successTitle) {
      successTitle.focus()
    }

    this.announceToScreenReader('Votes envoyés avec succès! Merci pour votre participation.')
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
    errorDiv.className = 'error-message show'
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
   * Save votes to localStorage as backup
   */
  saveVotesToStorage() {
    try {
      const voteData = {
        voterName: this.voterName,
        votes: this.votes,
        timestamp: Date.now()
      }
      localStorage.setItem('cardinal-votes-backup', JSON.stringify(voteData))
    } catch (error) {
      console.warn('Could not save votes to localStorage:', error)
    }
  }

  /**
   * Load votes from localStorage if available
   */
  loadVotesFromStorage() {
    try {
      const stored = localStorage.getItem('cardinal-votes-backup')
      if (stored) {
        const voteData = JSON.parse(stored)
        // Only restore if less than 1 hour old
        if (Date.now() - voteData.timestamp < 3600000) {
          this.voterName = voteData.voterName || ''
          this.votes = voteData.votes || {}
          return true
        }
      }
    } catch (error) {
      console.warn('Could not load votes from localStorage:', error)
    }
    return false
  }

  /**
   * Clear votes from localStorage
   */
  clearVotesFromStorage() {
    try {
      localStorage.removeItem('cardinal-votes-backup')
    } catch (error) {
      console.warn('Could not clear votes from localStorage:', error)
    }
  }

  /**
   * Load and display voter counter
   */
  async loadVoterCounter() {
    const voterCounter = document.getElementById('voter-counter')
    if (!voterCounter) return

    try {
      const response = await fetch('/api/results', {
        signal: AbortSignal.timeout(5000) // 5 second timeout
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      const voterCount = data.total_voters || 0

      // Update counter display
      voterCounter.classList.remove('loading', 'error')

      if (voterCount === 0) {
        voterCounter.innerHTML = '<span>Soyez le premier à voter !</span>'
      } else if (voterCount === 1) {
        voterCounter.innerHTML = '<span><span class="voter-counter-number">1</span> personne a déjà voté</span>'
      } else {
        voterCounter.innerHTML = `<span><span class="voter-counter-number">${voterCount}</span> personnes ont déjà voté</span>`
      }

      // Announce to screen readers
      this.announceToScreenReader(
        `Compteur de votes mis à jour: ${voterCount} ${voterCount <= 1 ? 'personne a' : 'personnes ont'} déjà voté`
      )
    } catch (error) {
      console.warn('Failed to load voter counter:', error)

      voterCounter.classList.remove('loading')
      voterCounter.classList.add('error')
      voterCounter.innerHTML = '<span>Impossible de charger le compteur</span>'

      // Don't announce errors to screen readers as it's not critical
    }
  }
}

/**
 * Results page functionality
 */
class ResultsApp {
  constructor() {
    if (window.location.pathname === '/results') {
      this.liveRegion = document.getElementById('live-region')
      this.initializeEventListeners()
      this.loadResults()
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
   * Initialize event listeners
   */
  initializeEventListeners() {
    // Share button
    const shareBtn = document.getElementById('share-results')
    if (shareBtn) {
      shareBtn.addEventListener('click', () => this.showShareModal())
    }

    // Export button
    const exportBtn = document.getElementById('export-results')
    if (exportBtn) {
      exportBtn.addEventListener('click', () => this.exportResults())
    }

    // Toggle detailed votes
    const toggleBtn = document.getElementById('toggle-detailed-votes')
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.toggleDetailedVotes())
    }

    // Modal close
    const closeModal = document.getElementById('close-share-modal')
    if (closeModal) {
      closeModal.addEventListener('click', () => this.hideShareModal())
    }

    // Share options
    document.addEventListener('click', e => {
      const shareOption = e.target.closest('.share-option')
      if (shareOption) {
        const platform = shareOption.dataset.platform
        this.shareOnPlatform(platform)
      }
    })

    // Keyboard navigation for modal
    document.addEventListener('keydown', e => {
      const modal = document.getElementById('share-modal')
      if (modal && modal.getAttribute('aria-hidden') === 'false') {
        if (e.key === 'Escape') {
          this.hideShareModal()
        }
      }
    })
  }

  /**
   * Show share modal
   */
  showShareModal() {
    const modal = document.getElementById('share-modal')
    if (modal) {
      modal.style.display = 'flex'
      modal.setAttribute('aria-hidden', 'false')

      // Focus first share option
      const firstOption = modal.querySelector('.share-option')
      if (firstOption) {
        firstOption.focus()
      }

      this.announceToScreenReader('Fenêtre de partage ouverte')
    }
  }

  /**
   * Hide share modal
   */
  hideShareModal() {
    const modal = document.getElementById('share-modal')
    if (modal) {
      modal.style.display = 'none'
      modal.setAttribute('aria-hidden', 'true')

      // Return focus to share button
      const shareBtn = document.getElementById('share-results')
      if (shareBtn) {
        shareBtn.focus()
      }
    }
  }

  /**
   * Share on social platform
   */
  shareOnPlatform(platform) {
    const url = window.location.href
    const text = "Découvrez les résultats du vote pour le logo ToV'éCo!"

    let shareUrl
    switch (platform) {
      case 'twitter':
        shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`
        break
      case 'facebook':
        shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`
        break
      case 'linkedin':
        shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`
        break
      case 'copy':
        if (navigator.clipboard) {
          navigator.clipboard.writeText(url).then(() => {
            this.announceToScreenReader('Lien copié dans le presse-papiers')
            this.showTemporaryMessage('Lien copié!')
          })
        } else {
          // Fallback for older browsers
          const textArea = document.createElement('textarea')
          textArea.value = url
          document.body.appendChild(textArea)
          textArea.select()
          document.execCommand('copy')
          document.body.removeChild(textArea)
          this.announceToScreenReader('Lien copié dans le presse-papiers')
          this.showTemporaryMessage('Lien copié!')
        }
        this.hideShareModal()
        return
    }

    if (shareUrl) {
      window.open(shareUrl, '_blank', 'width=600,height=400')
      this.hideShareModal()
      this.announceToScreenReader(`Partage sur ${platform} ouvert`)
    }
  }

  /**
   * Export results as image or PDF
   */
  exportResults() {
    // For now, just trigger print dialog
    this.announceToScreenReader("Ouverture de la boîte de dialogue d'impression")
    window.print()
  }

  /**
   * Show temporary success message
   */
  showTemporaryMessage(message) {
    const messageDiv = document.createElement('div')
    messageDiv.className = 'temporary-message'
    messageDiv.textContent = message
    messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success-color);
            color: white;
            padding: 1rem;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-lg);
            z-index: 1001;
            animation: slideInRight 0.3s ease-out;
        `

    document.body.appendChild(messageDiv)

    setTimeout(() => {
      messageDiv.style.animation = 'slideOutRight 0.3s ease-in'
      setTimeout(() => {
        if (messageDiv.parentNode) {
          messageDiv.remove()
        }
      }, 300)
    }, 2000)
  }

  async loadResults() {
    const loadingState = document.getElementById('loading-state')
    const errorState = document.getElementById('error-state')
    const resultsContent = document.getElementById('results-content')

    try {
      this.announceToScreenReader('Chargement des résultats...')

      const response = await fetch('/api/results?include_votes=true', {
        signal: AbortSignal.timeout(10000)
      })

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage
        try {
          const errorData = JSON.parse(errorText)
          errorMessage = errorData.message || 'Erreur serveur'
        } catch {
          errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      const data = await response.json()

      // Hide loading state
      if (loadingState) {
        loadingState.style.display = 'none'
      }

      this.displayResults(data)

      // Show results content
      if (resultsContent) {
        resultsContent.style.display = 'block'
      }

      this.announceToScreenReader('Résultats chargés avec succès')
    } catch (error) {
      console.error('Error loading results:', error)

      // Hide loading state
      if (loadingState) {
        loadingState.style.display = 'none'
      }

      let errorMessage
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        errorMessage = 'Timeout: la requête a pris trop de temps. Veuillez réessayer.'
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage = 'Erreur de connexion. Vérifiez votre connexion internet.'
      } else {
        errorMessage = error.message || 'Impossible de charger les résultats'
      }

      this.showError(errorMessage)
      this.announceToScreenReader(`Erreur: ${errorMessage}`)
    }
  }

  displayResults(data) {
    // Update statistics
    const totalVoters = document.getElementById('total-voters')
    const totalLogos = document.getElementById('total-logos')
    const totalVotes = document.getElementById('total-votes')

    if (totalVoters) {
      totalVoters.textContent = data.total_voters || 0
    }
    if (totalLogos) {
      totalLogos.textContent = Object.keys(data.summary || {}).length
    }
    if (totalVotes) {
      // Calculate total evaluations
      const totalEvaluations = Object.values(data.summary || {}).reduce(
        (sum, stats) => sum + (stats.total_votes || 0),
        0
      )
      totalVotes.textContent = totalEvaluations
    }

    // Display results grid
    const resultsGrid = document.getElementById('results-grid')
    if (resultsGrid && data.summary) {
      const sortedResults = Object.entries(data.summary).sort(
        (a, b) => (b[1].total_score || 0) - (a[1].total_score || 0)
      )

      // Calculate score distribution for color coding
      const scores = sortedResults.map(([, stats]) => stats.total_score || 0)
      const colorClasses = this.calculateColorClasses(scores)

      const resultsHTML = sortedResults
        .map(([logo, stats], index) => {
          const ranking = index + 1
          const scoreClass = stats.total_score > 0 ? 'positive' : stats.total_score < 0 ? 'negative' : 'neutral'
          const scoreText = stats.total_score > 0 ? `+${stats.total_score}` : `${stats.total_score}`
          const isWinner = ranking === 1
          const colorClass = colorClasses[index]

          return `
                        <div class="result-card ${isWinner ? 'winner' : ''} ${colorClass}" role="listitem" aria-label="Rang ${ranking}: Logo avec score total ${scoreText}">
                            <div class="result-rank">${ranking}</div>
                            <img src="/logos/${logo}" alt="Logo classement ${ranking}" class="result-logo" loading="lazy">
                            <div class="result-info">
                                <div class="result-score ${scoreClass}">${scoreText}</div>
                                <div class="result-votes">${stats.total_votes} vote${stats.total_votes > 1 ? 's' : ''}</div>
                            </div>
                        </div>
                    `
        })
        .join('')

      resultsGrid.innerHTML = resultsHTML
    }

    // Build detailed voting table if individual votes are available
    if (data.votes && data.votes.length > 0) {
      this.buildDetailedVotingTable(data.votes, data.summary)
    }

    // Focus on results title
    const resultsTitle = document.getElementById('results-title')
    if (resultsTitle) {
      resultsTitle.focus()
    }
  }

  /**
   * Calculate color classes based on score distribution
   */
  calculateColorClasses(scores) {
    if (scores.length === 0) return []
    if (scores.length === 1) return ['score-medium']

    const minScore = Math.min(...scores)
    const maxScore = Math.max(...scores)
    const scoreRange = maxScore - minScore

    // If all scores are the same, use medium color
    if (scoreRange === 0) {
      return new Array(scores.length).fill('score-medium')
    }

    return scores.map(score => {
      // Normalize score to 0-1 range
      const normalizedScore = (score - minScore) / scoreRange

      // Map to color classes (7 levels for smooth gradient)
      if (normalizedScore >= 0.95) return 'score-highest'
      if (normalizedScore >= 0.75) return 'score-high'
      if (normalizedScore >= 0.6) return 'score-medium-high'
      if (normalizedScore >= 0.4) return 'score-medium'
      if (normalizedScore >= 0.25) return 'score-medium-low'
      if (normalizedScore >= 0.05) return 'score-low'
      return 'score-lowest'
    })
  }

  showError(message) {
    const errorState = document.getElementById('error-state')
    const errorMessage = document.getElementById('error-message')

    if (errorState && errorMessage) {
      errorMessage.textContent = message
      errorState.style.display = 'flex'

      // Focus the retry button
      const retryBtn = document.getElementById('retry-btn')
      if (retryBtn) {
        retryBtn.focus()
      }
    }
  }

  /**
   * Toggle detailed votes table visibility
   */
  toggleDetailedVotes() {
    const toggleBtn = document.getElementById('toggle-detailed-votes')
    const content = document.getElementById('detailed-votes-content')
    const toggleText = toggleBtn.querySelector('.toggle-text')
    const toggleIcon = toggleBtn.querySelector('.toggle-icon')

    const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true'

    if (isExpanded) {
      // Hide table
      content.style.display = 'none'
      toggleBtn.setAttribute('aria-expanded', 'false')
      toggleText.textContent = 'Afficher'
      toggleIcon.textContent = '▼'
      this.announceToScreenReader('Tableau des votes masqué')
    } else {
      // Show table
      content.style.display = 'block'
      toggleBtn.setAttribute('aria-expanded', 'true')
      toggleText.textContent = 'Masquer'
      toggleIcon.textContent = '▲'
      this.announceToScreenReader('Tableau des votes affiché')
    }
  }

  /**
   * Build detailed voting table from individual votes
   */
  buildDetailedVotingTable(votes, summary) {
    const table = document.getElementById('detailed-votes-table')
    if (!table || !votes || votes.length === 0) return

    // Get all logos sorted alphabetically
    const allLogos = Object.keys(summary).sort()

    // Build table header
    const thead = document.createElement('thead')
    const headerRow = document.createElement('tr')

    // First column: Voter name
    const voterHeader = document.createElement('th')
    voterHeader.className = 'voter-name-header'
    voterHeader.textContent = 'Votant'
    voterHeader.setAttribute('scope', 'col')
    headerRow.appendChild(voterHeader)

    // Logo columns
    allLogos.forEach(logo => {
      const logoHeader = document.createElement('th')
      logoHeader.className = 'logo-header'
      logoHeader.setAttribute('scope', 'col')
      logoHeader.setAttribute('aria-label', `Votes pour ${logo}`)

      // Add logo number (e.g., "1" for "cardinal1.png")
      const logoNumber = logo.match(/\d+/)?.[0] || logo
      logoHeader.innerHTML = `
                <div class="logo-header-content">
                    <img src="/logos/${logo}" alt="Logo ${logoNumber}" class="logo-header-img" loading="lazy">
                    <span class="logo-number">${logoNumber}</span>
                </div>
            `
      headerRow.appendChild(logoHeader)
    })

    thead.appendChild(headerRow)

    // Build table body
    const tbody = document.createElement('tbody')

    votes.forEach((vote, index) => {
      const row = document.createElement('tr')
      row.className = index % 2 === 0 ? 'row-even' : 'row-odd'

      // Voter name cell
      const voterCell = document.createElement('td')
      voterCell.className = 'voter-name-cell'
      voterCell.textContent = vote.voter_name
      voterCell.setAttribute('scope', 'row')
      row.appendChild(voterCell)

      // Score cells for each logo
      allLogos.forEach(logo => {
        const scoreCell = document.createElement('td')
        scoreCell.className = 'score-cell'

        const rating = vote.ratings[logo]
        if (rating !== undefined) {
          const scoreClass = this.getScoreClass(rating)
          const scoreText = rating > 0 ? `+${rating}` : rating.toString()

          scoreCell.innerHTML = `<span class="score-value ${scoreClass}">${scoreText}</span>`
          scoreCell.setAttribute('aria-label', `${vote.voter_name}: ${this.getRatingLabel(rating)} pour logo ${logo}`)
        } else {
          scoreCell.innerHTML = '<span class="score-missing">-</span>'
          scoreCell.setAttribute('aria-label', `${vote.voter_name}: pas de vote pour logo ${logo}`)
        }

        row.appendChild(scoreCell)
      })

      tbody.appendChild(row)
    })

    // Clear table and add new content
    table.innerHTML = ''
    table.appendChild(thead)
    table.appendChild(tbody)

    // Announce table creation
    this.announceToScreenReader(`Tableau détaillé créé avec ${votes.length} votants et ${allLogos.length} logos`)
  }

  /**
   * Get CSS class for score color coding
   */
  getScoreClass(rating) {
    if (rating > 0) return 'score-positive'
    if (rating < 0) return 'score-negative'
    return 'score-neutral'
  }

  /**
   * Get rating label for accessibility
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
}

// Initialize the appropriate app based on the current page
document.addEventListener('DOMContentLoaded', () => {
  try {
    if (window.location.pathname === '/results') {
      new ResultsApp()
    } else {
      new VotingApp()
    }
  } catch (error) {
    console.error('Failed to initialize app:', error)

    // Show fallback error message
    const fallbackError = document.createElement('div')
    fallbackError.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #dc2626;">
                <h2>Erreur d'initialisation</h2>
                <p>Une erreur est survenue lors du chargement de l'application.</p>
                <button onclick="window.location.reload()" style="margin: 1rem; padding: 0.5rem 1rem; border: none; background: #2D5820; color: white; border-radius: 4px; cursor: pointer;">
                    Recharger la page
                </button>
            </div>
        `
    document.body.appendChild(fallbackError)
  }
})

// Add CSS animations for temporary messages
if (!document.querySelector('#temp-animations')) {
  const style = document.createElement('style')
  style.id = 'temp-animations'
  style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `
  document.head.appendChild(style)
}

// Global error handling
window.addEventListener('error', event => {
  console.error('Global error:', event.error)
  // Could send to analytics or error reporting service
})

window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled promise rejection:', event.reason)
  // Could send to analytics or error reporting service
})
