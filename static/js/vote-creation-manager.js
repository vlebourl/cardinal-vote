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
      case 'remove-image': {
        const optionId = element.dataset.optionId
        this.removeImage(optionId)
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

        <!-- Enhanced Image Upload Interface -->
        <div class="option-image-upload" data-option-id="${optionId}">
          <input type="file" id="image-${optionId}" accept=".png,.jpg,.jpeg,.gif,.webp" class="image-input">

          <div class="upload-content" onclick="document.getElementById('image-${optionId}').click()">
            <span class="material-icons upload-icon">cloud_upload</span>
            <div class="upload-text">Click or drag image here</div>
            <div class="upload-hint">PNG, JPG, GIF, WebP (max 10MB)</div>
          </div>

          <div class="upload-progress">
            <span class="material-icons">cloud_upload</span>
            <div class="upload-progress-text">Uploading image...</div>
          </div>
        </div>

        <div class="image-preview-container" id="preview-${optionId}" style="display: none;">
          <!-- Image preview will be inserted here dynamically -->
        </div>

        <div class="upload-error" id="error-${optionId}" style="display: none;">
          <span class="material-icons">error</span>
          <span class="error-message"></span>
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

      // Initialize image upload functionality for the new option
      this.initializeImageUpload(optionId)
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
      .map((input, index) => {
        const optionId = input.id
        const previewContainer = document.getElementById(`preview-${optionId}`)

        // Check if this option has an uploaded image
        let imageData = null
        if (previewContainer && previewContainer.dataset.imageFilename) {
          imageData = {
            filename: previewContainer.dataset.imageFilename,
            info: JSON.parse(previewContainer.dataset.imageInfo || '{}')
          }
        }

        return {
          option_type: imageData ? 'image' : 'text',
          title: input.value.trim(),
          content: input.value.trim(),
          display_order: index,
          image_filename: imageData ? imageData.filename : null
        }
      })
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

  // Enhanced Image Upload Interface Methods
  initializeImageUpload(optionId) {
    const uploadContainer = document.querySelector(`.option-image-upload[data-option-id="${optionId}"]`)
    const fileInput = document.getElementById(`image-${optionId}`)

    if (!uploadContainer || !fileInput) return

    // File input change handler
    fileInput.addEventListener('change', e => {
      this.handleImageFileSelect(e, optionId)
    })

    // Drag and drop handlers
    uploadContainer.addEventListener('dragover', e => {
      e.preventDefault()
      uploadContainer.classList.add('drag-over')
    })

    uploadContainer.addEventListener('dragleave', e => {
      e.preventDefault()
      uploadContainer.classList.remove('drag-over')
    })

    uploadContainer.addEventListener('drop', e => {
      e.preventDefault()
      uploadContainer.classList.remove('drag-over')

      const files = e.dataTransfer.files
      if (files.length > 0) {
        this.handleImageFile(files[0], optionId)
      }
    })
  }

  async handleImageFileSelect(event, optionId) {
    const file = event.target.files[0]
    if (file) {
      await this.handleImageFile(file, optionId)
    }
  }

  async handleImageFile(file, optionId) {
    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp']
    if (!allowedTypes.includes(file.type)) {
      this.showImageError(optionId, 'Please select a valid image file (PNG, JPG, GIF, WebP)')
      return
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      this.showImageError(optionId, 'File size must be less than 10MB')
      return
    }

    // Clear any previous errors
    this.clearImageError(optionId)

    // Show upload progress
    this.setImageUploadState(optionId, 'uploading')

    try {
      const uploadedImageData = await this.uploadImageFile(file)
      this.showImagePreview(optionId, uploadedImageData, file)
      this.setImageUploadState(optionId, 'uploaded')
    } catch (error) {
      console.error('Image upload error:', error)
      this.showImageError(optionId, error.message || 'Failed to upload image')
      this.setImageUploadState(optionId, 'error')
    }
  }

  async uploadImageFile(file) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${this.API_BASE}/votes/images/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.getAccessToken()}`
      },
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Upload failed')
    }

    return await response.json()
  }

  showImagePreview(optionId, imageData, file) {
    const previewContainer = document.getElementById(`preview-${optionId}`)

    if (previewContainer) {
      // Create image preview HTML
      const previewHtml = `
        <div class="image-preview">
          <img src="/uploads/${imageData.filename}" alt="${file.name}" class="image-thumbnail">
          <div class="image-info">
            <div class="image-filename">${file.name}</div>
            <div class="image-details">${this.formatFileSize(file.size)} • ${imageData.width}×${imageData.height}px</div>
          </div>
          <button type="button" class="remove-image-btn" data-action="remove-image" data-option-id="${optionId}">
            <span class="material-icons">close</span>
          </button>
        </div>
      `

      previewContainer.innerHTML = previewHtml
      previewContainer.style.display = 'block'

      // Store image data for form submission
      previewContainer.dataset.imageFilename = imageData.filename
      previewContainer.dataset.imageInfo = JSON.stringify(imageData)

      // Add remove image handler
      const removeBtn = previewContainer.querySelector('.remove-image-btn')
      if (removeBtn) {
        removeBtn.addEventListener('click', () => this.removeImage(optionId))
      }
    }
  }

  removeImage(optionId) {
    const previewContainer = document.getElementById(`preview-${optionId}`)
    const fileInput = document.getElementById(`image-${optionId}`)

    if (previewContainer) {
      previewContainer.style.display = 'none'
      previewContainer.innerHTML = ''
      delete previewContainer.dataset.imageFilename
      delete previewContainer.dataset.imageInfo
    }

    if (fileInput) {
      fileInput.value = ''
    }

    this.setImageUploadState(optionId, 'ready')
  }

  setImageUploadState(optionId, state) {
    const uploadContainer = document.querySelector(`.option-image-upload[data-option-id="${optionId}"]`)

    if (uploadContainer) {
      // Reset all states
      uploadContainer.classList.remove('uploading', 'uploaded', 'error')

      switch (state) {
        case 'uploading':
          uploadContainer.classList.add('uploading')
          break
        case 'uploaded':
          uploadContainer.classList.add('uploaded')
          uploadContainer.style.display = 'none' // Hide upload area when image is uploaded
          break
        case 'error':
          uploadContainer.classList.add('error')
          break
        case 'ready':
          uploadContainer.style.display = 'block' // Show upload area again
          break
      }
    }
  }

  showImageError(optionId, message) {
    const errorContainer = document.getElementById(`error-${optionId}`)

    if (errorContainer) {
      const errorMessage = errorContainer.querySelector('.error-message')
      if (errorMessage) {
        errorMessage.textContent = message
      }
      errorContainer.style.display = 'flex'
    }
  }

  clearImageError(optionId) {
    const errorContainer = document.getElementById(`error-${optionId}`)

    if (errorContainer) {
      errorContainer.style.display = 'none'
    }
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes'

    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
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
