/**
 * Test Data Factory for Cardinal Vote Platform
 *
 * Provides comprehensive test data generation with:
 * - Dynamic data generation for unique test scenarios
 * - Static test data for consistent testing
 * - Data validation and sanitization
 * - Performance-optimized data sets
 * - Error scenario data generation
 */

import { faker } from '@faker-js/faker';

/**
 * User Data Factory
 */
export class UserDataFactory {
  static createUser(overrides = {}) {
    const timestamp = Date.now();

    return {
      email: `testuser.${timestamp}@cardinalvote.local`,
      password: 'TestUser123!',
      firstName: faker.person.firstName(),
      lastName: faker.person.lastName(),
      displayName: faker.person.fullName(),
      role: 'user',
      verified: true,
      active: true,
      createdAt: new Date().toISOString(),
      ...overrides
    };
  }

  static createAdmin(overrides = {}) {
    return this.createUser({
      email: `admin.${Date.now()}@cardinalvote.local`,
      password: 'AdminTest123!',
      role: 'admin',
      permissions: ['vote:create', 'vote:manage', 'user:manage', 'admin:access'],
      ...overrides
    });
  }

  static createUserBatch(count = 5, overrides = {}) {
    return Array.from({ length: count }, (_, index) =>
      this.createUser({
        email: `testuser.${Date.now()}.${index}@cardinalvote.local`,
        displayName: `Test User ${index + 1}`,
        ...overrides
      })
    );
  }

  static createInvalidUser(type = 'email') {
    const base = this.createUser();

    switch (type) {
      case 'email':
        return { ...base, email: 'invalid-email-format' };
      case 'password':
        return { ...base, password: '123' }; // Too short
      case 'missing_email':
        return { ...base, email: '' };
      case 'missing_password':
        return { ...base, password: '' };
      case 'special_chars':
        return { ...base, email: 'test+special@domain.com' };
      default:
        return { ...base, email: 'invalid-email-format' };
    }
  }
}

/**
 * Vote Data Factory
 */
export class VoteDataFactory {
  static createVote(overrides = {}) {
    const timestamp = Date.now();

    return {
      title: `Test Vote ${timestamp}`,
      description: faker.lorem.paragraph(),
      options: [
        'Option A',
        'Option B'
      ],
      type: 'single-choice',
      isPublic: true,
      allowAnonymous: true,
      startDate: new Date().toISOString(),
      endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
      createdBy: 'admin.test@cardinalvote.local',
      maxOptionsPerVoter: 1,
      requireRegistration: false,
      tags: ['test', 'automated'],
      ...overrides
    };
  }

  static createMultiChoiceVote(optionCount = 4, overrides = {}) {
    const options = Array.from({ length: optionCount }, (_, index) =>
      `Option ${String.fromCharCode(65 + index)}`
    );

    return this.createVote({
      title: `Multi-Choice Test Vote - ${optionCount} Options`,
      description: `A test vote with ${optionCount} options for multi-choice validation`,
      options,
      type: 'multi-choice',
      maxOptionsPerVoter: Math.min(3, optionCount - 1),
      ...overrides
    });
  }

  static createComplexVote(overrides = {}) {
    return this.createVote({
      title: 'Complex Test Vote with Advanced Features',
      description: faker.lorem.paragraphs(3),
      options: Array.from({ length: 20 }, (_, index) =>
        `${faker.company.name()} - Option ${index + 1}`
      ),
      type: 'ranked-choice',
      isPublic: false,
      allowAnonymous: false,
      requireRegistration: true,
      maxOptionsPerVoter: 5,
      tags: ['complex', 'test', 'ranked', 'advanced'],
      settings: {
        showResults: 'after_voting',
        allowComments: true,
        notifyOnUpdate: true,
        autoClose: true
      },
      ...overrides
    });
  }

  static createTimeBasedVote(duration = 'hours', amount = 1, overrides = {}) {
    const startDate = new Date();
    const endDate = new Date(startDate);

    switch (duration) {
      case 'minutes':
        endDate.setMinutes(endDate.getMinutes() + amount);
        break;
      case 'hours':
        endDate.setHours(endDate.getHours() + amount);
        break;
      case 'days':
        endDate.setDate(endDate.getDate() + amount);
        break;
      default:
        endDate.setHours(endDate.getHours() + amount);
    }

    return this.createVote({
      title: `Time-Limited Vote (${amount} ${duration})`,
      description: `This vote expires in ${amount} ${duration}`,
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString(),
      ...overrides
    });
  }

  static createInvalidVote(type = 'title') {
    const base = this.createVote();

    switch (type) {
      case 'title':
        return { ...base, title: '' };
      case 'options':
        return { ...base, options: [] };
      case 'single_option':
        return { ...base, options: ['Only One Option'] };
      case 'too_many_options':
        return {
          ...base,
          options: Array.from({ length: 101 }, (_, i) => `Option ${i + 1}`)
        };
      case 'past_end_date':
        return {
          ...base,
          endDate: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
        };
      default:
        return { ...base, title: '' };
    }
  }
}

/**
 * Form Data Factory
 */
export class FormDataFactory {
  static createRegistrationData(overrides = {}) {
    return {
      email: `newuser.${Date.now()}@cardinalvote.local`,
      password: 'NewUser123!',
      confirmPassword: 'NewUser123!',
      firstName: faker.person.firstName(),
      lastName: faker.person.lastName(),
      agreeToTerms: true,
      subscribeToNewsletter: false,
      ...overrides
    };
  }

  static createLoginData(userType = 'user', overrides = {}) {
    const users = {
      admin: {
        email: 'admin.test@cardinalvote.local',
        password: 'AdminTest123!'
      },
      user: {
        email: 'user1.test@cardinalvote.local',
        password: 'UserTest123!'
      },
      user2: {
        email: 'user2.test@cardinalvote.local',
        password: 'UserTest123!'
      }
    };

    return {
      ...users[userType] || users.user,
      rememberMe: false,
      ...overrides
    };
  }

  static createVoteSubmissionData(voteOptions, selections = 1, overrides = {}) {
    const selectedOptions = Array.isArray(selections)
      ? selections
      : voteOptions.slice(0, selections);

    return {
      voteId: `vote_${Date.now()}`,
      selectedOptions,
      voterEmail: `voter.${Date.now()}@cardinalvote.local`,
      isAnonymous: false,
      comments: faker.lorem.sentence(),
      submittedAt: new Date().toISOString(),
      ...overrides
    };
  }

  static createInvalidFormData(formType = 'registration', errorType = 'email') {
    switch (formType) {
      case 'registration':
        const regData = this.createRegistrationData();
        switch (errorType) {
          case 'email':
            return { ...regData, email: 'invalid-email' };
          case 'password':
            return { ...regData, password: '123' };
          case 'confirm_password':
            return { ...regData, confirmPassword: 'different' };
          case 'terms':
            return { ...regData, agreeToTerms: false };
          default:
            return { ...regData, email: 'invalid-email' };
        }

      case 'login':
        const loginData = this.createLoginData();
        switch (errorType) {
          case 'email':
            return { ...loginData, email: '' };
          case 'password':
            return { ...loginData, password: '' };
          case 'invalid_credentials':
            return { ...loginData, password: 'WrongPassword123!' };
          default:
            return { ...loginData, email: '' };
        }

      default:
        return {};
    }
  }
}

/**
 * Performance Test Data Factory
 */
export class PerformanceDataFactory {
  static createLargeDataset(size = 'medium') {
    const sizes = {
      small: { users: 10, votes: 5, submissions: 50 },
      medium: { users: 100, votes: 20, submissions: 500 },
      large: { users: 1000, votes: 100, submissions: 5000 },
      xlarge: { users: 10000, votes: 500, submissions: 50000 }
    };

    const config = sizes[size] || sizes.medium;

    return {
      users: UserDataFactory.createUserBatch(config.users),
      votes: Array.from({ length: config.votes }, () => VoteDataFactory.createVote()),
      submissions: Array.from({ length: config.submissions }, () =>
        FormDataFactory.createVoteSubmissionData(['Option A', 'Option B'])
      )
    };
  }

  static createStressTestData() {
    return {
      concurrentUsers: Array.from({ length: 50 }, () => UserDataFactory.createUser()),
      rapidVoteSubmissions: Array.from({ length: 100 }, (_, index) =>
        FormDataFactory.createVoteSubmissionData(
          ['Option A', 'Option B'],
          1,
          { voterEmail: `stress.test.${index}@cardinalvote.local` }
        )
      ),
      complexVotes: Array.from({ length: 10 }, () => VoteDataFactory.createComplexVote())
    };
  }
}

/**
 * Error Scenario Data Factory
 */
export class ErrorScenarioDataFactory {
  static createNetworkErrorScenarios() {
    return {
      timeoutScenario: {
        description: 'Request timeout simulation',
        delay: 30000, // 30 seconds
        response: null
      },
      serverErrorScenario: {
        description: '500 Internal Server Error',
        statusCode: 500,
        response: { error: 'Internal server error' }
      },
      notFoundScenario: {
        description: '404 Not Found Error',
        statusCode: 404,
        response: { error: 'Resource not found' }
      },
      unauthorizedScenario: {
        description: '401 Unauthorized Error',
        statusCode: 401,
        response: { error: 'Unauthorized access' }
      },
      rateLimitScenario: {
        description: '429 Too Many Requests',
        statusCode: 429,
        response: { error: 'Rate limit exceeded' }
      }
    };
  }

  static createValidationErrorScenarios() {
    return {
      registration: {
        invalidEmail: FormDataFactory.createInvalidFormData('registration', 'email'),
        weakPassword: FormDataFactory.createInvalidFormData('registration', 'password'),
        passwordMismatch: FormDataFactory.createInvalidFormData('registration', 'confirm_password'),
        termsNotAccepted: FormDataFactory.createInvalidFormData('registration', 'terms')
      },
      login: {
        emptyEmail: FormDataFactory.createInvalidFormData('login', 'email'),
        emptyPassword: FormDataFactory.createInvalidFormData('login', 'password'),
        invalidCredentials: FormDataFactory.createInvalidFormData('login', 'invalid_credentials')
      },
      voteCreation: {
        emptyTitle: VoteDataFactory.createInvalidVote('title'),
        noOptions: VoteDataFactory.createInvalidVote('options'),
        singleOption: VoteDataFactory.createInvalidVote('single_option'),
        tooManyOptions: VoteDataFactory.createInvalidVote('too_many_options')
      }
    };
  }
}

/**
 * Test Data Manager - Central interface for all test data
 */
export class TestDataManager {
  constructor() {
    this.cache = new Map();
    this.cleanup = [];
  }

  // User management
  createUser(type = 'user', overrides = {}) {
    switch (type) {
      case 'admin':
        return UserDataFactory.createAdmin(overrides);
      case 'batch':
        return UserDataFactory.createUserBatch(overrides.count || 5, overrides);
      case 'invalid':
        return UserDataFactory.createInvalidUser(overrides.errorType);
      default:
        return UserDataFactory.createUser(overrides);
    }
  }

  // Vote management
  createVote(type = 'basic', overrides = {}) {
    switch (type) {
      case 'multi-choice':
        return VoteDataFactory.createMultiChoiceVote(overrides.optionCount, overrides);
      case 'complex':
        return VoteDataFactory.createComplexVote(overrides);
      case 'time-limited':
        return VoteDataFactory.createTimeBasedVote(
          overrides.duration,
          overrides.amount,
          overrides
        );
      case 'invalid':
        return VoteDataFactory.createInvalidVote(overrides.errorType);
      default:
        return VoteDataFactory.createVote(overrides);
    }
  }

  // Form data management
  createFormData(type, subtype, overrides = {}) {
    switch (type) {
      case 'registration':
        return subtype === 'invalid'
          ? FormDataFactory.createInvalidFormData('registration', overrides.errorType)
          : FormDataFactory.createRegistrationData(overrides);
      case 'login':
        return subtype === 'invalid'
          ? FormDataFactory.createInvalidFormData('login', overrides.errorType)
          : FormDataFactory.createLoginData(subtype, overrides);
      case 'vote-submission':
        return FormDataFactory.createVoteSubmissionData(
          overrides.options,
          overrides.selections,
          overrides
        );
      default:
        throw new Error(`Unknown form type: ${type}`);
    }
  }

  // Performance testing data
  createPerformanceData(size = 'medium') {
    return PerformanceDataFactory.createLargeDataset(size);
  }

  createStressTestData() {
    return PerformanceDataFactory.createStressTestData();
  }

  // Error scenario data
  createErrorScenarios(type = 'network') {
    switch (type) {
      case 'network':
        return ErrorScenarioDataFactory.createNetworkErrorScenarios();
      case 'validation':
        return ErrorScenarioDataFactory.createValidationErrorScenarios();
      default:
        return {};
    }
  }

  // Caching utilities
  cache(key, data) {
    this.cache.set(key, data);
    return data;
  }

  getCached(key) {
    return this.cache.get(key);
  }

  clearCache() {
    this.cache.clear();
  }

  // Cleanup management
  addCleanup(cleanupFn) {
    this.cleanup.push(cleanupFn);
  }

  async runCleanup() {
    for (const cleanupFn of this.cleanup) {
      try {
        await cleanupFn();
      } catch (error) {
        console.error('Cleanup error:', error);
      }
    }
    this.cleanup = [];
  }
}

// Export singleton instance
export const testDataManager = new TestDataManager();
