// Test data for Cardinal Vote platform validation

export const TEST_USERS = {
  ADMIN: {
    email: 'admin.test@cardinalvote.local',
    password: 'AdminTest123!',
    role: 'admin',
    displayName: 'Admin Test User'
  },
  USER_1: {
    email: 'user1.test@cardinalvote.local',
    password: 'UserTest123!',
    role: 'user',
    displayName: 'User Test 1'
  },
  USER_2: {
    email: 'user2.test@cardinalvote.local',
    password: 'UserTest123!',
    role: 'user',
    displayName: 'User Test 2'
  },
  INVALID_USER: {
    email: 'invalid@example.com',
    password: 'WrongPassword123!',
    role: 'user',
    displayName: 'Invalid User'
  }
};

export const TEST_VOTES = {
  BASIC: {
    title: 'Basic Test Vote - Sprint 1',
    description: 'A simple test vote for validation testing',
    options: ['Option A', 'Option B']
  },
  DETAILED: {
    title: 'Detailed Test Vote - Sprint 2',
    description: 'A comprehensive test vote with multiple options for Sprint 2 validation',
    options: ['First Choice', 'Second Choice', 'Third Choice', 'Fourth Choice']
  },
  COMPLEX: {
    title: 'Complex Multi-Option Vote',
    description: 'Testing maximum option limits and dynamic form behavior',
    options: [
      'Option 1', 'Option 2', 'Option 3', 'Option 4', 'Option 5',
      'Option 6', 'Option 7', 'Option 8', 'Option 9', 'Option 10',
      'Option 11', 'Option 12', 'Option 13', 'Option 14', 'Option 15',
      'Option 16', 'Option 17', 'Option 18', 'Option 19', 'Option 20'
    ]
  },
  MINIMUM: {
    title: 'Minimum Options Vote',
    description: 'Testing minimum option requirements (2 options)',
    options: ['Yes', 'No']
  }
};

export const TEST_FORM_DATA = {
  REGISTRATION: {
    VALID: {
      email: 'newuser.test@cardinalvote.local',
      password: 'NewUser123!',
      confirmPassword: 'NewUser123!',
      firstName: 'New',
      lastName: 'User',
      agreeToTerms: true
    },
    INVALID_EMAIL: {
      email: 'invalid-email-format',
      password: 'ValidPass123!',
      confirmPassword: 'ValidPass123!'
    },
    INVALID_PASSWORD: {
      email: 'valid@example.com',
      password: '123', // Too short
      confirmPassword: '123'
    },
    MISMATCHED_PASSWORDS: {
      email: 'valid@example.com',
      password: 'ValidPass123!',
      confirmPassword: 'DifferentPass123!'
    }
  },
  LOGIN: {
    VALID: TEST_USERS.USER_1,
    EMPTY_FIELDS: {
      email: '',
      password: ''
    },
    INVALID_EMAIL: {
      email: 'nonexistent@example.com',
      password: 'SomePassword123!'
    },
    INVALID_PASSWORD: {
      email: TEST_USERS.USER_1.email,
      password: 'WrongPassword'
    }
  }
};

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    VERIFY: '/auth/verify',
    REFRESH: '/auth/refresh'
  },
  VOTES: {
    CREATE: '/api/votes',
    LIST: '/api/votes',
    GET: '/api/votes/{id}',
    UPDATE: '/api/votes/{id}',
    DELETE: '/api/votes/{id}',
    VOTE: '/api/votes/{id}/vote'
  },
  USER: {
    PROFILE: '/api/user/profile',
    DASHBOARD: '/api/user/dashboard',
    VOTES: '/api/user/votes'
  }
};

export const VALIDATION_PATTERNS = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PASSWORD: {
    MIN_LENGTH: 8,
    REQUIRES_UPPERCASE: /[A-Z]/,
    REQUIRES_LOWERCASE: /[a-z]/,
    REQUIRES_DIGIT: /\d/,
    REQUIRES_SPECIAL: /[!@#$%^&*(),.?":{}|<>]/
  },
  JWT_TOKEN: /^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$/
};

export const MATERIAL_DESIGN_ELEMENTS = {
  ICONS: [
    'admin_panel_settings',
    'rocket_launch',
    'dashboard',
    'help_outline',
    'analytics',
    'palette',
    'speed',
    'security',
    'devices',
    'share',
    'menu',
    'search',
    'more_vert'
  ],
  COLORS: {
    PRIMARY: '#1976d2',
    SECONDARY: '#dc004e',
    SURFACE: '#ffffff',
    BACKGROUND: '#fafafa'
  },
  BREAKPOINTS: {
    MOBILE: { width: 375, height: 667 },
    TABLET: { width: 768, height: 1024 },
    DESKTOP: { width: 1200, height: 800 },
    LARGE_DESKTOP: { width: 1920, height: 1080 }
  }
};

export const PERFORMANCE_THRESHOLDS = {
  PAGE_LOAD_TIME: 5000, // 5 seconds max
  API_RESPONSE_TIME: 2000, // 2 seconds max
  AUTHENTICATION_TIME: 3000, // 3 seconds max
  FORM_SUBMISSION_TIME: 5000 // 5 seconds max
};

export const ERROR_MESSAGES = {
  AUTHENTICATION: {
    INVALID_CREDENTIALS: 'Invalid email or password',
    ACCOUNT_LOCKED: 'Account is locked',
    EMAIL_NOT_VERIFIED: 'Email not verified',
    SESSION_EXPIRED: 'Session has expired'
  },
  VALIDATION: {
    REQUIRED_FIELD: 'This field is required',
    INVALID_EMAIL: 'Please enter a valid email address',
    PASSWORD_TOO_SHORT: 'Password must be at least 8 characters',
    PASSWORDS_DONT_MATCH: 'Passwords do not match'
  },
  VOTE_CREATION: {
    TITLE_REQUIRED: 'Vote title is required',
    MIN_OPTIONS: 'At least 2 options are required',
    MAX_OPTIONS: 'Maximum 20 options allowed',
    DUPLICATE_OPTIONS: 'Options must be unique'
  }
};

export const TEST_SCENARIOS = {
  SMOKE_TESTS: {
    description: 'Critical path functionality',
    tests: [
      'User can access landing page',
      'User can attempt login',
      'Dashboard loads after authentication',
      'Basic navigation works'
    ]
  },
  AUTHENTICATION_FLOW: {
    description: 'Complete authentication workflow',
    tests: [
      'Registration form validation',
      'Login form validation',
      'JWT token generation',
      'Session persistence',
      'Logout functionality'
    ]
  },
  MATERIAL_DESIGN: {
    description: 'Material Design 3 compliance',
    tests: [
      'Material icons display correctly',
      'Button styles and interactions',
      'Card layouts and shadows',
      'Responsive breakpoints',
      'Color scheme compliance'
    ]
  },
  CROSS_BROWSER: {
    description: 'Cross-browser compatibility',
    browsers: ['chromium', 'firefox', 'webkit'],
    tests: [
      'All features work in Chrome',
      'All features work in Firefox',
      'All features work in Safari',
      'Mobile responsive design'
    ]
  }
};

// Utility functions for test data
export const testDataUtils = {
  generateRandomUser() {
    const timestamp = Date.now();
    return {
      email: `testuser.${timestamp}@cardinalvote.local`,
      password: `TestPass${timestamp}!`,
      displayName: `Test User ${timestamp}`
    };
  },

  generateRandomVote() {
    const timestamp = Date.now();
    return {
      title: `Test Vote ${timestamp}`,
      description: `Generated test vote at ${new Date().toISOString()}`,
      options: ['Option A', 'Option B', `Option ${timestamp}`]
    };
  },

  validateJWTToken(token) {
    if (!token) return false;
    return VALIDATION_PATTERNS.JWT_TOKEN.test(token);
  },

  validateEmail(email) {
    return VALIDATION_PATTERNS.EMAIL.test(email);
  },

  validatePassword(password) {
    const { MIN_LENGTH, REQUIRES_UPPERCASE, REQUIRES_LOWERCASE, REQUIRES_DIGIT } = VALIDATION_PATTERNS.PASSWORD;

    return password.length >= MIN_LENGTH &&
           REQUIRES_UPPERCASE.test(password) &&
           REQUIRES_LOWERCASE.test(password) &&
           REQUIRES_DIGIT.test(password);
  }
};
