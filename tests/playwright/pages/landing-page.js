import { expect } from '@playwright/test';

export class LandingPage {
  constructor(page) {
    this.page = page;

    // Element selectors based on the current page structure
    this.signInButton = 'button:has-text("Sign In")';
    this.getStartedButton = 'button:has-text("Get Started")';
    this.navigationMenu = 'button:has-text("Open navigation menu")';

    // Modal selectors (to be implemented when modals are visible)
    this.loginModal = '[data-testid="login-modal"]';
    this.registerModal = '[data-testid="register-modal"]';

    // Form selectors
    this.emailInput = '[data-testid="login-email"], input[type="email"]';
    this.passwordInput = '[data-testid="login-password"], input[type="password"]';
    this.loginSubmitButton = '[data-testid="login-submit"]';
    this.registerSubmitButton = '[data-testid="register-submit"]';

    // Error message selectors
    this.errorMessage = '.error-message, .alert, [role="alert"]';
  }

  async goto() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  async clickSignIn() {
    await this.page.click(this.signInButton);
    // Wait for modal to appear or page to change
    await this.page.waitForTimeout(1000);
  }

  async clickGetStarted() {
    await this.page.click(this.getStartedButton);
    // Wait for modal to appear or page to change
    await this.page.waitForTimeout(1000);
  }

  async isSignInButtonVisible() {
    return await this.page.isVisible(this.signInButton);
  }

  async isGetStartedButtonVisible() {
    return await this.page.isVisible(this.getStartedButton);
  }

  // Modal-related methods
  async waitForLoginModal() {
    try {
      await this.page.waitForSelector(this.loginModal, { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async waitForRegisterModal() {
    try {
      await this.page.waitForSelector(this.registerModal, { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async fillLoginForm(email, password) {
    await this.page.fill(this.emailInput, email);
    await this.page.fill(this.passwordInput, password);
  }

  async submitLoginForm() {
    await this.page.click(this.loginSubmitButton);

    // Wait for either success (redirect) or error message
    const responses = await Promise.race([
      this.page.waitForURL('**/dashboard', { timeout: 5000 }).then(() => 'success'),
      this.page.waitForSelector(this.errorMessage, { timeout: 5000 }).then(() => 'error'),
      this.page.waitForTimeout(5000).then(() => 'timeout')
    ]);

    return responses;
  }

  async getErrorMessage() {
    const errorElement = await this.page.locator(this.errorMessage).first();
    if (await errorElement.isVisible()) {
      return await errorElement.textContent();
    }
    return null;
  }

  // Material Design validation methods
  async validateMaterialDesignElements() {
    // Check for Material Icons
    const materialIcons = this.page.locator('.material-icons');
    const iconCount = await materialIcons.count();
    expect(iconCount).toBeGreaterThan(0);

    // Check for Material Design buttons
    const buttons = this.page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);

    return {
      materialIcons: iconCount,
      buttons: buttonCount
    };
  }

  async checkResponsiveLayout() {
    // Test different viewport sizes
    const viewports = [
      { width: 1200, height: 800 }, // Desktop
      { width: 768, height: 1024 }, // Tablet
      { width: 375, height: 667 }   // Mobile
    ];

    const results = {};

    for (const viewport of viewports) {
      await this.page.setViewportSize(viewport);
      await this.page.waitForTimeout(500); // Allow for responsive adjustments

      const isSignInVisible = await this.isSignInButtonVisible();
      const isGetStartedVisible = await this.isGetStartedButtonVisible();

      results[`${viewport.width}x${viewport.height}`] = {
        signInVisible: isSignInVisible,
        getStartedVisible: isGetStartedVisible
      };
    }

    return results;
  }

  // JWT Token inspection methods (for testing sessionStorage)
  async getSessionStorageToken() {
    return await this.page.evaluate(() => {
      return window.sessionStorage.getItem('jwt') ||
             window.sessionStorage.getItem('auth_token') ||
             window.sessionStorage.getItem('token');
    });
  }

  async getAllSessionStorage() {
    return await this.page.evaluate(() => {
      const items = {};
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        items[key] = sessionStorage.getItem(key);
      }
      return items;
    });
  }

  async clearSessionStorage() {
    await this.page.evaluate(() => {
      sessionStorage.clear();
    });
  }

  // Network request monitoring
  async monitorAuthRequests() {
    const requests = [];

    this.page.on('request', request => {
      const url = request.url();
      if (url.includes('/auth/') || url.includes('/login') || url.includes('/register')) {
        requests.push({
          url: url,
          method: request.method(),
          headers: request.headers(),
          timestamp: Date.now()
        });
      }
    });

    return requests;
  }

  async getPageConsoleMessages() {
    const messages = [];

    this.page.on('console', msg => {
      messages.push({
        type: msg.type(),
        text: msg.text(),
        timestamp: Date.now()
      });
    });

    return messages;
  }
}
