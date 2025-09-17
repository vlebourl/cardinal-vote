import { expect } from '@playwright/test';
import { BasePage } from './base-page.js';
import { MATERIAL_DESIGN_FIXTURES } from '../fixtures/data/material-design-fixtures.js';
import { PERFORMANCE_FIXTURES } from '../fixtures/data/performance-accessibility-fixtures.js';

/**
 * Enhanced Error Page Object Model
 *
 * Extends BasePage with comprehensive error handling and testing including:
 * - HTTP error page validation (404, 500, 403, etc.)
 * - Network error simulation and recovery
 * - Form validation error testing
 * - Authentication error scenarios
 * - Error message and feedback validation
 * - Error recovery workflow testing
 * - Accessibility compliance for error states
 */
export class EnhancedErrorPage extends BasePage {
  constructor(page) {
    super(page);

    // HTTP error page elements
    this.httpErrors = {
      errorContainer: '[data-testid="error-container"], .error-page',
      errorCode: '[data-testid="error-code"], .error-code',
      errorTitle: '[data-testid="error-title"], .error-title, h1',
      errorMessage: '[data-testid="error-message"], .error-message',
      errorDescription: '[data-testid="error-description"], .error-description',
      homeButton: '[data-testid="home-button"], a:has-text("Home"), button:has-text("Home")',
      backButton: '[data-testid="back-button"], button:has-text("Back")',
      retryButton: '[data-testid="retry-button"], button:has-text("Retry")',
      reportButton: '[data-testid="report-error"], button:has-text("Report")',
      supportLink: '[data-testid="support-link"], a:has-text("Support")'
    };

    // Form validation error elements
    this.formErrors = {
      fieldError: '.field-error, .form-error, [role="alert"]',
      globalError: '[data-testid="global-error"], .global-error',
      validationSummary: '[data-testid="validation-summary"], .validation-summary',
      errorList: '[data-testid="error-list"], .error-list',
      errorIcon: '[data-testid="error-icon"], .error-icon',
      clearErrorsButton: '[data-testid="clear-errors"], button:has-text("Clear")'
    };

    // Network error elements
    this.networkErrors = {
      offlineIndicator: '[data-testid="offline-indicator"], .offline-indicator',
      connectionError: '[data-testid="connection-error"], .connection-error',
      timeoutError: '[data-testid="timeout-error"], .timeout-error',
      retryIndicator: '[data-testid="retry-indicator"], .retry-indicator',
      reconnectButton: '[data-testid="reconnect"], button:has-text("Reconnect")',
      offlineMessage: '[data-testid="offline-message"], .offline-message'
    };

    // Authentication error elements
    this.authErrors = {
      loginError: '[data-testid="login-error"], .login-error',
      sessionExpiredModal: '[data-testid="session-expired"], .session-expired-modal',
      unauthorizedMessage: '[data-testid="unauthorized"], .unauthorized-message',
      loginRedirectButton: '[data-testid="login-redirect"], button:has-text("Login")',
      refreshSessionButton: '[data-testid="refresh-session"], button:has-text("Refresh")'
    };

    // Vote-specific error elements
    this.voteErrors = {
      voteNotFoundError: '[data-testid="vote-not-found"], .vote-not-found',
      voteClosedError: '[data-testid="vote-closed"], .vote-closed',
      duplicateVoteError: '[data-testid="duplicate-vote"], .duplicate-vote',
      permissionError: '[data-testid="permission-error"], .permission-error',
      votingDisabledError: '[data-testid="voting-disabled"], .voting-disabled'
    };

    // Error recovery elements
    this.recovery = {
      recoveryContainer: '[data-testid="recovery-container"], .recovery-container',
      recoverySteps: '[data-testid="recovery-steps"], .recovery-steps',
      recoveryStep: '[data-testid="recovery-step"], .recovery-step',
      tryAgainButton: '[data-testid="try-again"], button:has-text("Try Again")',
      contactSupportButton: '[data-testid="contact-support"], button:has-text("Contact Support")',
      debugInfoToggle: '[data-testid="debug-info"], .debug-info-toggle',
      debugDetails: '[data-testid="debug-details"], .debug-details'
    };

    // Error notification elements
    this.notifications = {
      errorToast: '[data-testid="error-toast"], .error-toast',
      warningToast: '[data-testid="warning-toast"], .warning-toast',
      errorBanner: '[data-testid="error-banner"], .error-banner',
      dismissButton: '[data-testid="dismiss-error"], .dismiss-error',
      toastContainer: '[data-testid="toast-container"], .toast-container'
    };

    // Loading and timeout elements
    this.loadingErrors = {
      loadingTimeout: '[data-testid="loading-timeout"], .loading-timeout',
      slowConnectionWarning: '[data-testid="slow-connection"], .slow-connection',
      loadingFailed: '[data-testid="loading-failed"], .loading-failed',
      partialLoadError: '[data-testid="partial-load"], .partial-load-error'
    };
  }

  /**
   * HTTP Error Page Testing Methods
   */
  async goto404() {
    const loadTime = await super.goto('/non-existent-page-12345');
    await this.waitForErrorPage();
    return loadTime;
  }

  async goto500() {
    // This would typically require server-side setup to trigger 500 errors
    const loadTime = await super.goto('/trigger-500-error');
    await this.waitForErrorPage();
    return loadTime;
  }

  async goto403() {
    const loadTime = await super.goto('/admin/restricted-without-auth');
    await this.waitForErrorPage();
    return loadTime;
  }

  async waitForErrorPage() {
    await this.waitForElement(this.httpErrors.errorContainer, 'visible', 10000);

    // Wait for error content to load
    await Promise.race([
      this.waitForElement(this.httpErrors.errorCode),
      this.waitForElement(this.httpErrors.errorTitle),
      this.page.waitForTimeout(5000)
    ]);
  }

  async getErrorPageInfo() {
    const errorInfo = {
      code: await this.getElementText(this.httpErrors.errorCode).catch(() => ''),
      title: await this.getElementText(this.httpErrors.errorTitle).catch(() => ''),
      message: await this.getElementText(this.httpErrors.errorMessage).catch(() => ''),
      description: await this.getElementText(this.httpErrors.errorDescription).catch(() => ''),
      hasHomeButton: await this.isElementVisible(this.httpErrors.homeButton),
      hasBackButton: await this.isElementVisible(this.httpErrors.backButton),
      hasRetryButton: await this.isElementVisible(this.httpErrors.retryButton),
      hasSupportLink: await this.isElementVisible(this.httpErrors.supportLink)
    };

    return errorInfo;
  }

  async validateErrorPageStructure() {
    const validation = {
      hasErrorContainer: await this.isElementVisible(this.httpErrors.errorContainer),
      hasErrorCode: await this.isElementVisible(this.httpErrors.errorCode),
      hasErrorTitle: await this.isElementVisible(this.httpErrors.errorTitle),
      hasActionButtons: await this.hasActionButtons(),
      isAccessible: await this.validateErrorAccessibility()
    };

    return validation;
  }

  async hasActionButtons() {
    const buttons = [
      this.httpErrors.homeButton,
      this.httpErrors.backButton,
      this.httpErrors.retryButton
    ];

    for (const button of buttons) {
      if (await this.isElementVisible(button)) {
        return true;
      }
    }

    return false;
  }

  async tryErrorRecovery() {
    if (await this.isElementVisible(this.httpErrors.retryButton)) {
      await this.clickElement(this.httpErrors.retryButton);

      // Wait for either success or continued error
      const result = await Promise.race([
        this.page.waitForNavigation({ waitUntil: 'networkidle', timeout: 10000 }).then(() => 'navigation'),
        this.waitForElement(this.httpErrors.errorContainer, 'visible', 5000).then(() => 'still_error'),
        this.page.waitForTimeout(10000).then(() => 'timeout')
      ]);

      return { attempted: true, result };
    }

    return { attempted: false, result: 'no_retry_button' };
  }

  async navigateHome() {
    if (await this.isElementVisible(this.httpErrors.homeButton)) {
      await this.clickElement(this.httpErrors.homeButton);
      await this.waitForURL('**/', 10000);
      return true;
    }

    return false;
  }

  /**
   * Form Validation Error Testing Methods
   */
  async getFormErrors() {
    const errorElements = await this.page.locator(this.formErrors.fieldError).all();
    const errors = [];

    for (const [index, errorElement] of errorElements.entries()) {
      if (await errorElement.isVisible()) {
        const errorData = await errorElement.evaluate((el, idx) => {
          return {
            index: idx,
            text: el.textContent?.trim() || '',
            field: el.getAttribute('data-field') || '',
            type: el.getAttribute('data-error-type') || 'validation',
            visible: true
          };
        }, index);

        errors.push(errorData);
      }
    }

    return errors;
  }

  async getGlobalErrors() {
    const globalErrorElements = await this.page.locator(this.formErrors.globalError).all();
    const errors = [];

    for (const errorElement of globalErrorElements) {
      if (await errorElement.isVisible()) {
        const text = await errorElement.textContent();
        errors.push({
          text: text?.trim() || '',
          type: 'global',
          visible: true
        });
      }
    }

    return errors;
  }

  async hasValidationErrors() {
    const fieldErrors = await this.getFormErrors();
    const globalErrors = await this.getGlobalErrors();

    return fieldErrors.length > 0 || globalErrors.length > 0;
  }

  async clearFormErrors() {
    if (await this.isElementVisible(this.formErrors.clearErrorsButton)) {
      await this.clickElement(this.formErrors.clearErrorsButton);
      await this.page.waitForTimeout(500);
    }
  }

  async validateFormErrorDisplay() {
    const validation = {
      hasErrorIcons: await this.isElementVisible(this.formErrors.errorIcon),
      hasErrorList: await this.isElementVisible(this.formErrors.errorList),
      hasValidationSummary: await this.isElementVisible(this.formErrors.validationSummary),
      errorsCount: (await this.getFormErrors()).length,
      globalErrorsCount: (await this.getGlobalErrors()).length
    };

    return validation;
  }

  /**
   * Network Error Testing Methods
   */
  async simulateOfflineMode() {
    // Set browser offline
    await this.page.context().setOffline(true);

    // Wait for offline indicator
    await this.waitForElement(this.networkErrors.offlineIndicator, 'visible', 5000).catch(() => {
      // Offline indicator might not be present
    });

    return {
      offline: true,
      hasOfflineIndicator: await this.isElementVisible(this.networkErrors.offlineIndicator),
      hasOfflineMessage: await this.isElementVisible(this.networkErrors.offlineMessage)
    };
  }

  async restoreOnlineMode() {
    await this.page.context().setOffline(false);

    // Wait for offline indicator to disappear
    await this.page.waitForFunction(() => {
      const indicator = document.querySelector('[data-testid="offline-indicator"], .offline-indicator');
      return !indicator || !indicator.offsetParent;
    }, { timeout: 5000 }).catch(() => {
      // Offline indicator might persist
    });

    return {
      online: true,
      offlineIndicatorGone: !await this.isElementVisible(this.networkErrors.offlineIndicator)
    };
  }

  async simulateSlowConnection() {
    // Throttle network to simulate slow connection
    const cdpSession = await this.page.context().newCDPSession(this.page);
    await cdpSession.send('Network.enable');
    await cdpSession.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: 50 * 1024, // 50 KB/s
      uploadThroughput: 50 * 1024,
      latency: 2000 // 2 second latency
    });

    // Try to load a resource and check for slow connection warning
    await this.page.reload({ waitUntil: 'networkidle' });

    return {
      hasSlowConnectionWarning: await this.isElementVisible(this.networkErrors.slowConnectionWarning)
    };
  }

  async simulateConnectionTimeout() {
    // This would require intercepting network requests
    await this.page.route('**/api/**', route => {
      // Delay the response to simulate timeout
      setTimeout(() => {
        route.abort('timedout');
      }, 30000);
    });

    // Trigger a request that will timeout
    await this.page.reload();

    return {
      hasTimeoutError: await this.isElementVisible(this.networkErrors.timeoutError, 35000),
      hasRetryButton: await this.isElementVisible(this.networkErrors.reconnectButton)
    };
  }

  async testNetworkRecovery() {
    // Simulate offline, then back online
    await this.simulateOfflineMode();
    await this.page.waitForTimeout(2000);

    const recoveryResult = await this.restoreOnlineMode();

    // Test reconnect functionality
    if (await this.isElementVisible(this.networkErrors.reconnectButton)) {
      await this.clickElement(this.networkErrors.reconnectButton);
      await this.page.waitForTimeout(1000);
    }

    return {
      ...recoveryResult,
      reconnectAttempted: await this.isElementVisible(this.networkErrors.reconnectButton)
    };
  }

  /**
   * Authentication Error Testing Methods
   */
  async simulateSessionExpired() {
    // Clear authentication tokens
    await this.page.evaluate(() => {
      localStorage.removeItem('jwt');
      localStorage.removeItem('auth_token');
      sessionStorage.removeItem('jwt');
      sessionStorage.removeItem('auth_token');
    });

    // Try to access a protected resource
    await this.goto('/dashboard');

    return {
      hasSessionExpiredModal: await this.isElementVisible(this.authErrors.sessionExpiredModal, 5000),
      hasLoginRedirect: await this.isElementVisible(this.authErrors.loginRedirectButton),
      redirectedToLogin: this.page.url().includes('/login')
    };
  }

  async simulateUnauthorizedAccess() {
    // Try to access admin area without proper permissions
    await this.goto('/admin');

    return {
      hasUnauthorizedMessage: await this.isElementVisible(this.authErrors.unauthorizedMessage),
      hasLoginRedirect: await this.isElementVisible(this.authErrors.loginRedirectButton),
      statusCode: await this.page.evaluate(() => {
        return fetch('/admin').then(response => response.status).catch(() => null);
      })
    };
  }

  async handleSessionExpiry() {
    if (await this.isElementVisible(this.authErrors.sessionExpiredModal)) {
      if (await this.isElementVisible(this.authErrors.refreshSessionButton)) {
        await this.clickElement(this.authErrors.refreshSessionButton);

        // Wait for either success or login redirect
        const result = await Promise.race([
          this.page.waitForFunction(() => {
            return !document.querySelector('[data-testid="session-expired"], .session-expired-modal');
          }, { timeout: 5000 }).then(() => 'refreshed'),
          this.waitForURL('**/login', 5000).then(() => 'login_required'),
          this.page.waitForTimeout(5000).then(() => 'timeout')
        ]);

        return { handled: true, result };
      } else if (await this.isElementVisible(this.authErrors.loginRedirectButton)) {
        await this.clickElement(this.authErrors.loginRedirectButton);
        await this.waitForURL('**/login', 5000);
        return { handled: true, result: 'redirected_to_login' };
      }
    }

    return { handled: false, result: 'no_session_expired_modal' };
  }

  /**
   * Vote-Specific Error Testing Methods
   */
  async testVoteNotFound() {
    await this.goto('/vote/non-existent-vote-12345');

    return {
      hasVoteNotFoundError: await this.isElementVisible(this.voteErrors.voteNotFoundError),
      errorMessage: await this.getElementText(this.voteErrors.voteNotFoundError).catch(() => ''),
      hasHomeButton: await this.isElementVisible(this.httpErrors.homeButton)
    };
  }

  async testVoteClosedError() {
    // This would require a closed vote ID or simulation
    await this.goto('/vote/closed-vote-id');

    return {
      hasVoteClosedError: await this.isElementVisible(this.voteErrors.voteClosedError),
      errorMessage: await this.getElementText(this.voteErrors.voteClosedError).catch(() => ''),
      hasViewResultsOption: await this.isElementVisible('button:has-text("View Results")')
    };
  }

  async testDuplicateVoteError() {
    // This would require attempting to vote twice
    return {
      hasDuplicateVoteError: await this.isElementVisible(this.voteErrors.duplicateVoteError),
      errorMessage: await this.getElementText(this.voteErrors.duplicateVoteError).catch(() => ''),
      hasChangeVoteOption: await this.isElementVisible('button:has-text("Change Vote")')
    };
  }

  async testPermissionError() {
    // This would require accessing a private vote without permission
    return {
      hasPermissionError: await this.isElementVisible(this.voteErrors.permissionError),
      errorMessage: await this.getElementText(this.voteErrors.permissionError).catch(() => ''),
      hasLoginOption: await this.isElementVisible(this.authErrors.loginRedirectButton)
    };
  }

  /**
   * Error Recovery Testing Methods
   */
  async testErrorRecoveryWorkflow() {
    const recovery = {
      hasRecoveryContainer: await this.isElementVisible(this.recovery.recoveryContainer),
      hasRecoverySteps: await this.isElementVisible(this.recovery.recoverySteps),
      hasTryAgainButton: await this.isElementVisible(this.recovery.tryAgainButton),
      hasContactSupportButton: await this.isElementVisible(this.recovery.contactSupportButton),
      hasDebugInfo: await this.isElementVisible(this.recovery.debugInfoToggle)
    };

    return recovery;
  }

  async showDebugInformation() {
    if (await this.isElementVisible(this.recovery.debugInfoToggle)) {
      await this.clickElement(this.recovery.debugInfoToggle);
      await this.waitForElement(this.recovery.debugDetails, 'visible', 2000).catch(() => {});

      const debugInfo = await this.getElementText(this.recovery.debugDetails).catch(() => '');
      return { shown: true, debugInfo };
    }

    return { shown: false, debugInfo: '' };
  }

  async getRecoverySteps() {
    const stepElements = await this.page.locator(this.recovery.recoveryStep).all();
    const steps = [];

    for (const [index, step] of stepElements.entries()) {
      const stepText = await step.textContent();
      steps.push({
        index: index + 1,
        text: stepText?.trim() || '',
        completed: await step.evaluate(el => el.classList.contains('completed'))
      });
    }

    return steps;
  }

  /**
   * Error Notification Testing Methods
   */
  async getErrorNotifications() {
    const notifications = {
      errorToasts: await this.getToastNotifications('error'),
      warningToasts: await this.getToastNotifications('warning'),
      errorBanners: await this.getBannerNotifications()
    };

    return notifications;
  }

  async getToastNotifications(type = 'error') {
    const selector = type === 'error' ? this.notifications.errorToast : this.notifications.warningToast;
    const toastElements = await this.page.locator(selector).all();
    const toasts = [];

    for (const [index, toast] of toastElements.entries()) {
      if (await toast.isVisible()) {
        const toastData = await toast.evaluate((el, idx) => ({
          index: idx,
          text: el.textContent?.trim() || '',
          type: el.getAttribute('data-type') || type,
          dismissible: !!el.querySelector('.dismiss-error, [data-testid="dismiss-error"]')
        }), index);

        toasts.push(toastData);
      }
    }

    return toasts;
  }

  async getBannerNotifications() {
    const bannerElements = await this.page.locator(this.notifications.errorBanner).all();
    const banners = [];

    for (const [index, banner] of bannerElements.entries()) {
      if (await banner.isVisible()) {
        const bannerData = await banner.evaluate((el, idx) => ({
          index: idx,
          text: el.textContent?.trim() || '',
          dismissible: !!el.querySelector('.dismiss-error, [data-testid="dismiss-error"]'),
          persistent: el.classList.contains('persistent')
        }), index);

        banners.push(bannerData);
      }
    }

    return banners;
  }

  async dismissErrorNotification(index = 0) {
    const dismissButtons = await this.page.locator(this.notifications.dismissButton).all();

    if (index < dismissButtons.length) {
      await dismissButtons[index].click();
      await this.page.waitForTimeout(300);
      return true;
    }

    return false;
  }

  /**
   * Accessibility Validation for Error States
   */
  async validateErrorAccessibility() {
    const accessibility = {
      hasAriaLive: await this.validateAriaLiveRegions(),
      hasErrorRole: await this.validateErrorRoles(),
      hasKeyboardAccess: await this.validateKeyboardAccessForErrors(),
      hasScreenReaderSupport: await this.validateScreenReaderSupport()
    };

    return accessibility;
  }

  async validateAriaLiveRegions() {
    const liveRegions = await this.page.locator('[aria-live], [role="alert"]').all();

    for (const region of liveRegions) {
      const ariaLive = await region.getAttribute('aria-live');
      const role = await region.getAttribute('role');

      if (ariaLive === 'assertive' || ariaLive === 'polite' || role === 'alert') {
        return true;
      }
    }

    return false;
  }

  async validateErrorRoles() {
    const errorElements = await this.page.locator('[role="alert"], .error-message, .field-error').all();
    let hasProperRoles = 0;

    for (const element of errorElements) {
      const role = await element.getAttribute('role');
      if (role === 'alert') {
        hasProperRoles++;
      }
    }

    return {
      totalErrors: errorElements.length,
      withProperRoles: hasProperRoles,
      percentage: errorElements.length > 0 ? (hasProperRoles / errorElements.length) * 100 : 0
    };
  }

  async validateKeyboardAccessForErrors() {
    // Test if error recovery buttons are keyboard accessible
    const actionButtons = await this.page.locator(
      `${this.httpErrors.retryButton}, ${this.httpErrors.homeButton}, ${this.recovery.tryAgainButton}`
    ).all();

    let accessibleButtons = 0;

    for (const button of actionButtons) {
      await button.focus();
      const isFocused = await button.evaluate(el => document.activeElement === el);
      if (isFocused) {
        accessibleButtons++;
      }
    }

    return {
      totalButtons: actionButtons.length,
      accessibleButtons,
      allAccessible: actionButtons.length > 0 && accessibleButtons === actionButtons.length
    };
  }

  async validateScreenReaderSupport() {
    const support = {
      hasAltText: await this.validateErrorImageAltText(),
      hasDescriptiveText: await this.validateDescriptiveErrorText(),
      hasProperHeadings: await this.validateErrorPageHeadings()
    };

    return support;
  }

  async validateErrorImageAltText() {
    const images = await this.page.locator('.error-page img, .error-container img').all();
    let imagesWithAlt = 0;

    for (const image of images) {
      const alt = await image.getAttribute('alt');
      if (alt && alt.trim() !== '') {
        imagesWithAlt++;
      }
    }

    return {
      totalImages: images.length,
      imagesWithAlt,
      allHaveAlt: images.length > 0 && imagesWithAlt === images.length
    };
  }

  async validateDescriptiveErrorText() {
    const errorTitle = await this.getElementText(this.httpErrors.errorTitle).catch(() => '');
    const errorMessage = await this.getElementText(this.httpErrors.errorMessage).catch(() => '');

    return {
      hasTitleText: errorTitle.length > 0,
      hasMessageText: errorMessage.length > 0,
      isDescriptive: errorTitle.length > 10 && errorMessage.length > 20
    };
  }

  async validateErrorPageHeadings() {
    const headings = await this.page.locator('h1, h2, h3, h4, h5, h6').all();

    return {
      hasHeadings: headings.length > 0,
      headingCount: headings.length,
      hasMainHeading: await this.isElementVisible('h1')
    };
  }

  /**
   * Performance Monitoring for Error Scenarios
   */
  async measureErrorPagePerformance() {
    const startTime = Date.now();

    // Test 404 page load performance
    await this.goto404();
    const errorPageLoadTime = Date.now() - startTime;

    // Test error recovery performance
    const recoveryStartTime = Date.now();
    const recoveryResult = await this.tryErrorRecovery();
    const recoveryTime = Date.now() - recoveryStartTime;

    return {
      errorPageLoadTime,
      recoveryTime,
      recoveryAttempted: recoveryResult.attempted,
      recoveryResult: recoveryResult.result,
      errorPageAcceptable: errorPageLoadTime < PERFORMANCE_FIXTURES.THRESHOLDS.PAGE_LOAD.ACCEPTABLE,
      recoveryAcceptable: recoveryTime < PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.PAGE_TRANSITION
    };
  }
}
