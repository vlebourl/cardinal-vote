// Vote Creation Manager - Material Design 3
// Handles vote creation modal functionality, dynamic options, and form submission

class VoteCreationManager {
  constructor() {
    this.API_BASE = '/api'
    this.maxOptions = 20
    this.minOptions = 2
    this.currentOptionCount = 0
    this.modal = null
    this.form = null
    this.optionsContainer = null
    this.addOptionBtn = null
    this.optionCounter = null
    this.accessCodeField = null
    this.useAccessCodeSwitch = null
  }

  static init() {
    const manager = new VoteCreationManager()
    manager.initializeElements()
    manager.initializeEventListeners()
    manager.initializeDefaultOptions()
  }

  initializeElements() {
    this.modal = document.getElementById('voteCreationModalScrim')
    this.form = document.getElementById('voteCreationForm')
    this.optionsContainer = document.getElementById('voteOptionsContainer')
    this.addOptionBtn = document.getElementById('addOptionBtn')
    this.optionCounter = document.querySelector('.option-counter')
    this.accessCodeField = document.getElementById('accessCodeField')
    this.useAccessCodeSwitch = document.getElementById('useAccessCode')
  }

  initializeEventListeners() {
    // Global click handler for data-action buttons
    document.addEventListener('click', e => {
      const action = e.target.closest('[data-action]')?.dataset.action
      if (action) {
        this.handleAction(action, e.target)
      }
    })

    // Form submission
    if (this.form) {
      this.form.addEventListener('submit', e => this.handleCreateVote(e))
    }

    // Access code toggle
    if (this.useAccessCodeSwitch) {
      this.useAccessCodeSwitch.addEventListener('change', e => {
        this.toggleAccessCodeField(e.target.checked)
      })
    }

    // Close modal on escape key
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && this.isModalOpen()) {
        this.closeModal()
      }
    })

    // Close modal when clicking on scrim
    if (this.modal) {
      this.modal.addEventListener('click', e => {
        if (e.target === this.modal) {
          this.closeModal()
        }
      })
    }
  }

  handleAction(action, element) {
    switch (action) {
      case 'create-vote':
        this.showModal()
        break
      case 'close-modal':
        if (element.dataset.modal === 'vote-creation') {
          this.closeModal()
        }
        break
      case 'add-option':
        this.addOptionField()
        break
      case 'remove-option': {
        const optionId = element.dataset.optionId
        this.removeOptionField(optionId)
        break
      }
    }
  }

  showModal() {
    if (this.modal) {
      this.modal.classList.add('md-dialog-scrim-visible')
      this.modal.setAttribute('aria-hidden', 'false')

      // Focus first input
      const firstInput = this.modal.querySelector('input')
      if (firstInput) {
        setTimeout(() => firstInput.focus(), 100)
      }

      // Clear any previous errors and reset form
      this.clearErrors()
      this.resetForm()
    }
  }

  closeModal() {
    if (this.modal) {
      this.modal.classList.remove('md-dialog-scrim-visible')
      this.modal.setAttribute('aria-hidden', 'true')
      this.clearErrors()
    }
  }

  isModalOpen() {
    return this.modal && this.modal.classList.contains('md-dialog-scrim-visible')
  }

  initializeDefaultOptions() {
    // Clear existing options
    if (this.optionsContainer) {
      this.optionsContainer.innerHTML = ''
    }
    this.currentOptionCount = 0

    // Create initial 2 options
    this.addOptionField('Option 1', true)
    this.addOptionField('Option 2', true)
  }

  addOptionField(placeholder = '', isDefault = false) {
    if (this.currentOptionCount >= this.maxOptions) {
      this.showSnackbar(`Maximum ${this.maxOptions} options allowed`)
      return
    }

    const optionId = `option-${Date.now()}-${this.currentOptionCount}`
    const optionNumber = this.currentOptionCount + 1
    const optionHtml = `
      <div class="vote-option-field" data-option-id="${optionId}">
        <div class="md-text-field md-text-field-outlined">
          <input type="text" id="${optionId}" class="md-text-field-input option-input"
                 placeholder=" " required maxlength="200" value="${placeholder}">
          <label for="${optionId}" class="md-text-field-label">Option ${optionNumber}</label>
        </div>
        ${
          !isDefault && this.currentOptionCount >= this.minOptions
            ? `
        <button type="button" class="remove-option-btn"
                data-action="remove-option" data-option-id="${optionId}"
                aria-label="Remove option ${optionNumber}">
          <span class="material-icons">close</span>
        </button>
        `
            : ''
        }
      </div>
    `

    if (this.optionsContainer) {
      this.optionsContainer.insertAdjacentHTML('beforeend', optionHtml)
      this.currentOptionCount++
      this.updateOptionCounter()
      this.updateAddButtonState()
    }
  }

  removeOptionField(optionId) {
    if (this.currentOptionCount <= this.minOptions) {
      this.showSnackbar(`Minimum ${this.minOptions} options required`)
      return
    }

    const optionField = document.querySelector(`[data-option-id="${optionId}"]`)
    if (optionField) {
      // Add removing animation class
      optionField.classList.add('removing')

      // Remove after animation completes
      setTimeout(() => {
        optionField.remove()
        this.currentOptionCount--
        this.updateOptionCounter()
        this.updateAddButtonState()
        this.renumberOptions()
      }, 300)
    }
  }

  renumberOptions() {
    const options = document.querySelectorAll('.vote-option-field')
    options.forEach((option, index) => {
      const label = option.querySelector('.md-text-field-label')
      const removeBtn = option.querySelector('.remove-option-btn')
      const optionNumber = index + 1

      if (label) {
        label.textContent = `Option ${optionNumber}`
      }
      if (removeBtn) {
        removeBtn.setAttribute('aria-label', `Remove option ${optionNumber}`)
      }
    })
  }

  updateOptionCounter() {
    if (this.optionCounter) {
      this.optionCounter.textContent = `${this.currentOptionCount} of ${this.maxOptions} options`
    }
  }

  updateAddButtonState() {
    if (this.addOptionBtn) {
      if (this.currentOptionCount >= this.maxOptions) {
        this.addOptionBtn.disabled = true
        this.addOptionBtn.classList.add('disabled')
      } else {
        this.addOptionBtn.disabled = false
        this.addOptionBtn.classList.remove('disabled')
      }
    }
  }

  toggleAccessCodeField(show) {
    if (this.accessCodeField) {
      if (show) {
        this.accessCodeField.style.display = 'block'
        this.accessCodeField.classList.remove('hide')
        this.accessCodeField.classList.add('show')
      } else {
        this.accessCodeField.classList.remove('show')
        this.accessCodeField.classList.add('hide')
        setTimeout(() => {
          if (!document.getElementById('useAccessCode').checked) {
            this.accessCodeField.style.display = 'none'
          }
        }, 300)
      }
    }
  }

  async handleCreateVote(event) {
    event.preventDefault()

    const submitBtn = document.getElementById('createVoteBtn')
    const formData = this.collectFormData()

    if (!this.validateFormData(formData)) {
      return
    }

    this.setButtonLoading(submitBtn, true)
    this.clearErrors()

    try {
      const response = await fetch(`${this.API_BASE}/votes/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getAccessToken()}`
        },
        body: JSON.stringify(formData)
      })

      const data = await response.json()

      if (response.ok) {
        this.closeModal()
        this.showSnackbar('Vote created successfully!')

        // Redirect to vote preview with sharing options after short delay
        setTimeout(() => {
          window.location.href = `/vote-preview/${data.id}?sharing=true`
        }, 1500)
      } else {
        // Handle validation errors
        if (data.details && Array.isArray(data.details)) {
          const errorMessage = data.details.join(', ')
          this.showError(errorMessage)
        } else {
          this.showError(data.message || 'Failed to create vote. Please try again.')
        }
      }
    } catch (error) {
      console.error('Vote creation error:', error)
      this.showError('Network error. Please check your connection and try again.')
    } finally {
      this.setButtonLoading(submitBtn, false)
    }
  }

  collectFormData() {
    const title = document.getElementById('voteTitle').value.trim()
    const description = document.getElementById('voteDescription').value.trim()
    const requireAuth = document.getElementById('requireAuth').checked
    const useAccessCode = document.getElementById('useAccessCode').checked
    const accessCode = useAccessCode ? document.getElementById('accessCode').value.trim() : null

    const options = Array.from(document.querySelectorAll('.option-input'))
      .map((input, index) => ({
        option_type: 'text',
        title: input.value.trim(),
        content: input.value.trim(),
        display_order: index
      }))
      .filter(option => option.title.length > 0)

    return {
      title,
      description: description || null,
      options,
      require_auth: requireAuth,
      access_code: accessCode,
      starts_at: null, // For future enhancement
      ends_at: null // For future enhancement
    }
  }

  validateFormData(formData) {
    // Basic client-side validation
    if (!formData.title) {
      this.showError('Vote title is required')
      return false
    }

    if (formData.options.length < this.minOptions) {
      this.showError(`At least ${this.minOptions} options are required`)
      return false
    }

    if (formData.options.length > this.maxOptions) {
      this.showError(`Maximum ${this.maxOptions} options allowed`)
      return false
    }

    // Check for duplicate options
    const optionTitles = formData.options.map(opt => opt.title.toLowerCase())
    const duplicates = optionTitles.filter((title, index) => optionTitles.indexOf(title) !== index)
    if (duplicates.length > 0) {
      this.showError('Duplicate options are not allowed')
      return false
    }

    // Validate access code if enabled
    if (formData.access_code && formData.access_code.length < 4) {
      this.showError('Access code must be at least 4 characters long')
      return false
    }

    return true
  }

  resetForm() {
    if (this.form) {
      this.form.reset()
    }

    // Reset access code field
    if (this.accessCodeField) {
      this.accessCodeField.style.display = 'none'
      this.accessCodeField.classList.remove('show', 'hide')
    }

    // Reset options to default
    this.initializeDefaultOptions()
  }

  showError(message) {
    const errorElement = document.getElementById('voteCreationError')
    const messageElement = document.getElementById('voteCreationErrorMessage')

    if (errorElement && messageElement) {
      messageElement.textContent = message
      errorElement.style.display = 'flex'
    }
  }

  clearErrors() {
    const errorElement = document.getElementById('voteCreationError')
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
        textElement.style.display = 'none'
        loadingElement.style.display = 'inline-block'
      } else {
        button.disabled = false
        button.classList.remove('loading')
        textElement.style.display = 'inline'
        loadingElement.style.display = 'none'
      }
    }
  }

  // Utility methods
  getAccessToken() {
    return sessionStorage.getItem('access_token')
  }

  showSnackbar(message) {
    // Use existing snackbar function from dashboard
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

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  VoteCreationManager.init()
})
