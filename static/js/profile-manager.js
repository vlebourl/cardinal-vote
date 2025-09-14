// Profile Manager JavaScript
// Handles profile management functionality and user interactions

class ProfileManager {
  constructor() {
    this.API_BASE = '/api'
    this.currentUser = null
    this.modalScrim = null
    this.modal = null
    this.activeTab = 'info'
    this.isLoading = false
  }

  static init() {
    if (window.profileManager) return
    window.profileManager = new ProfileManager()
    window.profileManager.initializeElements()
    window.profileManager.initializeEventListeners()
  }

  initializeElements() {
    this.modalScrim = document.getElementById('profileModalScrim')
    this.modal = document.getElementById('profileModal')
  }

  initializeEventListeners() {
    // Profile info form submission
    const profileInfoForm = document.getElementById('profileInfoForm')
    if (profileInfoForm) {
      profileInfoForm.addEventListener('submit', e => {
        e.preventDefault()
        this.saveProfileInfo()
      })
    }

    // Password change form submission
    const passwordChangeForm = document.getElementById('passwordChangeForm')
    if (passwordChangeForm) {
      passwordChangeForm.addEventListener('submit', e => {
        e.preventDefault()
        this.changePassword()
      })
    }

    // Password strength checking
    const newPasswordInput = document.getElementById('newPassword')
    if (newPasswordInput) {
      newPasswordInput.addEventListener('input', e => {
        this.updatePasswordStrength(e.target.value)
      })
    }

    // Password confirmation validation
    const confirmPasswordInput = document.getElementById('confirmPassword')
    if (confirmPasswordInput) {
      confirmPasswordInput.addEventListener('input', () => {
        this.validatePasswordConfirmation()
      })
    }

    // Modal close on escape key
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && this.modalScrim && this.modalScrim.getAttribute('aria-hidden') === 'false') {
        this.closeModal()
      }
    })

    // Close modal when clicking outside
    if (this.modalScrim) {
      this.modalScrim.addEventListener('click', e => {
        if (e.target === this.modalScrim) {
          this.closeModal()
        }
      })
    }
  }

  openModal() {
    if (!this.modalScrim || !this.modal) return

    // Load current user data
    this.loadCurrentUser()

    // Show modal
    this.modalScrim.setAttribute('aria-hidden', 'false')
    this.modalScrim.style.display = 'flex'

    setTimeout(() => {
      this.modalScrim.classList.add('visible')
      this.modal.classList.add('visible')
    }, 10)

    // Focus first input
    const firstInput = document.getElementById('profileFirstName')
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 100)
    }
  }

  closeModal() {
    if (!this.modalScrim || !this.modal) return

    this.modalScrim.classList.remove('visible')
    this.modal.classList.remove('visible')

    setTimeout(() => {
      this.modalScrim.setAttribute('aria-hidden', 'true')
      this.modalScrim.style.display = 'none'
      this.resetForms()
    }, 200)
  }

  switchTab(tabName) {
    if (this.activeTab === tabName) return

    // Update tab buttons
    const tabs = document.querySelectorAll('.md-tab')
    tabs.forEach(tab => {
      const isActive = tab.dataset.tab === tabName
      tab.classList.toggle('md-tab-active', isActive)
      tab.setAttribute('aria-selected', isActive.toString())
    })

    // Update tab panels
    const panels = document.querySelectorAll('.md-tab-panel')
    panels.forEach(panel => {
      let panelId = `${tabName}-panel`
      if (tabName === 'info') {
        panelId = 'profile-info-panel'
      }
      const isActive = panel.id === panelId
      panel.classList.toggle('md-tab-panel-active', isActive)
    })

    // Update action buttons
    const saveProfileBtn = document.getElementById('saveProfileBtn')
    const changePasswordBtn = document.getElementById('changePasswordBtn')

    if (saveProfileBtn && changePasswordBtn) {
      if (tabName === 'info') {
        saveProfileBtn.style.display = 'flex'
        changePasswordBtn.style.display = 'none'
      } else if (tabName === 'password') {
        saveProfileBtn.style.display = 'none'
        changePasswordBtn.style.display = 'flex'
      } else {
        // Account tab - hide both buttons
        saveProfileBtn.style.display = 'none'
        changePasswordBtn.style.display = 'none'
      }
    }

    // Load account data when switching to account tab
    if (tabName === 'account') {
      this.loadAccountData()
    }

    this.activeTab = tabName
    this.clearMessages()
  }

  async loadCurrentUser() {
    const token = this.getAccessToken()
    if (!token) return

    try {
      const response = await fetch(`${this.API_BASE}/auth/profile`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        this.currentUser = await response.json()
        this.populateProfileForm()
        this.updateEmailVerificationStatus()
      } else {
        this.showError('profileInfo', 'Failed to load profile data')
      }
    } catch (error) {
      console.error('Error loading profile:', error)
      this.showError('profileInfo', 'Network error loading profile data')
    }
  }

  populateProfileForm() {
    if (!this.currentUser) return

    const firstNameInput = document.getElementById('profileFirstName')
    const lastNameInput = document.getElementById('profileLastName')
    const emailInput = document.getElementById('profileEmail')

    if (firstNameInput) firstNameInput.value = this.currentUser.first_name || ''
    if (lastNameInput) lastNameInput.value = this.currentUser.last_name || ''
    if (emailInput) emailInput.value = this.currentUser.email || ''
  }

  updateEmailVerificationStatus() {
    if (!this.currentUser) return

    const verificationIcon = document.getElementById('verificationIcon')
    const verificationText = document.getElementById('verificationText')
    const verificationDetails = document.getElementById('verificationDetails')

    if (verificationIcon && verificationText && verificationDetails) {
      const isVerified = this.currentUser.email_verified || false

      if (isVerified) {
        verificationIcon.textContent = 'verified'
        verificationIcon.className = 'material-icons verification-icon verified'
        verificationText.textContent = 'Email verified'
        verificationDetails.textContent = 'Your email address is verified and active.'
      } else {
        verificationIcon.textContent = 'warning'
        verificationIcon.className = 'material-icons verification-icon unverified'
        verificationText.textContent = 'Email not verified'
        verificationDetails.textContent = 'Please check your email for a verification link.'
      }
    }
  }

  async saveProfileInfo() {
    if (this.isLoading) return

    const firstNameInput = document.getElementById('profileFirstName')
    const lastNameInput = document.getElementById('profileLastName')
    const emailInput = document.getElementById('profileEmail')

    if (!firstNameInput || !lastNameInput || !emailInput) return

    // Validate inputs
    const firstName = firstNameInput.value.trim()
    const lastName = lastNameInput.value.trim()
    const email = emailInput.value.trim()

    if (!firstName || !lastName || !email) {
      this.showError('profileInfo', 'Please fill in all required fields')
      return
    }

    if (!this.isValidEmail(email)) {
      this.showError('profileInfo', 'Please enter a valid email address')
      return
    }

    this.setLoading('save', true)

    const token = this.getAccessToken()
    const updateData = {
      first_name: firstName,
      last_name: lastName,
      email
    }

    try {
      const response = await fetch(`${this.API_BASE}/auth/profile`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      })

      const result = await response.json()

      if (response.ok) {
        this.showSuccess('profileInfo', result.message || 'Profile updated successfully')

        // Update current user data
        this.currentUser = { ...this.currentUser, ...updateData }

        // Update display name in dashboard
        if (window.dashboard && window.dashboard.updateUserDisplay) {
          window.dashboard.user = this.currentUser
          window.dashboard.updateUserDisplay()
        }

        // If email changed, update verification status
        if (email !== this.currentUser.email) {
          this.updateEmailVerificationStatus()
        }
      } else {
        this.showError('profileInfo', result.detail || 'Failed to update profile')
      }
    } catch (error) {
      console.error('Error updating profile:', error)
      this.showError('profileInfo', 'Network error updating profile')
    } finally {
      this.setLoading('save', false)
    }
  }

  async changePassword() {
    if (this.isLoading) return

    const currentPasswordInput = document.getElementById('currentPassword')
    const newPasswordInput = document.getElementById('newPassword')
    const confirmPasswordInput = document.getElementById('confirmPassword')

    if (!currentPasswordInput || !newPasswordInput || !confirmPasswordInput) return

    const currentPassword = currentPasswordInput.value
    const newPassword = newPasswordInput.value
    const confirmPassword = confirmPasswordInput.value

    // Validate passwords
    if (!currentPassword || !newPassword || !confirmPassword) {
      this.showError('passwordChange', 'Please fill in all password fields')
      return
    }

    if (newPassword.length < 8) {
      this.showError('passwordChange', 'New password must be at least 8 characters long')
      return
    }

    if (newPassword !== confirmPassword) {
      this.showError('passwordChange', 'New passwords do not match')
      return
    }

    this.setLoading('changePassword', true)

    const token = this.getAccessToken()
    const passwordData = {
      current_password: currentPassword,
      new_password: newPassword
    }

    try {
      const response = await fetch(`${this.API_BASE}/auth/change-password`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(passwordData)
      })

      const result = await response.json()

      if (response.ok) {
        this.showSuccess('passwordChange', result.message || 'Password changed successfully')

        // Clear password form
        currentPasswordInput.value = ''
        newPasswordInput.value = ''
        confirmPasswordInput.value = ''
        this.hidePasswordStrength()
      } else {
        this.showError('passwordChange', result.detail || 'Failed to change password')
      }
    } catch (error) {
      console.error('Error changing password:', error)
      this.showError('passwordChange', 'Network error changing password')
    } finally {
      this.setLoading('changePassword', false)
    }
  }

  updatePasswordStrength(password) {
    const strengthContainer = document.getElementById('passwordStrength')
    const strengthBar = document.getElementById('strengthBar')
    const strengthText = document.getElementById('strengthText')

    if (!strengthContainer || !strengthBar || !strengthText) return

    if (!password) {
      strengthContainer.style.display = 'none'
      return
    }

    strengthContainer.style.display = 'block'

    const strength = this.calculatePasswordStrength(password)
    const strengthLevels = ['weak', 'fair', 'good', 'strong']
    const strengthLevel = strengthLevels[Math.min(strength, 3)]

    strengthBar.className = `strength-bar ${strengthLevel}`
    strengthText.textContent = strengthLevel.charAt(0).toUpperCase() + strengthLevel.slice(1)
  }

  calculatePasswordStrength(password) {
    let strength = 0

    if (password.length >= 8) strength++
    if (/[a-z]/.test(password)) strength++
    if (/[A-Z]/.test(password)) strength++
    if (/[0-9]/.test(password)) strength++
    if (/[^A-Za-z0-9]/.test(password)) strength++

    return Math.max(0, strength - 1)
  }

  validatePasswordConfirmation() {
    const newPasswordInput = document.getElementById('newPassword')
    const confirmPasswordInput = document.getElementById('confirmPassword')

    if (!newPasswordInput || !confirmPasswordInput) return

    const newPassword = newPasswordInput.value
    const confirmPassword = confirmPasswordInput.value

    if (confirmPassword && newPassword !== confirmPassword) {
      this.showFieldError(confirmPasswordInput, 'Passwords do not match')
    } else {
      this.clearFieldError(confirmPasswordInput)
    }
  }

  hidePasswordStrength() {
    const strengthContainer = document.getElementById('passwordStrength')
    if (strengthContainer) {
      strengthContainer.style.display = 'none'
    }
  }

  setLoading(buttonType, isLoading) {
    this.isLoading = isLoading

    const buttonId = buttonType === 'save' ? 'saveProfileBtn' : 'changePasswordBtn'
    const button = document.getElementById(buttonId)

    if (button) {
      const btnText = button.querySelector('.btn-text')
      const btnLoading = button.querySelector('.btn-loading')

      button.disabled = isLoading

      if (btnText && btnLoading) {
        if (isLoading) {
          btnText.style.display = 'none'
          btnLoading.style.display = 'inline-block'
          btnLoading.classList.add('rotating')
        } else {
          btnText.style.display = 'inline-block'
          btnLoading.style.display = 'none'
          btnLoading.classList.remove('rotating')
        }
      }
    }
  }

  showError(type, message) {
    const errorId = type === 'profileInfo' ? 'profileInfoError' : 'passwordChangeError'
    const messageId = type === 'profileInfo' ? 'profileInfoErrorMessage' : 'passwordChangeErrorMessage'

    const errorElement = document.getElementById(errorId)
    const messageElement = document.getElementById(messageId)

    if (errorElement && messageElement) {
      messageElement.textContent = message
      errorElement.style.display = 'flex'
    }

    // Hide success message
    const successId = type === 'profileInfo' ? 'profileInfoSuccess' : 'passwordChangeSuccess'
    const successElement = document.getElementById(successId)
    if (successElement) {
      successElement.style.display = 'none'
    }
  }

  showSuccess(type, message) {
    const successId = type === 'profileInfo' ? 'profileInfoSuccess' : 'passwordChangeSuccess'
    const messageId = type === 'profileInfo' ? 'profileInfoSuccessMessage' : 'passwordChangeSuccessMessage'

    const successElement = document.getElementById(successId)
    const messageElement = document.getElementById(messageId)

    if (successElement && messageElement) {
      messageElement.textContent = message
      successElement.style.display = 'flex'
    }

    // Hide error message
    const errorId = type === 'profileInfo' ? 'profileInfoError' : 'passwordChangeError'
    const errorElement = document.getElementById(errorId)
    if (errorElement) {
      errorElement.style.display = 'none'
    }
  }

  clearMessages() {
    const messageElements = ['profileInfoError', 'profileInfoSuccess', 'passwordChangeError', 'passwordChangeSuccess']

    messageElements.forEach(id => {
      const element = document.getElementById(id)
      if (element) {
        element.style.display = 'none'
      }
    })
  }

  showFieldError(inputElement, message) {
    inputElement.classList.add('md-text-field-error')

    let errorElement = inputElement.parentNode.querySelector('.field-error')
    if (!errorElement) {
      errorElement = document.createElement('div')
      errorElement.className = 'field-error'
      inputElement.parentNode.appendChild(errorElement)
    }

    errorElement.textContent = message
    errorElement.style.display = 'block'
  }

  clearFieldError(inputElement) {
    inputElement.classList.remove('md-text-field-error')

    const errorElement = inputElement.parentNode.querySelector('.field-error')
    if (errorElement) {
      errorElement.style.display = 'none'
    }
  }

  resetForms() {
    const profileForm = document.getElementById('profileInfoForm')
    const passwordForm = document.getElementById('passwordChangeForm')

    if (profileForm) profileForm.reset()
    if (passwordForm) passwordForm.reset()

    this.clearMessages()
    this.hidePasswordStrength()

    // Clear field errors
    const errorFields = document.querySelectorAll('.md-text-field-error')
    errorFields.forEach(field => {
      this.clearFieldError(field)
    })

    // Reset to info tab
    this.switchTab('info')
  }

  // Utility methods
  getAccessToken() {
    return sessionStorage.getItem('access_token')
  }

  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  // Account Management Methods
  async loadAccountData() {
    if (!this.currentUser) return

    // Populate account creation date
    const accountCreatedElement = document.getElementById('accountCreatedDate')
    if (accountCreatedElement && this.currentUser.created_at) {
      const createdDate = new Date(this.currentUser.created_at)
      accountCreatedElement.textContent = createdDate.toLocaleDateString()
    }

    // For now, we'll show placeholder data for vote count
    // In a real implementation, this would come from an API endpoint
    const totalVotesElement = document.getElementById('totalVotesCount')
    if (totalVotesElement) {
      totalVotesElement.textContent = '0' // Placeholder
    }

    // Last login would typically come from user data
    const lastLoginElement = document.getElementById('lastLoginDate')
    if (lastLoginElement) {
      lastLoginElement.textContent = 'Current session'
    }
  }

  showDeleteConfirmation() {
    const modalScrim = document.getElementById('deleteAccountModalScrim')
    const modal = document.querySelector('.delete-account-dialog')

    if (!modalScrim || !modal) return

    // Show modal
    modalScrim.setAttribute('aria-hidden', 'false')
    modalScrim.style.display = 'flex'

    setTimeout(() => {
      modalScrim.classList.add('visible')
      modal.classList.add('visible')
    }, 10)

    // Focus first input
    const confirmationInput = document.getElementById('deleteConfirmationInput')
    if (confirmationInput) {
      setTimeout(() => confirmationInput.focus(), 100)
    }

    // Set up confirmation validation
    this.setupDeletionValidation()
  }

  closeDeleteModal() {
    const modalScrim = document.getElementById('deleteAccountModalScrim')
    const modal = document.querySelector('.delete-account-dialog')

    if (!modalScrim || !modal) return

    modalScrim.classList.remove('visible')
    modal.classList.remove('visible')

    setTimeout(() => {
      modalScrim.setAttribute('aria-hidden', 'true')
      modalScrim.style.display = 'none'
      this.resetDeleteForm()
    }, 200)
  }

  setupDeletionValidation() {
    const confirmationInput = document.getElementById('deleteConfirmationInput')
    const passwordInput = document.getElementById('deletePasswordConfirmation')
    const confirmButton = document.getElementById('confirmDeleteBtn')

    if (!confirmationInput || !passwordInput || !confirmButton) return

    const validateForm = () => {
      const confirmationValid = confirmationInput.value.trim() === 'DELETE'
      const passwordValid = passwordInput.value.trim().length > 0

      confirmButton.disabled = !(confirmationValid && passwordValid)
    }

    confirmationInput.addEventListener('input', validateForm)
    passwordInput.addEventListener('input', validateForm)
  }

  resetDeleteForm() {
    const confirmationInput = document.getElementById('deleteConfirmationInput')
    const passwordInput = document.getElementById('deletePasswordConfirmation')
    const reasonInput = document.getElementById('deleteReasonInput')
    const confirmButton = document.getElementById('confirmDeleteBtn')
    const errorElement = document.getElementById('deleteAccountError')

    if (confirmationInput) confirmationInput.value = ''
    if (passwordInput) passwordInput.value = ''
    if (reasonInput) reasonInput.value = ''
    if (confirmButton) confirmButton.disabled = true
    if (errorElement) errorElement.style.display = 'none'
  }

  async confirmAccountDeletion() {
    if (this.isLoading) return

    const confirmationInput = document.getElementById('deleteConfirmationInput')
    const passwordInput = document.getElementById('deletePasswordConfirmation')
    const reasonInput = document.getElementById('deleteReasonInput')

    if (!confirmationInput || !passwordInput) return

    const confirmation = confirmationInput.value.trim()
    const password = passwordInput.value.trim()
    const reason = reasonInput ? reasonInput.value.trim() : ''

    // Validate inputs
    if (confirmation !== 'DELETE') {
      this.showDeleteError('Please type "DELETE" exactly to confirm')
      return
    }

    if (!password) {
      this.showDeleteError('Please enter your current password')
      return
    }

    this.setDeleteLoading(true)

    const token = this.getAccessToken()
    const deleteData = {
      current_password: password,
      confirmation: confirmation,
      reason: reason || undefined
    }

    try {
      const response = await fetch(`${this.API_BASE}/auth/account`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(deleteData)
      })

      const result = await response.json()

      if (response.ok) {
        // Account successfully deleted - log out immediately
        this.handlePostDeletionLogout()
      } else {
        this.showDeleteError(result.detail || 'Failed to delete account')
      }
    } catch (error) {
      console.error('Error deleting account:', error)
      this.showDeleteError('Network error. Please try again.')
    } finally {
      this.setDeleteLoading(false)
    }
  }

  handlePostDeletionLogout() {
    // Clear all session data
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')

    // Close modal
    this.closeDeleteModal()
    this.closeModal()

    // Show success message briefly, then redirect
    if (window.dashboard && window.dashboard.showSnackbar) {
      window.dashboard.showSnackbar('Account successfully deleted. Goodbye!')
    }

    // Redirect to landing page after brief delay
    setTimeout(() => {
      window.location.href = '/'
    }, 2000)
  }

  setDeleteLoading(isLoading) {
    this.isLoading = isLoading

    const button = document.getElementById('confirmDeleteBtn')
    if (button) {
      const btnText = button.querySelector('.btn-text')
      const btnLoading = button.querySelector('.btn-loading')

      button.disabled = isLoading

      if (btnText && btnLoading) {
        if (isLoading) {
          btnText.style.display = 'none'
          btnLoading.style.display = 'inline-block'
          btnLoading.classList.add('rotating')
        } else {
          btnText.style.display = 'inline-block'
          btnLoading.style.display = 'none'
          btnLoading.classList.remove('rotating')
        }
      }
    }
  }

  showDeleteError(message) {
    const errorElement = document.getElementById('deleteAccountError')
    const messageElement = document.getElementById('deleteAccountErrorMessage')

    if (errorElement && messageElement) {
      messageElement.textContent = message
      errorElement.style.display = 'flex'
    }
  }
}

// Initialize profile manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  ProfileManager.init()
})
