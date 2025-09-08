/**
 * Login page JavaScript functionality
 * Handles form validation, submission, and password reset
 */

class LoginManager {
    constructor() {
        this.form = document.getElementById('login-form');
        this.emailInput = document.getElementById('email');
        this.passwordInput = document.getElementById('password');
        this.rememberMeInput = document.getElementById('remember-me');
        this.submitButton = this.form.querySelector('button[type="submit"]');
        this.messageDiv = document.getElementById('form-message');
        this.liveRegion = document.getElementById('live-region');

        // Password reset modal elements
        this.forgotPasswordModal = document.getElementById('forgot-password-modal');
        this.forgotPasswordForm = document.getElementById('forgot-password-form');
        this.resetEmailInput = document.getElementById('reset-email');
        this.resetMessageDiv = document.getElementById('reset-message');

        this.isSubmitting = false;

        this.initializeEventListeners();
        this.initializePasswordToggle();
        this.initializeForgotPasswordModal();
    }

    initializeEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Real-time validation
        this.emailInput.addEventListener('blur', () => this.validateEmail());
        this.passwordInput.addEventListener('blur', () => this.validatePassword());

        // Clear errors on input
        this.emailInput.addEventListener('input', () => this.clearFieldError('email'));
        this.passwordInput.addEventListener('input', () => this.clearFieldError('password'));

        // Remember me persistence
        this.loadRememberMe();
    }

    initializePasswordToggle() {
        const passwordToggle = document.querySelector('.password-toggle');
        if (passwordToggle) {
            passwordToggle.addEventListener('click', () => {
                const type = this.passwordInput.type === 'password' ? 'text' : 'password';
                this.passwordInput.type = type;

                const icon = passwordToggle.querySelector('.password-toggle-icon');
                icon.textContent = type === 'password' ? '👁️' : '🙈';

                passwordToggle.setAttribute('aria-label',
                    type === 'password' ? 'Afficher le mot de passe' : 'Masquer le mot de passe'
                );
            });
        }
    }

    initializeForgotPasswordModal() {
        // Open modal
        const forgotPasswordLink = document.querySelector('.forgot-password-link');
        forgotPasswordLink.addEventListener('click', (e) => {
            e.preventDefault();
            this.openForgotPasswordModal();
        });

        // Close modal
        const modalClose = this.forgotPasswordModal.querySelector('.modal-close');
        modalClose.addEventListener('click', () => this.closeForgotPasswordModal());

        const cancelButton = this.forgotPasswordModal.querySelector('[data-action="cancel"]');
        cancelButton.addEventListener('click', () => this.closeForgotPasswordModal());

        // Close on backdrop click
        this.forgotPasswordModal.addEventListener('click', (e) => {
            if (e.target === this.forgotPasswordModal) {
                this.closeForgotPasswordModal();
            }
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.forgotPasswordModal.hidden) {
                this.closeForgotPasswordModal();
            }
        });

        // Handle password reset form
        this.forgotPasswordForm.addEventListener('submit', (e) => this.handlePasswordReset(e));
        this.resetEmailInput.addEventListener('blur', () => this.validateResetEmail());
        this.resetEmailInput.addEventListener('input', () => this.clearResetError());
    }

    validateEmail() {
        const email = this.emailInput.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!email) {
            this.setFieldError('email', 'L\'adresse email est obligatoire.');
            return false;
        }

        if (!emailRegex.test(email)) {
            this.setFieldError('email', 'Veuillez entrer une adresse email valide.');
            return false;
        }

        this.setFieldSuccess('email');
        return true;
    }

    validatePassword() {
        const password = this.passwordInput.value;

        if (!password) {
            this.setFieldError('password', 'Le mot de passe est obligatoire.');
            return false;
        }

        if (password.length < 8) {
            this.setFieldError('password', 'Le mot de passe doit contenir au moins 8 caractères.');
            return false;
        }

        this.setFieldSuccess('password');
        return true;
    }

    validateResetEmail() {
        const email = this.resetEmailInput.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!email) {
            this.setResetError('L\'adresse email est obligatoire.');
            return false;
        }

        if (!emailRegex.test(email)) {
            this.setResetError('Veuillez entrer une adresse email valide.');
            return false;
        }

        this.clearResetError();
        return true;
    }

    setFieldError(fieldName, message) {
        const fieldGroup = document.getElementById(fieldName).closest('.field-group');
        const errorDiv = document.getElementById(`${fieldName}-error`);

        fieldGroup.classList.add('has-error');
        fieldGroup.classList.remove('has-success');
        errorDiv.textContent = message;
        errorDiv.setAttribute('aria-live', 'polite');
    }

    setFieldSuccess(fieldName) {
        const fieldGroup = document.getElementById(fieldName).closest('.field-group');
        const errorDiv = document.getElementById(`${fieldName}-error`);

        fieldGroup.classList.remove('has-error');
        fieldGroup.classList.add('has-success');
        errorDiv.textContent = '';
        errorDiv.removeAttribute('aria-live');
    }

    clearFieldError(fieldName) {
        const fieldGroup = document.getElementById(fieldName).closest('.field-group');
        const errorDiv = document.getElementById(`${fieldName}-error`);

        fieldGroup.classList.remove('has-error', 'has-success');
        errorDiv.textContent = '';
        errorDiv.removeAttribute('aria-live');
    }

    setResetError(message) {
        const errorDiv = document.getElementById('reset-email-error');
        errorDiv.textContent = message;
        errorDiv.setAttribute('aria-live', 'polite');
    }

    clearResetError() {
        const errorDiv = document.getElementById('reset-email-error');
        errorDiv.textContent = '';
        errorDiv.removeAttribute('aria-live');
    }

    showMessage(message, type = 'error') {
        this.messageDiv.textContent = message;
        this.messageDiv.className = `form-message ${type}`;
        this.messageDiv.hidden = false;
        this.messageDiv.setAttribute('aria-live', 'polite');

        // Announce to screen readers
        this.liveRegion.textContent = message;

        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                this.messageDiv.hidden = true;
            }, 5000);
        }
    }

    hideMessage() {
        this.messageDiv.hidden = true;
        this.messageDiv.removeAttribute('aria-live');
    }

    showResetMessage(message, type = 'error') {
        this.resetMessageDiv.textContent = message;
        this.resetMessageDiv.className = `form-message ${type}`;
        this.resetMessageDiv.hidden = false;
        this.resetMessageDiv.setAttribute('aria-live', 'polite');
    }

    hideResetMessage() {
        this.resetMessageDiv.hidden = true;
        this.resetMessageDiv.removeAttribute('aria-live');
    }

    setSubmitLoading(loading) {
        const btnText = this.submitButton.querySelector('.btn-text');
        const btnLoading = this.submitButton.querySelector('.btn-loading');

        if (loading) {
            btnText.hidden = true;
            btnLoading.hidden = false;
            this.submitButton.disabled = true;
            this.form.classList.add('form-loading');
        } else {
            btnText.hidden = false;
            btnLoading.hidden = true;
            this.submitButton.disabled = false;
            this.form.classList.remove('form-loading');
        }

        this.isSubmitting = loading;
    }

    setResetLoading(loading) {
        const resetButton = this.forgotPasswordForm.querySelector('button[type="submit"]');
        const btnText = resetButton.querySelector('.btn-text');
        const btnLoading = resetButton.querySelector('.btn-loading');

        if (loading) {
            btnText.hidden = true;
            btnLoading.hidden = false;
            resetButton.disabled = true;
        } else {
            btnText.hidden = false;
            btnLoading.hidden = true;
            resetButton.disabled = false;
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        if (this.isSubmitting) return;

        this.hideMessage();

        // Validate all fields
        const isEmailValid = this.validateEmail();
        const isPasswordValid = this.validatePassword();

        if (!isEmailValid || !isPasswordValid) {
            this.showMessage('Veuillez corriger les erreurs ci-dessus.');
            return;
        }

        this.setSubmitLoading(true);

        try {
            const formData = {
                email: this.emailInput.value.trim(),
                password: this.passwordInput.value
            };

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Save remember me preference
                if (this.rememberMeInput.checked) {
                    this.saveRememberMe(formData.email);
                } else {
                    this.clearRememberMe();
                }

                // Store auth tokens
                localStorage.setItem('access_token', data.access_token);
                if (data.refresh_token) {
                    localStorage.setItem('refresh_token', data.refresh_token);
                }

                this.showMessage('Connexion réussie ! Redirection en cours...', 'success');

                // Redirect to dashboard
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1000);

            } else {
                this.showMessage(data.message || 'Erreur de connexion. Vérifiez vos identifiants.');
            }

        } catch (error) {
            console.error('Login error:', error);
            this.showMessage('Erreur de connexion. Veuillez réessayer.');
        } finally {
            this.setSubmitLoading(false);
        }
    }

    async handlePasswordReset(e) {
        e.preventDefault();

        this.hideResetMessage();

        if (!this.validateResetEmail()) {
            return;
        }

        this.setResetLoading(true);

        try {
            const response = await fetch('/api/auth/request-password-reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: this.resetEmailInput.value.trim()
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.showResetMessage('Un email de réinitialisation a été envoyé à votre adresse.', 'success');
                setTimeout(() => {
                    this.closeForgotPasswordModal();
                }, 2000);
            } else {
                this.showResetMessage(data.message || 'Erreur lors de l\'envoi de l\'email.');
            }

        } catch (error) {
            console.error('Password reset error:', error);
            this.showResetMessage('Erreur lors de l\'envoi de l\'email. Veuillez réessayer.');
        } finally {
            this.setResetLoading(false);
        }
    }

    openForgotPasswordModal() {
        this.forgotPasswordModal.hidden = false;
        this.resetEmailInput.focus();
        this.hideResetMessage();

        // Trap focus in modal
        document.body.style.overflow = 'hidden';
    }

    closeForgotPasswordModal() {
        this.forgotPasswordModal.hidden = true;
        this.forgotPasswordForm.reset();
        this.clearResetError();
        this.hideResetMessage();

        // Restore focus
        document.querySelector('.forgot-password-link').focus();
        document.body.style.overflow = '';
    }

    saveRememberMe(email) {
        localStorage.setItem('remember_email', email);
        localStorage.setItem('remember_me', 'true');
    }

    clearRememberMe() {
        localStorage.removeItem('remember_email');
        localStorage.removeItem('remember_me');
    }

    loadRememberMe() {
        const rememberMe = localStorage.getItem('remember_me') === 'true';
        const rememberedEmail = localStorage.getItem('remember_email');

        if (rememberMe && rememberedEmail) {
            this.emailInput.value = rememberedEmail;
            this.rememberMeInput.checked = true;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LoginManager();
});
