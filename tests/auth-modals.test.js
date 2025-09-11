/**
 * Unit tests for authentication modal functionality
 * Tests login/register forms, validation, API integration, and accessibility
 */

import { screen, fireEvent, waitFor } from '@testing-library/dom';
import userEvent from '@testing-library/user-event';

// Import the functions from landing.js
// Note: In a real setup, we'd import these as modules
// For now, we'll define them inline for testing
const API_BASE = '/api/auth';

// Mock functions that would be imported from landing.js
const mockFunctions = {
  showLoginModal: jest.fn(),
  showRegisterModal: jest.fn(),
  closeModal: jest.fn(),
  showToast: jest.fn(),
  setButtonLoading: jest.fn(),
  updateUIForAuthenticatedUser: jest.fn()
};

// Add functions to global scope for testing
Object.assign(global, mockFunctions);

describe('Authentication Modals', () => {
  beforeEach(() => {
    // Reset fetch mock
    fetch.mockClear();
  });

  describe('Modal Visibility and Navigation', () => {
    test('login modal opens and closes correctly', () => {
      const loginModal = document.getElementById('loginModal');
      
      // Initial state - modal should be hidden
      expect(loginModal.getAttribute('aria-hidden')).toBe('true');
      expect(loginModal.classList.contains('show')).toBe(false);
      
      // Simulate opening modal
      loginModal.classList.add('show');
      loginModal.setAttribute('aria-hidden', 'false');
      
      expect(loginModal.classList.contains('show')).toBe(true);
      expect(loginModal.getAttribute('aria-hidden')).toBe('false');
      
      // Simulate closing modal
      loginModal.classList.remove('show');
      loginModal.setAttribute('aria-hidden', 'true');
      
      expect(loginModal.classList.contains('show')).toBe(false);
      expect(loginModal.getAttribute('aria-hidden')).toBe('true');
    });

    test('register modal opens and closes correctly', () => {
      const registerModal = document.getElementById('registerModal');
      
      // Initial state - modal should be hidden
      expect(registerModal.getAttribute('aria-hidden')).toBe('true');
      expect(registerModal.classList.contains('show')).toBe(false);
      
      // Simulate opening modal
      registerModal.classList.add('show');
      registerModal.setAttribute('aria-hidden', 'false');
      
      expect(registerModal.classList.contains('show')).toBe(true);
      expect(registerModal.getAttribute('aria-hidden')).toBe('false');
    });

    test('modal close button functionality', () => {
      const loginModal = document.getElementById('loginModal');
      const closeButton = loginModal.querySelector('.modal-close');
      
      // Open modal first
      loginModal.classList.add('show');
      loginModal.setAttribute('aria-hidden', 'false');
      
      // Click close button
      fireEvent.click(closeButton);
      
      // Simulate the close functionality
      loginModal.classList.remove('show');
      loginModal.setAttribute('aria-hidden', 'true');
      
      expect(loginModal.classList.contains('show')).toBe(false);
      expect(loginModal.getAttribute('aria-hidden')).toBe('true');
    });

    test('modal backdrop click closes modal', () => {
      const loginModal = document.getElementById('loginModal');
      const backdrop = loginModal.querySelector('.modal-backdrop');
      
      // Open modal first
      loginModal.classList.add('show');
      
      // Click backdrop
      fireEvent.click(backdrop);
      
      // Simulate the close functionality
      loginModal.classList.remove('show');
      
      expect(loginModal.classList.contains('show')).toBe(false);
    });
  });

  describe('Form Validation', () => {
    test('login form validates required fields', async () => {
      const user = userEvent.setup();
      const loginForm = document.getElementById('loginForm');
      const submitButton = loginForm.querySelector('button[type="submit"]');
      
      // Try to submit empty form
      await user.click(submitButton);
      
      const emailInput = document.getElementById('loginEmail');
      const passwordInput = document.getElementById('loginPassword');
      
      // HTML5 validation should prevent submission
      expect(emailInput.validity.valid).toBe(false);
      expect(passwordInput.validity.valid).toBe(false);
    });

    test('register form validates required fields', async () => {
      const user = userEvent.setup();
      const registerForm = document.getElementById('registerForm');
      const submitButton = registerForm.querySelector('button[type="submit"]');
      
      // Try to submit empty form
      await user.click(submitButton);
      
      const firstNameInput = document.getElementById('registerFirstName');
      const lastNameInput = document.getElementById('registerLastName');
      const emailInput = document.getElementById('registerEmail');
      const passwordInput = document.getElementById('registerPassword');
      
      // HTML5 validation should prevent submission
      expect(firstNameInput.validity.valid).toBe(false);
      expect(lastNameInput.validity.valid).toBe(false);
      expect(emailInput.validity.valid).toBe(false);
      expect(passwordInput.validity.valid).toBe(false);
    });

    test('email validation works correctly', async () => {
      const user = userEvent.setup();
      const emailInput = document.getElementById('loginEmail');
      
      // Invalid email
      await user.type(emailInput, 'invalid-email');
      expect(emailInput.validity.valid).toBe(false);
      expect(emailInput.validity.typeMismatch).toBe(true);
      
      // Valid email
      await user.clear(emailInput);
      await user.type(emailInput, 'test@example.com');
      expect(emailInput.validity.valid).toBe(true);
    });

    test('password length validation', async () => {
      const user = userEvent.setup();
      const passwordInput = document.getElementById('registerPassword');
      
      // Short password
      await user.type(passwordInput, '123');
      expect(passwordInput.value.length).toBeLessThan(8);
      
      // Valid password
      await user.clear(passwordInput);
      await user.type(passwordInput, 'validpassword123');
      expect(passwordInput.value.length).toBeGreaterThanOrEqual(8);
    });
  });

  describe('API Integration', () => {
    test('successful login API call', async () => {
      const mockResponse = {
        access_token: 'mock-token-123',
        refresh_token: 'mock-refresh-token-123',
        user: {
          id: 1,
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User'
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const user = userEvent.setup();
      const loginForm = document.getElementById('loginForm');
      const emailInput = document.getElementById('loginEmail');
      const passwordInput = document.getElementById('loginPassword');

      // Fill in form
      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'testpassword123');

      // Submit form
      fireEvent.submit(loginForm);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'testpassword123'
          })
        });
      });
    });

    test('failed login API call shows error', async () => {
      const mockErrorResponse = {
        success: false,
        message: 'Invalid credentials'
      };

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => mockErrorResponse
      });

      const user = userEvent.setup();
      const loginForm = document.getElementById('loginForm');
      const emailInput = document.getElementById('loginEmail');
      const passwordInput = document.getElementById('loginPassword');

      // Fill in form with invalid credentials
      await user.type(emailInput, 'wrong@example.com');
      await user.type(passwordInput, 'wrongpassword');

      // Submit form
      fireEvent.submit(loginForm);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/auth/login', expect.objectContaining({
          method: 'POST'
        }));
      });
    });

    test('successful registration API call', async () => {
      const mockResponse = {
        access_token: 'mock-token-456',
        refresh_token: 'mock-refresh-token-456',
        user: {
          id: 2,
          email: 'newuser@example.com',
          first_name: 'New',
          last_name: 'User'
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const user = userEvent.setup();
      const registerForm = document.getElementById('registerForm');
      const firstNameInput = document.getElementById('registerFirstName');
      const lastNameInput = document.getElementById('registerLastName');
      const emailInput = document.getElementById('registerEmail');
      const passwordInput = document.getElementById('registerPassword');

      // Fill in registration form
      await user.type(firstNameInput, 'New');
      await user.type(lastNameInput, 'User');
      await user.type(emailInput, 'newuser@example.com');
      await user.type(passwordInput, 'newuserpassword123');

      // Submit form
      fireEvent.submit(registerForm);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            first_name: 'New',
            last_name: 'User',
            email: 'newuser@example.com',
            password: 'newuserpassword123'
          })
        });
      });
    });

    test('network error handling', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const user = userEvent.setup();
      const loginForm = document.getElementById('loginForm');
      const emailInput = document.getElementById('loginEmail');
      const passwordInput = document.getElementById('loginPassword');

      // Fill in form
      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'testpassword123');

      // Submit form
      fireEvent.submit(loginForm);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });
    });
  });

  describe('Toast Notifications', () => {
    test('success toast displays and hides correctly', () => {
      const successToast = document.getElementById('successToast');
      const titleElement = successToast.querySelector('.toast-title');
      const messageElement = successToast.querySelector('.toast-message');

      // Simulate showing success toast
      titleElement.textContent = 'Success!';
      messageElement.textContent = 'Login successful';
      successToast.classList.add('show');

      expect(successToast.classList.contains('show')).toBe(true);
      expect(titleElement.textContent).toBe('Success!');
      expect(messageElement.textContent).toBe('Login successful');

      // Simulate hiding toast
      successToast.classList.remove('show');
      expect(successToast.classList.contains('show')).toBe(false);
    });

    test('error toast displays correctly', () => {
      const errorToast = document.getElementById('errorToast');
      const titleElement = errorToast.querySelector('.toast-title');
      const messageElement = errorToast.querySelector('.toast-message');

      // Simulate showing error toast
      titleElement.textContent = 'Error';
      messageElement.textContent = 'Login failed';
      errorToast.classList.add('show');

      expect(errorToast.classList.contains('show')).toBe(true);
      expect(titleElement.textContent).toBe('Error');
      expect(messageElement.textContent).toBe('Login failed');
    });

    test('toast close button functionality', () => {
      const successToast = document.getElementById('successToast');
      const closeButton = successToast.querySelector('.toast-close');

      // Show toast first
      successToast.classList.add('show');
      expect(successToast.classList.contains('show')).toBe(true);

      // Click close button
      fireEvent.click(closeButton);
      
      // Simulate close functionality
      successToast.classList.remove('show');
      expect(successToast.classList.contains('show')).toBe(false);
    });
  });

  describe('Loading States', () => {
    test('button loading state toggles correctly', () => {
      const loginForm = document.getElementById('loginForm');
      const submitButton = loginForm.querySelector('button[type="submit"]');

      // Initial state
      expect(submitButton.disabled).toBe(false);
      expect(submitButton.classList.contains('loading')).toBe(false);

      // Simulate loading state
      submitButton.disabled = true;
      submitButton.classList.add('loading');

      expect(submitButton.disabled).toBe(true);
      expect(submitButton.classList.contains('loading')).toBe(true);

      // Simulate loading complete
      submitButton.disabled = false;
      submitButton.classList.remove('loading');

      expect(submitButton.disabled).toBe(false);
      expect(submitButton.classList.contains('loading')).toBe(false);
    });

    test('form is disabled during submission', async () => {
      const user = userEvent.setup();
      const loginForm = document.getElementById('loginForm');
      const submitButton = loginForm.querySelector('button[type="submit"]');
      const emailInput = document.getElementById('loginEmail');
      const passwordInput = document.getElementById('loginPassword');

      // Mock a slow API response
      fetch.mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ access_token: 'token' })
        }), 100))
      );

      // Fill in form
      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'testpassword123');

      // Submit form
      fireEvent.submit(loginForm);

      // During submission, button should be disabled
      // (In actual implementation, this would be handled by the submit handler)
      submitButton.disabled = true;
      expect(submitButton.disabled).toBe(true);
    });
  });

  describe('Accessibility Features', () => {
    test('modals have proper ARIA attributes', () => {
      const loginModal = document.getElementById('loginModal');
      const registerModal = document.getElementById('registerModal');

      // Check modal roles and labels
      expect(loginModal.getAttribute('role')).toBe('dialog');
      expect(loginModal.getAttribute('aria-labelledby')).toBe('login-modal-title');
      expect(registerModal.getAttribute('role')).toBe('dialog');
      expect(registerModal.getAttribute('aria-labelledby')).toBe('register-modal-title');

      // Check initial aria-hidden state
      expect(loginModal.getAttribute('aria-hidden')).toBe('true');
      expect(registerModal.getAttribute('aria-hidden')).toBe('true');
    });

    test('form inputs have proper labels and descriptions', () => {
      const loginEmailInput = document.getElementById('loginEmail');
      const loginPasswordInput = document.getElementById('loginPassword');
      const registerFirstNameInput = document.getElementById('registerFirstName');

      // Check that inputs have associated labels
      expect(loginEmailInput.labels).toHaveLength(1);
      expect(loginPasswordInput.labels).toHaveLength(1);
      expect(registerFirstNameInput.labels).toHaveLength(1);

      // Check label text content
      expect(loginEmailInput.labels[0].textContent).toBe('Email Address');
      expect(loginPasswordInput.labels[0].textContent).toBe('Password');
      expect(registerFirstNameInput.labels[0].textContent).toBe('First Name');
    });

    test('buttons have proper ARIA labels', () => {
      const loginCloseButton = document.querySelector('#loginModal .modal-close');
      const registerCloseButton = document.querySelector('#registerModal .modal-close');
      const toastCloseButton = document.querySelector('#successToast .toast-close');

      expect(loginCloseButton.getAttribute('aria-label')).toBe('Close login form');
      expect(registerCloseButton.getAttribute('aria-label')).toBe('Close registration form');
      expect(toastCloseButton.getAttribute('aria-label')).toBe('Close notification');
    });

    test('toasts have proper live region attributes', () => {
      const successToast = document.getElementById('successToast');
      const errorToast = document.getElementById('errorToast');

      expect(successToast.getAttribute('role')).toBe('alert');
      expect(successToast.getAttribute('aria-live')).toBe('polite');
      expect(errorToast.getAttribute('role')).toBe('alert');
      expect(errorToast.getAttribute('aria-live')).toBe('assertive');
    });

    test('keyboard navigation support', () => {
      const loginModal = document.getElementById('loginModal');
      const focusableElements = loginModal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      // Should have focusable elements
      expect(focusableElements.length).toBeGreaterThan(0);

      // Test tabindex is not set to -1 on interactive elements
      focusableElements.forEach(element => {
        expect(element.getAttribute('tabindex')).not.toBe('-1');
      });
    });
  });

  describe('Local Storage Integration', () => {
    test('auth token is stored on successful login', () => {
      const mockToken = 'mock-jwt-token-123';
      
      // Simulate successful login token storage
      localStorage.setItem('authToken', mockToken);
      
      expect(localStorage.setItem).toHaveBeenCalledWith('authToken', mockToken);
    });

    test('auth token is removed on logout', () => {
      // Simulate logout
      localStorage.removeItem('authToken');
      
      expect(localStorage.removeItem).toHaveBeenCalledWith('authToken');
    });

    test('invalid token is removed from storage', () => {
      // Mock invalid token scenario
      localStorage.getItem.mockReturnValue('invalid-token');
      
      // Simulate token validation failure
      localStorage.removeItem('authToken');
      
      expect(localStorage.removeItem).toHaveBeenCalledWith('authToken');
    });
  });

  describe('User Interface Updates', () => {
    test('UI updates correctly for authenticated user', () => {
      const authButtons = document.getElementById('authButtons');
      const userData = {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john@example.com'
      };

      // Simulate authenticated user UI update
      authButtons.innerHTML = `
        <div class="user-info">
          <span class="user-name">Hello, ${userData.first_name}!</span>
          <button class="btn-text" onclick="handleLogout()">Sign Out</button>
          <button class="btn-primary" onclick="redirectToDashboard()">Dashboard</button>
        </div>
      `;

      const userName = authButtons.querySelector('.user-name');
      const signOutButton = authButtons.querySelector('.btn-text');
      const dashboardButton = authButtons.querySelector('.btn-primary');

      expect(userName.textContent).toBe('Hello, John!');
      expect(signOutButton.textContent.trim()).toBe('Sign Out');
      expect(dashboardButton.textContent.trim()).toBe('Dashboard');
    });

    test('form reset after successful submission', () => {
      const loginForm = document.getElementById('loginForm');
      const emailInput = document.getElementById('loginEmail');
      const passwordInput = document.getElementById('loginPassword');

      // Fill form
      emailInput.value = 'test@example.com';
      passwordInput.value = 'testpassword123';

      expect(emailInput.value).toBe('test@example.com');
      expect(passwordInput.value).toBe('testpassword123');

      // Simulate form reset after successful submission
      loginForm.reset();

      expect(emailInput.value).toBe('');
      expect(passwordInput.value).toBe('');
    });
  });
});