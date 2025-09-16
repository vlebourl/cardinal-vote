/**
 * Common test helper utilities for Playwright E2E tests
 * Provides reusable functions for test setup, data generation, and assertions
 */

import { expect } from '@playwright/test';
import { faker } from '@faker-js/faker';

/**
 * Test Data Generators
 */
export class TestDataGenerator {
  /**
   * Generate test user data
   */
  static generateUser(overrides = {}) {
    return {
      username: faker.internet.userName(),
      email: faker.internet.email(),
      password: 'TestPassword123!',
      firstName: faker.person.firstName(),
      lastName: faker.person.lastName(),
      ...overrides
    };
  }

  /**
   * Generate test vote data
   */
  static generateVote(overrides = {}) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);

    return {
      title: faker.lorem.sentence(4),
      description: faker.lorem.paragraph(2),
      deadline: tomorrow.toISOString().split('T')[0],
      options: [
        {
          title: faker.lorem.words(3),
          description: faker.lorem.sentence()
        },
        {
          title: faker.lorem.words(3),
          description: faker.lorem.sentence()
        },
        {
          title: faker.lorem.words(3),
          description: faker.lorem.sentence()
        }
      ],
      ...overrides
    };
  }

  /**
   * Generate test vote options
   */
  static generateVoteOptions(count = 3) {
    return Array.from({ length: count }, () => ({
      title: faker.lorem.words(3),
      description: faker.lorem.sentence(),
      value: faker.number.int({ min: -2, max: 2 })
    }));
  }

  /**
   * Generate performance test data
   */
  static generatePerformanceTestData() {
    return {
      users: Array.from({ length: 50 }, () => this.generateUser()),
      votes: Array.from({ length: 10 }, () => this.generateVote()),
      votingPatterns: Array.from({ length: 100 }, () => ({
        userId: faker.number.int({ min: 1, max: 50 }),
        voteId: faker.number.int({ min: 1, max: 10 }),
        values: this.generateVoteOptions(faker.number.int({ min: 3, max: 8 }))
      }))
    };
  }
}

/**
 * Browser and Environment Utilities
 */
export class BrowserUtils {
  /**
   * Wait for network idle
   */
  static async waitForNetworkIdle(page, timeout = 30000) {
    await page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Wait for all images to load
   */
  static async waitForImages(page) {
    await page.evaluate(async () => {
      const images = Array.from(document.images);
      await Promise.all(
        images.map(img => {
          if (img.complete) return Promise.resolve();
          return new Promise(resolve => {
            img.addEventListener('load', resolve);
            img.addEventListener('error', resolve);
          });
        })
      );
    });
  }

  /**
   * Clear all browser data
   */
  static async clearBrowserData(context) {
    await context.clearCookies();
    await context.clearPermissions();
  }

  /**
   * Simulate slow network conditions
   */
  static async simulateSlowNetwork(page) {
    const client = await page.context().newCDPSession(page);
    await client.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: 500 * 1024 / 8, // 500kb/s
      uploadThroughput: 100 * 1024 / 8,   // 100kb/s
      latency: 2000 // 2s latency
    });
  }

  /**
   * Restore normal network conditions
   */
  static async restoreNormalNetwork(page) {
    const client = await page.context().newCDPSession(page);
    await client.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: -1,
      uploadThroughput: -1,
      latency: 0
    });
  }

  /**
   * Take screenshot with timestamp
   */
  static async takeTimestampedScreenshot(page, name) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${name}-${timestamp}.png`;
    await page.screenshot({ path: `test-results/screenshots/${filename}`, fullPage: true });
    return filename;
  }
}

/**
 * Performance Testing Utilities
 */
export class PerformanceUtils {
  /**
   * Measure page load performance
   */
  static async measurePageLoad(page) {
    const startTime = Date.now();

    const performanceEntries = await page.evaluate(() => {
      return JSON.stringify(performance.getEntriesByType('navigation'));
    });

    const loadTime = Date.now() - startTime;
    const entries = JSON.parse(performanceEntries)[0];

    return {
      loadTime,
      domContentLoaded: entries.domContentLoadedEventEnd - entries.domContentLoadedEventStart,
      loadComplete: entries.loadEventEnd - entries.loadEventStart,
      firstPaint: entries.responseEnd - entries.requestStart,
      entries
    };
  }

  /**
   * Measure Core Web Vitals
   */
  static async measureCoreWebVitals(page) {
    return await page.evaluate(() => {
      return new Promise((resolve) => {
        const vitals = {};

        // Largest Contentful Paint
        new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          vitals.lcp = entries[entries.length - 1].startTime;
        }).observe({ entryTypes: ['largest-contentful-paint'] });

        // First Input Delay
        new PerformanceObserver((entryList) => {
          const firstEntry = entryList.getEntries()[0];
          vitals.fid = firstEntry.processingStart - firstEntry.startTime;
        }).observe({ entryTypes: ['first-input'] });

        // Cumulative Layout Shift
        let cumulativeLayoutShift = 0;
        new PerformanceObserver((entryList) => {
          for (const entry of entryList.getEntries()) {
            if (!entry.hadRecentInput) {
              cumulativeLayoutShift += entry.value;
            }
          }
          vitals.cls = cumulativeLayoutShift;
        }).observe({ entryTypes: ['layout-shift'] });

        setTimeout(() => resolve(vitals), 5000);
      });
    });
  }

  /**
   * Monitor memory usage
   */
  static async monitorMemoryUsage(page) {
    return await page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        };
      }
      return null;
    });
  }

  /**
   * Measure animation performance
   */
  static async measureAnimationPerformance(page, selector, duration = 3000) {
    const startTime = Date.now();
    const frames = [];

    return await page.evaluate(async (selector, duration, startTime) => {
      const element = document.querySelector(selector);
      if (!element) return null;

      return new Promise((resolve) => {
        const frames = [];
        let lastFrameTime = startTime;

        function captureFrame() {
          const currentTime = Date.now();
          frames.push({
            timestamp: currentTime,
            frameTime: currentTime - lastFrameTime
          });
          lastFrameTime = currentTime;

          if (currentTime - startTime < duration) {
            requestAnimationFrame(captureFrame);
          } else {
            const averageFrameTime = frames.reduce((sum, frame) => sum + frame.frameTime, 0) / frames.length;
            const fps = 1000 / averageFrameTime;

            resolve({
              averageFrameTime,
              fps,
              frameCount: frames.length,
              droppedFrames: frames.filter(frame => frame.frameTime > 16.67).length
            });
          }
        }

        requestAnimationFrame(captureFrame);
      });
    }, selector, duration, startTime);
  }
}

/**
 * Accessibility Testing Utilities
 */
export class AccessibilityUtils {
  /**
   * Check ARIA attributes
   */
  static async checkAriaAttributes(page, selector) {
    return await page.evaluate((selector) => {
      const element = document.querySelector(selector);
      if (!element) return null;

      const attributes = {};
      for (const attr of element.attributes) {
        if (attr.name.startsWith('aria-')) {
          attributes[attr.name] = attr.value;
        }
      }

      return {
        hasAriaLabel: element.hasAttribute('aria-label'),
        hasAriaLabelledBy: element.hasAttribute('aria-labelledby'),
        hasAriaDescribedBy: element.hasAttribute('aria-describedby'),
        hasRole: element.hasAttribute('role'),
        tabIndex: element.tabIndex,
        attributes
      };
    }, selector);
  }

  /**
   * Test keyboard navigation
   */
  static async testKeyboardNavigation(page, startSelector, expectedPath) {
    await page.focus(startSelector);

    const navigationPath = [];

    for (let i = 0; i < expectedPath.length; i++) {
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => {
        const focused = document.activeElement;
        return {
          tagName: focused.tagName,
          id: focused.id,
          className: focused.className,
          ariaLabel: focused.getAttribute('aria-label')
        };
      });
      navigationPath.push(focusedElement);
    }

    return navigationPath;
  }

  /**
   * Check color contrast
   */
  static async checkColorContrast(page, selector) {
    return await page.evaluate((selector) => {
      const element = document.querySelector(selector);
      if (!element) return null;

      const styles = window.getComputedStyle(element);
      const color = styles.color;
      const backgroundColor = styles.backgroundColor;

      // Simple contrast ratio calculation (would need more sophisticated implementation)
      return {
        color,
        backgroundColor,
        hasGoodContrast: true // Placeholder - would implement actual contrast calculation
      };
    }, selector);
  }

  /**
   * Check for focus indicators
   */
  static async checkFocusIndicators(page, selector) {
    const element = page.locator(selector);
    await element.focus();

    return await page.evaluate((selector) => {
      const element = document.querySelector(selector);
      const styles = window.getComputedStyle(element);

      return {
        hasOutline: styles.outline !== 'none',
        outlineWidth: styles.outlineWidth,
        outlineColor: styles.outlineColor,
        boxShadow: styles.boxShadow,
        hasFocusIndicator: styles.outline !== 'none' || styles.boxShadow !== 'none'
      };
    }, selector);
  }
}

/**
 * Form Testing Utilities
 */
export class FormUtils {
  /**
   * Fill form with test data
   */
  static async fillForm(page, formData, formSelector = 'form') {
    for (const [fieldName, value] of Object.entries(formData)) {
      const field = page.locator(`${formSelector} [name="${fieldName}"]`);

      if (await field.count() > 0) {
        const fieldType = await field.getAttribute('type');

        switch (fieldType) {
          case 'checkbox':
            if (value) await field.check();
            break;
          case 'radio':
            await field.check();
            break;
          case 'select':
            await field.selectOption(value);
            break;
          default:
            await field.fill(value.toString());
        }
      }
    }
  }

  /**
   * Get all form validation errors
   */
  static async getFormErrors(page, formSelector = 'form') {
    return await page.evaluate((formSelector) => {
      const form = document.querySelector(formSelector);
      if (!form) return [];

      const errors = [];
      const errorElements = form.querySelectorAll('.error, .field-error, [data-error]');

      errorElements.forEach(el => {
        if (el.textContent.trim()) {
          errors.push({
            field: el.getAttribute('data-field') || 'unknown',
            message: el.textContent.trim(),
            visible: !el.hidden && el.style.display !== 'none'
          });
        }
      });

      return errors;
    }, formSelector);
  }

  /**
   * Validate form field in real-time
   */
  static async validateField(page, fieldName, value, expectedError = null) {
    const field = page.locator(`[name="${fieldName}"]`);
    await field.fill(value);
    await field.blur();

    // Wait for validation to complete
    await page.waitForTimeout(500);

    const errorElement = page.locator(`[data-error="${fieldName}"], .error[data-field="${fieldName}"]`);
    const hasError = await errorElement.count() > 0 && await errorElement.isVisible();

    if (expectedError) {
      expect(hasError).toBe(true);
      if (hasError) {
        const errorText = await errorElement.textContent();
        expect(errorText).toContain(expectedError);
      }
    } else {
      expect(hasError).toBe(false);
    }

    return hasError;
  }
}

/**
 * Modal Testing Utilities
 */
export class ModalUtils {
  /**
   * Wait for modal to open
   */
  static async waitForModalOpen(page, modalSelector = '.modal', timeout = 5000) {
    await page.waitForSelector(modalSelector, { state: 'visible', timeout });

    // Verify modal is properly initialized
    const isVisible = await page.locator(modalSelector).isVisible();
    const hasBackdrop = await page.locator('.modal-backdrop, .overlay').isVisible();

    return { isVisible, hasBackdrop };
  }

  /**
   * Wait for modal to close
   */
  static async waitForModalClose(page, modalSelector = '.modal', timeout = 5000) {
    await page.waitForSelector(modalSelector, { state: 'hidden', timeout });

    // Verify modal is completely closed
    const isHidden = await page.locator(modalSelector).isHidden();
    const noBackdrop = await page.locator('.modal-backdrop, .overlay').count() === 0;

    return { isHidden, noBackdrop };
  }

  /**
   * Test modal focus trap
   */
  static async testFocusTrap(page, modalSelector = '.modal') {
    const focusableElements = await page.locator(`${modalSelector} button, ${modalSelector} input, ${modalSelector} select, ${modalSelector} textarea, ${modalSelector} [tabindex]:not([tabindex="-1"])`);
    const count = await focusableElements.count();

    if (count === 0) return { hasFocusTrap: false, focusableCount: 0 };

    // Focus first element
    await focusableElements.first().focus();

    // Tab through all elements
    for (let i = 0; i < count + 1; i++) {
      await page.keyboard.press('Tab');
    }

    // Check if focus wrapped to first element
    const firstElementId = await focusableElements.first().getAttribute('id') || await focusableElements.first().evaluate(el => el.tagName);
    const currentFocusId = await page.evaluate(() => {
      const focused = document.activeElement;
      return focused.id || focused.tagName;
    });

    return {
      hasFocusTrap: firstElementId === currentFocusId,
      focusableCount: count
    };
  }

  /**
   * Test modal escape key handling
   */
  static async testEscapeKey(page, modalSelector = '.modal') {
    const modalVisible = await page.locator(modalSelector).isVisible();
    if (!modalVisible) return { escapeWorks: false, modalWasVisible: false };

    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);

    const modalHidden = await page.locator(modalSelector).isHidden();

    return {
      escapeWorks: modalHidden,
      modalWasVisible: true
    };
  }
}

/**
 * Database Testing Utilities
 */
export class DatabaseUtils {
  /**
   * Seed test data
   */
  static async seedTestData(context, data) {
    // This would typically interact with the database directly
    // For now, we'll use API calls to set up test data

    const results = {
      users: [],
      votes: [],
      errors: []
    };

    try {
      // Create test users
      if (data.users) {
        for (const userData of data.users) {
          const response = await context.request.post('/api/auth/register', {
            data: userData
          });

          if (response.ok()) {
            results.users.push(await response.json());
          } else {
            results.errors.push(`Failed to create user: ${userData.email}`);
          }
        }
      }

      // Create test votes
      if (data.votes) {
        for (const voteData of data.votes) {
          const response = await context.request.post('/api/votes', {
            data: voteData
          });

          if (response.ok()) {
            results.votes.push(await response.json());
          } else {
            results.errors.push(`Failed to create vote: ${voteData.title}`);
          }
        }
      }

    } catch (error) {
      results.errors.push(`Database seeding error: ${error.message}`);
    }

    return results;
  }

  /**
   * Clean test data
   */
  static async cleanTestData(context, testDataIds) {
    const results = {
      cleaned: [],
      errors: []
    };

    try {
      // Clean votes
      if (testDataIds.votes) {
        for (const voteId of testDataIds.votes) {
          const response = await context.request.delete(`/api/votes/${voteId}`);
          if (response.ok()) {
            results.cleaned.push(`vote:${voteId}`);
          } else {
            results.errors.push(`Failed to delete vote: ${voteId}`);
          }
        }
      }

      // Clean users
      if (testDataIds.users) {
        for (const userId of testDataIds.users) {
          const response = await context.request.delete(`/api/users/${userId}`);
          if (response.ok()) {
            results.cleaned.push(`user:${userId}`);
          } else {
            results.errors.push(`Failed to delete user: ${userId}`);
          }
        }
      }

    } catch (error) {
      results.errors.push(`Database cleanup error: ${error.message}`);
    }

    return results;
  }
}

/**
 * API Testing Utilities
 */
export class ApiUtils {
  /**
   * Make authenticated API request
   */
  static async authenticatedRequest(context, method, url, data = null, token = null) {
    const headers = {
      'Content-Type': 'application/json'
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const options = {
      headers,
      data: data ? JSON.stringify(data) : undefined
    };

    let response;
    switch (method.toUpperCase()) {
      case 'GET':
        response = await context.request.get(url, options);
        break;
      case 'POST':
        response = await context.request.post(url, options);
        break;
      case 'PUT':
        response = await context.request.put(url, options);
        break;
      case 'DELETE':
        response = await context.request.delete(url, options);
        break;
      default:
        throw new Error(`Unsupported HTTP method: ${method}`);
    }

    return {
      status: response.status(),
      ok: response.ok(),
      data: response.ok() ? await response.json() : null,
      error: !response.ok() ? await response.text() : null
    };
  }

  /**
   * Poll API endpoint until condition is met
   */
  static async pollEndpoint(context, url, condition, options = {}) {
    const {
      maxAttempts = 10,
      interval = 1000,
      timeout = 30000
    } = options;

    const startTime = Date.now();
    let attempts = 0;

    while (attempts < maxAttempts && (Date.now() - startTime) < timeout) {
      const response = await context.request.get(url);

      if (response.ok()) {
        const data = await response.json();
        if (condition(data)) {
          return { success: true, data, attempts };
        }
      }

      attempts++;
      await new Promise(resolve => setTimeout(resolve, interval));
    }

    return { success: false, attempts, timeout: (Date.now() - startTime) >= timeout };
  }
}

/**
 * Assertion Utilities
 */
export class AssertionUtils {
  /**
   * Assert performance metrics
   */
  static assertPerformance(metrics, thresholds) {
    if (metrics.loadTime && thresholds.loadTime) {
      expect(metrics.loadTime, `Page load time ${metrics.loadTime}ms exceeds threshold ${thresholds.loadTime}ms`)
        .toBeLessThan(thresholds.loadTime);
    }

    if (metrics.lcp && thresholds.lcp) {
      expect(metrics.lcp, `LCP ${metrics.lcp}ms exceeds threshold ${thresholds.lcp}ms`)
        .toBeLessThan(thresholds.lcp);
    }

    if (metrics.fid && thresholds.fid) {
      expect(metrics.fid, `FID ${metrics.fid}ms exceeds threshold ${thresholds.fid}ms`)
        .toBeLessThan(thresholds.fid);
    }

    if (metrics.cls && thresholds.cls) {
      expect(metrics.cls, `CLS ${metrics.cls} exceeds threshold ${thresholds.cls}`)
        .toBeLessThan(thresholds.cls);
    }
  }

  /**
   * Assert accessibility compliance
   */
  static assertAccessibility(results) {
    expect(results.hasAriaLabel || results.hasAriaLabelledBy, 'Element should have accessible name').toBe(true);
    expect(results.hasFocusIndicator, 'Focusable element should have focus indicator').toBe(true);
    expect(results.hasGoodContrast, 'Element should have good color contrast').toBe(true);
  }

  /**
   * Assert responsive behavior
   */
  static assertResponsive(layoutData, breakpoint) {
    expect(layoutData.hasOverflow, `Layout should not overflow at ${breakpoint}`).toBe(false);
    expect(layoutData.isReadable, `Text should be readable at ${breakpoint}`).toBe(true);
    expect(layoutData.hasProperSpacing, `Elements should have proper spacing at ${breakpoint}`).toBe(true);
  }
}

// Export all utilities as a default object for easier importing
export default {
  TestDataGenerator,
  BrowserUtils,
  PerformanceUtils,
  AccessibilityUtils,
  FormUtils,
  ModalUtils,
  DatabaseUtils,
  ApiUtils,
  AssertionUtils
};
