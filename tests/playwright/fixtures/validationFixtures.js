/**
 * Validation fixtures for Playwright E2E tests
 * Contains test data for validation scenarios
 */

export const VALIDATION_FIXTURES = {
  // Invalid email formats for testing
  INVALID_EMAILS: [
    'invalid',
    'invalid@',
    'invalid@domain',
    '@domain.com',
    'test@',
    '.test@domain.com',
    'test@domain.',
    'test space@domain.com',
    'test..test@domain.com'
  ],

  // Weak passwords for testing
  WEAK_PASSWORDS: [
    '123',
    'password',
    'abc',
    '12345678',
    'qwerty',
    'Password',
    'password123',
    'weakpass'
  ],

  // Existing user data for duplicate testing
  EXISTING_USER: {
    email: 'existing@example.com',
    username: 'existinguser'
  },

  // Vote title constraints
  VOTE_TITLE_MAX_LENGTH: 200,
  OPTION_TITLE_MAX_LENGTH: 100,

  // Invalid vote values (outside -2 to +2 range)
  INVALID_VOTE_VALUES: [-3, -10, 3, 5, 100, -100],

  // Invalid allocation limits for admin settings
  INVALID_ALLOCATION_LIMITS: [-1, 0, 101, 1000, -10],

  // File paths for testing file upload validation
  LARGE_FILE_PATH: '/tmp/large-test-file.jpg',
  INVALID_FILE_TYPE_PATH: '/tmp/invalid-file.exe',

  // Invalid backup file for admin restore testing
  INVALID_BACKUP_FILE: '/tmp/invalid-backup.json'
};

export const PERFORMANCE_FIXTURES = {
  THRESHOLDS: {
    NAVIGATION: {
      PAGE_LOAD: 3000, // 3 seconds
      MODAL_OPEN: 500,  // 500ms
      FORM_SUBMIT: 2000 // 2 seconds
    },

    VALIDATION: {
      FIELD_VALIDATION: 200,    // 200ms for single field
      MULTIPLE_FIELDS: 1000,    // 1 second for multiple fields
      ASYNC_MIN: 500,           // Minimum time for async validation
      ASYNC_MAX: 3000           // Maximum time for async validation
    },

    INTERACTION: {
      BUTTON_CLICK: 100,        // 100ms for button response
      INPUT_RESPONSE: 50,       // 50ms for input response
      SCROLL_RESPONSE: 16       // 16ms for smooth scrolling (60fps)
    },

    RENDERING: {
      LAYOUT_SHIFT: 0.1,        // CLS threshold
      FIRST_PAINT: 1000,        // First paint time
      LARGEST_CONTENT: 2500,    // LCP threshold
      FIRST_INPUT_DELAY: 100    // FID threshold
    }
  }
};
