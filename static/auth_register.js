/**
 * Registration page JavaScript functionality
 * Handles form validation, submission, and password strength checking
 */

class RegisterManager {
  constructor() {
    this.form = document.getElementById('register-form')
    this.firstNameInput = document.getElementById('first-name')
    this.lastNameInput = document.getElementById('last-name')
    this.emailInput = document.getElementById('email')
    this.passwordInput = document.getElementById('password')
    this.passwordConfirmInput = document.getElementById('password-confirm')
    this.termsAcceptInput = document.getElementById('terms-accept')
    this.marketingAcceptInput = document.getElementById('marketing-accept')
    this.submitButton = this.form.querySelector('button[type="submit"]')
    this.messageDiv = document.getElementById('form-message')
    this.liveRegion = document.getElementById('live-region')

    // Strength indicator elements
    this.passwordStrengthDiv = document.getElementById('password-strength')
    this.passwordStrengthFill = document.getElementById('password-strength-fill')
    this.passwordStrengthText = document.getElementById('password-strength-text')

    // Success screen elements
    this.successScreen = document.getElementById('success-screen')
    this.resendButton = document.getElementById('resend-verification')

    this.isSubmitting = false
    this.userEmail = null

    this.initializeEventListeners()
    this.initializePasswordToggles()
    this.initializePasswordStrength()
  }

  initializeEventListeners() {
    // Form submission
    this.form.addEventListener('submit', e => this.handleSubmit(e))

    // Real-time validation
    this.firstNameInput.addEventListener('blur', () => this.validateFirstName())
    this.lastNameInput.addEventListener('blur', () => this.validateLastName())
    this.emailInput.addEventListener('blur', () => this.validateEmail())
    this.passwordInput.addEventListener('blur', () => this.validatePassword())
    this.passwordConfirmInput.addEventListener('blur', () => this.validatePasswordConfirm())
    this.termsAcceptInput.addEventListener('change', () => this.validateTerms())

    // Clear errors on input
    this.firstNameInput.addEventListener('input', () => this.clearFieldError('first-name'))
    this.lastNameInput.addEventListener('input', () => this.clearFieldError('last-name'))
    this.emailInput.addEventListener('input', () => this.clearFieldError('email'))
    this.passwordInput.addEventListener('input', () => {
      this.clearFieldError('password')
      this.updatePasswordStrength()
    })
    this.passwordConfirmInput.addEventListener('input', () => this.clearFieldError('password-confirm'))

    // Resend verification email
    if (this.resendButton) {
      this.resendButton.addEventListener('click', () => this.resendVerificationEmail())
    }
  }

  initializePasswordToggles() {
    const passwordToggles = document.querySelectorAll('.password-toggle')
    passwordToggles.forEach((toggle, index) => {
      toggle.addEventListener('click', () => {
        const input = index === 0 ? this.passwordInput : this.passwordConfirmInput
        const type = input.type === 'password' ? 'text' : 'password'
        input.type = type

        const icon = toggle.querySelector('.password-toggle-icon')
        icon.textContent = type === 'password' ? '👁️' : '🙈'

        toggle.setAttribute('aria-label', type === 'password' ? 'Afficher le mot de passe' : 'Masquer le mot de passe')
      })
    })
  }

  initializePasswordStrength() {
    this.passwordInput.addEventListener('input', () => {
      this.updatePasswordStrength()
    })
  }

  updatePasswordStrength() {
    const password = this.passwordInput.value

    if (!password) {
      this.passwordStrengthDiv.classList.remove('show')
      return
    }

    this.passwordStrengthDiv.classList.add('show')

    const strength = this.calculatePasswordStrength(password)

    // Update visual indicator
    this.passwordStrengthFill.className = `password-strength-fill ${strength.level}`
    this.passwordStrengthText.textContent = strength.text
    this.passwordStrengthText.className = `password-strength-text ${strength.level}`
  }

  calculatePasswordStrength(password) {
    let score = 0
    const checks = {
      length: password.length >= 8,
      lowercase: /[a-z]/.test(password),
      uppercase: /[A-Z]/.test(password),
      numbers: /[0-9]/.test(password),
      special: /[^A-Za-z0-9]/.test(password)
    }

    // Calculate score
    if (checks.length) score += 20
    if (checks.lowercase) score += 20
    if (checks.uppercase) score += 20
    if (checks.numbers) score += 20
    if (checks.special) score += 20

    // Length bonus
    if (password.length >= 12) score += 10
    if (password.length >= 16) score += 10

    // Determine strength level and text
    if (score < 40) {
      return { level: 'weak', text: 'Mot de passe faible' }
    } else if (score < 60) {
      return { level: 'medium', text: 'Mot de passe moyen' }
    } else if (score < 80) {
      return { level: 'good', text: 'Bon mot de passe' }
    } else {
      return { level: 'strong', text: 'Mot de passe fort' }
    }
  }

  validateFirstName() {
    const firstName = this.firstNameInput.value.trim()

    if (!firstName) {
      this.setFieldError('first-name', 'Le prénom est obligatoire.')
      return false
    }

    if (firstName.length < 2) {
      this.setFieldError('first-name', 'Le prénom doit contenir au moins 2 caractères.')
      return false
    }

    if (!/^[a-zA-ZÀ-ÿ\s'-]+$/.test(firstName)) {
      this.setFieldError('first-name', 'Le prénom contient des caractères non valides.')
      return false
    }

    this.setFieldSuccess('first-name')
    return true
  }

  validateLastName() {
    const lastName = this.lastNameInput.value.trim()

    if (!lastName) {
      this.setFieldError('last-name', 'Le nom est obligatoire.')
      return false
    }

    if (lastName.length < 2) {
      this.setFieldError('last-name', 'Le nom doit contenir au moins 2 caractères.')
      return false
    }

    if (!/^[a-zA-ZÀ-ÿ\s'-]+$/.test(lastName)) {
      this.setFieldError('last-name', 'Le nom contient des caractères non valides.')
      return false
    }

    this.setFieldSuccess('last-name')
    return true
  }

  validateEmail() {
    const email = this.emailInput.value.trim()
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

    if (!email) {
      this.setFieldError('email', "L'adresse email est obligatoire.")
      return false
    }

    if (!emailRegex.test(email)) {
      this.setFieldError('email', 'Veuillez entrer une adresse email valide.')
      return false
    }

    this.setFieldSuccess('email')
    return true
  }

  validatePassword() {
    const password = this.passwordInput.value

    if (!password) {
      this.setFieldError('password', 'Le mot de passe est obligatoire.')
      return false
    }

    if (password.length < 8) {
      this.setFieldError('password', 'Le mot de passe doit contenir au moins 8 caractères.')
      return false
    }

    if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])/.test(password)) {
      this.setFieldError('password', 'Le mot de passe doit contenir des minuscules, majuscules et chiffres.')
      return false
    }

    this.setFieldSuccess('password')
    return true
  }

  validatePasswordConfirm() {
    const password = this.passwordInput.value
    const passwordConfirm = this.passwordConfirmInput.value

    if (!passwordConfirm) {
      this.setFieldError('password-confirm', 'La confirmation du mot de passe est obligatoire.')
      return false
    }

    if (password !== passwordConfirm) {
      this.setFieldError('password-confirm', 'Les mots de passe ne correspondent pas.')
      return false
    }

    this.setFieldSuccess('password-confirm')
    return true
  }

  validateTerms() {
    if (!this.termsAcceptInput.checked) {
      this.setFieldError('terms-accept', "Vous devez accepter les conditions d'utilisation.")
      return false
    }

    this.clearFieldError('terms-accept')
    return true
  }

  setFieldError(fieldName, message) {
    const fieldGroup = document.getElementById(fieldName).closest('.field-group, .checkbox-group')
    const errorDiv = document.getElementById(`${fieldName}-error`)

    if (fieldGroup) {
      fieldGroup.classList.add('has-error')
      fieldGroup.classList.remove('has-success')
    }

    if (errorDiv) {
      errorDiv.textContent = message
      errorDiv.setAttribute('aria-live', 'polite')
    }
  }

  setFieldSuccess(fieldName) {
    const fieldGroup = document.getElementById(fieldName).closest('.field-group')
    const errorDiv = document.getElementById(`${fieldName}-error`)

    if (fieldGroup) {
      fieldGroup.classList.remove('has-error')
      fieldGroup.classList.add('has-success')
    }

    if (errorDiv) {
      errorDiv.textContent = ''
      errorDiv.removeAttribute('aria-live')
    }
  }

  clearFieldError(fieldName) {
    const fieldGroup = document.getElementById(fieldName).closest('.field-group, .checkbox-group')
    const errorDiv = document.getElementById(`${fieldName}-error`)

    if (fieldGroup) {
      fieldGroup.classList.remove('has-error', 'has-success')
    }

    if (errorDiv) {
      errorDiv.textContent = ''
      errorDiv.removeAttribute('aria-live')
    }
  }

  showMessage(message, type = 'error') {
    this.messageDiv.textContent = message
    this.messageDiv.className = `form-message ${type}`
    this.messageDiv.hidden = false
    this.messageDiv.setAttribute('aria-live', 'polite')

    // Announce to screen readers
    this.liveRegion.textContent = message

    // Auto-hide success messages
    if (type === 'success') {
      setTimeout(() => {
        this.messageDiv.hidden = true
      }, 5000)
    }
  }

  hideMessage() {
    this.messageDiv.hidden = true
    this.messageDiv.removeAttribute('aria-live')
  }

  setSubmitLoading(loading) {
    const btnText = this.submitButton.querySelector('.btn-text')
    const btnLoading = this.submitButton.querySelector('.btn-loading')

    if (loading) {
      btnText.hidden = true
      btnLoading.hidden = false
      this.submitButton.disabled = true
      this.form.classList.add('form-loading')
    } else {
      btnText.hidden = false
      btnLoading.hidden = true
      this.submitButton.disabled = false
      this.form.classList.remove('form-loading')
    }

    this.isSubmitting = loading
  }

  setResendLoading(loading) {
    if (!this.resendButton) return

    const btnText = this.resendButton.querySelector('.btn-text')
    const btnLoading = this.resendButton.querySelector('.btn-loading')

    if (loading) {
      btnText.hidden = true
      btnLoading.hidden = false
      this.resendButton.disabled = true
    } else {
      btnText.hidden = false
      btnLoading.hidden = true
      this.resendButton.disabled = false
    }
  }

  async handleSubmit(e) {
    e.preventDefault()

    if (this.isSubmitting) return

    this.hideMessage()

    // Validate all fields
    const isFirstNameValid = this.validateFirstName()
    const isLastNameValid = this.validateLastName()
    const isEmailValid = this.validateEmail()
    const isPasswordValid = this.validatePassword()
    const isPasswordConfirmValid = this.validatePasswordConfirm()
    const isTermsValid = this.validateTerms()

    if (
      !isFirstNameValid ||
      !isLastNameValid ||
      !isEmailValid ||
      !isPasswordValid ||
      !isPasswordConfirmValid ||
      !isTermsValid
    ) {
      this.showMessage('Veuillez corriger les erreurs ci-dessus.')
      return
    }

    this.setSubmitLoading(true)

    try {
      const formData = {
        first_name: this.firstNameInput.value.trim(),
        last_name: this.lastNameInput.value.trim(),
        email: this.emailInput.value.trim(),
        password: this.passwordInput.value,
        marketing_consent: this.marketingAcceptInput.checked
      }

      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      const data = await response.json()

      if (response.ok && data.success) {
        // Store email for resend functionality
        this.userEmail = formData.email

        // Show success screen
        this.showSuccessScreen()
      } else {
        this.showMessage(data.message || 'Erreur lors de la création du compte.')
      }
    } catch (error) {
      console.error('Registration error:', error)
      this.showMessage('Erreur lors de la création du compte. Veuillez réessayer.')
    } finally {
      this.setSubmitLoading(false)
    }
  }

  async resendVerificationEmail() {
    if (!this.userEmail) return

    this.setResendLoading(true)

    try {
      const response = await fetch('/api/auth/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: this.userEmail
        })
      })

      const data = await response.json()

      if (response.ok && data.success) {
        // Show success message temporarily
        const originalText = this.resendButton.querySelector('.btn-text').textContent
        this.resendButton.querySelector('.btn-text').textContent = 'Email envoyé !'

        setTimeout(() => {
          this.resendButton.querySelector('.btn-text').textContent = originalText
        }, 3000)
      } else {
        alert(data.message || "Erreur lors de l'envoi de l'email.")
      }
    } catch (error) {
      console.error('Resend verification error:', error)
      alert("Erreur lors de l'envoi de l'email. Veuillez réessayer.")
    } finally {
      this.setResendLoading(false)
    }
  }

  showSuccessScreen() {
    // Hide registration form
    const mainScreen = document.querySelector('.screen.active')
    mainScreen.classList.remove('active')

    // Show success screen
    this.successScreen.classList.add('active')

    // Focus on success screen for screen readers
    const successTitle = document.getElementById('success-title')
    successTitle.focus()

    // Announce success to screen readers
    this.liveRegion.textContent = 'Compte créé avec succès ! Vérifiez votre email pour activer votre compte.'
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new RegisterManager()
})
