import { test, expect } from '@playwright/test';
import { EnhancedLandingPage } from '../../pages/landing-page.enhanced.js';
import { EnhancedDashboardPage } from '../../pages/dashboard-page.enhanced.js';
import { EnhancedVoteCreationPage } from '../../pages/vote-creation-page.enhanced.js';
import { EnhancedPublicVotingPage } from '../../pages/public-voting-page.enhanced.js';
import { EnhancedAdminPage } from '../../pages/admin-page.enhanced.js';
import { testDataManager } from '../../fixtures/data/test-data-factory.js';
import { MATERIAL_DESIGN_FIXTURES } from '../../fixtures/data/material-design-fixtures.js';

test.describe('Advanced Responsive Design Tests', () => {
  test.describe.configure({ mode: 'parallel' });

  let landingPage;
  let dashboardPage;
  let voteCreationPage;
  let publicVotingPage;
  let adminPage;

  test.beforeEach(async ({ page }) => {
    landingPage = new EnhancedLandingPage(page);
    dashboardPage = new EnhancedDashboardPage(page);
    voteCreationPage = new EnhancedVoteCreationPage(page);
    publicVotingPage = new EnhancedPublicVotingPage(page);
    adminPage = new EnhancedAdminPage(page);
  });

  test.afterEach(async ({ page }) => {
    await testDataManager.runCleanup();
  });

  test.describe('Material Design Breakpoint Testing', () => {
    test('should adapt layout across all Material Design breakpoints', async ({ page }) => {
      await landingPage.goto();

      const breakpoints = MATERIAL_DESIGN_FIXTURES.BREAKPOINTS;
      const responsiveResults = {};

      for (const [name, breakpoint] of Object.entries(breakpoints)) {
        // Set viewport to breakpoint
        await page.setViewportSize({
          width: breakpoint.minWidth + 50,
          height: 800
        });

        await page.waitForTimeout(500); // Allow layout to adjust

        // Test navigation responsiveness
        const navigationTest = await landingPage.validateResponsiveNavigation();

        // Test content layout
        const layoutTest = await landingPage.analyzeLayout();

        // Test interactive elements
        const interactionTest = await landingPage.validateResponsiveInteraction();

        responsiveResults[name] = {
          viewport: { width: breakpoint.minWidth + 50, height: 800 },
          navigation: navigationTest,
          layout: layoutTest,
          interaction: interactionTest,
          hasOverflow: layoutTest.hasOverflow,
          isUsable: navigationTest.isUsable && interactionTest.isUsable
        };

        // Verify no horizontal overflow
        expect(layoutTest.hasOverflow).toBe(false);
        expect(responsiveResults[name].isUsable).toBe(true);
      }

      return responsiveResults;
    });

    test('should handle intermediate viewport sizes smoothly', async ({ page }) => {
      await landingPage.goto();

      // Test viewports between major breakpoints
      const intermediateViewports = [
        { width: 600, height: 800 }, // Between xs and sm
        { width: 900, height: 800 }, // Between sm and md
        { width: 1100, height: 800 }, // Between md and lg
        { width: 1400, height: 800 }  // Between lg and xl
      ];

      for (const viewport of intermediateViewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(300);

        // Check for layout stability
        const layoutStability = await page.evaluate(() => {
          return {
            hasHorizontalScroll: document.documentElement.scrollWidth > document.documentElement.clientWidth,
            hasVerticalOverflow: document.body.scrollHeight > window.innerHeight + 100, // Allow some overflow
            elementsVisible: document.querySelectorAll(':visible').length
          };
        });

        expect(layoutStability.hasHorizontalScroll).toBe(false);
        expect(layoutStability.elementsVisible).toBeGreaterThan(0);
      }
    });
  });

  test.describe('Mobile-First Responsive Navigation', () => {
    test('should show mobile navigation on small screens', async ({ page }) => {
      await landingPage.goto();

      // Mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      // Check for mobile navigation elements
      const mobileNav = await landingPage.validateMobileNavigation();

      expect(mobileNav.hasMobileMenu).toBe(true);
      expect(mobileNav.isAccessible).toBe(true);

      // Test mobile menu functionality
      if (mobileNav.hasMobileToggle) {
        await landingPage.clickElement('[data-testid="mobile-toggle"], .mobile-toggle, .hamburger-menu');

        // Menu should expand
        const menuExpanded = await landingPage.isElementVisible(
          '.mobile-menu-open, .nav-expanded, [aria-expanded="true"]', 2000
        );
        expect(menuExpanded).toBe(true);

        // Test menu item accessibility
        const menuItems = await page.locator('.mobile-menu a, .mobile-nav a').all();
        expect(menuItems.length).toBeGreaterThan(0);

        for (const item of menuItems.slice(0, 3)) {
          const isClickable = await item.evaluate(el => {
            const computed = window.getComputedStyle(el);
            return computed.cursor === 'pointer' && computed.pointerEvents !== 'none';
          });
          expect(isClickable).toBe(true);
        }
      }
    });

    test('should hide mobile navigation on desktop screens', async ({ page }) => {
      await landingPage.goto();

      // Desktop viewport
      await page.setViewportSize({ width: 1200, height: 800 });
      await page.waitForTimeout(500);

      const desktopNav = await landingPage.validateDesktopNavigation();

      expect(desktopNav.hasDesktopMenu).toBe(true);
      expect(desktopNav.mobileElementsHidden).toBe(true);

      // Mobile toggle should be hidden
      const mobileToggleVisible = await landingPage.isElementVisible(
        '[data-testid="mobile-toggle"], .mobile-toggle, .hamburger-menu'
      );
      expect(mobileToggleVisible).toBe(false);
    });

    test('should maintain navigation functionality across breakpoints', async ({ page }) => {
      await landingPage.goto();

      const navigationBreakpoints = [
        { width: 320, height: 568 },  // Small mobile
        { width: 768, height: 1024 }, // Tablet
        { width: 1024, height: 768 }, // Desktop
        { width: 1440, height: 900 }  // Large desktop
      ];

      for (const viewport of navigationBreakpoints) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(300);

        // Essential navigation should always be present
        const essentialNav = await landingPage.validateEssentialNavigation();

        expect(essentialNav.hasSignInAccess).toBe(true);
        expect(essentialNav.hasGetStartedAccess).toBe(true);
        expect(essentialNav.isKeyboardAccessible).toBe(true);

        // Test sign-in access
        const signInAccessible = viewport.width < 768
          ? await landingPage.isElementVisible('.mobile-menu, .hamburger-menu')
          : await landingPage.isElementVisible('button:has-text("Sign In")');

        expect(signInAccessible).toBe(true);
      }
    });
  });

  test.describe('Dashboard Responsive Layout', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/auth/test-login?user=user1&role=user');
      await dashboardPage.goto();
    });

    test('should adapt dashboard layout for different screen sizes', async ({ page }) => {
      const responsiveValidation = await dashboardPage.validateResponsiveDashboard();

      for (const [breakpointName, validation] of Object.entries(responsiveValidation)) {
        expect(validation.navigation.createButtonVisible).toBe(true);

        if (validation.viewport.width < 768) {
          // Mobile: Should have hamburger menu or compact navigation
          expect(validation.navigation.hasHamburgerMenu).toBe(true);
        } else {
          // Desktop: Should have full navigation
          expect(validation.navigation.tabsVisible).toBe(true);
        }

        // Vote cards should be responsive
        if (validation.voteCards.hasCards) {
          expect(validation.voteCards.responsive).toBe(true);
          validation.voteCards.cardMetrics.forEach(metric => {
            expect(metric.visible).toBe(true);
            expect(metric.width).toBeGreaterThan(0);
          });
        }
      }
    });

    test('should handle vote card grid responsiveness', async ({ page }) => {
      const viewports = [
        { width: 320, height: 568, expectedColumns: 1 },
        { width: 768, height: 1024, expectedColumns: 2 },
        { width: 1200, height: 800, expectedColumns: 3 },
        { width: 1600, height: 900, expectedColumns: 4 }
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(500);

        const voteCards = await dashboardPage.getVoteCards();

        if (voteCards.length > 0) {
          // Check grid layout
          const gridLayout = await page.evaluate(() => {
            const container = document.querySelector('.vote-cards, .cards-grid, [data-testid="vote-cards"]');
            if (!container) return null;

            const computed = window.getComputedStyle(container);
            return {
              display: computed.display,
              gridTemplateColumns: computed.gridTemplateColumns,
              gap: computed.gap
            };
          });

          if (gridLayout) {
            expect(['grid', 'flex']).toContain(gridLayout.display);

            if (gridLayout.display === 'grid') {
              const columnCount = gridLayout.gridTemplateColumns.split(' ').length;
              expect(columnCount).toBeGreaterThanOrEqual(1);
              expect(columnCount).toBeLessThanOrEqual(viewport.expectedColumns + 1);
            }
          }
        }
      }
    });

    test('should maintain dashboard functionality on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      // Test mobile dashboard functionality
      const mobileValidation = await dashboardPage.validateMobileDashboard();

      expect(mobileValidation.createVoteAccessible).toBe(true);
      expect(mobileValidation.voteCardsAccessible).toBe(true);
      expect(mobileValidation.navigationAccessible).toBe(true);

      // Test create vote on mobile
      if (mobileValidation.createVoteAccessible) {
        await dashboardPage.clickElement(dashboardPage.navigation.createVoteButton);
        await page.waitForURL('**/create-vote', 5000);
        expect(page.url()).toContain('create-vote');
      }
    });
  });

  test.describe('Vote Creation Form Responsiveness', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/auth/test-login?user=user1&role=user');
      await voteCreationPage.goto();
    });

    test('should adapt vote creation form for mobile devices', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      const mobileFormValidation = await voteCreationPage.validateMobileFormLayout();

      expect(mobileFormValidation.fieldsStackVertically).toBe(true);
      expect(mobileFormValidation.formWidthAppropriate).toBe(true);
      expect(mobileFormValidation.touchTargetsAppropriate).toBe(true);

      // Test form interaction on mobile
      const voteData = testDataManager.createVote('basic');
      const fillResult = await voteCreationPage.fillBasicInformation(voteData);
      expect(fillResult.isAcceptable).toBe(true);

      // Test step navigation on mobile
      const stepNavigation = await voteCreationPage.validateMobileStepNavigation();
      expect(stepNavigation.navigationVisible).toBe(true);
      expect(stepNavigation.buttonsAccessible).toBe(true);
    });

    test('should handle option management on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      const voteData = testDataManager.createVote('basic');
      await voteCreationPage.fillBasicInformation(voteData);
      await voteCreationPage.goToNextStep();

      // Test adding options on mobile
      await voteCreationPage.addVoteOption({ text: 'Mobile Option 1' });
      await voteCreationPage.addVoteOption({ text: 'Mobile Option 2' });

      const options = await voteCreationPage.getOptions();
      expect(options.length).toBe(2);

      // Test mobile-specific option interactions
      const mobileOptionValidation = await voteCreationPage.validateMobileOptionManagement();
      expect(mobileOptionValidation.optionsStackVertically).toBe(true);
      expect(mobileOptionValidation.removeButtonsAccessible).toBe(true);
      expect(mobileOptionValidation.reorderingPossible).toBe(true);
    });

    test('should adapt form controls for touch interaction', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      // Test touch target sizes
      const touchTargets = await page.evaluate(() => {
        const interactiveElements = document.querySelectorAll('button, input, select, textarea, a[href]');
        const touchTargetSizes = [];

        interactiveElements.forEach(el => {
          const rect = el.getBoundingClientRect();
          touchTargetSizes.push({
            element: el.tagName,
            width: rect.width,
            height: rect.height,
            meetsMinimum: rect.width >= 44 && rect.height >= 44 // WCAG minimum
          });
        });

        return touchTargetSizes;
      });

      // Most interactive elements should meet touch target requirements
      const validTouchTargets = touchTargets.filter(target => target.meetsMinimum);
      expect(validTouchTargets.length / touchTargets.length).toBeGreaterThan(0.8);
    });
  });

  test.describe('Public Voting Interface Responsiveness', () => {
    test('should provide responsive voting interface', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-responsive-vote');

      const viewports = [
        { width: 320, height: 568 },  // iPhone SE
        { width: 375, height: 812 },  // iPhone X
        { width: 768, height: 1024 }, // iPad
        { width: 1024, height: 768 }  // iPad landscape
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(500);

        const votingValidation = await publicVotingPage.validateResponsiveVoting();

        expect(votingValidation.optionsVisible).toBe(true);
        expect(votingValidation.submitButtonAccessible).toBe(true);
        expect(votingValidation.layoutStable).toBe(true);

        // Test voting interaction
        const options = await publicVotingPage.getVoteOptions();
        if (options.length > 0) {
          const selectionResult = await publicVotingPage.selectOption(0);
          expect(selectionResult.isAcceptable).toBe(true);
        }
      }
    });

    test('should handle results display responsively', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-results-vote');

      // Submit a vote first
      const options = await publicVotingPage.getVoteOptions();
      if (options.length > 0) {
        await publicVotingPage.selectOption(0);
        await publicVotingPage.submitVote();
      }

      const mobileViewport = { width: 375, height: 667 };
      await page.setViewportSize(mobileViewport);
      await page.waitForTimeout(500);

      const results = await publicVotingPage.getVoteResults();
      expect(results.length).toBeGreaterThan(0);

      // Verify results are readable on mobile
      const resultsValidation = await publicVotingPage.validateMobileResults();
      expect(resultsValidation.textReadable).toBe(true);
      expect(resultsValidation.barsVisible).toBe(true);
      expect(resultsValidation.percentagesVisible).toBe(true);
    });

    test('should support mobile touch voting', async ({ page }) => {
      await publicVotingPage.gotoPublicVote('test-touch-vote');
      await page.setViewportSize({ width: 375, height: 667 });

      const mobileValidation = await publicVotingPage.validateMobileVoting();
      expect(mobileValidation.touchInteractions.length).toBeGreaterThan(0);

      // Test touch interactions if supported
      if (mobileValidation.touchInteractions.some(interaction => interaction.touchWorked)) {
        const touchTest = await publicVotingPage.validateTouchInteractions();
        expect(touchTest.some(interaction => interaction.touchWorked)).toBe(true);
      }

      // Test swipe gestures if supported
      if (mobileValidation.hasSwipeSupport.supported) {
        expect(mobileValidation.hasSwipeSupport.tested).toBe(true);
      }
    });
  });

  test.describe('Admin Interface Responsiveness', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/auth/test-login?user=admin&role=admin');
      await adminPage.goto();
    });

    test('should adapt admin interface for tablets and mobile', async ({ page }) => {
      const viewports = [
        { width: 768, height: 1024 }, // Tablet portrait
        { width: 1024, height: 768 }, // Tablet landscape
        { width: 375, height: 667 }   // Mobile
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(500);

        const adminValidation = await adminPage.validateResponsiveAdmin();

        expect(adminValidation.navigationAccessible).toBe(true);
        expect(adminValidation.contentReadable).toBe(true);
        expect(adminValidation.actionsAccessible).toBe(true);

        if (viewport.width < 768) {
          // Mobile admin should have condensed layout
          expect(adminValidation.hasCondensedLayout).toBe(true);
          expect(adminValidation.hasCollapsibleSections).toBe(true);
        }
      }
    });

    test('should handle data tables responsively', async ({ page }) => {
      await adminPage.navigateToAdminSection('users');

      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      const tableValidation = await adminPage.validateResponsiveDataTable();

      expect(tableValidation.horizontalScrollProvided).toBe(true);
      expect(tableValidation.essentialColumnsVisible).toBe(true);
      expect(tableValidation.actionButtonsAccessible).toBe(true);

      // Test table interaction on mobile
      const users = await adminPage.getUserList();
      if (users.length > 0) {
        // Should be able to perform actions on mobile
        const mobileActionResult = await adminPage.testMobileTableActions();
        expect(mobileActionResult.actionsPerformable).toBe(true);
      }
    });

    test('should maintain admin form usability on mobile', async ({ page }) => {
      await adminPage.navigateToAdminSection('settings');
      await page.setViewportSize({ width: 375, height: 667 });

      const formValidation = await adminPage.validateMobileAdminForms();

      expect(formValidation.fieldsStackVertically).toBe(true);
      expect(formValidation.labelsVisible).toBe(true);
      expect(formValidation.submitButtonAccessible).toBe(true);

      // Test form interaction
      const settings = {
        siteTitle: 'Mobile Test Title'
      };

      const updateResult = await adminPage.updateSystemSettings(settings);
      expect(updateResult.success).toBe(true);
    });
  });

  test.describe('Cross-Device Consistency', () => {
    test('should maintain visual consistency across devices', async ({ page }) => {
      await landingPage.goto();

      const devices = [
        { width: 375, height: 667, name: 'iPhone' },
        { width: 768, height: 1024, name: 'iPad' },
        { width: 1200, height: 800, name: 'Desktop' }
      ];

      const consistencyResults = {};

      for (const device of devices) {
        await page.setViewportSize(device);
        await page.waitForTimeout(500);

        const visualValidation = await landingPage.validateVisualConsistency();

        consistencyResults[device.name] = {
          colorsConsistent: visualValidation.colorsConsistent,
          typographyConsistent: visualValidation.typographyConsistent,
          spacingConsistent: visualValidation.spacingConsistent,
          brandingVisible: visualValidation.brandingVisible
        };

        expect(visualValidation.colorsConsistent).toBe(true);
        expect(visualValidation.brandingVisible).toBe(true);
      }

      // Compare consistency across devices
      const allDevicesConsistent = Object.values(consistencyResults).every(result =>
        result.colorsConsistent && result.brandingVisible
      );
      expect(allDevicesConsistent).toBe(true);
    });

    test('should maintain feature parity across form factors', async ({ page }) => {
      const testScenarios = [
        {
          viewport: { width: 375, height: 667 },
          name: 'mobile',
          requiredFeatures: ['authentication', 'voting', 'results']
        },
        {
          viewport: { width: 768, height: 1024 },
          name: 'tablet',
          requiredFeatures: ['authentication', 'voting', 'results', 'creation']
        },
        {
          viewport: { width: 1200, height: 800 },
          name: 'desktop',
          requiredFeatures: ['authentication', 'voting', 'results', 'creation', 'admin']
        }
      ];

      for (const scenario of testScenarios) {
        await page.setViewportSize(scenario.viewport);
        await page.waitForTimeout(500);

        const featureValidation = await landingPage.validateFeatureAvailability();

        scenario.requiredFeatures.forEach(feature => {
          expect(featureValidation[feature]).toBe(true);
        });
      }
    });
  });

  test.describe('Performance Impact of Responsive Design', () => {
    test('should maintain performance across viewport changes', async ({ page }) => {
      await landingPage.goto();

      const viewportChanges = [
        { width: 1200, height: 800 },
        { width: 375, height: 667 },
        { width: 768, height: 1024 },
        { width: 1024, height: 768 }
      ];

      const performanceMetrics = [];

      for (const viewport of viewportChanges) {
        const startTime = Date.now();

        await page.setViewportSize(viewport);
        await page.waitForLoadState('networkidle');

        const resizeTime = Date.now() - startTime;
        performanceMetrics.push({ viewport, resizeTime });

        expect(resizeTime).toBeLessThan(1000); // Should resize quickly
      }

      // Performance shouldn't degrade significantly
      const avgResizeTime = performanceMetrics.reduce((sum, m) => sum + m.resizeTime, 0) / performanceMetrics.length;
      expect(avgResizeTime).toBeLessThan(500);
    });

    test('should optimize resource loading for mobile', async ({ page }) => {
      // Mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      const mobileLoadStart = Date.now();
      await landingPage.goto();
      const mobileLoadTime = Date.now() - mobileLoadStart;

      // Desktop viewport
      await page.setViewportSize({ width: 1200, height: 800 });

      const desktopLoadStart = Date.now();
      await landingPage.goto();
      const desktopLoadTime = Date.now() - desktopLoadStart;

      // Mobile should not be significantly slower
      expect(mobileLoadTime / desktopLoadTime).toBeLessThan(1.5);

      // Both should meet performance thresholds
      expect(mobileLoadTime).toBeLessThan(5000);
      expect(desktopLoadTime).toBeLessThan(3000);
    });
  });

  test.describe('Responsive Accessibility', () => {
    test('should maintain accessibility across screen sizes', async ({ page }) => {
      await landingPage.goto();

      const viewports = [
        { width: 375, height: 667 },
        { width: 768, height: 1024 },
        { width: 1200, height: 800 }
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(500);

        const accessibility = await landingPage.validateAccessibility();

        expect(accessibility.keyboardNavigation.tabNavigationWorks).toBe(true);
        expect(accessibility.focusManagement.focusableElementCount).toBeGreaterThan(0);
        expect(accessibility.semanticStructure.hasMainContent).toBe(true);

        // Test focus indicators are visible at all sizes
        const focusVisibility = await landingPage.validateFocusVisibilityAtSize(viewport);
        expect(focusVisibility.focusIndicatorsVisible).toBe(true);
      }
    });

    test('should support zoom up to 200% without loss of functionality', async ({ page }) => {
      await landingPage.goto();

      // Test different zoom levels
      const zoomLevels = [1.0, 1.5, 2.0];

      for (const zoom of zoomLevels) {
        await page.evaluate((zoomLevel) => {
          document.body.style.zoom = zoomLevel;
        }, zoom);

        await page.waitForTimeout(500);

        const zoomValidation = await landingPage.validateZoomAccessibility();

        expect(zoomValidation.contentReadable).toBe(true);
        expect(zoomValidation.navigationUsable).toBe(true);
        expect(zoomValidation.noHorizontalScroll).toBe(true);

        // Test essential functionality still works
        const functionalityTest = await landingPage.testEssentialFunctionalityAtZoom();
        expect(functionalityTest.signInAccessible).toBe(true);
        expect(functionalityTest.getStartedAccessible).toBe(true);
      }

      // Reset zoom
      await page.evaluate(() => {
        document.body.style.zoom = 1.0;
      });
    });
  });
});
