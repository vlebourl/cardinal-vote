import { expect } from '@playwright/test';
import { MATERIAL_DESIGN_FIXTURES } from '../fixtures/data/material-design-fixtures.js';
import { PERFORMANCE_FIXTURES } from '../fixtures/data/performance-accessibility-fixtures.js';

/**
 * Base Page Object Model
 *
 * Provides common functionality for all page objects including:
 * - Navigation and loading utilities
 * - Material Design validation
 * - Performance monitoring
 * - Accessibility testing
 * - Error handling and debugging
 * - Responsive design validation
 */
export class BasePage {
  constructor(page) {
    this.page = page;
    this.baseURL = process.env.BASE_URL || 'http://localhost:8000';
    this.defaultTimeout = 10000;
    this.retryOptions = { timeout: this.defaultTimeout };
  }

  /**
   * Navigation Methods
   */
  async goto(path = '/') {
    const url = path.startsWith('http') ? path : `${this.baseURL}${path}`;
    const startTime = Date.now();

    await this.page.goto(url, { waitUntil: 'networkidle' });

    const loadTime = Date.now() - startTime;

    // Log performance warning if page load is slow
    if (loadTime > PERFORMANCE_FIXTURES.THRESHOLDS.PAGE_LOAD.ACCEPTABLE) {
      console.warn(`⚠️  Slow page load: ${loadTime}ms for ${url}`);
    }

    return loadTime;
  }

  async waitForLoadState(state = 'networkidle') {
    await this.page.waitForLoadState(state);
  }

  async reload(options = {}) {
    return await this.page.reload({ waitUntil: 'networkidle', ...options });
  }

  /**
   * Element Interaction Methods
   */
  async clickElement(selector, options = {}) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', timeout: this.defaultTimeout });
    await element.click(options);
  }

  async fillField(selector, value, options = {}) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', timeout: this.defaultTimeout });
    await element.fill(value, options);
  }

  async selectOption(selector, value, options = {}) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', timeout: this.defaultTimeout });
    await element.selectOption(value, options);
  }

  async uploadFile(selector, filePath) {
    const element = this.page.locator(selector);
    await element.setInputFiles(filePath);
  }

  /**
   * Element State Checking
   */
  async isElementVisible(selector, timeout = 5000) {
    try {
      await this.page.locator(selector).waitFor({ state: 'visible', timeout });
      return true;
    } catch {
      return false;
    }
  }

  async isElementEnabled(selector) {
    const element = this.page.locator(selector);
    return await element.isEnabled();
  }

  async isElementChecked(selector) {
    const element = this.page.locator(selector);
    return await element.isChecked();
  }

  async getElementText(selector) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', timeout: this.defaultTimeout });
    return await element.textContent();
  }

  async getElementValue(selector) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', timeout: this.defaultTimeout });
    return await element.inputValue();
  }

  async getElementAttribute(selector, attribute) {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible', timeout: this.defaultTimeout });
    return await element.getAttribute(attribute);
  }

  /**
   * Waiting Methods
   */
  async waitForElement(selector, state = 'visible', timeout = this.defaultTimeout) {
    await this.page.locator(selector).waitFor({ state, timeout });
  }

  async waitForText(text, timeout = this.defaultTimeout) {
    await this.page.waitForSelector(`text=${text}`, { timeout });
  }

  async waitForURL(pattern, timeout = this.defaultTimeout) {
    await this.page.waitForURL(pattern, { timeout });
  }

  async waitForResponse(urlPattern, timeout = this.defaultTimeout) {
    return await this.page.waitForResponse(urlPattern, { timeout });
  }

  async waitForRequest(urlPattern, timeout = this.defaultTimeout) {
    return await this.page.waitForRequest(urlPattern, { timeout });
  }

  /**
   * Material Design Validation
   */
  async validateMaterialDesign() {
    const validation = {
      colors: await this.validateMaterialColors(),
      typography: await this.validateMaterialTypography(),
      components: await this.validateMaterialComponents(),
      icons: await this.validateMaterialIcons()
    };

    return validation;
  }

  async validateMaterialColors() {
    const colorTests = [];

    // Check primary color usage
    const primaryElements = await this.page.locator('[class*="primary"], .mdc-button--raised').all();
    for (const element of primaryElements) {
      const backgroundColor = await element.evaluate(el =>
        window.getComputedStyle(el).backgroundColor
      );
      colorTests.push({
        element: await element.getAttribute('class'),
        backgroundColor,
        isPrimary: true
      });
    }

    return {
      primaryColorUsage: colorTests.length > 0,
      colorTests
    };
  }

  async validateMaterialTypography() {
    const typographyTests = [];

    // Check common typography elements
    const typographySelectors = ['h1', 'h2', 'h3', 'p', '.mdc-typography--headline1', '.mdc-typography--body1'];

    for (const selector of typographySelectors) {
      const elements = await this.page.locator(selector).all();
      for (const element of elements) {
        const styles = await element.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            fontFamily: computed.fontFamily,
            fontSize: computed.fontSize,
            fontWeight: computed.fontWeight,
            lineHeight: computed.lineHeight
          };
        });

        typographyTests.push({
          selector,
          styles,
          usesRoboto: styles.fontFamily.includes('Roboto')
        });
      }
    }

    return {
      usesRobotoFont: typographyTests.some(test => test.usesRoboto),
      typographyTests
    };
  }

  async validateMaterialComponents() {
    const componentTests = {
      buttons: await this.validateMaterialButtons(),
      cards: await this.validateMaterialCards(),
      textFields: await this.validateMaterialTextFields()
    };

    return componentTests;
  }

  async validateMaterialButtons() {
    const buttons = await this.page.locator('button, .mdc-button').all();
    const buttonTests = [];

    for (const button of buttons) {
      const styles = await button.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          minHeight: computed.minHeight,
          borderRadius: computed.borderRadius,
          padding: computed.padding,
          display: computed.display
        };
      });

      buttonTests.push({
        text: await button.textContent(),
        styles,
        hasProperHeight: parseInt(styles.minHeight) >= 36 // Minimum button height
      });
    }

    return {
      buttonCount: buttonTests.length,
      buttonTests,
      hasButtons: buttonTests.length > 0
    };
  }

  async validateMaterialCards() {
    const cards = await this.page.locator('.card, .mdc-card, [class*="card"]').all();
    const cardTests = [];

    for (const card of cards) {
      const styles = await card.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          borderRadius: computed.borderRadius,
          boxShadow: computed.boxShadow,
          padding: computed.padding,
          backgroundColor: computed.backgroundColor
        };
      });

      cardTests.push({
        styles,
        hasElevation: styles.boxShadow !== 'none',
        hasRoundedCorners: parseInt(styles.borderRadius) > 0
      });
    }

    return {
      cardCount: cardTests.length,
      cardTests,
      hasCards: cardTests.length > 0
    };
  }

  async validateMaterialTextFields() {
    const textFields = await this.page.locator('input[type="text"], input[type="email"], input[type="password"], textarea, .mdc-text-field').all();
    const textFieldTests = [];

    for (const field of textFields) {
      const styles = await field.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          minHeight: computed.minHeight,
          borderRadius: computed.borderRadius,
          padding: computed.padding,
          fontSize: computed.fontSize
        };
      });

      textFieldTests.push({
        type: await field.getAttribute('type') || 'text',
        styles,
        hasProperHeight: parseInt(styles.minHeight) >= 40 // Minimum field height
      });
    }

    return {
      textFieldCount: textFieldTests.length,
      textFieldTests,
      hasTextFields: textFieldTests.length > 0
    };
  }

  async validateMaterialIcons() {
    const materialIcons = await this.page.locator('.material-icons, .material-symbols-outlined').all();
    const iconTests = [];

    for (const icon of materialIcons) {
      const styles = await icon.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          fontSize: computed.fontSize,
          fontFamily: computed.fontFamily,
          lineHeight: computed.lineHeight
        };
      });

      iconTests.push({
        text: await icon.textContent(),
        styles,
        isMaterialIcon: styles.fontFamily.includes('Material')
      });
    }

    return {
      iconCount: iconTests.length,
      iconTests,
      hasMaterialIcons: iconTests.length > 0
    };
  }

  /**
   * Responsive Design Validation
   */
  async validateResponsiveDesign() {
    const breakpoints = MATERIAL_DESIGN_FIXTURES.BREAKPOINTS;
    const results = {};

    for (const [name, breakpoint] of Object.entries(breakpoints)) {
      await this.page.setViewportSize({
        width: breakpoint.minWidth + 50,
        height: 800
      });

      await this.page.waitForTimeout(500); // Allow layout to adjust

      results[name] = {
        viewport: { width: breakpoint.minWidth + 50, height: 800 },
        layout: await this.analyzeLayout(),
        navigation: await this.validateNavigationAtBreakpoint()
      };
    }

    return results;
  }

  async analyzeLayout() {
    return await this.page.evaluate(() => {
      return {
        hasOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        contentWidth: document.documentElement.scrollWidth,
        viewportWidth: document.documentElement.clientWidth,
        bodyClasses: document.body.className
      };
    });
  }

  async validateNavigationAtBreakpoint() {
    const mobileMenu = await this.isElementVisible('[data-testid="mobile-menu"], .mobile-menu, .hamburger-menu');
    const desktopNav = await this.isElementVisible('[data-testid="desktop-nav"], .desktop-nav, .main-navigation');

    return {
      hasMobileMenu: mobileMenu,
      hasDesktopNav: desktopNav,
      isResponsive: mobileMenu || desktopNav
    };
  }

  /**
   * Performance Monitoring
   */
  async measurePageLoadTime() {
    const startTime = Date.now();
    await this.page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;

    return {
      loadTime,
      isAcceptable: loadTime < PERFORMANCE_FIXTURES.THRESHOLDS.PAGE_LOAD.ACCEPTABLE,
      isGood: loadTime < PERFORMANCE_FIXTURES.THRESHOLDS.PAGE_LOAD.GOOD,
      isExcellent: loadTime < PERFORMANCE_FIXTURES.THRESHOLDS.PAGE_LOAD.EXCELLENT
    };
  }

  async measureInteractionTime(action) {
    const startTime = Date.now();
    await action();
    const interactionTime = Date.now() - startTime;

    return {
      interactionTime,
      isAcceptable: interactionTime < PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.PAGE_TRANSITION
    };
  }

  /**
   * Accessibility Validation
   */
  async validateAccessibility() {
    const validation = {
      focusManagement: await this.validateFocusManagement(),
      ariaAttributes: await this.validateAriaAttributes(),
      keyboardNavigation: await this.validateKeyboardAccess(),
      semanticStructure: await this.validateSemanticStructure()
    };

    return validation;
  }

  async validateFocusManagement() {
    // Check if focusable elements have visible focus indicators
    const focusableElements = await this.page.locator('button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])').all();
    const focusTests = [];

    for (const element of focusableElements.slice(0, 5)) { // Test first 5 elements
      await element.focus();
      const styles = await element.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          outline: computed.outline,
          outlineWidth: computed.outlineWidth,
          boxShadow: computed.boxShadow
        };
      });

      focusTests.push({
        hasVisibleFocus: styles.outline !== 'none' || styles.outlineWidth !== '0px' || styles.boxShadow !== 'none'
      });
    }

    return {
      focusableElementCount: focusableElements.length,
      visibleFocusCount: focusTests.filter(test => test.hasVisibleFocus).length,
      focusTests
    };
  }

  async validateAriaAttributes() {
    const ariaElements = await this.page.locator('[aria-label], [aria-labelledby], [aria-describedby], [role]').all();
    const ariaTests = [];

    for (const element of ariaElements) {
      const attributes = await element.evaluate(el => {
        const attrs = {};
        for (const attr of el.attributes) {
          if (attr.name.startsWith('aria-') || attr.name === 'role') {
            attrs[attr.name] = attr.value;
          }
        }
        return attrs;
      });

      ariaTests.push({
        tagName: await element.evaluate(el => el.tagName),
        attributes,
        hasAriaLabel: 'aria-label' in attributes,
        hasRole: 'role' in attributes
      });
    }

    return {
      ariaElementCount: ariaTests.length,
      ariaTests,
      hasAriaElements: ariaTests.length > 0
    };
  }

  async validateKeyboardAccess() {
    // Simple keyboard navigation test
    const initialActiveElement = await this.page.evaluate(() => document.activeElement?.tagName);

    await this.page.keyboard.press('Tab');
    await this.page.waitForTimeout(100);

    const afterTabElement = await this.page.evaluate(() => document.activeElement?.tagName);

    return {
      initialElement: initialActiveElement,
      afterTabElement: afterTabElement,
      tabNavigationWorks: initialActiveElement !== afterTabElement
    };
  }

  async validateSemanticStructure() {
    const headings = await this.page.locator('h1, h2, h3, h4, h5, h6').all();
    const landmarks = await this.page.locator('main, nav, aside, header, footer, [role="main"], [role="navigation"], [role="banner"], [role="contentinfo"]').all();

    return {
      headingCount: headings.length,
      landmarkCount: landmarks.length,
      hasMainContent: await this.isElementVisible('main, [role="main"]'),
      hasNavigation: await this.isElementVisible('nav, [role="navigation"]')
    };
  }

  /**
   * Error Handling and Debugging
   */
  async takeScreenshot(name = 'screenshot') {
    const timestamp = Date.now();
    const filename = `tests/playwright/screenshots/${name}-${timestamp}.png`;
    await this.page.screenshot({ path: filename, fullPage: true });
    return filename;
  }

  async getPageInfo() {
    return await this.page.evaluate(() => ({
      url: window.location.href,
      title: document.title,
      userAgent: navigator.userAgent,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      cookies: document.cookie,
      localStorage: Object.fromEntries(
        Object.keys(localStorage).map(key => [key, localStorage.getItem(key)])
      ),
      sessionStorage: Object.fromEntries(
        Object.keys(sessionStorage).map(key => [key, sessionStorage.getItem(key)])
      )
    }));
  }

  async getConsoleMessages() {
    const messages = [];
    this.page.on('console', msg => {
      messages.push({
        type: msg.type(),
        text: msg.text(),
        timestamp: Date.now()
      });
    });
    return messages;
  }

  async handleDialog(accept = true, promptText = '') {
    this.page.on('dialog', async dialog => {
      if (accept) {
        await dialog.accept(promptText);
      } else {
        await dialog.dismiss();
      }
    });
  }

  /**
   * Form Interaction Helpers
   */
  async fillForm(formData) {
    for (const [field, value] of Object.entries(formData)) {
      const selector = `[name="${field}"], [data-testid="${field}"], #${field}`;
      await this.fillField(selector, value);
    }
  }

  async submitForm(submitSelector = 'button[type="submit"], input[type="submit"]') {
    await this.clickElement(submitSelector);
  }

  async validateFormErrors() {
    const errorSelectors = [
      '.error-message',
      '.alert-danger',
      '[role="alert"]',
      '.field-error',
      '.form-error'
    ];

    const errors = [];
    for (const selector of errorSelectors) {
      const elements = await this.page.locator(selector).all();
      for (const element of elements) {
        if (await element.isVisible()) {
          errors.push({
            selector,
            text: await element.textContent(),
            visible: true
          });
        }
      }
    }

    return errors;
  }
}
