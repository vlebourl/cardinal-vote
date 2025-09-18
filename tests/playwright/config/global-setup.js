import { chromium } from '@playwright/test';
import fs from 'fs';
import path from 'path';

/**
 * Global setup for Playwright tests
 *
 * Performs environment initialization, creates required directories,
 * validates test environment, and sets up global test state.
 */
async function globalSetup(config) {
  console.log('🚀 Starting Playwright global setup...');

  // Get environment configuration
  const isCI = !!process.env.CI;
  const testEnv = process.env.TEST_ENV || 'development';
  const baseURL = process.env.BASE_URL || config.use?.baseURL || 'http://localhost:8000';

  console.log(`📊 Environment: ${testEnv}`);
  console.log(`🌐 Base URL: ${baseURL}`);
  console.log(`🔧 CI Mode: ${isCI}`);

  // Create required directories
  const requiredDirs = [
    'tests/playwright/.auth',
    'tests/playwright/reports/html',
    'tests/playwright/reports',
    'tests/playwright/test-results',
    'tests/playwright/screenshots',
    'tests/playwright/videos',
    'tests/playwright/traces'
  ];

  for (const dir of requiredDirs) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      console.log(`📁 Created directory: ${dir}`);
    }
  }

  // Validate test environment
  try {
    console.log('🔍 Validating test environment...');

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Test connection to base URL
    const response = await page.goto(baseURL, {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    if (!response || !response.ok()) {
      throw new Error(`Failed to connect to ${baseURL}. Status: ${response?.status()}`);
    }

    console.log(`✅ Successfully connected to ${baseURL}`);

    // Check for critical page elements
    const titleElement = await page.locator('title').first();
    const title = await titleElement.textContent();
    console.log(`📄 Page title: "${title}"`);

    // Save environment validation info
    const validationInfo = {
      timestamp: new Date().toISOString(),
      environment: testEnv,
      baseURL,
      pageTitle: title,
      status: 'validated',
      userAgent: await page.evaluate(() => navigator.userAgent)
    };

    fs.writeFileSync(
      'tests/playwright/.auth/environment-validation.json',
      JSON.stringify(validationInfo, null, 2)
    );

    await browser.close();
    console.log('✅ Environment validation completed successfully');

  } catch (error) {
    console.error('❌ Environment validation failed:', error.message);

    // Save error information for debugging
    const errorInfo = {
      timestamp: new Date().toISOString(),
      environment: testEnv,
      baseURL,
      error: error.message,
      status: 'failed'
    };

    fs.writeFileSync(
      'tests/playwright/.auth/environment-validation.json',
      JSON.stringify(errorInfo, null, 2)
    );

    if (isCI) {
      throw error; // Fail CI build if environment validation fails
    } else {
      console.log('⚠️  Continuing in development mode despite validation failure');
    }
  }

  // Initialize global test state
  const globalState = {
    setupTimestamp: new Date().toISOString(),
    environment: testEnv,
    baseURL,
    isCI,
    testRunId: `test-${Date.now()}`
  };

  fs.writeFileSync(
    'tests/playwright/.auth/global-state.json',
    JSON.stringify(globalState, null, 2)
  );

  console.log('✅ Global setup completed successfully');
  return globalState;
}

export default globalSetup;
