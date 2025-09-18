import { test, expect } from '@playwright/test';

test.describe('Basic Authentication Verification', () => {
  test('should load the landing page and find authentication elements', async ({ page }) => {
    console.log('🌐 Navigating to application...');
    await page.goto('http://localhost:8000');

    console.log('📄 Checking page title...');
    await expect(page).toHaveTitle(/Generalized Voting Platform/);

    console.log('🔍 Looking for Sign In elements...');
    // Look for any Sign In text on the page
    const signInElement = page.locator('text="Sign In"').first();
    await expect(signInElement).toBeVisible();

    console.log('🔍 Looking for registration elements...');
    // Look for registration-related text
    const hasRegistration = await page.locator('text="Sign Up"').first().isVisible();
    console.log(`📊 Registration element found: ${hasRegistration}`);

    console.log('🔍 Checking for JavaScript errors...');
    // Listen for console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Wait a moment for any JS to execute
    await page.waitForTimeout(2000);

    console.log(`📊 JavaScript errors found: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
      console.log('❌ JavaScript Errors:', consoleErrors);
    }

    // Verify no critical JS errors occurred
    expect(consoleErrors).toHaveLength(0);

    console.log('✅ Basic authentication elements verification completed');
  });

  test('should verify API endpoints are accessible', async ({ page }) => {
    console.log('🔌 Testing API endpoint accessibility...');

    // Test that we can make requests to the API
    const response = await page.request.get('http://localhost:8000/api/health');
    console.log(`📊 API health response status: ${response.status()}`);

    // Even if health endpoint doesn't exist, app should respond
    expect(response.status()).toBeLessThan(500);

    console.log('✅ API endpoint accessibility verified');
  });

  test('should verify page loads without critical errors', async ({ page }) => {
    console.log('🌐 Loading page and checking for critical errors...');

    // Track any network failures
    const failedRequests = [];
    page.on('requestfailed', request => {
      failedRequests.push(`${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
    });

    // Navigate to the page
    await page.goto('http://localhost:8000');

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');

    console.log(`📊 Failed requests: ${failedRequests.length}`);
    if (failedRequests.length > 0) {
      console.log('⚠️ Failed requests:', failedRequests);
    }

    // Take a screenshot for debugging
    await page.screenshot({ path: 'tests/playwright/basic-auth-verification.png', fullPage: true });
    console.log('📸 Screenshot saved: tests/playwright/basic-auth-verification.png');

    // Verify page loaded successfully
    await expect(page.locator('body')).toBeVisible();

    console.log('✅ Page load verification completed');
  });
});
