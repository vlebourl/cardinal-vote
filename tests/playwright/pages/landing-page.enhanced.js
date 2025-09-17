import { expect } from '@playwright/test';
import { BasePage } from './base-page.js';
import { testDataManager } from '../fixtures/data/test-data-factory.js';
import { MATERIAL_DESIGN_FIXTURES } from '../fixtures/data/material-design-fixtures.js';

/**
 * Enhanced Landing Page Object Model
 *
 * Comprehensive landing page interactions including:
 * - Navigation and authentication flows
 * - Material Design validation
 * - Responsive behavior testing
 * - Form interaction and validation
 * - Performance monitoring
 * - Accessibility compliance
 */
export class EnhancedLandingPage extends BasePage {
  constructor(page) {
    super(page);

    // Navigation selectors
    this.selectors = {
      // Primary navigation
      signInButton: 'button:has-text("Sign In"), [data-testid="sign-in-button"]',
      getStartedButton: 'button:has-text("Get Started"), [data-testid="get-started-button"]',
      navigationMenu: 'button:has-text("Open navigation menu"), [data-testid="mobile-menu-button"]',
      logoLink: '[data-testid="logo"], .logo, .brand',

      // Authentication modals
      loginModal: '[data-testid="login-modal"], .login-modal, .auth-modal',
      registerModal: '[data-testid="register-modal"], .register-modal, .signup-modal',
      modalOverlay: '.modal-overlay, .backdrop, [data-testid="modal-backdrop"]',
      modalCloseButton: '[data-testid="modal-close"], .modal-close, .close-button',

      // Login form
      loginForm: '[data-testid="login-form"], .login-form, form[action*="login"]',
      emailInput: '[data-testid="login-email"], input[type="email"], input[name="email"]',
      passwordInput: '[data-testid="login-password"], input[type="password"], input[name="password"]',
      loginSubmitButton: '[data-testid="login-submit"], button[type="submit"], .login-submit',
      rememberMeCheckbox: '[data-testid="remember-me"], input[name="remember"], .remember-me',
      forgotPasswordLink: '[data-testid="forgot-password"], .forgot-password, a[href*="forgot"]',

      // Registration form
      registerForm: '[data-testid="register-form"], .register-form, .signup-form',
      firstNameInput: '[data-testid="first-name"], input[name="firstName"], input[name="first_name"]',
      lastNameInput: '[data-testid="last-name"], input[name="lastName"], input[name="last_name"]',
      confirmPasswordInput: '[data-testid="confirm-password"], input[name="confirmPassword"]',
      termsCheckbox: '[data-testid="agree-terms"], input[name="agreeToTerms"], .terms-checkbox',
      registerSubmitButton: '[data-testid="register-submit"], .register-submit, .signup-submit',

      // Error and success messages
      errorMessage: '.error-message, .alert-danger, [role="alert"], .field-error',
      successMessage: '.success-message, .alert-success, .notification-success',
      validationError: '.validation-error, .form-error, .input-error',

      // Hero section
      heroSection: '[data-testid="hero"], .hero, .landing-hero',
      heroTitle: '[data-testid="hero-title"], .hero-title, .main-title',
      heroSubtitle: '[data-testid="hero-subtitle"], .hero-subtitle, .subtitle',
      ctaButton: '[data-testid="cta-button"], .cta-button, .primary-cta',

      // Features section
      featuresSection: '[data-testid="features"], .features, .features-section',
      featureCards: '[data-testid="feature-card"], .feature-card, .feature-item',

      // Footer
      footer: 'footer, [data-testid="footer"], .site-footer',
      footerLinks: 'footer a, .footer-link',

      // Loading states
      loadingSpinner: '[data-testid="loading"], .loading, .spinner',
      loadingOverlay: '[data-testid="loading-overlay"], .loading-overlay'
    };
  }

  /**
   * Navigation Methods
   */
  async goto() {
    const loadTime = await super.goto('/');
    await this.waitForPageReady();
    return loadTime;
  }

  async waitForPageReady() {
    // Wait for critical elements to be present
    await this.waitForElement(this.selectors.signInButton, 'visible', 15000);

    // Ensure no loading states are present
    await this.waitForLoadingToComplete();

    // Verify page is interactive
    await this.page.waitForFunction(() => document.readyState === 'complete');
  }

  async waitForLoadingToComplete() {
    const loadingElements = [
      this.selectors.loadingSpinner,
      this.selectors.loadingOverlay
    ];

    for (const selector of loadingElements) {
      try {
        await this.page.locator(selector).waitFor({ state: 'hidden', timeout: 5000 });
      } catch {
        // Loading element not present, continue
      }
    }
  }

  /**
   * Authentication Flow Methods
   */
  async clickSignIn() {
    const startTime = Date.now();
    await this.clickElement(this.selectors.signInButton);

    // Wait for modal or navigation change
    const modalAppeared = await this.waitForLoginModal();
    const navigationOccurred = await this.checkForNavigation();

    const interactionTime = Date.now() - startTime;

    return {
      modalAppeared,
      navigationOccurred,
      interactionTime,
      success: modalAppeared || navigationOccurred
    };
  }

  async clickGetStarted() {
    const startTime = Date.now();
    await this.clickElement(this.selectors.getStartedButton);

    // Wait for modal or navigation change
    const modalAppeared = await this.waitForRegisterModal();
    const navigationOccurred = await this.checkForNavigation();

    const interactionTime = Date.now() - startTime;

    return {
      modalAppeared,
      navigationOccurred,
      interactionTime,
      success: modalAppeared || navigationOccurred
    };
  }

  async waitForLoginModal(timeout = 5000) {
    try {
      await this.waitForElement(this.selectors.loginModal, 'visible', timeout);
      return true;
    } catch {
      return false;
    }
  }

  async waitForRegisterModal(timeout = 5000) {
    try {
      await this.waitForElement(this.selectors.registerModal, 'visible', timeout);
      return true;
    } catch {
      return false;
    }
  }

  async checkForNavigation() {
    const currentUrl = this.page.url();
    await this.page.waitForTimeout(1000);
    const newUrl = this.page.url();
    return currentUrl !== newUrl;
  }

  /**
   * Login Form Methods
   */
  async fillLoginForm(email, password, options = {}) {
    await this.waitForElement(this.selectors.loginForm, 'visible');

    const formData = {
      email: email || testDataManager.createFormData('login').email,
      password: password || testDataManager.createFormData('login').password,
      rememberMe: options.rememberMe || false
    };

    await this.fillField(this.selectors.emailInput, formData.email);
    await this.fillField(this.selectors.passwordInput, formData.password);

    if (formData.rememberMe && await this.isElementVisible(this.selectors.rememberMeCheckbox)) {
      await this.clickElement(this.selectors.rememberMeCheckbox);
    }

    return formData;
  }

  async submitLoginForm() {
    const startTime = Date.now();

    await this.clickElement(this.selectors.loginSubmitButton);

    // Wait for one of several possible outcomes
    const outcome = await Promise.race([
      // Success: Redirect to dashboard
      this.page.waitForURL('**/dashboard', { timeout: 10000 }).then(() => 'success'),
      this.page.waitForURL('**/admin', { timeout: 10000 }).then(() => 'success'),

      // Error: Error message appears
      this.waitForElement(this.selectors.errorMessage, 'visible', 10000).then(() => 'error'),

      // Validation: Form validation errors
      this.waitForElement(this.selectors.validationError, 'visible', 5000).then(() => 'validation'),

      // Timeout: No response
      this.page.waitForTimeout(10000).then(() => 'timeout')
    ]);

    const submissionTime = Date.now() - startTime;

    return {
      outcome,
      submissionTime,
      success: outcome === 'success'
    };
  }

  /**
   * Registration Form Methods
   */
  async fillRegistrationForm(userData = null) {
    await this.waitForElement(this.selectors.registerForm, 'visible');

    const formData = userData || testDataManager.createFormData('registration');

    await this.fillField(this.selectors.emailInput, formData.email);
    await this.fillField(this.selectors.passwordInput, formData.password);

    if (await this.isElementVisible(this.selectors.confirmPasswordInput)) {
      await this.fillField(this.selectors.confirmPasswordInput, formData.confirmPassword || formData.password);
    }

    if (await this.isElementVisible(this.selectors.firstNameInput)) {
      await this.fillField(this.selectors.firstNameInput, formData.firstName || 'Test');
    }

    if (await this.isElementVisible(this.selectors.lastNameInput)) {
      await this.fillField(this.selectors.lastNameInput, formData.lastName || 'User');
    }

    if (formData.agreeToTerms && await this.isElementVisible(this.selectors.termsCheckbox)) {
      await this.clickElement(this.selectors.termsCheckbox);
    }

    return formData;
  }

  async submitRegistrationForm() {
    const startTime = Date.now();

    await this.clickElement(this.selectors.registerSubmitButton);

    const outcome = await Promise.race([
      this.page.waitForURL('**/dashboard', { timeout: 10000 }).then(() => 'success'),
      this.page.waitForURL('**/verify', { timeout: 10000 }).then(() => 'verification'),
      this.waitForElement(this.selectors.errorMessage, 'visible', 10000).then(() => 'error'),
      this.waitForElement(this.selectors.validationError, 'visible', 5000).then(() => 'validation'),
      this.page.waitForTimeout(10000).then(() => 'timeout')
    ]);

    const submissionTime = Date.now() - startTime;

    return {
      outcome,
      submissionTime,
      success: outcome === 'success' || outcome === 'verification'
    };
  }

  /**
   * Element State Checking
   */
  async isSignInButtonVisible() {
    return await this.isElementVisible(this.selectors.signInButton);
  }

  async isGetStartedButtonVisible() {
    return await this.isElementVisible(this.selectors.getStartedButton);
  }

  async isLoginModalOpen() {
    return await this.isElementVisible(this.selectors.loginModal);
  }

  async isRegisterModalOpen() {
    return await this.isElementVisible(this.selectors.registerModal);
  }

  /**
   * Message Handling
   */
  async getErrorMessage() {
    try {
      const errorElement = this.page.locator(this.selectors.errorMessage).first();
      await errorElement.waitFor({ state: 'visible', timeout: 5000 });
      return await errorElement.textContent();
    } catch {
      return null;
    }
  }

  async getSuccessMessage() {
    try {
      const successElement = this.page.locator(this.selectors.successMessage).first();
      await successElement.waitFor({ state: 'visible', timeout: 5000 });
      return await successElement.textContent();
    } catch {
      return null;
    }
  }

  async getAllValidationErrors() {
    const errors = [];
    const errorElements = await this.page.locator(this.selectors.validationError).all();

    for (const element of errorElements) {
      if (await element.isVisible()) {
        errors.push({
          text: await element.textContent(),
          field: await element.getAttribute('data-field') || 'unknown'
        });
      }
    }

    return errors;
  }

  /**
   * Content Validation Methods
   */
  async validateHeroSection() {
    const heroValidation = {
      present: await this.isElementVisible(this.selectors.heroSection),
      title: null,
      subtitle: null,
      ctaButton: null
    };

    if (heroValidation.present) {
      heroValidation.title = await this.getElementText(this.selectors.heroTitle);
      heroValidation.subtitle = await this.getElementText(this.selectors.heroSubtitle);
      heroValidation.ctaButton = await this.isElementVisible(this.selectors.ctaButton);
    }

    return heroValidation;
  }

  async validateFeaturesSection() {
    const featuresValidation = {
      present: await this.isElementVisible(this.selectors.featuresSection),
      featureCount: 0,
      features: []
    };

    if (featuresValidation.present) {
      const featureElements = await this.page.locator(this.selectors.featureCards).all();
      featuresValidation.featureCount = featureElements.length;

      for (const feature of featureElements) {
        featuresValidation.features.push({
          title: await feature.locator('h3, .feature-title').textContent().catch(() => null),
          description: await feature.locator('p, .feature-description').textContent().catch(() => null),
          visible: await feature.isVisible()
        });
      }
    }

    return featuresValidation;
  }

  async validateFooter() {
    const footerValidation = {
      present: await this.isElementVisible(this.selectors.footer),
      linkCount: 0,
      links: []
    };

    if (footerValidation.present) {
      const footerLinks = await this.page.locator(this.selectors.footerLinks).all();
      footerValidation.linkCount = footerLinks.length;

      for (const link of footerLinks) {
        footerValidation.links.push({
          text: await link.textContent(),
          href: await link.getAttribute('href'),
          visible: await link.isVisible()
        });
      }
    }

    return footerValidation;
  }

  /**
   * Material Design Specific Validation
   */
  async validateMaterialDesignElements() {
    const mdValidation = await super.validateMaterialDesign();

    // Add landing page specific validations
    mdValidation.landingSpecific = {
      buttons: await this.validateMaterialButtons(),
      navigation: await this.validateMaterialNavigation(),
      hero: await this.validateMaterialHero(),
      cards: await this.validateMaterialCards()
    };

    return mdValidation;
  }

  async validateMaterialButtons() {
    const buttons = {
      signIn: await this.validateButtonMaterialDesign(this.selectors.signInButton),
      getStarted: await this.validateButtonMaterialDesign(this.selectors.getStartedButton),
      cta: await this.validateButtonMaterialDesign(this.selectors.ctaButton)
    };

    return buttons;
  }

  async validateButtonMaterialDesign(selector) {
    if (!await this.isElementVisible(selector)) {
      return { present: false };
    }

    const button = this.page.locator(selector);
    const styles = await button.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        minHeight: computed.minHeight,
        borderRadius: computed.borderRadius,
        padding: computed.padding,
        fontSize: computed.fontSize,
        fontWeight: computed.fontWeight,
        textTransform: computed.textTransform,
        backgroundColor: computed.backgroundColor,
        color: computed.color
      };
    });

    return {
      present: true,
      styles,
      meetsMinHeight: parseInt(styles.minHeight) >= 40,
      hasRoundedCorners: parseInt(styles.borderRadius) > 0,
      properFontWeight: parseInt(styles.fontWeight) >= 500
    };
  }

  async validateMaterialNavigation() {
    const navigation = {
      desktop: await this.isElementVisible('nav, .main-nav, .desktop-nav'),
      mobile: await this.isElementVisible(this.selectors.navigationMenu),
      responsive: false
    };

    // Test responsive behavior
    const currentViewport = this.page.viewportSize();

    // Test mobile viewport
    await this.page.setViewportSize({ width: 375, height: 667 });
    navigation.mobileVisible = await this.isElementVisible(this.selectors.navigationMenu);

    // Test desktop viewport
    await this.page.setViewportSize({ width: 1200, height: 800 });
    navigation.desktopVisible = await this.isElementVisible('nav, .main-nav, .desktop-nav');

    // Restore original viewport
    if (currentViewport) {
      await this.page.setViewportSize(currentViewport);
    }

    navigation.responsive = navigation.mobileVisible || navigation.desktopVisible;

    return navigation;
  }

  async validateMaterialHero() {
    if (!await this.isElementVisible(this.selectors.heroSection)) {
      return { present: false };
    }

    const hero = this.page.locator(this.selectors.heroSection);
    const styles = await hero.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        backgroundColor: computed.backgroundColor,
        backgroundImage: computed.backgroundImage,
        padding: computed.padding,
        textAlign: computed.textAlign,
        minHeight: computed.minHeight
      };
    });

    return {
      present: true,
      styles,
      hasBackground: styles.backgroundColor !== 'rgba(0, 0, 0, 0)' || styles.backgroundImage !== 'none',
      hasPadding: styles.padding !== '0px',
      hasMinHeight: parseInt(styles.minHeight) > 200
    };
  }

  /**
   * Responsive Design Testing
   */
  async checkResponsiveLayout() {
    const results = {};
    const breakpoints = [
      { name: 'mobile', width: 375, height: 667 },
      { name: 'tablet', width: 768, height: 1024 },
      { name: 'desktop', width: 1200, height: 800 },
      { name: 'large', width: 1920, height: 1080 }
    ];

    for (const breakpoint of breakpoints) {
      await this.page.setViewportSize(breakpoint);
      await this.page.waitForTimeout(500); // Allow layout to adjust

      results[breakpoint.name] = {
        viewport: breakpoint,
        signInVisible: await this.isSignInButtonVisible(),
        getStartedVisible: await this.isGetStartedButtonVisible(),
        mobileMenuVisible: await this.isElementVisible(this.selectors.navigationMenu),
        heroVisible: await this.isElementVisible(this.selectors.heroSection),
        layout: await this.analyzeLayout()
      };
    }

    return results;
  }

  /**
   * Session and Storage Management
   */
  async clearSessionStorage() {
    await this.page.evaluate(() => {
      sessionStorage.clear();
      localStorage.clear();
    });
  }

  async getSessionStorageToken() {
    return await this.page.evaluate(() => {
      return sessionStorage.getItem('jwt') ||
             sessionStorage.getItem('auth_token') ||
             sessionStorage.getItem('token') ||
             localStorage.getItem('jwt') ||
             localStorage.getItem('auth_token');
    });
  }

  async getAllSessionStorage() {
    return await this.page.evaluate(() => {
      const storage = {};
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        storage[key] = sessionStorage.getItem(key);
      }
      return storage;
    });
  }

  /**
   * Authentication Request Monitoring
   */
  async monitorAuthRequests() {
    const authRequests = [];

    this.page.on('request', request => {
      const url = request.url();
      if (this.isAuthRequest(url)) {
        authRequests.push({
          url,
          method: request.method(),
          headers: request.headers(),
          timestamp: Date.now()
        });
      }
    });

    this.page.on('response', response => {
      const url = response.url();
      if (this.isAuthRequest(url)) {
        const request = authRequests.find(req => req.url === url);
        if (request) {
          request.status = response.status();
          request.responseHeaders = response.headers();
          request.responseTime = Date.now() - request.timestamp;
        }
      }
    });

    return authRequests;
  }

  isAuthRequest(url) {
    const authPaths = ['/auth/', '/login', '/register', '/logout', '/verify'];
    return authPaths.some(path => url.includes(path));
  }

  /**
   * Form Validation Testing
   */
  async testFormValidation(formType = 'login') {
    const validationTests = [];

    if (formType === 'login') {
      await this.clickSignIn();
      if (await this.waitForLoginModal()) {
        // Test empty form submission
        await this.submitLoginForm();
        const errors = await this.getAllValidationErrors();
        validationTests.push({
          test: 'empty_form',
          errors,
          hasErrors: errors.length > 0
        });

        // Test invalid email
        await this.fillLoginForm('invalid-email', 'password');
        await this.submitLoginForm();
        const emailErrors = await this.getAllValidationErrors();
        validationTests.push({
          test: 'invalid_email',
          errors: emailErrors,
          hasErrors: emailErrors.length > 0
        });
      }
    }

    return validationTests;
  }

  /**
   * Performance Testing
   */
  async measureAuthenticationPerformance() {
    const performance = {
      signInClick: null,
      modalOpen: null,
      formSubmission: null
    };

    // Measure sign-in button click response
    const signInResult = await this.clickSignIn();
    performance.signInClick = signInResult.interactionTime;

    if (signInResult.modalAppeared) {
      // Measure form submission
      await this.fillLoginForm('test@example.com', 'password123');
      const submitResult = await this.submitLoginForm();
      performance.formSubmission = submitResult.submissionTime;
    }

    return performance;
  }
}
