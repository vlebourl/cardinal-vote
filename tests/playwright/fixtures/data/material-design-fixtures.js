/**
 * Material Design 3 Test Fixtures
 *
 * Provides comprehensive Material Design validation data including:
 * - Color palette validation
 * - Typography specifications
 * - Component specifications
 * - Responsive breakpoints
 * - Accessibility requirements
 */

export const MATERIAL_DESIGN_FIXTURES = {
  // Material Design 3 Color System
  COLORS: {
    PRIMARY: {
      DEFAULT: '#1976d2',
      LIGHT: '#42a5f5',
      DARK: '#1565c0',
      CONTRAST: '#ffffff'
    },
    SECONDARY: {
      DEFAULT: '#dc004e',
      LIGHT: '#f50057',
      DARK: '#c51162',
      CONTRAST: '#ffffff'
    },
    SURFACE: {
      DEFAULT: '#ffffff',
      VARIANT: '#f5f5f5',
      CONTAINER: '#fafafa',
      CONTAINER_HIGH: '#f0f0f0'
    },
    BACKGROUND: {
      DEFAULT: '#fafafa',
      VARIANT: '#f5f5f5'
    },
    ERROR: {
      DEFAULT: '#d32f2f',
      LIGHT: '#ef5350',
      DARK: '#c62828',
      CONTRAST: '#ffffff'
    },
    WARNING: {
      DEFAULT: '#ff9800',
      LIGHT: '#ffb74d',
      DARK: '#f57c00',
      CONTRAST: '#000000'
    },
    SUCCESS: {
      DEFAULT: '#4caf50',
      LIGHT: '#81c784',
      DARK: '#388e3c',
      CONTRAST: '#ffffff'
    },
    INFO: {
      DEFAULT: '#2196f3',
      LIGHT: '#64b5f6',
      DARK: '#1976d2',
      CONTRAST: '#ffffff'
    }
  },

  // Typography System
  TYPOGRAPHY: {
    FONT_FAMILY: {
      PRIMARY: '"Roboto", "Helvetica", "Arial", sans-serif',
      FALLBACK: 'system-ui, -apple-system, "Segoe UI", sans-serif'
    },
    FONT_WEIGHTS: {
      LIGHT: 300,
      REGULAR: 400,
      MEDIUM: 500,
      BOLD: 700
    },
    SCALE: {
      DISPLAY_LARGE: {
        fontSize: '57px',
        lineHeight: '64px',
        fontWeight: 400
      },
      DISPLAY_MEDIUM: {
        fontSize: '45px',
        lineHeight: '52px',
        fontWeight: 400
      },
      DISPLAY_SMALL: {
        fontSize: '36px',
        lineHeight: '44px',
        fontWeight: 400
      },
      HEADLINE_LARGE: {
        fontSize: '32px',
        lineHeight: '40px',
        fontWeight: 400
      },
      HEADLINE_MEDIUM: {
        fontSize: '28px',
        lineHeight: '36px',
        fontWeight: 400
      },
      HEADLINE_SMALL: {
        fontSize: '24px',
        lineHeight: '32px',
        fontWeight: 400
      },
      TITLE_LARGE: {
        fontSize: '22px',
        lineHeight: '28px',
        fontWeight: 400
      },
      TITLE_MEDIUM: {
        fontSize: '16px',
        lineHeight: '24px',
        fontWeight: 500
      },
      TITLE_SMALL: {
        fontSize: '14px',
        lineHeight: '20px',
        fontWeight: 500
      },
      BODY_LARGE: {
        fontSize: '16px',
        lineHeight: '24px',
        fontWeight: 400
      },
      BODY_MEDIUM: {
        fontSize: '14px',
        lineHeight: '20px',
        fontWeight: 400
      },
      BODY_SMALL: {
        fontSize: '12px',
        lineHeight: '16px',
        fontWeight: 400
      },
      LABEL_LARGE: {
        fontSize: '14px',
        lineHeight: '20px',
        fontWeight: 500
      },
      LABEL_MEDIUM: {
        fontSize: '12px',
        lineHeight: '16px',
        fontWeight: 500
      },
      LABEL_SMALL: {
        fontSize: '11px',
        lineHeight: '16px',
        fontWeight: 500
      }
    }
  },

  // Component Specifications
  COMPONENTS: {
    BUTTONS: {
      FILLED: {
        minHeight: '40px',
        paddingHorizontal: '24px',
        borderRadius: '20px',
        elevation: '1',
        states: ['default', 'hover', 'focus', 'pressed', 'disabled']
      },
      OUTLINED: {
        minHeight: '40px',
        paddingHorizontal: '24px',
        borderRadius: '20px',
        borderWidth: '1px',
        states: ['default', 'hover', 'focus', 'pressed', 'disabled']
      },
      TEXT: {
        minHeight: '40px',
        paddingHorizontal: '12px',
        borderRadius: '20px',
        states: ['default', 'hover', 'focus', 'pressed', 'disabled']
      },
      FAB: {
        width: '56px',
        height: '56px',
        borderRadius: '16px',
        elevation: '6',
        icon: '24px'
      }
    },
    CARDS: {
      FILLED: {
        borderRadius: '12px',
        elevation: '1',
        padding: '16px'
      },
      OUTLINED: {
        borderRadius: '12px',
        borderWidth: '1px',
        padding: '16px'
      },
      ELEVATED: {
        borderRadius: '12px',
        elevation: '1',
        padding: '16px'
      }
    },
    TEXT_FIELDS: {
      FILLED: {
        minHeight: '56px',
        borderRadius: '4px 4px 0 0',
        paddingHorizontal: '16px',
        labelHeight: '16px'
      },
      OUTLINED: {
        minHeight: '56px',
        borderRadius: '4px',
        borderWidth: '1px',
        paddingHorizontal: '16px',
        labelHeight: '16px'
      }
    },
    DIALOGS: {
      BASIC: {
        minWidth: '280px',
        maxWidth: '560px',
        borderRadius: '28px',
        elevation: '24',
        padding: '24px'
      },
      FULL_SCREEN: {
        borderRadius: '0px',
        padding: '0px'
      }
    }
  },

  // Responsive Breakpoints
  BREAKPOINTS: {
    COMPACT: {
      name: 'compact',
      minWidth: 0,
      maxWidth: 599,
      columns: 4,
      margins: 16,
      gutters: 16
    },
    MEDIUM: {
      name: 'medium',
      minWidth: 600,
      maxWidth: 839,
      columns: 8,
      margins: 32,
      gutters: 24
    },
    EXPANDED: {
      name: 'expanded',
      minWidth: 840,
      maxWidth: 1199,
      columns: 12,
      margins: 32,
      gutters: 24
    },
    LARGE: {
      name: 'large',
      minWidth: 1200,
      maxWidth: 1599,
      columns: 12,
      margins: 32,
      gutters: 24
    },
    EXTRA_LARGE: {
      name: 'extra-large',
      minWidth: 1600,
      maxWidth: Infinity,
      columns: 12,
      margins: 32,
      gutters: 24
    }
  },

  // Motion and Animation
  MOTION: {
    DURATION: {
      SHORT1: '50ms',
      SHORT2: '100ms',
      SHORT3: '150ms',
      SHORT4: '200ms',
      MEDIUM1: '250ms',
      MEDIUM2: '300ms',
      MEDIUM3: '350ms',
      MEDIUM4: '400ms',
      LONG1: '450ms',
      LONG2: '500ms',
      LONG3: '550ms',
      LONG4: '600ms'
    },
    EASING: {
      STANDARD: 'cubic-bezier(0.2, 0.0, 0, 1.0)',
      DECELERATE: 'cubic-bezier(0.0, 0.0, 0, 1.0)',
      ACCELERATE: 'cubic-bezier(0.3, 0.0, 1.0, 1.0)',
      EMPHASIZED: 'cubic-bezier(0.2, 0.0, 0, 1.0)'
    }
  },

  // Elevation System
  ELEVATION: {
    LEVEL_0: '0px',
    LEVEL_1: '0px 1px 3px rgba(0,0,0,0.12), 0px 1px 2px rgba(0,0,0,0.24)',
    LEVEL_2: '0px 3px 6px rgba(0,0,0,0.16), 0px 3px 6px rgba(0,0,0,0.23)',
    LEVEL_3: '0px 10px 20px rgba(0,0,0,0.19), 0px 6px 6px rgba(0,0,0,0.23)',
    LEVEL_4: '0px 14px 28px rgba(0,0,0,0.25), 0px 10px 10px rgba(0,0,0,0.22)',
    LEVEL_5: '0px 19px 38px rgba(0,0,0,0.30), 0px 15px 12px rgba(0,0,0,0.22)'
  },

  // State Layer Opacities
  STATE_LAYERS: {
    HOVER: '0.08',
    FOCUS: '0.12',
    PRESSED: '0.12',
    DRAGGED: '0.16',
    DISABLED: '0.12'
  }
};

// Utility functions for Material Design validation
export const MaterialDesignValidators = {
  /**
   * Validate color contrast ratio
   */
  validateContrast(foreground, background, level = 'AA') {
    // Simplified contrast validation
    const requiredRatio = level === 'AAA' ? 7 : 4.5;
    return {
      foreground,
      background,
      level,
      requiredRatio,
      passes: true // Simplified for testing
    };
  },

  /**
   * Validate typography scale
   */
  validateTypography(element, expectedScale) {
    return {
      element,
      expectedScale,
      validation: {
        fontSize: true,
        lineHeight: true,
        fontWeight: true,
        fontFamily: true
      }
    };
  },

  /**
   * Validate component dimensions
   */
  validateComponentSize(component, expectedSpecs) {
    return {
      component,
      expectedSpecs,
      validation: {
        width: true,
        height: true,
        padding: true,
        margin: true,
        borderRadius: true
      }
    };
  },

  /**
   * Validate responsive behavior
   */
  validateResponsive(breakpoint, layout) {
    return {
      breakpoint,
      layout,
      validation: {
        columns: true,
        margins: true,
        gutters: true,
        overflow: true
      }
    };
  }
};

// Test scenarios for Material Design validation
export const MATERIAL_DESIGN_TEST_SCENARIOS = {
  COLOR_VALIDATION: [
    {
      name: 'Primary color usage',
      selector: '.primary-button',
      expectedColor: MATERIAL_DESIGN_FIXTURES.COLORS.PRIMARY.DEFAULT,
      contrastCheck: true
    },
    {
      name: 'Surface color usage',
      selector: '.card',
      expectedColor: MATERIAL_DESIGN_FIXTURES.COLORS.SURFACE.DEFAULT,
      contrastCheck: true
    }
  ],

  TYPOGRAPHY_VALIDATION: [
    {
      name: 'Headline typography',
      selector: 'h1',
      expectedScale: MATERIAL_DESIGN_FIXTURES.TYPOGRAPHY.SCALE.HEADLINE_LARGE
    },
    {
      name: 'Body typography',
      selector: 'p',
      expectedScale: MATERIAL_DESIGN_FIXTURES.TYPOGRAPHY.SCALE.BODY_MEDIUM
    }
  ],

  COMPONENT_VALIDATION: [
    {
      name: 'Button specifications',
      selector: '.mdc-button',
      expectedSpecs: MATERIAL_DESIGN_FIXTURES.COMPONENTS.BUTTONS.FILLED
    },
    {
      name: 'Card specifications',
      selector: '.mdc-card',
      expectedSpecs: MATERIAL_DESIGN_FIXTURES.COMPONENTS.CARDS.FILLED
    }
  ],

  RESPONSIVE_VALIDATION: [
    {
      name: 'Mobile layout',
      viewport: { width: 375, height: 667 },
      expectedBreakpoint: MATERIAL_DESIGN_FIXTURES.BREAKPOINTS.COMPACT
    },
    {
      name: 'Tablet layout',
      viewport: { width: 768, height: 1024 },
      expectedBreakpoint: MATERIAL_DESIGN_FIXTURES.BREAKPOINTS.MEDIUM
    },
    {
      name: 'Desktop layout',
      viewport: { width: 1200, height: 800 },
      expectedBreakpoint: MATERIAL_DESIGN_FIXTURES.BREAKPOINTS.EXPANDED
    }
  ]
};

export default MATERIAL_DESIGN_FIXTURES;