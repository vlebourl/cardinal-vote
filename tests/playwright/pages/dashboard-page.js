import { expect } from '@playwright/test';

export class DashboardPage {
  constructor(page) {
    this.page = page;

    // Dashboard navigation selectors
    this.createVoteButton = '[data-testid="create-vote-button"], button:has-text("Create Vote"), a[href*="create"]';
    this.navigationDrawer = 'nav, [role="navigation"], .navigation-drawer';
    this.userInfo = '[data-testid="user-info"], .user-info, .profile';

    // Status cards selectors
    this.statusCards = '[data-testid="status-cards"], .status-cards, .stats';
    this.activeVotesCard = '[data-testid="active-votes"], .active-votes';
    this.totalVotesCard = '[data-testid="total-votes"], .total-votes';
    this.participantsCard = '[data-testid="participants"], .participants';

    // Activity timeline selectors
    this.activityTimeline = '[data-testid="activity-timeline"], .activity-timeline, .timeline';
    this.timelineItems = '[data-testid="timeline-item"], .timeline-item, .activity-item';

    // Material Design elements
    this.materialIcons = '.material-icons';
    this.materialButtons = 'button';
    this.materialCards = '.card, .mdc-card';

    // Logout/session elements
    this.logoutButton = '[data-testid="logout"], button:has-text("Logout"), button:has-text("Sign Out")';
    this.menuButton = 'button:has-text("menu"), button[aria-label*="menu"]';
  }

  async goto() {
    await this.page.goto('/dashboard');
    await this.page.waitForLoadState('networkidle');
  }

  async waitForDashboardLoad() {
    // Wait for key dashboard elements to be visible
    await this.page.waitForTimeout(2000); // Allow for dynamic content loading

    // Check if we're actually on the dashboard or if we got redirected
    const currentUrl = this.page.url();

    if (!currentUrl.includes('dashboard')) {
      throw new Error(`Expected to be on dashboard, but current URL is: ${currentUrl}`);
    }

    return true;
  }

  async isLoggedIn() {
    const currentUrl = this.page.url();
    return currentUrl.includes('dashboard') || currentUrl.includes('admin');
  }

  async navigateToVoteCreation() {
    const createVoteBtn = this.page.locator(this.createVoteButton).first();

    if (await createVoteBtn.isVisible()) {
      await createVoteBtn.click();
      await this.page.waitForURL('**/create**', { timeout: 5000 });
      return true;
    } else {
      // Try alternative navigation methods
      const alternativeSelectors = [
        'a:has-text("Create")',
        'button:has-text("New Vote")',
        '[href*="create"]',
        '.create-vote'
      ];

      for (const selector of alternativeSelectors) {
        if (await this.page.isVisible(selector)) {
          await this.page.click(selector);
          await this.page.waitForTimeout(1000);
          return true;
        }
      }
    }

    return false;
  }

  // Status cards validation
  async getStatusCardData() {
    const statusData = {};

    // Try different possible selectors for status information
    const cardSelectors = [
      { name: 'activeVotes', selectors: [this.activeVotesCard, '.active-votes', '[data-stat="active"]'] },
      { name: 'totalVotes', selectors: [this.totalVotesCard, '.total-votes', '[data-stat="total"]'] },
      { name: 'participants', selectors: [this.participantsCard, '.participants', '[data-stat="participants"]'] }
    ];

    for (const card of cardSelectors) {
      for (const selector of card.selectors) {
        const element = this.page.locator(selector).first();
        if (await element.isVisible()) {
          statusData[card.name] = await element.textContent();
          break;
        }
      }

      // If no specific card found, look for generic stats containers
      if (!statusData[card.name]) {
        statusData[card.name] = 'Not found';
      }
    }

    return statusData;
  }

  // Activity timeline validation
  async getActivityTimelineData() {
    const timelineData = [];

    const timelineElements = this.page.locator(this.timelineItems);
    const count = await timelineElements.count();

    for (let i = 0; i < count; i++) {
      const item = timelineElements.nth(i);
      const text = await item.textContent();
      timelineData.push({
        index: i,
        content: text.trim()
      });
    }

    // If no timeline items found, check for alternative structures
    if (timelineData.length === 0) {
      const alternativeSelectors = ['.activity', '.history', '.recent', '.events'];

      for (const selector of alternativeSelectors) {
        const elements = this.page.locator(selector);
        const altCount = await elements.count();

        if (altCount > 0) {
          for (let i = 0; i < altCount; i++) {
            const item = elements.nth(i);
            const text = await item.textContent();
            timelineData.push({
              index: i,
              content: text.trim(),
              source: selector
            });
          }
          break;
        }
      }
    }

    return timelineData;
  }

  // Material Design validation
  async validateMaterialDesignCompliance() {
    const results = {
      materialIcons: 0,
      buttons: 0,
      cards: 0,
      navigation: false
    };

    // Count Material Icons
    const icons = this.page.locator(this.materialIcons);
    results.materialIcons = await icons.count();

    // Count buttons
    const buttons = this.page.locator(this.materialButtons);
    results.buttons = await buttons.count();

    // Count cards
    const cards = this.page.locator(this.materialCards);
    results.cards = await cards.count();

    // Check navigation structure
    const nav = this.page.locator(this.navigationDrawer).first();
    results.navigation = await nav.isVisible();

    return results;
  }

  // Session validation
  async validateUserSession() {
    const sessionData = await this.page.evaluate(() => {
      const session = {
        sessionStorage: {},
        localStorage: {},
        cookies: document.cookie
      };

      // Get sessionStorage items
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        session.sessionStorage[key] = sessionStorage.getItem(key);
      }

      // Get localStorage items
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        session.localStorage[key] = localStorage.getItem(key);
      }

      return session;
    });

    // Look for JWT tokens or authentication data
    const hasAuthToken = !!(
      sessionData.sessionStorage.jwt ||
      sessionData.sessionStorage.token ||
      sessionData.sessionStorage.auth_token ||
      sessionData.localStorage.jwt ||
      sessionData.localStorage.token
    );

    return {
      hasAuthToken,
      sessionData: sessionData.sessionStorage,
      localStorageData: sessionData.localStorage,
      cookies: sessionData.cookies
    };
  }

  // Navigation testing
  async testNavigation() {
    const navigationResults = {
      menuAccessible: false,
      linksWorking: [],
      responsiveMenu: false
    };

    // Test menu button
    const menuBtn = this.page.locator(this.menuButton).first();
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
      navigationResults.menuAccessible = true;
      await this.page.waitForTimeout(500);
    }

    // Test common navigation links
    const commonLinks = [
      'a:has-text("Dashboard")',
      'a:has-text("Create")',
      'a:has-text("Votes")',
      'a:has-text("Profile")',
      'a:has-text("Settings")'
    ];

    for (const linkSelector of commonLinks) {
      const link = this.page.locator(linkSelector).first();
      if (await link.isVisible()) {
        const href = await link.getAttribute('href');
        navigationResults.linksWorking.push({
          text: await link.textContent(),
          href: href
        });
      }
    }

    // Test responsive menu behavior
    await this.page.setViewportSize({ width: 375, height: 667 }); // Mobile size
    await this.page.waitForTimeout(500);

    const mobileMenu = this.page.locator(this.menuButton);
    navigationResults.responsiveMenu = await mobileMenu.isVisible();

    return navigationResults;
  }

  // Performance testing
  async measurePageLoadTime() {
    const startTime = Date.now();
    await this.page.goto('/dashboard');
    await this.page.waitForLoadState('networkidle');
    const endTime = Date.now();

    return {
      loadTime: endTime - startTime,
      timestamp: new Date().toISOString()
    };
  }

  // Error handling
  async checkForErrors() {
    const errors = [];

    // Check for JavaScript errors in console
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push({
          type: 'console',
          message: msg.text(),
          timestamp: Date.now()
        });
      }
    });

    // Check for visual error indicators
    const errorSelectors = ['.error', '.alert-danger', '[role="alert"]', '.error-message'];

    for (const selector of errorSelectors) {
      const errorElements = this.page.locator(selector);
      const count = await errorElements.count();

      if (count > 0) {
        for (let i = 0; i < count; i++) {
          const element = errorElements.nth(i);
          const text = await element.textContent();
          errors.push({
            type: 'visual',
            selector: selector,
            message: text.trim(),
            timestamp: Date.now()
          });
        }
      }
    }

    return errors;
  }

  async logout() {
    const logoutBtn = this.page.locator(this.logoutButton).first();

    if (await logoutBtn.isVisible()) {
      await logoutBtn.click();
      await this.page.waitForURL('**/', { timeout: 5000 }); // Wait for redirect to home
      return true;
    }

    // Alternative logout methods
    const alternativeSelectors = [
      'button:has-text("Sign Out")',
      '[data-action="logout"]',
      '.logout'
    ];

    for (const selector of alternativeSelectors) {
      if (await this.page.isVisible(selector)) {
        await this.page.click(selector);
        await this.page.waitForTimeout(2000);
        return true;
      }
    }

    return false;
  }
}
