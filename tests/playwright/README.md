# Cardinal Vote Playwright E2E Testing

Comprehensive end-to-end testing suite for the Cardinal Vote platform using Playwright.

## 🎯 Overview

This testing suite provides comprehensive E2E testing coverage including:

- **Multi-browser testing** (Chromium, Firefox, WebKit)
- **Mobile and responsive testing**
- **Material Design validation**
- **Performance monitoring**
- **Accessibility compliance**
- **Error scenario testing**

## 📁 Directory Structure

```
tests/playwright/
├── specs/                          # Test specifications organized by category
│   ├── smoke/                      # Critical path smoke tests
│   ├── core/                       # Core functionality tests
│   ├── mobile/                     # Mobile-specific tests
│   ├── advanced/                   # Advanced feature tests
│   ├── error/                      # Error handling tests
│   ├── performance/                # Performance tests
│   └── accessibility/              # Accessibility tests
├── pages/                          # Page Object Models
│   ├── landing-page.js            # Landing page interactions
│   ├── dashboard-page.js          # Dashboard page interactions
│   ├── vote-creation-page.js      # Vote creation functionality
│   ├── public-voting-page.js      # Public voting interface
│   └── base-page.js               # Base page with common functionality
├── fixtures/                      # Test data and fixtures
│   ├── data/                      # Static test data files
│   ├── sql/                       # Database initialization scripts
│   ├── uploads/                   # Test file uploads
│   └── downloads/                 # Test file downloads
├── helpers/                       # Test helper functions
│   ├── auth-helper.js            # Authentication utilities
│   ├── data-helper.js            # Test data management
│   ├── ui-helper.js              # UI interaction utilities
│   └── performance-helper.js     # Performance measurement
├── utils/                         # Utility functions
│   ├── test-utils.js             # General test utilities
│   ├── screenshot-utils.js       # Screenshot management
│   └── report-utils.js           # Reporting utilities
├── config/                       # Configuration files
│   ├── global-setup.js           # Global test setup
│   ├── global-teardown.js        # Global test cleanup
│   └── prometheus.yml            # Monitoring configuration
├── reports/                      # Test reports and artifacts
│   ├── html/                     # HTML test reports
│   ├── json/                     # JSON test results
│   └── junit/                    # JUnit XML reports
├── screenshots/                  # Test screenshots
├── videos/                      # Test videos
├── traces/                      # Playwright traces
├── logs/                        # Test execution logs
├── .auth/                       # Authentication state files
├── Dockerfile.playwright       # Playwright container definition
├── package.json                # Node.js dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Docker and Docker Compose
- Cardinal Vote application running

### Local Setup

1. **Install dependencies:**
   ```bash
   cd tests/playwright
   npm install
   npx playwright install --with-deps
   ```

2. **Run tests locally:**
   ```bash
   # Run all tests
   npm test

   # Run specific test categories
   npm run test:smoke
   npm run test:core
   npm run test:mobile

   # Run with UI mode for debugging
   npm run test:ui
   ```

### Docker Setup

1. **Start test environment:**
   ```bash
   docker-compose -f docker-compose.playwright.yml up --build
   ```

2. **Run tests in Docker:**
   ```bash
   docker-compose -f docker-compose.playwright.yml --profile test up
   ```

## 🧪 Test Categories

### Smoke Tests (`specs/smoke/`)
Critical path functionality validation:
- Landing page loads correctly
- Authentication flow works
- Basic navigation functions

### Core Tests (`specs/core/`)
Main application functionality:
- User authentication and authorization
- Vote creation workflow
- Public voting process
- Dashboard functionality

### Mobile Tests (`specs/mobile/`)
Mobile and responsive testing:
- Touch interactions
- Mobile navigation
- Responsive layout validation
- Mobile-specific features

### Advanced Tests (`specs/advanced/`)
Advanced feature validation:
- Modal interactions
- Form validation
- Material Design compliance
- Complex user workflows

### Error Tests (`specs/error/`)
Error handling and edge cases:
- Network error scenarios
- Invalid input handling
- Server error responses
- Timeout scenarios

### Performance Tests (`specs/performance/`)
Performance monitoring:
- Page load times
- API response times
- Resource usage
- Memory leaks

### Accessibility Tests (`specs/accessibility/`)
Accessibility compliance:
- WCAG guidelines
- Screen reader compatibility
- Keyboard navigation
- ARIA attributes

## 📊 Test Execution

### Test Commands

```bash
# Core test commands
npm test                    # Run all tests
npm run test:headed        # Run with browser UI
npm run test:debug         # Debug mode with Playwright Inspector
npm run test:ui            # Interactive UI mode

# Category-specific tests
npm run test:smoke         # Critical path tests
npm run test:core          # Core functionality
npm run test:mobile        # Mobile and responsive
npm run test:accessibility # Accessibility compliance
npm run test:performance   # Performance benchmarks

# Environment-specific
npm run test:ci            # CI-optimized execution
npm run test:docker        # Docker environment
npm run test:parallel      # Parallel execution
npm run test:serial        # Serial execution

# Utility commands
npm run codegen           # Generate test code
npm run show-report       # Show HTML report
npm run clean            # Clean test artifacts
```

### Browser Projects

Tests run across multiple browser configurations:

- **smoke-chromium**: Critical path in Chrome
- **core-chromium/firefox/webkit**: Core functionality across browsers
- **mobile-chrome/safari**: Mobile browser testing
- **tablet-ipad**: Tablet-specific testing
- **advanced-chromium**: Advanced features
- **performance**: Performance benchmarks
- **accessibility**: A11y compliance
- **error-scenarios**: Error handling

## 🔧 Configuration

### Environment Variables

```bash
# Test environment
BASE_URL=http://localhost:8000
TEST_ENV=development
CI=false

# Test execution
HEADLESS=true
PARALLEL_WORKERS=4
TEST_TIMEOUT=60000

# Authentication
TEST_ADMIN_EMAIL=admin.test@cardinalvote.local
TEST_ADMIN_PASSWORD=AdminTest123!
TEST_USER_EMAIL=user1.test@cardinalvote.local
TEST_USER_PASSWORD=UserTest123!

# Debugging
DEBUG_MODE=false
CAPTURE_SCREENSHOTS=on-failure
CAPTURE_VIDEO=on-failure
CAPTURE_TRACE=on-failure
```

### Playwright Configuration

Key configuration in `playwright.config.js`:

- **Multi-browser support**: Chrome, Firefox, Safari, mobile variants
- **Test categorization**: Organized by priority and functionality
- **Enhanced reporting**: HTML, JSON, JUnit, GitHub Actions
- **Performance monitoring**: Timeout and retry configurations
- **Environment adaptation**: CI vs local development

## 📈 Monitoring and Reporting

### Test Reports

- **HTML Reports**: Interactive test results with screenshots and videos
- **JSON Results**: Machine-readable test data
- **JUnit XML**: CI/CD integration format
- **GitHub Actions**: Native GitHub integration

### Performance Monitoring

- **Prometheus Integration**: Metrics collection during test runs
- **Performance Thresholds**: Automated performance validation
- **Resource Monitoring**: Memory and CPU usage tracking

### Artifacts

- **Screenshots**: Captured on test failure
- **Videos**: Full test execution recordings
- **Traces**: Detailed execution traces for debugging
- **Logs**: Structured test execution logs

## 🔒 Authentication

### Test Users

The test environment includes pre-configured test users:

```javascript
// Admin user
email: 'admin.test@cardinalvote.local'
password: 'AdminTest123!'

// Regular users
email: 'user1.test@cardinalvote.local'
password: 'UserTest123!'

email: 'user2.test@cardinalvote.local'
password: 'UserTest123!'
```

### State Persistence

- Authentication state is persisted across tests
- Session storage and cookies are managed automatically
- Mock authentication available for isolated testing

## 🐛 Debugging

### Debug Mode

```bash
# Run tests in debug mode
npm run test:debug

# Run specific test in debug mode
npx playwright test --debug path/to/test.spec.js

# Generate tests interactively
npm run codegen
```

### Screenshots and Videos

```bash
# Enable screenshots for all tests
CAPTURE_SCREENSHOTS=always npm test

# Enable video recording
CAPTURE_VIDEO=on npm test

# Enable trace collection
CAPTURE_TRACE=on npm test
```

### Logs and Traces

- Console logs are captured automatically
- Network requests are monitored
- Performance metrics are collected
- Error details are preserved

## 🚀 CI/CD Integration

### GitHub Actions

The test suite integrates with GitHub Actions for:

- **Automated test execution** on PR creation
- **Multi-environment testing** (development, staging, production)
- **Performance regression detection**
- **Test result reporting** in PR comments

### Docker Integration

- **Containerized execution** for consistent environments
- **Isolated test databases** with known test data
- **Resource-limited execution** for CI efficiency
- **Artifact collection** and archiving

## 📝 Writing Tests

### Test Structure

```javascript
import { test, expect } from '@playwright/test';
import { LandingPage } from '../pages/landing-page.js';
import { TEST_USERS } from '../fixtures/test-data.js';

test.describe('Feature Description', () => {
  test('should perform specific action', async ({ page }) => {
    const landingPage = new LandingPage(page);

    await landingPage.goto();
    await landingPage.clickSignIn();

    await expect(page).toHaveURL(/dashboard/);
  });
});
```

### Best Practices

1. **Use Page Object Models** for all page interactions
2. **Leverage test data fixtures** for consistent data
3. **Add appropriate wait strategies** for dynamic content
4. **Use descriptive test names** and organize by functionality
5. **Include appropriate assertions** for validation
6. **Handle authentication state** properly
7. **Consider responsive design** for UI tests

## 🤝 Contributing

1. Follow the existing directory structure
2. Use meaningful test names and descriptions
3. Add appropriate test categories and metadata
4. Include performance and accessibility considerations
5. Update documentation for new features
6. Ensure tests pass in all browser configurations

## 📞 Support

For issues and questions:

- Check existing test documentation
- Review test execution logs
- Use debug mode for interactive troubleshooting
- Create GitHub issues for bugs or feature requests