import { expect } from '@playwright/test';
import { BasePage } from './base-page.js';
import { MATERIAL_DESIGN_FIXTURES } from '../fixtures/data/material-design-fixtures.js';
import { PERFORMANCE_FIXTURES } from '../fixtures/data/performance-accessibility-fixtures.js';

/**
 * Enhanced Dashboard Page Object Model
 *
 * Extends BasePage with comprehensive dashboard functionality including:
 * - Vote management and creation workflows
 * - User statistics and analytics
 * - Navigation and menu interactions
 * - Real-time updates and notifications
 * - Material Design validation
 * - Performance monitoring
 */
export class EnhancedDashboardPage extends BasePage {
  constructor(page) {
    super(page);

    // Main navigation elements
    this.navigation = {
      createVoteButton: '[data-testid="create-vote-btn"], button:has-text("Create Vote")',
      myVotesTab: '[data-testid="my-votes-tab"], .nav-tab:has-text("My Votes")',
      publicVotesTab: '[data-testid="public-votes-tab"], .nav-tab:has-text("Public Votes")',
      settingsTab: '[data-testid="settings-tab"], .nav-tab:has-text("Settings")',
      profileDropdown: '[data-testid="profile-dropdown"], .profile-menu',
      logoutButton: '[data-testid="logout-btn"], button:has-text("Logout")',
      hamburgerMenu: '[data-testid="mobile-menu"], .hamburger-menu, .menu-toggle'
    };

    // Vote management elements
    this.voteElements = {
      voteCard: '[data-testid="vote-card"], .vote-card',
      voteTitle: '[data-testid="vote-title"], .vote-title',
      voteDescription: '[data-testid="vote-description"], .vote-description',
      voteStatus: '[data-testid="vote-status"], .vote-status',
      editVoteButton: '[data-testid="edit-vote"], button:has-text("Edit")',
      deleteVoteButton: '[data-testid="delete-vote"], button:has-text("Delete")',
      viewResultsButton: '[data-testid="view-results"], button:has-text("Results")',
      shareVoteButton: '[data-testid="share-vote"], button:has-text("Share")',
      duplicateVoteButton: '[data-testid="duplicate-vote"], button:has-text("Duplicate")'
    };

    // Statistics and analytics elements
    this.statsElements = {
      totalVotes: '[data-testid="total-votes"], .stat-total-votes',
      activeVotes: '[data-testid="active-votes"], .stat-active-votes',
      totalResponses: '[data-testid="total-responses"], .stat-total-responses',
      recentActivity: '[data-testid="recent-activity"], .recent-activity',
      engagementChart: '[data-testid="engagement-chart"], .engagement-chart',
      performanceMetrics: '[data-testid="performance-metrics"], .performance-metrics'
    };

    // Filter and search elements
    this.filterElements = {
      searchInput: '[data-testid="vote-search"], input[placeholder*="Search"]',
      statusFilter: '[data-testid="status-filter"], .status-filter',
      typeFilter: '[data-testid="type-filter"], .type-filter',
      dateFilter: '[data-testid="date-filter"], .date-filter',
      sortDropdown: '[data-testid="sort-dropdown"], .sort-dropdown',
      clearFiltersButton: '[data-testid="clear-filters"], button:has-text("Clear")'
    };

    // Modal and dialog elements
    this.modals = {
      deleteConfirmModal: '[data-testid="delete-confirm-modal"], .delete-confirm-modal',
      shareModal: '[data-testid="share-modal"], .share-modal',
      settingsModal: '[data-testid="settings-modal"], .settings-modal',
      modalOverlay: '.modal-overlay, .backdrop',
      modalClose: '[data-testid="modal-close"], .modal-close, button:has-text("Close")',
      confirmButton: '[data-testid="confirm-button"], button:has-text("Confirm")',
      cancelButton: '[data-testid="cancel-button"], button:has-text("Cancel")'
    };

    // Notification elements
    this.notifications = {
      notificationBell: '[data-testid="notification-bell"], .notification-bell',
      notificationBadge: '[data-testid="notification-badge"], .notification-badge',
      notificationPanel: '[data-testid="notification-panel"], .notification-panel',
      notificationItem: '[data-testid="notification-item"], .notification-item',
      markAllReadButton: '[data-testid="mark-all-read"], button:has-text("Mark all read")'
    };
  }

  /**
   * Navigation Methods
   */
  async goto() {
    const loadTime = await super.goto('/dashboard');
    await this.waitForDashboardToLoad();
    return loadTime;
  }

  async waitForDashboardToLoad() {
    // Wait for key dashboard elements to be visible
    await Promise.all([
      this.waitForElement(this.navigation.createVoteButton),
      this.waitForElement(this.voteElements.voteCard, 'visible', 10000).catch(() => {
        // No votes might be present, which is fine
      }),
      this.waitForElement(this.statsElements.totalVotes, 'visible', 5000).catch(() => {
        // Stats might not be immediately available
      })
    ]);

    // Wait for any loading spinners to disappear
    await this.page.waitForFunction(() => {
      const spinners = document.querySelectorAll('.loading, .spinner, [data-testid="loading"]');
      return spinners.length === 0;
    }, { timeout: 10000 }).catch(() => {
      // Loading indicators might not be present
    });
  }

  /**
   * Vote Management Methods
   */
  async createNewVote() {
    const startTime = Date.now();
    await this.clickElement(this.navigation.createVoteButton);

    // Wait for navigation to vote creation page
    await this.waitForURL('**/create-vote', 10000);

    const navigationTime = Date.now() - startTime;
    return {
      navigationTime,
      isAcceptable: navigationTime < PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.PAGE_TRANSITION
    };
  }

  async getVoteCards() {
    await this.waitForElement(this.voteElements.voteCard, 'visible', 5000).catch(() => {
      // No votes present is acceptable
    });

    const voteCards = await this.page.locator(this.voteElements.voteCard).all();
    const votes = [];

    for (const card of voteCards) {
      const voteData = await this.extractVoteCardData(card);
      votes.push(voteData);
    }

    return votes;
  }

  async extractVoteCardData(cardElement) {
    return await cardElement.evaluate(card => {
      const titleElement = card.querySelector('[data-testid="vote-title"], .vote-title');
      const descriptionElement = card.querySelector('[data-testid="vote-description"], .vote-description');
      const statusElement = card.querySelector('[data-testid="vote-status"], .vote-status');

      return {
        title: titleElement?.textContent?.trim() || '',
        description: descriptionElement?.textContent?.trim() || '',
        status: statusElement?.textContent?.trim() || '',
        id: card.getAttribute('data-vote-id') || '',
        hasEditButton: !!card.querySelector('[data-testid="edit-vote"], button:has-text("Edit")'),
        hasDeleteButton: !!card.querySelector('[data-testid="delete-vote"], button:has-text("Delete")'),
        hasResultsButton: !!card.querySelector('[data-testid="view-results"], button:has-text("Results")')
      };
    });
  }

  async editVote(voteId) {
    const voteCard = this.page.locator(`[data-vote-id="${voteId}"]`).first();
    await voteCard.locator(this.voteElements.editVoteButton).click();
    await this.waitForURL(`**/edit-vote/**`);
  }

  async deleteVote(voteId) {
    const voteCard = this.page.locator(`[data-vote-id="${voteId}"]`).first();
    await voteCard.locator(this.voteElements.deleteVoteButton).click();

    // Wait for confirmation modal
    await this.waitForElement(this.modals.deleteConfirmModal);
    await this.clickElement(this.modals.confirmButton);

    // Wait for the vote to be removed from the list
    await this.page.waitForFunction((id) => {
      return !document.querySelector(`[data-vote-id="${id}"]`);
    }, voteId, { timeout: 10000 });
  }

  async shareVote(voteId) {
    const voteCard = this.page.locator(`[data-vote-id="${voteId}"]`).first();
    await voteCard.locator(this.voteElements.shareVoteButton).click();

    // Wait for share modal to appear
    await this.waitForElement(this.modals.shareModal);

    // Get share URL
    const shareUrl = await this.page.locator('.share-url, [data-testid="share-url"]').textContent();
    return shareUrl?.trim();
  }

  /**
   * Filter and Search Methods
   */
  async searchVotes(query) {
    await this.fillField(this.filterElements.searchInput, query);
    await this.page.keyboard.press('Enter');

    // Wait for search results to update
    await this.page.waitForTimeout(1000);

    return await this.getVoteCards();
  }

  async filterByStatus(status) {
    await this.clickElement(this.filterElements.statusFilter);
    await this.clickElement(`[data-value="${status}"], option:has-text("${status}")`);

    // Wait for filter to apply
    await this.page.waitForTimeout(1000);

    return await this.getVoteCards();
  }

  async clearAllFilters() {
    await this.clickElement(this.filterElements.clearFiltersButton);
    await this.page.waitForTimeout(1000);
  }

  /**
   * Statistics and Analytics Methods
   */
  async getStatistics() {
    const stats = {};

    try {
      stats.totalVotes = await this.getElementText(this.statsElements.totalVotes);
      stats.activeVotes = await this.getElementText(this.statsElements.activeVotes);
      stats.totalResponses = await this.getElementText(this.statsElements.totalResponses);
    } catch (error) {
      console.warn('Some statistics not available:', error.message);
    }

    return stats;
  }

  async validateEngagementChart() {
    if (await this.isElementVisible(this.statsElements.engagementChart)) {
      // Check if chart container exists and has content
      const chartContent = await this.page.evaluate((selector) => {
        const chart = document.querySelector(selector);
        return chart && (chart.children.length > 0 || chart.textContent.trim() !== '');
      }, this.statsElements.engagementChart);

      return { hasChart: true, hasContent: chartContent };
    }

    return { hasChart: false, hasContent: false };
  }

  /**
   * Navigation and Menu Methods
   */
  async switchToTab(tabName) {
    const tabSelectors = {
      'my-votes': this.navigation.myVotesTab,
      'public-votes': this.navigation.publicVotesTab,
      'settings': this.navigation.settingsTab
    };

    const tabSelector = tabSelectors[tabName.toLowerCase()];
    if (!tabSelector) {
      throw new Error(`Unknown tab: ${tabName}`);
    }

    const startTime = Date.now();
    await this.clickElement(tabSelector);

    // Wait for tab content to load
    await this.page.waitForTimeout(500);

    const switchTime = Date.now() - startTime;
    return {
      switchTime,
      isAcceptable: switchTime < PERFORMANCE_FIXTURES.THRESHOLDS.NAVIGATION.PAGE_TRANSITION
    };
  }

  async openProfileDropdown() {
    await this.clickElement(this.navigation.profileDropdown);
    await this.waitForElement(this.navigation.logoutButton);
  }

  async logout() {
    await this.openProfileDropdown();
    await this.clickElement(this.navigation.logoutButton);

    // Wait for redirect to login page
    await this.waitForURL('**/login', 10000).catch(async () => {
      // Might redirect to home page instead
      await this.waitForURL('**/', 5000);
    });
  }

  /**
   * Notification Methods
   */
  async openNotifications() {
    await this.clickElement(this.notifications.notificationBell);
    await this.waitForElement(this.notifications.notificationPanel);
  }

  async getNotificationCount() {
    if (await this.isElementVisible(this.notifications.notificationBadge)) {
      const badgeText = await this.getElementText(this.notifications.notificationBadge);
      return parseInt(badgeText) || 0;
    }
    return 0;
  }

  async markAllNotificationsRead() {
    await this.openNotifications();

    if (await this.isElementVisible(this.notifications.markAllReadButton)) {
      await this.clickElement(this.notifications.markAllReadButton);
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Modal Interaction Methods
   */
  async closeModal() {
    if (await this.isElementVisible(this.modals.modalOverlay)) {
      await this.clickElement(this.modals.modalClose);

      // Wait for modal to disappear
      await this.page.waitForFunction(() => {
        return !document.querySelector('.modal-overlay, .backdrop');
      }, { timeout: 5000 });
    }
  }

  /**
   * Responsive Design Validation
   */
  async validateResponsiveDashboard() {
    const breakpoints = MATERIAL_DESIGN_FIXTURES.BREAKPOINTS;
    const results = {};

    for (const [name, breakpoint] of Object.entries(breakpoints)) {
      await this.page.setViewportSize({
        width: breakpoint.minWidth + 50,
        height: 800
      });

      await this.page.waitForTimeout(500);

      results[name] = {
        viewport: { width: breakpoint.minWidth + 50, height: 800 },
        navigation: await this.validateResponsiveNavigation(),
        voteCards: await this.validateResponsiveVoteCards(),
        statistics: await this.validateResponsiveStatistics()
      };
    }

    return results;
  }

  async validateResponsiveNavigation() {
    const isMobile = await this.page.evaluate(() => window.innerWidth < 768);

    return {
      isMobile,
      hasHamburgerMenu: isMobile ? await this.isElementVisible(this.navigation.hamburgerMenu) : true,
      createButtonVisible: await this.isElementVisible(this.navigation.createVoteButton),
      tabsVisible: !isMobile || await this.isElementVisible(this.navigation.myVotesTab)
    };
  }

  async validateResponsiveVoteCards() {
    const cards = await this.page.locator(this.voteElements.voteCard).all();

    if (cards.length === 0) {
      return { hasCards: false, responsive: true };
    }

    const cardMetrics = [];
    for (const card of cards.slice(0, 3)) { // Test first 3 cards
      const boundingBox = await card.boundingBox();
      cardMetrics.push({
        width: boundingBox?.width || 0,
        height: boundingBox?.height || 0,
        visible: await card.isVisible()
      });
    }

    return {
      hasCards: cards.length > 0,
      cardCount: cards.length,
      cardMetrics,
      responsive: cardMetrics.every(metric => metric.visible && metric.width > 0)
    };
  }

  async validateResponsiveStatistics() {
    return {
      totalVotesVisible: await this.isElementVisible(this.statsElements.totalVotes),
      activeVotesVisible: await this.isElementVisible(this.statsElements.activeVotes),
      chartVisible: await this.isElementVisible(this.statsElements.engagementChart)
    };
  }

  /**
   * Performance Monitoring
   */
  async measureDashboardLoadPerformance() {
    const startTime = Date.now();

    await this.goto();

    const totalLoadTime = Date.now() - startTime;
    const voteCards = await this.getVoteCards();
    const statistics = await this.getStatistics();

    return {
      totalLoadTime,
      voteCount: voteCards.length,
      hasStatistics: Object.keys(statistics).length > 0,
      isAcceptable: totalLoadTime < PERFORMANCE_FIXTURES.THRESHOLDS.PAGE_LOAD.ACCEPTABLE,
      isGood: totalLoadTime < PERFORMANCE_FIXTURES.THRESHOLDS.PAGE_LOAD.GOOD,
      isExcellent: totalLoadTime < PERFORMANCE_FIXTURES.THRESHOLDS.PAGE_LOAD.EXCELLENT
    };
  }

  /**
   * Dashboard-specific Material Design Validation
   */
  async validateDashboardMaterialDesign() {
    const baseValidation = await super.validateMaterialDesign();

    // Dashboard-specific validations
    const dashboardValidation = {
      voteCards: await this.validateVoteCardDesign(),
      navigationTabs: await this.validateNavigationTabs(),
      actionButtons: await this.validateActionButtons(),
      statisticsDisplay: await this.validateStatisticsDesign()
    };

    return {
      ...baseValidation,
      dashboard: dashboardValidation
    };
  }

  async validateVoteCardDesign() {
    const cards = await this.page.locator(this.voteElements.voteCard).all();
    const cardValidations = [];

    for (const card of cards.slice(0, 3)) {
      const styles = await card.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          borderRadius: computed.borderRadius,
          boxShadow: computed.boxShadow,
          backgroundColor: computed.backgroundColor,
          padding: computed.padding
        };
      });

      cardValidations.push({
        hasElevation: styles.boxShadow !== 'none',
        hasRoundedCorners: parseInt(styles.borderRadius) > 0,
        hasProperPadding: parseInt(styles.padding) >= 16,
        styles
      });
    }

    return {
      cardCount: cards.length,
      validations: cardValidations,
      allCardsValid: cardValidations.every(v => v.hasElevation && v.hasRoundedCorners)
    };
  }

  async validateNavigationTabs() {
    const tabs = await this.page.locator('.nav-tab, [role="tab"]').all();
    const tabValidations = [];

    for (const tab of tabs) {
      const styles = await tab.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          minHeight: computed.minHeight,
          padding: computed.padding,
          borderBottom: computed.borderBottom
        };
      });

      tabValidations.push({
        hasProperHeight: parseInt(styles.minHeight) >= 48,
        hasProperPadding: parseInt(styles.padding) >= 12,
        styles
      });
    }

    return {
      tabCount: tabs.length,
      validations: tabValidations
    };
  }

  async validateActionButtons() {
    const buttons = await this.page.locator(this.navigation.createVoteButton).all();
    const buttonValidations = await super.validateMaterialButtons();

    return {
      ...buttonValidations,
      primaryActionVisible: buttons.length > 0
    };
  }

  async validateStatisticsDesign() {
    const statsElements = [
      this.statsElements.totalVotes,
      this.statsElements.activeVotes,
      this.statsElements.totalResponses
    ];

    const validations = [];
    for (const selector of statsElements) {
      if (await this.isElementVisible(selector)) {
        const styles = await this.page.locator(selector).evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            fontSize: computed.fontSize,
            fontWeight: computed.fontWeight,
            textAlign: computed.textAlign
          };
        });

        validations.push({
          selector,
          visible: true,
          hasLargeFont: parseInt(styles.fontSize) >= 24,
          isBold: parseInt(styles.fontWeight) >= 600,
          styles
        });
      }
    }

    return {
      statisticsCount: validations.length,
      validations
    };
  }
}
