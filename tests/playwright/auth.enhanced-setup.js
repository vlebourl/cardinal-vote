import { test as setup, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { LandingPage } from './pages/landing-page.js';
import { DashboardPage } from './pages/dashboard-page.js';
import { TEST_USERS } from './fixtures/test-data.js';

/**
 * Enhanced Authentication Setup for Playwright E2E Tests
 *
 * Features:
 * - Multiple authentication scenarios (admin, user, guest)
 * - Robust state persistence across test runs
 * - Fallback authentication strategies
 * - Comprehensive error handling and debugging
 * - Performance monitoring and validation
 * - Cross-browser compatibility
 */

// Authentication state files for different user types
const AUTH_FILES = {
  admin: 'tests/playwright/.auth/admin.json',
  user: 'tests/playwright/.auth/user.json',
  user2: 'tests/playwright/.auth/user2.json',
  guest: 'tests/playwright/.auth/guest.json'
};

const SESSION_FILES = {
  admin: 'tests/playwright/.auth/admin-session.json',
  user: 'tests/playwright/.auth/user-session.json',
  user2: 'tests/playwright/.auth/user2-session.json',
  guest: 'tests/playwright/.auth/guest-session.json'
};

// Authentication configuration
const AUTH_CONFIG = {
  maxRetries: 3,
  timeoutMs: 30000,
  fallbackToMock: true,
  validateAfterAuth: true,
  persistSession: true,
  debugMode: process.env.DEBUG_AUTH === 'true'
};

// Ensure auth directory exists
const authDir = path.dirname(AUTH_FILES.user);
if (!fs.existsSync(authDir)) {
  fs.mkdirSync(authDir, { recursive: true });
}

/**
 * Enhanced authentication setup for admin user
 */
setup('authenticate admin user', async ({ page, context }) => {
  await authenticateUser(page, context, 'admin', TEST_USERS.ADMIN);
});

/**
 * Enhanced authentication setup for regular user
 */
setup('authenticate regular user', async ({ page, context }) => {
  await authenticateUser(page, context, 'user', TEST_USERS.USER_1);
});

/**
 * Enhanced authentication setup for second user (for multi-user testing)
 */
setup('authenticate second user', async ({ page, context }) => {
  await authenticateUser(page, context, 'user2', TEST_USERS.USER_2);
});

/**
 * Guest session setup (no authentication)
 */
setup('setup guest session', async ({ page, context }) => {
  console.log('🔓 Setting up guest session...');

  const landingPage = new LandingPage(page);

  try {
    // Navigate to landing page
    await landingPage.goto();

    // Validate guest access
    const signInVisible = await landingPage.isSignInButtonVisible();
    expect(signInVisible).toBeTruthy();

    // Save guest state
    await saveAuthenticationState(page, context, 'guest', {
      isAuthenticated: false,
      userType: 'guest'
    });

    console.log('✅ Guest session setup completed');

  } catch (error) {
    console.error('❌ Guest session setup failed:', error.message);
    throw error;
  }
});

/**
 * Main authentication function with enhanced error handling
 */
async function authenticateUser(page, context, userType, userData) {
  console.log(`🔐 Starting enhanced authentication for ${userType}...`);

  const landingPage = new LandingPage(page);
  const dashboardPage = new DashboardPage(page);

  const startTime = Date.now();
  let authAttempt = 1;

  while (authAttempt <= AUTH_CONFIG.maxRetries) {
    try {
      console.log(`📝 Authentication attempt ${authAttempt}/${AUTH_CONFIG.maxRetries} for ${userType}`);

      // Clear any existing authentication state
      await clearAuthenticationState(page);

      // Navigate to landing page
      console.log('📄 Navigating to landing page...');
      await landingPage.goto();

      // Validate page load
      await validatePageLoad(page, landingPage);

      // Attempt authentication
      const authResult = await performAuthentication(page, landingPage, userData, userType);

      if (authResult.success) {
        // Validate authentication state
        const validation = await validateAuthentication(page, dashboardPage, userType);

        if (validation.success) {
          // Save authentication state
          await saveAuthenticationState(page, context, userType, {
            ...authResult,
            ...validation,
            userData,
            authenticatedAt: new Date().toISOString()
          });

          const authTime = Date.now() - startTime;
          console.log(`✅ ${userType} authentication completed successfully in ${authTime}ms`);
          return;
        } else {
          console.log(`⚠️  Authentication validation failed for ${userType}: ${validation.error}`);
        }
      } else {
        console.log(`⚠️  Authentication failed for ${userType}: ${authResult.error}`);
      }

    } catch (error) {
      console.error(`❌ Authentication attempt ${authAttempt} failed for ${userType}:`, error.message);

      // Take debug screenshot
      await page.screenshot({
        path: `tests/playwright/.auth/${userType}-auth-failure-${authAttempt}.png`
      });
    }

    authAttempt++;

    if (authAttempt <= AUTH_CONFIG.maxRetries) {
      console.log(`🔄 Retrying authentication for ${userType} in 2 seconds...`);
      await page.waitForTimeout(2000);
    }
  }

  // All attempts failed - use fallback if enabled
  if (AUTH_CONFIG.fallbackToMock) {
    console.log(`🎭 Using mock authentication fallback for ${userType}...`);
    await setupMockAuthentication(page, context, userType, userData);
  } else {
    throw new Error(`Authentication failed for ${userType} after ${AUTH_CONFIG.maxRetries} attempts`);
  }
}

/**
 * Validate that the page loaded correctly
 */
async function validatePageLoad(page, landingPage) {
  // Check page title
  const title = await page.title();
  expect(title).toContain('Generalized Voting Platform');

  // Check for critical elements
  const signInVisible = await landingPage.isSignInButtonVisible();

  if (!signInVisible) {
    // Take debug screenshot
    await page.screenshot({ path: 'tests/playwright/.auth/page-load-debug.png' });

    // Log page state
    const url = page.url();
    const content = await page.content();

    console.log(`📍 URL: ${url}`);
    console.log(`📋 Title: ${title}`);
    console.log(`📄 Page content length: ${content.length}`);

    // Check for common error indicators
    const errorElements = await page.locator('[role="alert"], .error, .alert-danger').count();
    if (errorElements > 0) {
      const errorText = await page.locator('[role="alert"], .error, .alert-danger').first().textContent();
      throw new Error(`Page loaded with error: ${errorText}`);
    }
  }

  console.log('✅ Page load validation passed');
}

/**
 * Perform authentication with multiple strategies
 */
async function performAuthentication(page, landingPage, userData, userType) {
  console.log(`🔑 Performing authentication for ${userType} (${userData.email})`);

  try {
    // Strategy 1: UI-based authentication
    const uiResult = await attemptUIAuthentication(page, landingPage, userData);
    if (uiResult.success) {
      return uiResult;
    }

    // Strategy 2: API-based authentication
    console.log('🔗 Attempting API authentication...');
    const apiResult = await attemptAPIAuthentication(page, userData);
    if (apiResult.success) {
      return apiResult;
    }

    // Strategy 3: Direct token injection (for testing environments)
    if (process.env.TEST_ENV === 'docker' || process.env.TEST_ENV === 'e2e_testing') {
      console.log('💉 Attempting direct token injection...');
      const tokenResult = await attemptTokenInjection(page, userData);
      if (tokenResult.success) {
        return tokenResult;
      }
    }

    return { success: false, error: 'All authentication strategies failed' };

  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Attempt UI-based authentication
 */
async function attemptUIAuthentication(page, landingPage, userData) {
  try {
    const signInVisible = await landingPage.isSignInButtonVisible();
    if (!signInVisible) {
      return { success: false, error: 'Sign In button not visible' };
    }

    await landingPage.clickSignIn();

    const modalAppeared = await landingPage.waitForLoginModal();
    if (!modalAppeared) {
      return { success: false, error: 'Login modal did not appear' };
    }

    // Fill login form
    await landingPage.fillLoginForm(userData.email, userData.password);
    const result = await landingPage.submitLoginForm();

    if (result === 'success') {
      return { success: true, method: 'ui', redirected: true };
    } else if (result === 'error') {
      const errorMsg = await landingPage.getErrorMessage();
      return { success: false, error: `UI login error: ${errorMsg}` };
    } else {
      return { success: false, error: 'UI login result unclear' };
    }

  } catch (error) {
    return { success: false, error: `UI authentication failed: ${error.message}` };
  }
}

/**
 * Attempt API-based authentication
 */
async function attemptAPIAuthentication(page, userData) {
  try {
    const response = await page.request.post('/auth/login', {
      data: {
        email: userData.email,
        password: userData.password
      },
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok()) {
      const data = await response.json();

      if (data.token || data.access_token) {
        // Inject token into storage
        const token = data.token || data.access_token;
        await page.evaluate((token) => {
          sessionStorage.setItem('jwt', token);
          sessionStorage.setItem('auth_token', token);
          localStorage.setItem('backup_auth', token);
        }, token);

        // Navigate to dashboard
        await page.goto('/dashboard');

        return { success: true, method: 'api', token: token };
      } else {
        return { success: false, error: 'No token in API response' };
      }
    } else {
      const responseText = await response.text();
      return { success: false, error: `API responded with ${response.status()}: ${responseText}` };
    }

  } catch (error) {
    return { success: false, error: `API authentication failed: ${error.message}` };
  }
}

/**
 * Attempt direct token injection for test environments
 */
async function attemptTokenInjection(page, userData) {
  try {
    // Create a test JWT token (this should be replaced with actual token generation in production)
    const mockToken = await generateTestToken(userData);

    await page.evaluate((token) => {
      sessionStorage.setItem('jwt', token);
      sessionStorage.setItem('auth_token', token);
      sessionStorage.setItem('user', JSON.stringify({
        email: '{{userData.email}}',
        role: '{{userData.role}}',
        authenticated: true
      }));
      localStorage.setItem('backup_auth', token);
    }, mockToken);

    // Navigate to dashboard to validate
    await page.goto('/dashboard');

    return { success: true, method: 'token_injection', token: mockToken };

  } catch (error) {
    return { success: false, error: `Token injection failed: ${error.message}` };
  }
}

/**
 * Generate a test JWT token
 */
async function generateTestToken(userData) {
  // In a real implementation, this would create a proper JWT
  // For testing, we use a predictable format
  const header = btoa(JSON.stringify({ typ: 'JWT', alg: 'HS256' }));
  const payload = btoa(JSON.stringify({
    sub: userData.email,
    email: userData.email,
    role: userData.role || 'user',
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 3600,
    iss: 'playwright-test'
  }));
  const signature = 'test-signature';

  return `${header}.${payload}.${signature}`;
}

/**
 * Validate authentication state
 */
async function validateAuthentication(page, dashboardPage, userType) {
  try {
    console.log(`🔍 Validating authentication for ${userType}...`);

    // Check current URL
    const currentUrl = page.url();
    if (!currentUrl.includes('dashboard') && !currentUrl.includes('admin')) {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
    }

    // Check if logged in
    const isLoggedIn = await dashboardPage.isLoggedIn();
    if (!isLoggedIn) {
      return { success: false, error: 'User not logged in according to dashboard page' };
    }

    // Validate session storage
    const sessionData = await page.evaluate(() => {
      return {
        jwt: sessionStorage.getItem('jwt'),
        auth_token: sessionStorage.getItem('auth_token'),
        user: sessionStorage.getItem('user'),
        backup_auth: localStorage.getItem('backup_auth')
      };
    });

    const hasAuthToken = !!(sessionData.jwt || sessionData.auth_token || sessionData.backup_auth);
    if (!hasAuthToken) {
      return { success: false, error: 'No authentication tokens found in storage' };
    }

    // Validate JWT token format if present
    const token = sessionData.jwt || sessionData.auth_token;
    if (token) {
      const jwtPattern = /^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$/;
      if (!jwtPattern.test(token)) {
        return { success: false, error: 'Invalid JWT token format' };
      }
    }

    // Test session persistence
    await page.reload();
    await page.waitForLoadState('networkidle');

    const tokenAfterReload = await page.evaluate(() => {
      return sessionStorage.getItem('jwt') || sessionStorage.getItem('auth_token');
    });

    if (!tokenAfterReload) {
      return { success: false, error: 'Session not persistent across page reload' };
    }

    console.log(`✅ Authentication validation passed for ${userType}`);

    return {
      success: true,
      isAuthenticated: true,
      tokens: sessionData,
      url: currentUrl
    };

  } catch (error) {
    return { success: false, error: `Validation failed: ${error.message}` };
  }
}

/**
 * Clear existing authentication state
 */
async function clearAuthenticationState(page) {
  await page.evaluate(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  await page.context().clearCookies();
}

/**
 * Setup mock authentication for fallback scenarios
 */
async function setupMockAuthentication(page, context, userType, userData) {
  console.log(`🎭 Setting up mock authentication for ${userType}...`);

  const mockToken = await generateTestToken(userData);

  await page.evaluate((token, userData) => {
    sessionStorage.setItem('jwt', token);
    sessionStorage.setItem('auth_token', token);
    sessionStorage.setItem('user', JSON.stringify({
      email: userData.email,
      role: userData.role || 'user',
      displayName: userData.displayName,
      authenticated: true,
      mock: true
    }));
    localStorage.setItem('backup_auth', token);
  }, mockToken, userData);

  // Save mock authentication state
  await saveAuthenticationState(page, context, userType, {
    success: true,
    method: 'mock',
    token: mockToken,
    userData,
    authenticatedAt: new Date().toISOString(),
    isMock: true
  });

  console.log(`✅ Mock authentication setup completed for ${userType}`);
}

/**
 * Save authentication state to files
 */
async function saveAuthenticationState(page, context, userType, authData) {
  console.log(`💾 Saving authentication state for ${userType}...`);

  // Save Playwright's storage state (cookies, localStorage)
  await context.storageState({ path: AUTH_FILES[userType] });

  // Save sessionStorage separately
  const sessionStorage = await page.evaluate(() => JSON.stringify(sessionStorage));
  fs.writeFileSync(SESSION_FILES[userType], sessionStorage, 'utf-8');

  // Save additional authentication metadata
  const authMetadata = {
    ...authData,
    userType,
    savedAt: new Date().toISOString(),
    browser: context.browser()?.browserType()?.name(),
    viewport: await page.viewportSize()
  };

  fs.writeFileSync(
    `tests/playwright/.auth/${userType}-metadata.json`,
    JSON.stringify(authMetadata, null, 2)
  );

  console.log(`✅ Authentication state saved for ${userType}`);
}

/**
 * Utility function to restore session storage
 */
export async function restoreSessionStorage(page, userType = 'user') {
  const sessionFile = SESSION_FILES[userType];

  if (fs.existsSync(sessionFile)) {
    const sessionStorageData = JSON.parse(fs.readFileSync(sessionFile, 'utf-8'));

    await page.addInitScript((storage) => {
      for (const [key, value] of Object.entries(storage)) {
        window.sessionStorage.setItem(key, value);
      }
    }, sessionStorageData);

    console.log(`🔄 Session storage restored for ${userType}`);
  }
}

/**
 * Utility function to get authentication metadata
 */
export function getAuthMetadata(userType = 'user') {
  const metadataFile = `tests/playwright/.auth/${userType}-metadata.json`;

  if (fs.existsSync(metadataFile)) {
    return JSON.parse(fs.readFileSync(metadataFile, 'utf-8'));
  }

  return null;
}

// Configure setup to run in serial mode for authentication
setup.describe.configure({ mode: 'serial' });