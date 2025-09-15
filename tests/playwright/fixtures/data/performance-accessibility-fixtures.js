/**
 * Performance and Accessibility Test Fixtures
 *
 * Provides comprehensive testing data for:
 * - Performance benchmarks and thresholds
 * - Accessibility compliance validation (WCAG 2.1)
 * - Load testing scenarios
 * - Performance monitoring metrics
 */

export const PERFORMANCE_FIXTURES = {
  // Performance Thresholds (in milliseconds)
  THRESHOLDS: {
    PAGE_LOAD: {
      EXCELLENT: 1000,
      GOOD: 2500,
      ACCEPTABLE: 5000,
      POOR: 10000
    },
    FIRST_CONTENTFUL_PAINT: {
      EXCELLENT: 1800,
      GOOD: 3000,
      ACCEPTABLE: 4000,
      POOR: 6000
    },
    LARGEST_CONTENTFUL_PAINT: {
      EXCELLENT: 2500,
      GOOD: 4000,
      ACCEPTABLE: 6000,
      POOR: 10000
    },
    FIRST_INPUT_DELAY: {
      EXCELLENT: 100,
      GOOD: 300,
      ACCEPTABLE: 500,
      POOR: 1000
    },
    CUMULATIVE_LAYOUT_SHIFT: {
      EXCELLENT: 0.1,
      GOOD: 0.25,
      ACCEPTABLE: 0.5,
      POOR: 1.0
    },
    API_RESPONSE: {
      AUTHENTICATION: 2000,
      VOTE_CREATION: 3000,
      VOTE_SUBMISSION: 1500,
      DATA_RETRIEVAL: 2500,
      FILE_UPLOAD: 10000
    },
    NAVIGATION: {
      PAGE_TRANSITION: 1000,
      MODAL_OPEN: 500,
      DROPDOWN_EXPAND: 300,
      FORM_VALIDATION: 200
    }
  },

  // Load Testing Scenarios
  LOAD_SCENARIOS: {
    LIGHT_LOAD: {
      concurrentUsers: 10,
      duration: '5m',
      rampUp: '1m',
      description: 'Light load for basic functionality testing'
    },
    NORMAL_LOAD: {
      concurrentUsers: 50,
      duration: '10m',
      rampUp: '2m',
      description: 'Normal expected load'
    },
    PEAK_LOAD: {
      concurrentUsers: 200,
      duration: '15m',
      rampUp: '5m',
      description: 'Peak usage load'
    },
    STRESS_LOAD: {
      concurrentUsers: 500,
      duration: '20m',
      rampUp: '5m',
      description: 'Stress testing beyond normal capacity'
    },
    SPIKE_LOAD: {
      concurrentUsers: 1000,
      duration: '5m',
      rampUp: '30s',
      description: 'Sudden traffic spike simulation'
    }
  },

  // Performance Monitoring Metrics
  METRICS: {
    CORE_WEB_VITALS: [
      'LCP', // Largest Contentful Paint
      'FID', // First Input Delay
      'CLS'  // Cumulative Layout Shift
    ],
    LOADING_METRICS: [
      'TTFB', // Time to First Byte
      'FCP',  // First Contentful Paint
      'SI',   // Speed Index
      'TTI',  // Time to Interactive
      'TBT'   // Total Blocking Time
    ],
    INTERACTIVITY_METRICS: [
      'FID', // First Input Delay
      'TBT', // Total Blocking Time
      'INP'  // Interaction to Next Paint
    ],
    VISUAL_STABILITY_METRICS: [
      'CLS', // Cumulative Layout Shift
      'VISUAL_COMPLETE',
      'LAYOUT_SHIFTS'
    ]
  },

  // Resource Monitoring
  RESOURCE_LIMITS: {
    MEMORY_USAGE: {
      WARNING: 100 * 1024 * 1024, // 100MB
      CRITICAL: 500 * 1024 * 1024  // 500MB
    },
    CPU_USAGE: {
      WARNING: 70, // 70%
      CRITICAL: 90  // 90%
    },
    NETWORK_PAYLOAD: {
      WARNING: 2 * 1024 * 1024, // 2MB
      CRITICAL: 5 * 1024 * 1024  // 5MB
    },
    REQUEST_COUNT: {
      WARNING: 50,
      CRITICAL: 100
    }
  }
};

export const ACCESSIBILITY_FIXTURES = {
  // WCAG 2.1 Compliance Levels
  WCAG_LEVELS: {
    A: 'Minimum level of accessibility',
    AA: 'Standard level for most websites',
    AAA: 'Highest level of accessibility'
  },

  // Accessibility Testing Scenarios
  TESTING_SCENARIOS: {
    KEYBOARD_NAVIGATION: {
      description: 'Test keyboard-only navigation',
      keys: ['Tab', 'Shift+Tab', 'Enter', 'Space', 'Escape', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'],
      requirements: [
        'All interactive elements must be reachable',
        'Focus order must be logical',
        'Focus indicators must be visible',
        'No keyboard traps'
      ]
    },
    SCREEN_READER: {
      description: 'Test screen reader compatibility',
      requirements: [
        'All images have alt text',
        'Headings are properly structured',
        'Form labels are associated',
        'ARIA attributes are correct',
        'Content is announced properly'
      ]
    },
    COLOR_CONTRAST: {
      description: 'Test color contrast ratios',
      minimumRatios: {
        normal: 4.5,
        large: 3.0,
        AAA_normal: 7.0,
        AAA_large: 4.5
      }
    },
    FOCUS_MANAGEMENT: {
      description: 'Test focus management',
      requirements: [
        'Focus is trapped in modals',
        'Focus returns to trigger element',
        'Skip links are provided',
        'Focus indicators are visible'
      ]
    }
  },

  // ARIA Attributes and Roles
  ARIA_ATTRIBUTES: {
    ESSENTIAL: [
      'aria-label',
      'aria-labelledby',
      'aria-describedby',
      'aria-expanded',
      'aria-hidden',
      'aria-live',
      'aria-atomic',
      'aria-relevant'
    ],
    ROLES: [
      'button',
      'link',
      'heading',
      'banner',
      'navigation',
      'main',
      'contentinfo',
      'complementary',
      'region',
      'article',
      'section',
      'dialog',
      'alertdialog',
      'alert',
      'status',
      'log',
      'marquee',
      'timer'
    ],
    STATES: [
      'aria-checked',
      'aria-disabled',
      'aria-expanded',
      'aria-hidden',
      'aria-invalid',
      'aria-pressed',
      'aria-selected'
    ]
  },

  // Color Accessibility
  COLOR_ACCESSIBILITY: {
    CONTRAST_RATIOS: {
      AA_NORMAL: 4.5,
      AA_LARGE: 3.0,
      AAA_NORMAL: 7.0,
      AAA_LARGE: 4.5
    },
    COLOR_BLIND_TYPES: [
      'protanopia', // Red-blind
      'deuteranopia', // Green-blind
      'tritanopia', // Blue-blind
      'achromatopsia' // Complete color blindness
    ],
    SAFE_COLORS: {
      HIGH_CONTRAST: [
        { foreground: '#000000', background: '#ffffff' },
        { foreground: '#ffffff', background: '#000000' },
        { foreground: '#2196f3', background: '#ffffff' },
        { foreground: '#ffffff', background: '#1976d2' }
      ]
    }
  },

  // Form Accessibility
  FORM_ACCESSIBILITY: {
    REQUIREMENTS: [
      'All form fields have labels',
      'Labels are properly associated',
      'Required fields are indicated',
      'Error messages are descriptive',
      'Instructions are clear',
      'Fieldsets group related fields'
    ],
    LABEL_TECHNIQUES: [
      'explicit-label', // <label for="id">
      'implicit-label', // <label><input></label>
      'aria-label',
      'aria-labelledby',
      'title-attribute'
    ]
  },

  // Media Accessibility
  MEDIA_ACCESSIBILITY: {
    IMAGES: {
      requirements: [
        'Decorative images have empty alt text',
        'Informative images have descriptive alt text',
        'Complex images have long descriptions',
        'Text in images is avoided'
      ]
    },
    VIDEOS: {
      requirements: [
        'Captions for all audio content',
        'Audio descriptions for visual content',
        'Transcripts available',
        'Controls are keyboard accessible'
      ]
    }
  }
};

// Performance Testing Utilities
export const PerformanceTestUtils = {
  /**
   * Generate performance test scenarios
   */
  generateLoadScenario(type = 'normal') {
    const scenario = PERFORMANCE_FIXTURES.LOAD_SCENARIOS[type.toUpperCase() + '_LOAD'];
    return {
      ...scenario,
      userActions: [
        'navigate_to_landing',
        'authenticate',
        'create_vote',
        'submit_vote',
        'view_results'
      ],
      thinkTime: type === 'stress' ? 1000 : 5000, // milliseconds between actions
      failureRate: type === 'stress' ? 0.05 : 0.01 // 5% for stress, 1% for normal
    };
  },

  /**
   * Create performance assertions
   */
  createPerformanceAssertions(metricType = 'page_load') {
    const thresholds = PERFORMANCE_FIXTURES.THRESHOLDS[metricType.toUpperCase()];
    return {
      excellent: thresholds?.EXCELLENT || 1000,
      good: thresholds?.GOOD || 2500,
      acceptable: thresholds?.ACCEPTABLE || 5000,
      poor: thresholds?.POOR || 10000
    };
  },

  /**
   * Monitor resource usage
   */
  createResourceMonitor() {
    return {
      memory: PERFORMANCE_FIXTURES.RESOURCE_LIMITS.MEMORY_USAGE,
      cpu: PERFORMANCE_FIXTURES.RESOURCE_LIMITS.CPU_USAGE,
      network: PERFORMANCE_FIXTURES.RESOURCE_LIMITS.NETWORK_PAYLOAD,
      requests: PERFORMANCE_FIXTURES.RESOURCE_LIMITS.REQUEST_COUNT
    };
  }
};

// Accessibility Testing Utilities
export const AccessibilityTestUtils = {
  /**
   * Generate accessibility test scenarios
   */
  generateA11yScenario(type = 'keyboard') {
    const scenario = ACCESSIBILITY_FIXTURES.TESTING_SCENARIOS[type.toUpperCase() + '_NAVIGATION'];
    return {
      ...scenario,
      testSteps: this.createTestSteps(type),
      assertions: this.createA11yAssertions(type)
    };
  },

  /**
   * Create test steps for accessibility testing
   */
  createTestSteps(type) {
    switch (type.toLowerCase()) {
      case 'keyboard':
        return [
          'Press Tab to navigate through interactive elements',
          'Verify focus indicators are visible',
          'Test all keyboard shortcuts',
          'Ensure no keyboard traps exist'
        ];
      case 'screen_reader':
        return [
          'Verify heading structure',
          'Check image alt text',
          'Validate ARIA attributes',
          'Test form label associations'
        ];
      case 'color_contrast':
        return [
          'Check text color contrast ratios',
          'Verify link color contrast',
          'Test focus indicator contrast',
          'Validate error message contrast'
        ];
      default:
        return ['Perform accessibility validation'];
    }
  },

  /**
   * Create accessibility assertions
   */
  createA11yAssertions(type) {
    const requirements = ACCESSIBILITY_FIXTURES.TESTING_SCENARIOS[type.toUpperCase() + '_NAVIGATION']?.requirements || [];
    return requirements.map(requirement => ({
      description: requirement,
      type: 'accessibility',
      level: 'AA'
    }));
  },

  /**
   * Validate color contrast
   */
  createContrastTest(foreground, background, level = 'AA', isLarge = false) {
    const requiredRatio = ACCESSIBILITY_FIXTURES.COLOR_ACCESSIBILITY.CONTRAST_RATIOS[
      `${level}_${isLarge ? 'LARGE' : 'NORMAL'}`
    ];

    return {
      foreground,
      background,
      level,
      isLarge,
      requiredRatio,
      testType: 'color_contrast'
    };
  }
};

// Test Data Generators
export const TestDataGenerators = {
  /**
   * Generate performance test data
   */
  generatePerformanceTestData(scenarioType = 'normal') {
    return {
      scenario: PerformanceTestUtils.generateLoadScenario(scenarioType),
      assertions: PerformanceTestUtils.createPerformanceAssertions(),
      monitoring: PerformanceTestUtils.createResourceMonitor(),
      metrics: PERFORMANCE_FIXTURES.METRICS.CORE_WEB_VITALS
    };
  },

  /**
   * Generate accessibility test data
   */
  generateAccessibilityTestData() {
    return {
      keyboardScenario: AccessibilityTestUtils.generateA11yScenario('keyboard'),
      screenReaderScenario: AccessibilityTestUtils.generateA11yScenario('screen_reader'),
      colorContrastTests: [
        AccessibilityTestUtils.createContrastTest('#000000', '#ffffff'),
        AccessibilityTestUtils.createContrastTest('#ffffff', '#1976d2'),
        AccessibilityTestUtils.createContrastTest('#2196f3', '#ffffff')
      ],
      ariaTests: ACCESSIBILITY_FIXTURES.ARIA_ATTRIBUTES.ESSENTIAL.map(attr => ({
        attribute: attr,
        required: true,
        testType: 'aria_validation'
      }))
    };
  }
};

export default {
  PERFORMANCE_FIXTURES,
  ACCESSIBILITY_FIXTURES,
  PerformanceTestUtils,
  AccessibilityTestUtils,
  TestDataGenerators
};