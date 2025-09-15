import { test, expect } from '@playwright/test';
import { EnhancedLandingPage } from '../../pages/landing-page.enhanced.js';
import { EnhancedDashboardPage } from '../../pages/dashboard-page.enhanced.js';
import { EnhancedErrorPage } from '../../pages/error-page.enhanced.js';
import { testDataManager } from '../../fixtures/data/test-data-factory.js';
import { PERFORMANCE_FIXTURES } from '../../fixtures/data/performance-accessibility-fixtures.js';

test.describe('Core Authentication Flow Tests', () => {
  test.describe.configure({ mode: 'parallel' });

  let landingPage;
  let dashboardPage;
  let errorPage;

  test.beforeEach(async ({ page }) => {
    landingPage = new EnhancedLandingPage(page);
    dashboardPage = new EnhancedDashboardPage(page);
    errorPage = new EnhancedErrorPage(page);
  });

  test.afterEach(async ({ page }) => {
    // Clean up any test data created during the test
    await testDataManager.runCleanup();
  });

  test.describe('User Registration Flow', () => {
    test('should successfully register a new user with valid data', async ({ page }) => {
      const userData = testDataManager.createFormData('registration', 'valid');

      await landingPage.goto();

      // Validate landing page loads properly
      const loadTime = await landingPage.measurePageLoadTime();
      expect(loadTime.isAcceptable).toBe(true);

      // Click get started button to open registration
      await landingPage.clickGetStarted();

      // Wait for registration modal/form
      const hasRegistrationForm = await landingPage.waitForRegistrationModal();
      expect(hasRegistrationForm).toBe(true);

      // Fill registration form
      const fillResult = await landingPage.fillRegistrationForm(userData);
      expect(fillResult.isAcceptable).toBe(true);

      // Validate form before submission
      const validation = await landingPage.validateRegistrationForm();
      expect(validation.email.isValid).toBe(true);
      expect(validation.password.isValid).toBe(true);
      expect(validation.confirmPassword.isValid).toBe(true);

      // Submit registration
      const submissionResult = await landingPage.submitRegistrationForm();
      expect(submissionResult.result).toBe('success');
      expect(submissionResult.isAcceptable).toBe(true);

      // Verify successful registration
      expect(submissionResult.redirectUrl).toMatch(/dashboard|welcome/);

      // Verify user is logged in
      const authState = await landingPage.getAuthenticationState();
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.userEmail).toBe(userData.email);
    });

    test('should handle registration with invalid email format', async ({ page }) => {
      const invalidUserData = testDataManager.createFormData('registration', 'invalid', {
        errorType: 'email'
      });

      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      // Fill form with invalid email
      await landingPage.fillRegistrationForm(invalidUserData);

      // Submit and expect validation errors
      const submissionResult = await landingPage.submitRegistrationForm();
      expect(submissionResult.result).toBe('error');

      // Validate specific error messages
      const errors = await landingPage.getFormErrors();
      expect(errors.some(error => error.field === 'email')).toBe(true);
      expect(errors.some(error => error.text.toLowerCase().includes('email'))).toBe(true);

      // Verify user is not authenticated
      const authState = await landingPage.getAuthenticationState();
      expect(authState.isAuthenticated).toBe(false);
    });

    test('should handle registration with weak password', async ({ page }) => {
      const weakPasswordData = testDataManager.createFormData('registration', 'invalid', {
        errorType: 'password'
      });

      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      await landingPage.fillRegistrationForm(weakPasswordData);

      const submissionResult = await landingPage.submitRegistrationForm();
      expect(submissionResult.result).toBe('error');

      // Validate password strength error
      const errors = await landingPage.getFormErrors();
      expect(errors.some(error => error.field === 'password')).toBe(true);
    });

    test('should handle password confirmation mismatch', async ({ page }) => {
      const mismatchData = testDataManager.createFormData('registration', 'invalid', {
        errorType: 'confirm_password'
      });

      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      await landingPage.fillRegistrationForm(mismatchData);

      const submissionResult = await landingPage.submitRegistrationForm();
      expect(submissionResult.result).toBe('error');

      // Validate password mismatch error
      const errors = await landingPage.getFormErrors();
      expect(errors.some(error => error.field === 'confirmPassword')).toBe(true);
    });

    test('should require terms and conditions acceptance', async ({ page }) => {
      const noTermsData = testDataManager.createFormData('registration', 'invalid', {
        errorType: 'terms'
      });

      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      await landingPage.fillRegistrationForm(noTermsData);

      const submissionResult = await landingPage.submitRegistrationForm();
      expect(submissionResult.result).toBe('error');

      // Validate terms acceptance error
      const errors = await landingPage.getFormErrors();
      expect(errors.some(error => error.field === 'agreeToTerms')).toBe(true);
    });

    test('should handle duplicate email registration', async ({ page }) => {
      // Use existing test user email
      const duplicateData = testDataManager.createFormData('registration', 'valid', {
        email: 'user1.test@cardinalvote.local' // From test data
      });

      await landingPage.goto();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      await landingPage.fillRegistrationForm(duplicateData);

      const submissionResult = await landingPage.submitRegistrationForm();
      expect(submissionResult.result).toBe('error');

      // Validate duplicate email error
      const errors = await landingPage.getFormErrors();
      expect(errors.some(error => error.text.toLowerCase().includes('already exists'))).toBe(true);
    });
  });

  test.describe('User Login Flow', () => {
    test('should successfully login with valid credentials', async ({ page }) => {
      const loginData = testDataManager.createFormData('login', 'user');

      await landingPage.goto();

      // Click sign in button
      await landingPage.clickSignIn();

      // Wait for login modal/form
      const hasLoginForm = await landingPage.waitForLoginModal();
      expect(hasLoginForm).toBe(true);

      // Fill and submit login form
      const fillResult = await landingPage.fillLoginForm(loginData.email, loginData.password);
      expect(fillResult.isAcceptable).toBe(true);

      const submissionResult = await landingPage.submitLoginForm();
      expect(submissionResult.result).toBe('success');
      expect(submissionResult.isAcceptable).toBe(true);

      // Verify successful login and redirect
      expect(page.url()).toMatch(/dashboard/);

      // Verify authentication state
      const authState = await landingPage.getAuthenticationState();
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.userEmail).toBe(loginData.email);

      // Verify session persistence
      const sessionData = await landingPage.getSessionData();
      expect(sessionData.hasJWT).toBe(true);
      expect(sessionData.sessionExpiry).toBeTruthy();
    });

    test('should handle login with invalid credentials', async ({ page }) => {
      const invalidLoginData = testDataManager.createFormData('login', 'invalid', {
        errorType: 'invalid_credentials'
      });

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      await landingPage.fillLoginForm(invalidLoginData.email, invalidLoginData.password);

      const submissionResult = await landingPage.submitLoginForm();
      expect(submissionResult.result).toBe('error');

      // Validate authentication error
      const errorMessage = await landingPage.getLoginErrorMessage();
      expect(errorMessage).toMatch(/invalid|incorrect|wrong/i);

      // Verify user is not authenticated
      const authState = await landingPage.getAuthenticationState();
      expect(authState.isAuthenticated).toBe(false);
    });

    test('should handle login with empty credentials', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      // Attempt to submit without filling form
      const submissionResult = await landingPage.submitLoginForm();
      expect(submissionResult.result).toBe('error');

      // Validate required field errors
      const errors = await landingPage.getFormErrors();
      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(error => error.field === 'email')).toBe(true);
      expect(errors.some(error => error.field === 'password')).toBe(true);
    });

    test('should maintain remember me functionality', async ({ page }) => {
      const loginData = testDataManager.createFormData('login', 'user', {
        rememberMe: true
      });

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      // Enable remember me option
      await landingPage.toggleRememberMe(true);

      await landingPage.fillLoginForm(loginData.email, loginData.password);
      const submissionResult = await landingPage.submitLoginForm();
      expect(submissionResult.result).toBe('success');

      // Verify remember me token is set
      const sessionData = await landingPage.getSessionData();
      expect(sessionData.hasRememberToken).toBe(true);

      // Test session persistence after page reload
      await page.reload();
      const authStateAfterReload = await landingPage.getAuthenticationState();
      expect(authStateAfterReload.isAuthenticated).toBe(true);
    });

    test('should handle admin login with special permissions', async ({ page }) => {
      const adminLoginData = testDataManager.createFormData('login', 'admin');

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      await landingPage.fillLoginForm(adminLoginData.email, adminLoginData.password);
      const submissionResult = await landingPage.submitLoginForm();
      expect(submissionResult.result).toBe('success');

      // Verify admin authentication state
      const authState = await landingPage.getAuthenticationState();
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.userRole).toBe('admin');
      expect(authState.permissions).toContain('admin:access');

      // Navigate to dashboard and verify admin features
      await dashboardPage.goto();
      const adminNavigation = await dashboardPage.isElementVisible('[data-testid="admin-nav"], .admin-navigation');
      expect(adminNavigation).toBe(true);
    });
  });

  test.describe('User Logout Flow', () => {
    test.beforeEach(async ({ page }) => {
      // Login before each logout test
      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();
      await landingPage.fillLoginForm(loginData.email, loginData.password);
      await landingPage.submitLoginForm();
      await dashboardPage.goto();
    });

    test('should successfully logout user', async ({ page }) => {
      // Verify user is initially logged in
      const initialAuthState = await dashboardPage.getAuthenticationState();
      expect(initialAuthState.isAuthenticated).toBe(true);

      // Perform logout
      await dashboardPage.logout();

      // Verify logout redirect
      expect(page.url()).toMatch(/\/$/); // Redirected to home

      // Verify authentication state is cleared
      const authStateAfterLogout = await landingPage.getAuthenticationState();
      expect(authStateAfterLogout.isAuthenticated).toBe(false);

      // Verify session data is cleared
      const sessionData = await landingPage.getSessionData();
      expect(sessionData.hasJWT).toBe(false);
      expect(sessionData.sessionStorage).toEqual({});
    });

    test('should handle logout from multiple tabs', async ({ context, page }) => {
      // Open another tab and login
      const secondPage = await context.newPage();
      const secondLandingPage = new EnhancedLandingPage(secondPage);

      await secondLandingPage.goto();
      const authState = await secondLandingPage.getAuthenticationState();
      expect(authState.isAuthenticated).toBe(true); // Should be logged in due to session

      // Logout from first tab
      await dashboardPage.logout();

      // Verify logout affects both tabs
      const firstTabAuthState = await landingPage.getAuthenticationState();
      expect(firstTabAuthState.isAuthenticated).toBe(false);

      // Refresh second tab and check auth state
      await secondPage.reload();
      const secondTabAuthState = await secondLandingPage.getAuthenticationState();
      expect(secondTabAuthState.isAuthenticated).toBe(false);

      await secondPage.close();
    });
  });

  test.describe('Session Management', () => {
    test('should handle session expiration gracefully', async ({ page }) => {
      const loginData = testDataManager.createFormData('login', 'user');

      // Login normally
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();
      await landingPage.fillLoginForm(loginData.email, loginData.password);
      await landingPage.submitLoginForm();

      // Simulate session expiration by clearing tokens
      await errorPage.simulateSessionExpired();

      // Try to access protected resource
      await dashboardPage.goto();

      // Should handle session expiry
      const sessionResult = await errorPage.handleSessionExpiry();
      expect(sessionResult.handled).toBe(true);
      expect(['refreshed', 'login_required', 'redirected_to_login']).toContain(sessionResult.result);
    });

    test('should refresh session tokens when needed', async ({ page }) => {
      const loginData = testDataManager.createFormData('login', 'user');

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();
      await landingPage.fillLoginForm(loginData.email, loginData.password);
      await landingPage.submitLoginForm();

      // Get initial session data
      const initialSession = await landingPage.getSessionData();
      expect(initialSession.hasJWT).toBe(true);

      // Simulate near-expiry and trigger refresh
      await page.evaluate(() => {
        const now = Date.now();
        const nearExpiry = new Date(now + 60000); // 1 minute from now
        localStorage.setItem('jwt_expiry', nearExpiry.toISOString());
      });

      // Navigate to dashboard (should trigger token refresh)
      await dashboardPage.goto();

      // Verify session is still valid
      const refreshedSession = await landingPage.getSessionData();
      expect(refreshedSession.hasJWT).toBe(true);
    });
  });

  test.describe('Password Reset Flow', () => {
    test('should handle password reset request', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      // Click forgot password link
      const forgotPasswordLink = page.locator('[data-testid="forgot-password"], a:has-text("Forgot Password")');
      if (await forgotPasswordLink.isVisible()) {
        await forgotPasswordLink.click();

        // Fill password reset form
        const resetEmail = 'user1.test@cardinalvote.local';
        await landingPage.fillField('input[name="email"], input[type="email"]', resetEmail);

        // Submit password reset request
        await landingPage.clickElement('button:has-text("Reset Password"), button[type="submit"]');

        // Verify success message
        const successMessage = await landingPage.waitForElement('.success-message, [role="status"]', 'visible', 5000);
        expect(successMessage).toBe(true);
      }
    });
  });

  test.describe('Authentication Performance', () => {
    test('should meet performance thresholds for authentication flows', async ({ page }) => {
      const loginData = testDataManager.createFormData('login', 'user');

      // Measure login performance
      const loginStartTime = Date.now();

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();
      await landingPage.fillLoginForm(loginData.email, loginData.password);
      const submissionResult = await landingPage.submitLoginForm();

      const totalLoginTime = Date.now() - loginStartTime;

      // Validate performance thresholds
      expect(submissionResult.isAcceptable).toBe(true);
      expect(totalLoginTime).toBeLessThan(PERFORMANCE_FIXTURES.THRESHOLDS.API_RESPONSE.AUTHENTICATION);

      // Measure logout performance
      await dashboardPage.goto();

      const logoutStartTime = Date.now();
      await dashboardPage.logout();
      const logoutTime = Date.now() - logoutStartTime;

      expect(logoutTime).toBeLessThan(PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.PAGE_TRANSITION);
    });
  });

  test.describe('Authentication Accessibility', () => {
    test('should have accessible authentication forms', async ({ page }) => {
      await landingPage.goto();

      // Test login form accessibility
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginAccessibility = await landingPage.validateAccessibility();
      expect(loginAccessibility.focusManagement.focusableElementCount).toBeGreaterThan(0);
      expect(loginAccessibility.ariaAttributes.hasAriaElements).toBe(true);
      expect(loginAccessibility.keyboardNavigation.tabNavigationWorks).toBe(true);

      // Test registration form accessibility
      await landingPage.closeModal();
      await landingPage.clickGetStarted();
      await landingPage.waitForRegistrationModal();

      const registrationAccessibility = await landingPage.validateAccessibility();
      expect(registrationAccessibility.semanticStructure.hasMainContent).toBe(true);
      expect(registrationAccessibility.semanticStructure.landmarkCount).toBeGreaterThan(0);
    });

    test('should support keyboard navigation for authentication', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      // Test keyboard navigation through form
      await page.keyboard.press('Tab'); // Email field
      await page.keyboard.type('test@example.com');

      await page.keyboard.press('Tab'); // Password field
      await page.keyboard.type('password123');

      await page.keyboard.press('Tab'); // Submit button
      await page.keyboard.press('Enter'); // Submit form

      // Should attempt login (even if it fails due to invalid credentials)
      const hasError = await landingPage.isElementVisible('.error-message, [role="alert"]', 3000);
      expect(hasError).toBe(true); // Invalid credentials should show error
    });
  });

  test.describe('Multi-Factor Authentication', () => {
    test('should handle 2FA when enabled', async ({ page }) => {
      // This test would require 2FA to be enabled in the system
      // For now, we'll test the UI presence and flow
      const loginData = testDataManager.createFormData('login', 'admin'); // Admin might have 2FA

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      await landingPage.fillLoginForm(loginData.email, loginData.password);
      const submissionResult = await landingPage.submitLoginForm();

      // Check if 2FA prompt appears
      const has2FAPrompt = await landingPage.isElementVisible('[data-testid="2fa-prompt"], .two-factor-prompt', 3000);

      if (has2FAPrompt) {
        // Test 2FA form accessibility and structure
        const twoFactorInput = page.locator('input[name="twoFactorCode"], input[placeholder*="code"]');
        expect(await twoFactorInput.isVisible()).toBe(true);

        // Test invalid 2FA code
        await twoFactorInput.fill('000000');
        await page.keyboard.press('Enter');

        const hasError = await landingPage.isElementVisible('.error-message, [role="alert"]', 3000);
        expect(hasError).toBe(true);
      }
    });
  });
});
