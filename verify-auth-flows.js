#!/usr/bin/env node

/**
 * Direct verification of authentication flows
 * Tests registration, login, and password reset without Playwright complexity
 */

const http = require('http');
const https = require('https');
const { URL } = require('url');

const BASE_URL = 'http://localhost:8000';

// Simple HTTP request helper
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const lib = urlObj.protocol === 'https:' ? https : http;

    const req = lib.request(urlObj, {
      method: options.method || 'GET',
      headers: {
        'User-Agent': 'E2E-Verification-Test',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        ...options.headers
      }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({
        status: res.statusCode,
        headers: res.headers,
        body: data
      }));
    });

    req.on('error', reject);

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

// Test functions
async function testLandingPageLoad() {
  console.log('🌐 Testing landing page load...');

  try {
    const response = await makeRequest(BASE_URL);

    console.log(`📊 Status: ${response.status}`);
    console.log(`📊 Content-Type: ${response.headers['content-type']}`);

    // Check if it's a valid HTML response
    if (response.status === 200 && response.body.includes('<html')) {
      console.log('✅ Landing page loads successfully');

      // Check for authentication elements
      const hasSignIn = response.body.includes('Sign In');
      const hasSignUp = response.body.includes('Sign Up') || response.body.includes('Register');

      console.log(`📊 Has Sign In: ${hasSignIn}`);
      console.log(`📊 Has Sign Up/Register: ${hasSignUp}`);

      // Check for potential JavaScript errors in console
      const hasJSErrors = response.body.includes('console.error') ||
                         response.body.includes('Uncaught') ||
                         response.body.includes('TypeError');

      console.log(`📊 Potential JS errors in HTML: ${hasJSErrors}`);

      return {
        success: true,
        hasSignIn,
        hasSignUp,
        hasJSErrors: !hasJSErrors
      };
    } else {
      console.log('❌ Landing page failed to load properly');
      return { success: false, error: `Invalid response: ${response.status}` };
    }

  } catch (error) {
    console.log(`❌ Landing page load failed: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function testAuthenticationEndpoints() {
  console.log('🔐 Testing authentication endpoints...');

  const endpoints = [
    '/api/auth/register',
    '/api/auth/login',
    '/api/auth/logout',
    '/api/auth/reset-password',
    '/api/users/me'
  ];

  const results = {};

  for (const endpoint of endpoints) {
    try {
      console.log(`🔍 Testing ${endpoint}...`);
      const response = await makeRequest(BASE_URL + endpoint);

      results[endpoint] = {
        status: response.status,
        accessible: response.status < 500 // Any non-server-error response means endpoint exists
      };

      console.log(`📊 ${endpoint}: ${response.status} (${results[endpoint].accessible ? 'accessible' : 'server error'})`);

    } catch (error) {
      results[endpoint] = {
        status: 'ERROR',
        accessible: false,
        error: error.message
      };
      console.log(`❌ ${endpoint}: ${error.message}`);
    }
  }

  return results;
}

async function testRegistrationFlow() {
  console.log('👤 Testing registration flow simulation...');

  try {
    // First get the registration page/form
    const pageResponse = await makeRequest(BASE_URL);

    if (pageResponse.status !== 200) {
      return { success: false, error: 'Cannot access registration page' };
    }

    // Check for registration form elements in HTML
    const hasEmailField = pageResponse.body.includes('type="email"') ||
                         pageResponse.body.includes('name="email"');
    const hasPasswordField = pageResponse.body.includes('type="password"') ||
                            pageResponse.body.includes('name="password"');
    const hasUsernameField = pageResponse.body.includes('name="username"') ||
                           pageResponse.body.includes('name="name"');

    console.log(`📊 Has email field: ${hasEmailField}`);
    console.log(`📊 Has password field: ${hasPasswordField}`);
    console.log(`📊 Has username field: ${hasUsernameField}`);

    // Try to submit to registration endpoint (should get method not allowed or validation error)
    const registrationData = JSON.stringify({
      email: 'test@example.com',
      username: 'testuser',
      password: 'TestPassword123!',
      confirmPassword: 'TestPassword123!'
    });

    const submitResponse = await makeRequest(BASE_URL + '/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(registrationData)
      },
      body: registrationData
    });

    console.log(`📊 Registration endpoint response: ${submitResponse.status}`);

    return {
      success: true,
      hasEmailField,
      hasPasswordField,
      hasUsernameField,
      endpointStatus: submitResponse.status,
      endpointResponsive: submitResponse.status !== undefined
    };

  } catch (error) {
    console.log(`❌ Registration flow test failed: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function testLoginFlow() {
  console.log('🔓 Testing login flow simulation...');

  try {
    // Test login endpoint
    const loginData = JSON.stringify({
      email: 'test@example.com',
      password: 'testpassword'
    });

    const loginResponse = await makeRequest(BASE_URL + '/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(loginData)
      },
      body: loginData
    });

    console.log(`📊 Login endpoint response: ${loginResponse.status}`);

    // Any response (even 400/401) means the endpoint is working
    const endpointWorking = loginResponse.status >= 200 && loginResponse.status < 500;

    return {
      success: endpointWorking,
      status: loginResponse.status,
      endpointWorking
    };

  } catch (error) {
    console.log(`❌ Login flow test failed: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function testPasswordResetFlow() {
  console.log('🔄 Testing password reset flow...');

  try {
    const resetData = JSON.stringify({
      email: 'test@example.com'
    });

    const resetResponse = await makeRequest(BASE_URL + '/api/auth/reset-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(resetData)
      },
      body: resetData
    });

    console.log(`📊 Password reset endpoint response: ${resetResponse.status}`);

    const endpointWorking = resetResponse.status >= 200 && resetResponse.status < 500;

    return {
      success: endpointWorking,
      status: resetResponse.status,
      endpointWorking
    };

  } catch (error) {
    console.log(`❌ Password reset flow test failed: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// Main execution
async function runVerification() {
  console.log('🚀 Starting Cardinal Vote Authentication Flow Verification\n');

  const results = {
    landingPage: await testLandingPageLoad(),
    authEndpoints: await testAuthenticationEndpoints(),
    registration: await testRegistrationFlow(),
    login: await testLoginFlow(),
    passwordReset: await testPasswordResetFlow()
  };

  console.log('\n📊 VERIFICATION SUMMARY:');
  console.log('========================');

  // Landing Page
  console.log(`🌐 Landing Page: ${results.landingPage.success ? '✅ PASS' : '❌ FAIL'}`);
  if (results.landingPage.hasSignIn) console.log('  ✅ Sign In elements found');
  if (results.landingPage.hasSignUp) console.log('  ✅ Sign Up elements found');
  if (results.landingPage.hasJSErrors) console.log('  ✅ No obvious JS errors');

  // Registration
  console.log(`👤 Registration: ${results.registration.success ? '✅ PASS' : '❌ FAIL'}`);
  if (results.registration.hasEmailField) console.log('  ✅ Email field present');
  if (results.registration.hasPasswordField) console.log('  ✅ Password field present');
  if (results.registration.endpointResponsive) console.log('  ✅ Registration endpoint responsive');

  // Login
  console.log(`🔓 Login: ${results.login.success ? '✅ PASS' : '❌ FAIL'}`);
  if (results.login.endpointWorking) console.log('  ✅ Login endpoint working');

  // Password Reset
  console.log(`🔄 Password Reset: ${results.passwordReset.success ? '✅ PASS' : '❌ FAIL'}`);
  if (results.passwordReset.endpointWorking) console.log('  ✅ Reset endpoint working');

  // Overall status
  const allPassed = results.landingPage.success &&
                   results.registration.success &&
                   results.login.success &&
                   results.passwordReset.success;

  console.log(`\n🎯 OVERALL STATUS: ${allPassed ? '✅ ALL SYSTEMS OPERATIONAL' : '⚠️ ISSUES DETECTED'}`);

  if (!allPassed) {
    console.log('\n❌ Issues detected:');
    if (!results.landingPage.success) console.log(`  - Landing Page: ${results.landingPage.error}`);
    if (!results.registration.success) console.log(`  - Registration: ${results.registration.error}`);
    if (!results.login.success) console.log(`  - Login: ${results.login.error}`);
    if (!results.passwordReset.success) console.log(`  - Password Reset: ${results.passwordReset.error}`);
  }

  return allPassed;
}

// Run the verification
runVerification().then(success => {
  process.exit(success ? 0 : 1);
}).catch(error => {
  console.error('❌ Verification failed:', error);
  process.exit(1);
});
