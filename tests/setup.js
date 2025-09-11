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
});

// Clean up after each test
afterEach(() => {
  jest.restoreAllMocks();
});
