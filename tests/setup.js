/**
 * Jest setup file for Cardinal Vote Platform frontend tests
 * Configures testing environment and global utilities
 */

require('@testing-library/jest-dom');

// Mock fetch API for authentication tests
global.fetch = jest.fn();

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

// Mock console methods to avoid noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

// Create simplified handlers for testing
const API_BASE = '/api/auth';

// Mock helper functions
global.showToast = jest.fn();
global.closeModal = jest.fn();
global.setButtonLoading = jest.fn();

// Form submission handlers (simplified versions from landing.js)
async function handleLogin(e) {
  e.preventDefault();

  const form = e.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const email = form.querySelector('#loginEmail').value;
  const password = form.querySelector('#loginPassword').value;

  setButtonLoading(submitBtn, true);

  try {
    const response = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        password
      })
    });

    const data = await response.json();

    if (response.ok) {
      localStorage.setItem('authToken', data.access_token);
      showToast('success', 'Welcome back!', 'You have been signed in successfully.');
      closeModal('loginModal');
    } else {
      showToast('error', 'Sign In Failed', data.message || 'Please check your credentials and try again.');
    }
  } catch (error) {
    console.error('Login error:', error);
    showToast('error', 'Connection Error', 'Unable to connect to the server. Please try again.');
  } finally {
    setButtonLoading(submitBtn, false);
  }
}

async function handleRegister(e) {
  e.preventDefault();

  const form = e.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const firstName = form.querySelector('#registerFirstName').value;
  const lastName = form.querySelector('#registerLastName').value;
  const email = form.querySelector('#registerEmail').value;
  const password = form.querySelector('#registerPassword').value;

  if (password.length < 8) {
    showToast('error', 'Invalid Password', 'Password must be at least 8 characters long.');
    return;
  }

  setButtonLoading(submitBtn, true);

  try {
    const response = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        email,
        password
      })
    });

    const data = await response.json();

    if (response.ok) {
      localStorage.setItem('authToken', data.access_token);
      showToast('success', 'Account Created!', 'Welcome to the platform. You can now create your first vote.');
      closeModal('registerModal');
    } else {
      showToast('error', 'Registration Failed', data.message || 'Please check your information and try again.');
    }
  } catch (error) {
    console.error('Registration error:', error);
    showToast('error', 'Connection Error', 'Unable to connect to the server. Please try again.');
  } finally {
    setButtonLoading(submitBtn, false);
  }
}

// Set up DOM for tests
document.body.innerHTML = `
  <div id="loginModal" class="modal" role="dialog" aria-labelledby="login-modal-title" aria-hidden="true">
    <div class="modal-backdrop"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h3 id="login-modal-title">Welcome Back</h3>
        <button class="modal-close" aria-label="Close login form">×</button>
      </div>
      <div class="modal-body">
        <form id="loginForm" class="auth-form">
          <div class="form-group">
            <label for="loginEmail" class="form-label">Email Address</label>
            <input type="email" id="loginEmail" class="form-input" required>
          </div>
          <div class="form-group">
            <label for="loginPassword" class="form-label">Password</label>
            <input type="password" id="loginPassword" class="form-input" required>
          </div>
          <div class="form-actions">
            <button type="submit" class="btn-form-primary">
              Sign In
              <div class="btn-loading" aria-hidden="true"></div>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <div id="registerModal" class="modal" role="dialog" aria-labelledby="register-modal-title" aria-hidden="true">
    <div class="modal-backdrop"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h3 id="register-modal-title">Create Your Account</h3>
        <button class="modal-close" aria-label="Close registration form">×</button>
      </div>
      <div class="modal-body">
        <form id="registerForm" class="auth-form">
          <div class="form-row">
            <div class="form-group">
              <label for="registerFirstName" class="form-label">First Name</label>
              <input type="text" id="registerFirstName" class="form-input" required>
            </div>
            <div class="form-group">
              <label for="registerLastName" class="form-label">Last Name</label>
              <input type="text" id="registerLastName" class="form-input" required>
            </div>
          </div>
          <div class="form-group">
            <label for="registerEmail" class="form-label">Email Address</label>
            <input type="email" id="registerEmail" class="form-input" required>
          </div>
          <div class="form-group">
            <label for="registerPassword" class="form-label">Password</label>
            <input type="password" id="registerPassword" class="form-input" required>
          </div>
          <div class="form-actions">
            <button type="submit" class="btn-form-primary">
              Create Account
              <div class="btn-loading" aria-hidden="true"></div>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <div id="successToast" class="toast success" role="alert" aria-live="polite">
    <div class="toast-icon" aria-hidden="true">✅</div>
    <div class="toast-content">
      <div class="toast-title">Success!</div>
      <div class="toast-message"></div>
    </div>
    <button class="toast-close" aria-label="Close notification">×</button>
  </div>

  <div id="errorToast" class="toast error" role="alert" aria-live="assertive">
    <div class="toast-icon" aria-hidden="true">❌</div>
    <div class="toast-content">
      <div class="toast-title">Error</div>
      <div class="toast-message"></div>
    </div>
    <button class="toast-close" aria-label="Close error">×</button>
  </div>

  <div id="authButtons">
    <button class="btn-text" onclick="showLoginModal()">Sign In</button>
    <button class="btn-primary" onclick="showRegisterModal()">Get Started</button>
  </div>
`;

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
  fetch.mockReset();
  mockLocalStorage.getItem.mockReturnValue(null);

  // Reset DOM classes and attributes
  document.querySelectorAll('.modal').forEach(modal => {
    modal.classList.remove('show');
    modal.setAttribute('aria-hidden', 'true');
  });

  document.querySelectorAll('.toast').forEach(toast => {
    toast.classList.remove('show');
  });

  // Reset forms
  document.querySelectorAll('form').forEach(form => {
    form.reset();
  });

  // Attach event listeners to forms
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');

  if (loginForm) {
    // Remove any existing listeners
    loginForm.replaceWith(loginForm.cloneNode(true));
    const newLoginForm = document.getElementById('loginForm');
    newLoginForm.addEventListener('submit', handleLogin);
  }

  if (registerForm) {
    // Remove any existing listeners
    registerForm.replaceWith(registerForm.cloneNode(true));
    const newRegisterForm = document.getElementById('registerForm');
    newRegisterForm.addEventListener('submit', handleRegister);
  }
});

// Clean up after each test
afterEach(() => {
  jest.restoreAllMocks();
});
