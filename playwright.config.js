import { defineConfig, devices } from '@playwright/test';

/**
 * Enhanced Playwright Configuration for Comprehensive E2E Testing
 *
 * Features:
 * - Multi-browser testing with mobile support
 * - Environment-specific configurations
 * - Test categorization and filtering
 * - Performance monitoring and reporting
 * - Accessibility testing support
 * - Enhanced error handling and retries
 * - CI/CD optimization
 *
 * @see https://playwright.dev/docs/test-configuration
 */

// Environment configuration
const isCI = !!process.env.CI;
const testEnv = process.env.TEST_ENV || 'development';
const baseURL = process.env.BASE_URL || 'http://localhost:8000';

// Test execution configuration based on environment
const getWorkerConfig = () => {
  if (isCI) {
    return { workers: 2, retries: 3 }; // More conservative in CI
  }
  return { workers: '50%', retries: 1 }; // Utilize more resources locally
};

const { workers, retries } = getWorkerConfig();

export default defineConfig({
  testDir: './tests/playwright',

  // Global test configuration
  fullyParallel: true,
  forbidOnly: isCI,
  retries,
  workers,

  // Global timeouts
  timeout: 60000, // 1 minute per test
  expect: { timeout: 10000 }, // 10 seconds for assertions

  // Enhanced reporting configuration
  reporter: [
    ['html', {
      outputFolder: 'tests/playwright/reports/html',
      open: 'never'
    }],
    ['json', {
      outputFile: 'tests/playwright/reports/results.json'
    }],
    ['junit', {
      outputFile: 'tests/playwright/reports/junit.xml'
    }],
    ['github'], // GitHub Actions integration
    ...(isCI ? [] : [['line']]), // Console output for local development
  ],

  // Output directories
  outputDir: 'tests/playwright/test-results',

  // Shared settings for all projects
  use: {
    baseURL,

    // Tracing and debugging
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    // Browser context settings
    viewport: { width: 1280, height: 720 },
    locale: 'en-US',
    timezoneId: 'America/New_York',

    // Network and performance
    actionTimeout: 15000,
    navigationTimeout: 30000,

    // Security and privacy
    ignoreHTTPSErrors: testEnv === 'development',

    // Additional context options for consistent testing
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
    },
  },

  // Test projects configuration
  projects: [
    // Authentication setup (required for most tests)
    {
      name: 'setup',
      testMatch: /.*\.setup\.js$/,
      use: { ...devices['Desktop Chrome'] },
    },

    // ========================================
    // SMOKE TESTS - Critical path validation
    // ========================================
    {
      name: 'smoke-chromium',
      testMatch: /.*smoke.*\.spec\.js$/,
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
      },
      dependencies: ['setup'],
      metadata: {
        category: 'smoke',
        priority: 'critical'
      }
    },

    // ========================================
    // CORE FLOW TESTS - Main functionality
    // ========================================
    {
      name: 'core-chromium',
      testMatch: [
        /.*authentication.*\.spec\.js$/,
        /.*vote-creation.*\.spec\.js$/,
        /.*public-voting.*\.spec\.js$/
      ],
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
      },
      dependencies: ['setup'],
      metadata: {
        category: 'core',
        priority: 'high'
      }
    },

    {
      name: 'core-firefox',
      testMatch: [
        /.*authentication.*\.spec\.js$/,
        /.*vote-creation.*\.spec\.js$/,
        /.*public-voting.*\.spec\.js$/
      ],
      use: { ...devices['Desktop Firefox'] },
      dependencies: ['setup'],
      metadata: {
        category: 'core',
        priority: 'high'
      }
    },

    {
      name: 'core-webkit',
      testMatch: [
        /.*authentication.*\.spec\.js$/,
        /.*vote-creation.*\.spec\.js$/,
        /.*public-voting.*\.spec\.js$/
      ],
      use: { ...devices['Desktop Safari'] },
      dependencies: ['setup'],
      metadata: {
        category: 'core',
        priority: 'high'
      }
    },

    // ========================================
    // RESPONSIVE AND MOBILE TESTING
    // ========================================
    {
      name: 'mobile-chrome',
      testMatch: [
        /.*responsive.*\.spec\.js$/,
        /.*mobile.*\.spec\.js$/,
        /.*touch.*\.spec\.js$/
      ],
      use: {
        ...devices['Pixel 5'],
        hasTouch: true,
        isMobile: true,
      },
      dependencies: ['setup'],
      metadata: {
        category: 'mobile',
        priority: 'medium'
      }
    },

    {
      name: 'mobile-safari',
      testMatch: [
        /.*responsive.*\.spec\.js$/,
        /.*mobile.*\.spec\.js$/,
        /.*touch.*\.spec\.js$/
      ],
      use: {
        ...devices['iPhone 12'],
        hasTouch: true,
        isMobile: true,
      },
      dependencies: ['setup'],
      metadata: {
        category: 'mobile',
        priority: 'medium'
      }
    },

    {
      name: 'tablet-ipad',
      testMatch: /.*responsive.*\.spec\.js$/,
      use: {
        ...devices['iPad Pro'],
        hasTouch: true,
      },
      dependencies: ['setup'],
      metadata: {
        category: 'tablet',
        priority: 'medium'
      }
    },

    // ========================================
    // ADVANCED SCENARIO TESTING
    // ========================================
    {
      name: 'advanced-chromium',
      testMatch: [
        /.*modal.*\.spec\.js$/,
        /.*form-validation.*\.spec\.js$/,
        /.*material-design.*\.spec\.js$/
      ],
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
      },
      dependencies: ['setup'],
      metadata: {
        category: 'advanced',
        priority: 'medium'
      }
    },

    // ========================================
    // ERROR SCENARIO AND EDGE CASE TESTING
    // ========================================
    {
      name: 'error-scenarios',
      testMatch: [
        /.*error.*\.spec\.js$/,
        /.*network.*\.spec\.js$/,
        /.*edge-case.*\.spec\.js$/
      ],
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
      },
      dependencies: ['setup'],
      metadata: {
        category: 'error',
        priority: 'medium'
      }
    },

    // ========================================
    // PERFORMANCE TESTING
    // ========================================
    {
      name: 'performance',
      testMatch: /.*performance.*\.spec\.js$/,
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
      },
      dependencies: ['setup'],
      metadata: {
        category: 'performance',
        priority: 'low'
      }
    },

    // ========================================
    // ACCESSIBILITY TESTING
    // ========================================
    {
      name: 'accessibility',
      testMatch: /.*a11y.*\.spec\.js$/,
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
      },
      dependencies: ['setup'],
      metadata: {
        category: 'accessibility',
        priority: 'medium'
      }
    },

    // ========================================
    // LEGACY SUPPORT (No-setup tests)
    // ========================================
    {
      name: 'legacy-adapted',
      testMatch: /.*(?:adapted|sprint[0-9]+).*\.spec\.js$/,
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
      },
      // No dependencies - runs without authentication setup
      metadata: {
        category: 'legacy',
        priority: 'low'
      }
    },

    // ========================================
    // HIGH-RESOLUTION TESTING
    // ========================================
    {
      name: 'high-res-desktop',
      testMatch: /.*ui.*\.spec\.js$/,
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        deviceScaleFactor: 2,
      },
      dependencies: ['setup'],
      metadata: {
        category: 'ui',
        priority: 'low'
      }
    },
  ],

  // Web server configuration with environment support
  webServer: {
    command: testEnv === 'docker'
      ? 'docker-compose up --build cardinal-vote'
      : 'echo "Using existing server at ' + baseURL + '"',
    port: new URL(baseURL).port || 8000,
    reuseExistingServer: !isCI,
    timeout: 120000, // 2 minutes for server startup
    env: {
      NODE_ENV: testEnv,
      PORT: new URL(baseURL).port || '8000',
    },
  },

  // Global setup and teardown
  globalSetup: require.resolve('./tests/playwright/config/global-setup.js'),
  globalTeardown: require.resolve('./tests/playwright/config/global-teardown.js'),
});
