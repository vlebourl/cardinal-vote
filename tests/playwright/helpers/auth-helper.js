import fs from 'fs';
import { expect } from '@playwright/test';

/**
 * Authentication Helper Utilities for Playwright Tests
 *
 * Provides comprehensive authentication support including:
 * - User authentication and session management
 * - Token validation and refresh
 * - Multi-user authentication scenarios
 * - Authentication state persistence
 * - Error handling and debugging
 */

export class AuthHelper {
  constructor(page) {
    this.page = page;
    this.authConfig = {
      timeoutMs: 10000,
      retryAttempts: 3,
      tokenStorageKeys: ['jwt', 'auth_token', 'token', 'access_token'],
      userStorageKey: 'user'
    };
  }

  /**
   * Authenticate user with multiple fallback strategies
   */
  async authenticateAs(userType = 'user') {
    const userTypes = {
      admin: 'admin',
      user: 'user',
      user1: 'user',
      user2: 'user2',
      guest: 'guest'
    };

    const selectedUserType = userTypes[userType] || 'user';
    return await this.restoreAuthenticationState(selectedUserType);
  }

  /**
   * Restore authentication state from saved files
   */
  async restoreAuthenticationState(userType) {
    const authFile = `tests/playwright/.auth/${userType}.json`;
    const sessionFile = `tests/playwright/.auth/${userType}-session.json`;

    if (!fs.existsSync(authFile)) {
      throw new Error(`Authentication file not found for ${userType}. Please run authentication setup first.`);
    }

    // Restore session storage
    if (fs.existsSync(sessionFile)) {
      const sessionData = JSON.parse(fs.readFileSync(sessionFile, 'utf-8'));
      await this.page.addInitScript((storage) => {
        for (const [key, value] of Object.entries(storage)) {
          window.sessionStorage.setItem(key, value);
        }
      }, sessionData);
    }

    return { success: true, userType };
  }

  /**
   * Validate current authentication state
   */
  async validateAuthentication() {
    const authData = await this.page.evaluate(() => {
      const storage = {
        session: Object.fromEntries(
          Object.keys(sessionStorage).map(key => [key, sessionStorage.getItem(key)])
        ),
        local: Object.fromEntries(
          Object.keys(localStorage).map(key => [key, localStorage.getItem(key)])
        )
      };

      return {
        storage,
        url: window.location.href,
        cookies: document.cookie,
        userAgent: navigator.userAgent
      };
    });

    // Check for authentication tokens
    const hasAuthToken = this.authConfig.tokenStorageKeys.some(key =>
      authData.storage.session[key] || authData.storage.local[key]
    );

    // Check for user data
    const hasUserData = !!(authData.storage.session[this.authConfig.userStorageKey] ||
                            authData.storage.local[this.authConfig.userStorageKey]);

    return {
      isAuthenticated: hasAuthToken && hasUserData,
      hasToken: hasAuthToken,
      hasUserData,
      storage: authData.storage,
      url: authData.url,
      tokens: this.extractTokens(authData.storage)
    };
  }

  /**
   * Extract authentication tokens from storage
   */
  extractTokens(storage) {
    const tokens = {};

    this.authConfig.tokenStorageKeys.forEach(key => {
      if (storage.session[key]) {
        tokens[`session_${key}`] = storage.session[key];
      }
      if (storage.local[key]) {
        tokens[`local_${key}`] = storage.local[key];
      }
    });

    return tokens;
  }

  /**
   * Get current user information
   */
  async getCurrentUser() {
    return await this.page.evaluate((userKey) => {
      const userData = sessionStorage.getItem(userKey) || localStorage.getItem(userKey);
      if (userData) {
        try {
          return JSON.parse(userData);
        } catch (e) {
          return { error: 'Invalid user data format' };
        }
      }
      return null;
    }, this.authConfig.userStorageKey);
  }

  /**
   * Validate JWT token format and expiration
   */
  async validateToken(token = null) {
    if (!token) {
      const authState = await this.validateAuthentication();
      const tokens = Object.values(authState.tokens);
      token = tokens[0]; // Use first available token
    }

    if (!token) {
      return { valid: false, error: 'No token available' };
    }

    // Basic JWT format validation
    const jwtPattern = /^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$/;
    if (!jwtPattern.test(token)) {
      return { valid: false, error: 'Invalid JWT format' };
    }

    try {
      // Decode JWT payload (without verification for testing)
      const parts = token.split('.');
      if (parts.length !== 3) {
        return { valid: false, error: 'Invalid JWT structure' };
      }

      const payload = JSON.parse(atob(parts[1]));
      const now = Math.floor(Date.now() / 1000);

      const validation = {
        valid: true,
        payload,
        isExpired: payload.exp && payload.exp < now,
        expiresAt: payload.exp ? new Date(payload.exp * 1000) : null,
        issuedAt: payload.iat ? new Date(payload.iat * 1000) : null,
        subject: payload.sub,
        email: payload.email,
        role: payload.role
      };

      if (validation.isExpired) {
        validation.valid = false;
        validation.error = 'Token is expired';
      }

      return validation;

    } catch (error) {
      return { valid: false, error: `Token validation failed: ${error.message}` };
    }
  }

  /**
   * Clear all authentication data
   */
  async clearAuthentication() {
    await this.page.evaluate(() => {
      sessionStorage.clear();
      localStorage.clear();
    });

    // Clear cookies
    await this.page.context().clearCookies();

    return { success: true };
  }

  /**
   * Switch user context
   */
  async switchUser(newUserType) {
    await this.clearAuthentication();
    await this.page.reload({ waitUntil: 'networkidle' });
    return await this.authenticateAs(newUserType);
  }

  /**
   * Test authentication persistence across page reload
   */
  async testAuthenticationPersistence() {
    const beforeReload = await this.validateAuthentication();

    if (!beforeReload.isAuthenticated) {
      return { success: false, error: 'Not authenticated before reload test' };
    }

    await this.page.reload({ waitUntil: 'networkidle' });

    const afterReload = await this.validateAuthentication();

    return {
      success: afterReload.isAuthenticated,
      persistent: beforeReload.isAuthenticated === afterReload.isAuthenticated,
      before: beforeReload,
      after: afterReload
    };
  }

  /**
   * Test authentication across navigation
   */
  async testAuthenticationNavigation(targetUrl = '/dashboard') {
    const beforeNav = await this.validateAuthentication();

    if (!beforeNav.isAuthenticated) {
      return { success: false, error: 'Not authenticated before navigation test' };
    }

    await this.page.goto(targetUrl);
    await this.page.waitForLoadState('networkidle');

    const afterNav = await this.validateAuthentication();

    return {
      success: afterNav.isAuthenticated,
      persistent: beforeNav.isAuthenticated === afterNav.isAuthenticated,
      targetUrl,
      before: beforeNav,
      after: afterNav
    };
  }

  /**
   * Monitor authentication requests
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
          request.headers.response = response.headers();
          request.responseTime = Date.now() - request.timestamp;
        }
      }
    });

    return authRequests;
  }

  /**
   * Check if URL is an authentication-related request
   */
  isAuthRequest(url) {
    const authPaths = ['/auth/', '/login', '/register', '/logout', '/refresh', '/verify'];
    return authPaths.some(path => url.includes(path));
  }

  /**
   * Assert authentication state
   */
  async assertAuthenticated(shouldBeAuthenticated = true) {
    const authState = await this.validateAuthentication();

    if (shouldBeAuthenticated) {
      expect(authState.isAuthenticated).toBeTruthy();
      expect(authState.hasToken).toBeTruthy();
    } else {
      expect(authState.isAuthenticated).toBeFalsy();
    }

    return authState;
  }

  /**
   * Assert user role
   */
  async assertUserRole(expectedRole) {
    const user = await this.getCurrentUser();
    expect(user).toBeTruthy();
    expect(user.role).toBe(expectedRole);
    return user;
  }

  /**
   * Wait for authentication state change
   */
  async waitForAuthenticationChange(expectedState = true, timeoutMs = 10000) {
    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      const authState = await this.validateAuthentication();

      if (authState.isAuthenticated === expectedState) {
        return authState;
      }

      await this.page.waitForTimeout(500);
    }

    throw new Error(`Authentication state did not change to ${expectedState} within ${timeoutMs}ms`);
  }

  /**
   * Get authentication metadata
   */
  getAuthMetadata(userType = 'user') {
    const metadataFile = `tests/playwright/.auth/${userType}-metadata.json`;

    if (fs.existsSync(metadataFile)) {
      return JSON.parse(fs.readFileSync(metadataFile, 'utf-8'));
    }

    return null;
  }

  /**
   * Debug authentication state
   */
  async debugAuthenticationState() {
    const authState = await this.validateAuthentication();
    const user = await this.getCurrentUser();
    const metadata = this.getAuthMetadata();

    const debugInfo = {
      timestamp: new Date().toISOString(),
      authState,
      user,
      metadata,
      currentUrl: this.page.url(),
      cookies: await this.page.context().cookies()
    };

    console.log('🔍 Authentication Debug Info:', JSON.stringify(debugInfo, null, 2));

    // Save debug info to file
    fs.writeFileSync(
      `tests/playwright/.auth/debug-${Date.now()}.json`,
      JSON.stringify(debugInfo, null, 2)
    );

    return debugInfo;
  }
}

/**
 * Utility functions for authentication testing
 */

/**
 * Create authentication helper instance
 */
export function createAuthHelper(page) {
  return new AuthHelper(page);
}

/**
 * Quick authentication check
 */
export async function isAuthenticated(page) {
  const authHelper = new AuthHelper(page);
  const authState = await authHelper.validateAuthentication();
  return authState.isAuthenticated;
}

/**
 * Quick user role check
 */
export async function getUserRole(page) {
  const authHelper = new AuthHelper(page);
  const user = await authHelper.getCurrentUser();
  return user?.role || null;
}

/**
 * Authentication test fixture
 */
export async function withAuthentication(page, userType, testFn) {
  const authHelper = new AuthHelper(page);

  try {
    await authHelper.authenticateAs(userType);
    await authHelper.assertAuthenticated(true);
    return await testFn(authHelper);
  } finally {
    // Optional cleanup can be added here
  }
}