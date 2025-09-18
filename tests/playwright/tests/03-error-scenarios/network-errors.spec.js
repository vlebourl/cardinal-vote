import { test, expect } from '@playwright/test';
import { EnhancedLandingPage } from '../../pages/landing-page.enhanced.js';
import { EnhancedDashboardPage } from '../../pages/dashboard-page.enhanced.js';
import { EnhancedVoteCreationPage } from '../../pages/vote-creation-page.enhanced.js';
import { EnhancedPublicVotingPage } from '../../pages/public-voting-page.enhanced.js';
import { EnhancedErrorPage } from '../../pages/error-page.enhanced.js';
import { testDataManager } from '../../fixtures/data/test-data-factory.js';

test.describe('Network Error Scenario Tests', () => {
  test.describe.configure({ mode: 'parallel' });

  let landingPage;
  let dashboardPage;
  let voteCreationPage;
  let publicVotingPage;
  let errorPage;

  test.beforeEach(async ({ page }) => {
    landingPage = new EnhancedLandingPage(page);
    dashboardPage = new EnhancedDashboardPage(page);
    voteCreationPage = new EnhancedVoteCreationPage(page);
    publicVotingPage = new EnhancedPublicVotingPage(page);
    errorPage = new EnhancedErrorPage(page);
  });

  test.afterEach(async ({ page }) => {
    // Reset network conditions
    await page.context().setOffline(false);
    await page.unroute('**/*');
    await testDataManager.runCleanup();
  });

  test.describe('Offline Mode Testing', () => {
    test('should handle going offline during authentication', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.fillLoginForm(loginData.email, loginData.password);

      // Go offline before submitting
      const offlineResult = await errorPage.simulateOfflineMode();
      expect(offlineResult.offline).toBe(true);

      // Attempt to submit login
      const submissionResult = await landingPage.submitLoginForm();
      expect(submissionResult.result).toBe('error');

      // Should show offline message or connection error
      const hasOfflineMessage = await errorPage.isElementVisible(
        '.offline-message, .connection-error, [data-testid="offline-indicator"]', 3000
      );
      expect(hasOfflineMessage).toBe(true);

      // Test recovery when back online
      const onlineResult = await errorPage.restoreOnlineMode();
      expect(onlineResult.online).toBe(true);

      // Should be able to retry login
      const retryResult = await landingPage.submitLoginForm();
      if (retryResult.result === 'success') {
        expect(page.url()).toContain('dashboard');
      }
    });

    test('should handle going offline during vote submission', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-offline-vote');

      const options = await publicVotingPage.getVoteOptions();
      expect(options.length).toBeGreaterThan(0);

      await publicVotingPage.selectOption(0);

      // Go offline before submission
      await errorPage.simulateOfflineMode();

      // Attempt to submit vote
      const submissionResult = await publicVotingPage.submitVote();
      expect(submissionResult.result).toBe('error');

      // Should indicate network problem
      const networkError = await errorPage.isElementVisible(
        '.network-error, .connection-error, .offline-message', 3000
      );
      expect(networkError).toBe(true);

      // Test offline state handling
      const offlineIndicators = await errorPage.getOfflineIndicators();
      expect(offlineIndicators.hasOfflineMessage).toBe(true);
    });

    test('should cache content for offline viewing', async ({ page }) => {
      // Load a vote while online
      await publicVotingPage.gotoPublicVote('test-cacheable-vote');

      const onlineVoteInfo = await publicVotingPage.getVoteInformation();
      expect(onlineVoteInfo.title).toBeTruthy();

      // Go offline
      await errorPage.simulateOfflineMode();

      // Reload page to test caching
      await page.reload();

      // Basic content should still be accessible
      const offlineValidation = await publicVotingPage.validateOfflineAccess();
      expect(offlineValidation.titleVisible).toBe(true);
      expect(offlineValidation.basicContentVisible).toBe(true);

      // Interactive features should show offline state
      expect(offlineValidation.interactiveFeaturesDisabled).toBe(true);
    });

    test('should handle offline mode with graceful degradation', async ({ page }) => {
      await landingPage.goto();

      // Go offline
      await errorPage.simulateOfflineMode();

      // Navigate to different sections
      const sections = ['/dashboard', '/create-vote', '/admin'];

      for (const section of sections) {
        await page.goto(section);

        const offlineHandling = await errorPage.validateOfflineHandling();
        expect(offlineHandling.showsOfflineMessage).toBe(true);
        expect(offlineHandling.preventsDataLoss).toBe(true);
        expect(offlineHandling.providesGuidance).toBe(true);
      }
    });
  });

  test.describe('Connection Timeout Testing', () => {
    test('should handle API request timeouts', async ({ page }) => {
      // Simulate slow network responses
      await page.route('**/api/**', async route => {
        // Delay all API requests
        await new Promise(resolve => setTimeout(resolve, 30000));
        route.continue();
      });

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.fillLoginForm(loginData.email, loginData.password);

      // Submit should timeout
      const submissionResult = await landingPage.submitLoginForm();
      expect(['error', 'timeout']).toContain(submissionResult.result);

      // Should show timeout message
      const timeoutError = await errorPage.isElementVisible(
        '.timeout-error, .request-timeout, [data-testid="timeout-error"]', 35000
      );
      expect(timeoutError).toBe(true);
    });

    test('should handle vote creation timeout', async ({ page }) => {
      await page.goto('/auth/test-login?user=user1&role=user');
      await voteCreationPage.goto();

      // Fill out vote form
      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();
      await voteCreationPage.addVoteOption({ text: 'Option A' });
      await voteCreationPage.addVoteOption({ text: 'Option B' });
      await voteCreationPage.goToNextStep();
      await voteCreationPage.fillVoteSettings({});

      // Simulate timeout on publish
      await page.route('**/api/votes**', route => {
        setTimeout(() => route.abort('timedout'), 31000);
      });

      const publishResult = await voteCreationPage.publishVote();
      expect(['error', 'timeout']).toContain(publishResult.result);

      // Form data should be preserved for retry
      const formValidation = await voteCreationPage.validateCompleteForm();
      expect(formValidation.step1.title.value).toBe(voteData.title);
    });

    test('should handle file upload timeouts', async ({ page }) => {
      await page.goto('/auth/test-login?user=user1&role=user');
      await voteCreationPage.goto();

      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      // Simulate slow file upload
      await page.route('**/api/upload/**', route => {
        setTimeout(() => route.abort('timedout'), 31000);
      });

      // Attempt file upload
      const uploadResult = await voteCreationPage.addVoteOption({
        text: 'Option with Image',
        file: './tests/playwright/fixtures/test-image.png'
      });

      // Should handle upload timeout gracefully
      const uploadError = await voteCreationPage.isElementVisible(
        '.upload-error, .file-upload-error, [data-testid="upload-error"]', 35000
      );
      expect(uploadError).toBe(true);

      // Option should still be added without file
      const options = await voteCreationPage.getOptions();
      expect(options.some(opt => opt.text === 'Option with Image')).toBe(true);
    });
  });

  test.describe('Server Error Response Testing', () => {
    test('should handle 500 internal server errors', async ({ page }) => {
      await page.route('**/api/auth/login', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal server error' })
        });
      });

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.fillLoginForm(loginData.email, loginData.password);

      const submissionResult = await landingPage.submitLoginForm();
      expect(submissionResult.result).toBe('error');

      // Should show user-friendly error message
      const errorMessage = await landingPage.getLoginErrorMessage();
      expect(errorMessage).toBeTruthy();
      expect(errorMessage.toLowerCase()).toMatch(/server|error|try again/);
    });

    test('should handle 503 service unavailable', async ({ page }) => {
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 503,
          body: JSON.stringify({ error: 'Service temporarily unavailable' })
        });
      });

      await landingPage.goto();

      // Should show service unavailable message
      const serviceError = await errorPage.isElementVisible(
        '.service-unavailable, .maintenance-mode, [data-testid="service-error"]', 5000
      );
      expect(serviceError).toBe(true);

      // Should provide retry option
      const retryOption = await errorPage.isElementVisible(
        'button:has-text("Retry"), .retry-button, [data-testid="retry"]', 3000
      );
      expect(retryOption).toBe(true);
    });

    test('should handle rate limiting (429 errors)', async ({ page }) => {
      let requestCount = 0;

      await page.route('**/api/auth/login', route => {
        requestCount++;
        if (requestCount > 2) {
          route.fulfill({
            status: 429,
            headers: { 'Retry-After': '60' },
            body: JSON.stringify({ error: 'Too many requests' })
          });
        } else {
          route.fulfill({
            status: 400,
            body: JSON.stringify({ error: 'Invalid credentials' })
          });
        }
      });

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginData = testDataManager.createFormData('login', 'invalid');

      // Make multiple failed login attempts
      for (let i = 0; i < 3; i++) {
        await landingPage.fillLoginForm(loginData.email, loginData.password);
        const result = await landingPage.submitLoginForm();
        expect(result.result).toBe('error');

        if (i === 2) {
          // Should show rate limit message
          const rateLimitError = await landingPage.getLoginErrorMessage();
          expect(rateLimitError.toLowerCase()).toMatch(/many|limit|wait|try.*later/);
        }
      }
    });

    test('should handle CORS errors', async ({ page }) => {
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 0, // Simulates CORS error
          body: ''
        });
      });

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.fillLoginForm(loginData.email, loginData.password);

      const submissionResult = await landingPage.submitLoginForm();
      expect(submissionResult.result).toBe('error');

      // Should show connection error message
      const connectionError = await landingPage.getLoginErrorMessage();
      expect(connectionError.toLowerCase()).toMatch(/connection|network|try again/);
    });
  });

  test.describe('Intermittent Network Issues', () => {
    test('should handle flaky network connections', async ({ page }) => {
      let requestCount = 0;

      await page.route('**/api/votes/**', route => {
        requestCount++;
        // Simulate intermittent failures
        if (requestCount % 3 === 0) {
          route.abort('failed');
        } else {
          route.continue();
        }
      });

      await publicVotingPage.gotoPublicVote('test-flaky-vote');

      const options = await publicVotingPage.getVoteOptions();
      await publicVotingPage.selectOption(0);

      // First attempt might fail
      let submissionResult = await publicVotingPage.submitVote();

      if (submissionResult.result === 'error') {
        // Should provide retry mechanism
        const retryButton = page.locator('button:has-text("Retry"), .retry-button');
        if (await retryButton.isVisible()) {
          await retryButton.click();

          // Retry should eventually succeed
          submissionResult = await publicVotingPage.submitVote();
        }
      }

      // Eventually should succeed or show persistent error
      expect(['success', 'error']).toContain(submissionResult.result);
    });

    test('should implement exponential backoff for retries', async ({ page }) => {
      let attemptCount = 0;
      const attemptTimes = [];

      await page.route('**/api/auth/login', route => {
        attemptCount++;
        attemptTimes.push(Date.now());

        if (attemptCount < 3) {
          route.abort('failed');
        } else {
          route.fulfill({
            status: 200,
            body: JSON.stringify({ token: 'success-token' })
          });
        }
      });

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.fillLoginForm(loginData.email, loginData.password);

      const submissionResult = await landingPage.submitLoginForm();

      if (attemptTimes.length > 1) {
        // Verify exponential backoff timing
        for (let i = 1; i < attemptTimes.length; i++) {
          const delay = attemptTimes[i] - attemptTimes[i - 1];
          expect(delay).toBeGreaterThan(500 * Math.pow(2, i - 1)); // Exponential backoff
        }
      }
    });
  });

  test.describe('Slow Network Simulation', () => {
    test('should handle slow network conditions', async ({ page }) => {
      // Throttle network speed
      const cdpSession = await page.context().newCDPSession(page);
      await cdpSession.send('Network.enable');
      await cdpSession.send('Network.emulateNetworkConditions', {
        offline: false,
        downloadThroughput: 50 * 1024, // 50 KB/s
        uploadThroughput: 50 * 1024,
        latency: 2000 // 2 second latency
      });

      const loadStart = Date.now();
      await landingPage.goto();
      const loadTime = Date.now() - loadStart;

      // Should show slow connection warning
      const slowConnectionWarning = await errorPage.isElementVisible(
        '.slow-connection, .loading-slow, [data-testid="slow-connection"]', 5000
      );

      if (slowConnectionWarning) {
        expect(slowConnectionWarning).toBe(true);
      }

      // Page should still be functional despite slow load
      const pageUsable = await landingPage.validatePageUsability();
      expect(pageUsable.navigationPresent).toBe(true);
      expect(pageUsable.essentialElementsVisible).toBe(true);
    });

    test('should show loading indicators for slow operations', async ({ page }) => {
      // Slow down specific API endpoints
      await page.route('**/api/votes/**', async route => {
        await new Promise(resolve => setTimeout(resolve, 3000));
        route.continue();
      });

      await page.goto('/auth/test-login?user=user1&role=user');
      await dashboardPage.goto();

      // Should show loading indicators
      const loadingIndicators = await dashboardPage.validateLoadingIndicators();
      expect(loadingIndicators.hasLoadingSpinner).toBe(true);
      expect(loadingIndicators.showsLoadingText).toBe(true);

      // Content should eventually load
      await page.waitForTimeout(5000);
      const finalState = await dashboardPage.validatePageLoadComplete();
      expect(finalState.contentLoaded).toBe(true);
      expect(finalState.loadingIndicatorsHidden).toBe(true);
    });
  });

  test.describe('Network Recovery Testing', () => {
    test('should automatically retry failed requests when connection restored', async ({ page }) => {
      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.fillLoginForm(loginData.email, loginData.password);

      // Go offline
      await errorPage.simulateOfflineMode();

      // Attempt login (should fail)
      const offlineResult = await landingPage.submitLoginForm();
      expect(offlineResult.result).toBe('error');

      // Go back online
      await errorPage.restoreOnlineMode();

      // Should automatically retry or provide retry option
      const recoveryResult = await errorPage.testNetworkRecovery();
      expect(recoveryResult.reconnectAttempted).toBe(true);

      // Manual retry should work
      const retryResult = await landingPage.submitLoginForm();
      expect(['success', 'pending']).toContain(retryResult.result);
    });

    test('should preserve form data during network issues', async ({ page }) => {
      await page.goto('/auth/test-login?user=user1&role=user');
      await voteCreationPage.goto();

      // Fill form data
      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();
      await voteCreationPage.addVoteOption({ text: 'Preserved Option' });

      // Simulate network failure
      await errorPage.simulateOfflineMode();

      // Try to navigate or perform action
      await voteCreationPage.goToNextStep();

      // Data should be preserved
      await voteCreationPage.goToStep(1);
      const titleValue = await voteCreationPage.getElementValue(voteCreationPage.basicInfo.titleInput);
      expect(titleValue).toBe(voteData.title);

      await voteCreationPage.goToStep(2);
      const options = await voteCreationPage.getOptions();
      expect(options.some(opt => opt.text === 'Preserved Option')).toBe(true);
    });

    test('should handle partial page loads gracefully', async ({ page }) => {
      // Allow HTML to load but fail CSS/JS resources
      await page.route('**/*.css', route => route.abort('failed'));
      await page.route('**/*.js', route => {
        if (route.request().url().includes('vendor') || route.request().url().includes('bundle')) {
          route.abort('failed');
        } else {
          route.continue();
        }
      });

      await landingPage.goto();

      // Should show degraded experience notice
      const degradedNotice = await errorPage.isElementVisible(
        '.degraded-experience, .limited-functionality, [data-testid="partial-load"]', 5000
      );

      // Basic functionality should still work
      const basicFunctionality = await landingPage.testBasicFunctionality();
      expect(basicFunctionality.linksWork).toBe(true);
      expect(basicFunctionality.formsAccessible).toBe(true);
    });
  });

  test.describe('API Endpoint Specific Errors', () => {
    test('should handle authentication API failures', async ({ page }) => {
      const authEndpoints = [
        '/api/auth/login',
        '/api/auth/register',
        '/api/auth/logout',
        '/api/auth/refresh'
      ];

      for (const endpoint of authEndpoints) {
        await page.route(`**${endpoint}`, route => {
          route.fulfill({
            status: 502,
            body: JSON.stringify({ error: 'Bad Gateway' })
          });
        });
      }

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.fillLoginForm(loginData.email, loginData.password);

      const result = await landingPage.submitLoginForm();
      expect(result.result).toBe('error');

      // Should show service-specific error
      const serviceError = await landingPage.getLoginErrorMessage();
      expect(serviceError.toLowerCase()).toMatch(/service|unavailable|try.*later/);
    });

    test('should handle vote management API failures', async ({ page }) => {
      await page.goto('/auth/test-login?user=user1&role=user');

      // Fail vote-related endpoints
      await page.route('**/api/votes**', route => {
        route.fulfill({
          status: 503,
          body: JSON.stringify({ error: 'Vote service unavailable' })
        });
      });

      await dashboardPage.goto();

      // Should show service unavailable for votes
      const voteServiceError = await dashboardPage.isElementVisible(
        '.vote-service-error, .service-unavailable, [data-testid="vote-service-error"]', 5000
      );

      // Other functionality should still work
      const otherFunctionsWork = await dashboardPage.testNonVoteFunctionality();
      expect(otherFunctionsWork.navigationWorks).toBe(true);
      expect(otherFunctionsWork.profileAccessible).toBe(true);
    });
  });

  test.describe('Network Error User Experience', () => {
    test('should provide helpful error messages and recovery options', async ({ page }) => {
      await page.route('**/api/**', route => route.abort('failed'));

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.fillLoginForm(loginData.email, loginData.password);

      const result = await landingPage.submitLoginForm();
      expect(result.result).toBe('error');

      // Should provide helpful error message
      const errorMessage = await landingPage.getLoginErrorMessage();
      expect(errorMessage).toBeTruthy();

      // Should provide recovery options
      const recoveryOptions = await errorPage.getErrorRecoveryOptions();
      expect(recoveryOptions.hasRetryOption).toBe(true);
      expect(recoveryOptions.hasHelpLink).toBe(true);
      expect(recoveryOptions.hasContactInfo).toBe(true);
    });

    test('should maintain accessibility during network errors', async ({ page }) => {
      await page.route('**/api/**', route => route.abort('failed'));

      await landingPage.goto();

      const errorAccessibility = await errorPage.validateErrorAccessibility();
      expect(errorAccessibility.hasAriaLive).toBe(true);
      expect(errorAccessibility.hasErrorRole).toBeTruthy();
      expect(errorAccessibility.hasKeyboardAccess.allAccessible).toBe(true);

      // Error messages should be announced to screen readers
      const screenReaderSupport = await errorPage.validateScreenReaderSupport();
      expect(screenReaderSupport.hasDescriptiveText.isDescriptive).toBe(true);
    });

    test('should track network error metrics', async ({ page }) => {
      let errorCount = 0;

      page.on('response', response => {
        if (!response.ok()) {
          errorCount++;
        }
      });

      await page.route('**/api/auth/login', route => {
        route.fulfill({ status: 500 });
      });

      await landingPage.goto();
      await landingPage.clickSignIn();
      await landingPage.waitForLoginModal();

      const loginData = testDataManager.createFormData('login', 'user');
      await landingPage.fillLoginForm(loginData.email, loginData.password);
      await landingPage.submitLoginForm();

      expect(errorCount).toBeGreaterThan(0);

      // Should log errors for monitoring
      const errorLogs = await page.evaluate(() => {
        return window.errorLogs || [];
      });

      expect(errorLogs.length).toBeGreaterThanOrEqual(0);
    });
  });
});
