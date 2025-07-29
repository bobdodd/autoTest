/*
 * AutoTest - Help System and Tooltips
 * Contextual help, tooltips, and documentation system
 */

(function() {
  'use strict';

  // Check if AutoTest utilities are available
  if (!window.AutoTest || !window.AutoTest.A11y) {
    console.error('AutoTest utilities not available');
    return;
  }

  const A11y = window.AutoTest.A11y;

  /**
   * Help System Manager
   */
  const HelpSystem = {
    // Help content registry
    helpContent: new Map(),
    
    // Tooltip registry
    tooltips: new Map(),
    
    // Current active tooltip
    activeTooltip: null,
    
    // Help modal state
    helpModalOpen: false,
    
    // Settings
    settings: {
      tooltipDelay: 500,
      tooltipDismissDelay: 3000,
      enableContextualHelp: true,
      enableTooltips: true,
      enableHelpHints: true
    },

    /**
     * Initialize the help system
     */
    init: function() {
      this.registerHelpContent();
      this.setupTooltips();
      this.setupContextualHelp();
      this.setupHelpModals();
      this.setupKeyboardShortcuts();
      this.setupHelpHints();
      
      // Announce help system is ready
      setTimeout(() => {
        A11y.announce('Help system activated. Press F1 for contextual help, Alt+H for keyboard shortcuts.');
      }, 1500);
    },

    /**
     * Register help content for different contexts
     */
    registerHelpContent: function() {
      // Dashboard help
      this.helpContent.set('dashboard', {
        title: 'Dashboard Overview',
        content: `
          <p>The dashboard provides an overview of your accessibility testing activities:</p>
          <ul>
            <li><strong>Recent Projects:</strong> Quick access to your most recently worked on projects</li>
            <li><strong>Test Statistics:</strong> Overview of completed tests and identified issues</li>
            <li><strong>Quick Actions:</strong> Fast access to common tasks like creating new projects or running tests</li>
            <li><strong>Recent Activity:</strong> Timeline of recent testing activities and results</li>
          </ul>
        `,
        shortcuts: [
          { key: 'G H', action: 'Go to dashboard' },
          { key: 'N', action: 'Create new project' },
          { key: 'R', action: 'Run quick test' }
        ]
      });

      // Projects help
      this.helpContent.set('projects', {
        title: 'Project Management',
        content: `
          <p>Projects help you organize your accessibility testing efforts:</p>
          <ul>
            <li><strong>Create Project:</strong> Set up a new accessibility testing project with websites and configuration</li>
            <li><strong>Project Settings:</strong> Configure test parameters, schedules, and notification preferences</li>
            <li><strong>Website Management:</strong> Add, edit, and organize websites within your project</li>
            <li><strong>Test History:</strong> View historical test results and track improvement over time</li>
          </ul>
        `,
        shortcuts: [
          { key: 'G P', action: 'Go to projects' },
          { key: 'N', action: 'Create new project' },
          { key: 'E', action: 'Edit selected project' }
        ]
      });

      // Testing help
      this.helpContent.set('testing', {
        title: 'Accessibility Testing',
        content: `
          <p>Our testing system evaluates websites against WCAG 2.1 guidelines:</p>
          <ul>
            <li><strong>Automated Tests:</strong> Run comprehensive accessibility scans using industry-standard tools</li>
            <li><strong>Manual Review:</strong> Guided manual testing for issues that require human evaluation</li>
            <li><strong>Test Results:</strong> Detailed reports with violation descriptions, severity levels, and remediation guidance</li>
            <li><strong>Compliance Reports:</strong> Generate formal compliance reports for stakeholders</li>
          </ul>
        `,
        shortcuts: [
          { key: 'G T', action: 'Go to testing' },
          { key: 'R', action: 'Run test' },
          { key: 'V', action: 'View results' }
        ]
      });

      // Reports help
      this.helpContent.set('reports', {
        title: 'Reporting System',
        content: `
          <p>Generate comprehensive accessibility reports:</p>
          <ul>
            <li><strong>Executive Summary:</strong> High-level overview for stakeholders and decision makers</li>
            <li><strong>Technical Report:</strong> Detailed technical findings for developers and designers</li>
            <li><strong>Compliance Audit:</strong> Formal compliance documentation for legal and regulatory requirements</li>
            <li><strong>Progress Tracking:</strong> Historical analysis showing improvement over time</li>
          </ul>
        `,
        shortcuts: [
          { key: 'G R', action: 'Go to reports' },
          { key: 'N', action: 'Generate new report' },
          { key: 'D', action: 'Download report' }
        ]
      });

      // Form help
      this.helpContent.set('forms', {
        title: 'Form Navigation',
        content: `
          <p>Tips for efficient form navigation:</p>
          <ul>
            <li><strong>Tab Navigation:</strong> Use Tab to move forward, Shift+Tab to move backward between fields</li>
            <li><strong>Field Validation:</strong> Invalid fields will be announced with specific error messages</li>
            <li><strong>Required Fields:</strong> Required fields are marked with asterisks (*) and announced by screen readers</li>
            <li><strong>Field Help:</strong> Many fields have additional help text available via tooltips</li>
          </ul>
        `,
        shortcuts: [
          { key: 'Tab', action: 'Next field' },
          { key: 'Shift+Tab', action: 'Previous field' },
          { key: 'Enter', action: 'Submit form' }
        ]
      });

      // Table help
      this.helpContent.set('tables', {
        title: 'Table Navigation',
        content: `
          <p>Efficiently navigate data tables:</p>
          <ul>
            <li><strong>Cell Navigation:</strong> Use Ctrl+Arrow keys to move between cells</li>
            <li><strong>Row Selection:</strong> Click checkboxes or use Space to select/deselect rows</li>
            <li><strong>Column Sorting:</strong> Click column headers to sort data</li>
            <li><strong>Filtering:</strong> Use search and filter controls to find specific data</li>
          </ul>
        `,
        shortcuts: [
          { key: 'Ctrl+→', action: 'Next cell' },
          { key: 'Ctrl+←', action: 'Previous cell' },
          { key: 'Ctrl+↑', action: 'Cell above' },
          { key: 'Ctrl+↓', action: 'Cell below' }
        ]
      });
    },

    /**
     * Setup tooltip system
     */
    setupTooltips: function() {
      if (!this.settings.enableTooltips) return;

      // Find all elements with tooltip attributes
      const tooltipElements = document.querySelectorAll('[data-tooltip], [title]');
      
      tooltipElements.forEach(element => {
        this.initializeTooltip(element);
      });

      // Setup dynamic tooltip observation
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const tooltipElements = node.querySelectorAll('[data-tooltip], [title]');
              tooltipElements.forEach(element => {
                this.initializeTooltip(element);
              });
            }
          });
        });
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    },

    /**
     * Initialize tooltip for an element
     */
    initializeTooltip: function(element) {
      // Convert title attribute to data-tooltip for better control
      if (element.hasAttribute('title') && !element.hasAttribute('data-tooltip')) {
        element.setAttribute('data-tooltip', element.getAttribute('title'));
        element.removeAttribute('title');
      }

      const tooltipText = element.getAttribute('data-tooltip');
      if (!tooltipText) return;

      // Add ARIA attributes
      const tooltipId = `tooltip-${Math.random().toString(36).substr(2, 9)}`;
      element.setAttribute('aria-describedby', tooltipId);

      let showTimer = null;
      let hideTimer = null;

      // Mouse events
      element.addEventListener('mouseenter', () => {
        if (hideTimer) {
          clearTimeout(hideTimer);
          hideTimer = null;
        }
        
        showTimer = setTimeout(() => {
          this.showTooltip(element, tooltipText, tooltipId);
        }, this.settings.tooltipDelay);
      });

      element.addEventListener('mouseleave', () => {
        if (showTimer) {
          clearTimeout(showTimer);
          showTimer = null;
        }
        
        hideTimer = setTimeout(() => {
          this.hideTooltip(tooltipId);
        }, 100);
      });

      // Focus events for keyboard users
      element.addEventListener('focus', () => {
        this.showTooltip(element, tooltipText, tooltipId);
      });

      element.addEventListener('blur', () => {
        setTimeout(() => {
          this.hideTooltip(tooltipId);
        }, 100);
      });

      // Store tooltip reference
      this.tooltips.set(tooltipId, {
        element: element,
        text: tooltipText,
        id: tooltipId
      });
    },

    /**
     * Show tooltip
     */
    showTooltip: function(element, text, tooltipId) {
      // Remove any existing tooltip
      this.hideAllTooltips();

      const tooltip = document.createElement('div');
      tooltip.id = tooltipId;
      tooltip.className = 'tooltip';
      tooltip.setAttribute('role', 'tooltip');
      tooltip.textContent = text;

      document.body.appendChild(tooltip);

      // Position tooltip
      this.positionTooltip(tooltip, element);

      // Set active tooltip
      this.activeTooltip = tooltip;

      // Auto-hide after delay
      setTimeout(() => {
        if (this.activeTooltip === tooltip) {
          this.hideTooltip(tooltipId);
        }
      }, this.settings.tooltipDismissDelay);

      // Announce to screen readers
      A11y.announce(`Tooltip: ${text}`, 'polite');
    },

    /**
     * Position tooltip relative to element
     */
    positionTooltip: function(tooltip, element) {
      const elementRect = element.getBoundingClientRect();
      const tooltipRect = tooltip.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      let top = elementRect.bottom + 8;
      let left = elementRect.left + (elementRect.width / 2) - (tooltipRect.width / 2);

      // Adjust if tooltip goes off screen
      if (left < 8) {
        left = 8;
      } else if (left + tooltipRect.width > viewportWidth - 8) {
        left = viewportWidth - tooltipRect.width - 8;
      }

      // If tooltip goes below viewport, show above element
      if (top + tooltipRect.height > viewportHeight - 8) {
        top = elementRect.top - tooltipRect.height - 8;
      }

      tooltip.style.position = 'fixed';
      tooltip.style.top = `${top}px`;
      tooltip.style.left = `${left}px`;
      tooltip.style.zIndex = '10000';
    },

    /**
     * Hide specific tooltip
     */
    hideTooltip: function(tooltipId) {
      const tooltip = document.getElementById(tooltipId);
      if (tooltip) {
        tooltip.remove();
        if (this.activeTooltip === tooltip) {
          this.activeTooltip = null;
        }
      }
    },

    /**
     * Hide all tooltips
     */
    hideAllTooltips: function() {
      const tooltips = document.querySelectorAll('.tooltip');
      tooltips.forEach(tooltip => tooltip.remove());
      this.activeTooltip = null;
    },

    /**
     * Setup contextual help system
     */
    setupContextualHelp: function() {
      if (!this.settings.enableContextualHelp) return;

      // F1 key for contextual help
      document.addEventListener('keydown', (e) => {
        if (e.key === 'F1') {
          e.preventDefault();
          this.showContextualHelp(e.target);
        }
      });

      // Help buttons
      document.addEventListener('click', (e) => {
        if (e.target.matches('[data-help-trigger]')) {
          e.preventDefault();
          const context = e.target.getAttribute('data-help-trigger');
          this.showHelpModal(context);
        }
      });
    },

    /**
     * Show contextual help based on current element
     */
    showContextualHelp: function(element) {
      let context = 'general';

      // Determine context based on element
      if (element.closest('[data-help-context]')) {
        context = element.closest('[data-help-context]').getAttribute('data-help-context');
      } else if (element.closest('form')) {
        context = 'forms';
      } else if (element.closest('table')) {
        context = 'tables';
      } else if (element.closest('.dashboard')) {
        context = 'dashboard';
      } else if (window.location.pathname.includes('/projects')) {
        context = 'projects';
      } else if (window.location.pathname.includes('/testing')) {
        context = 'testing';
      } else if (window.location.pathname.includes('/reports')) {
        context = 'reports';
      }

      this.showHelpModal(context);
    },

    /**
     * Setup help modal functionality
     */
    setupHelpModals: function() {
      // Add event listeners for modal triggers
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.helpModalOpen) {
          this.closeHelpModal();
        }
      });
    },

    /**
     * Show help modal for specific context
     */
    showHelpModal: function(context) {
      const helpData = this.helpContent.get(context);
      
      if (!helpData) {
        A11y.announce('No specific help available for this context. Press Alt+H for keyboard shortcuts.');
        return;
      }

      const modal = this.createHelpModal(helpData);
      document.body.appendChild(modal);

      // Focus the modal
      const firstButton = modal.querySelector('button');
      if (firstButton) {
        firstButton.focus();
      }

      this.helpModalOpen = true;
      A11y.trapFocus(modal);
      A11y.announce(`${helpData.title} help opened`);
    },

    /**
     * Create help modal
     */
    createHelpModal: function(helpData) {
      const modal = document.createElement('div');
      modal.className = 'help-modal';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-labelledby', 'help-modal-title');
      modal.setAttribute('aria-modal', 'true');

      let shortcutsHtml = '';
      if (helpData.shortcuts && helpData.shortcuts.length > 0) {
        shortcutsHtml = `
          <div class="help-shortcuts">
            <h3>Keyboard Shortcuts</h3>
            <dl class="shortcut-list">
              ${helpData.shortcuts.map(shortcut => `
                <dt>${shortcut.key}</dt>
                <dd>${shortcut.action}</dd>
              `).join('')}
            </dl>
          </div>
        `;
      }

      modal.innerHTML = `
        <div class="modal-backdrop"></div>
        <div class="modal-content">
          <div class="modal-header">
            <h2 id="help-modal-title">${helpData.title}</h2>
            <button type="button" class="modal-close" aria-label="Close help">×</button>
          </div>
          <div class="modal-body">
            <div class="help-content">
              ${helpData.content}
            </div>
            ${shortcutsHtml}
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" id="help-more-info">More Information</button>
            <button type="button" class="btn btn-primary modal-close">Got it</button>
          </div>
        </div>
      `;

      // Handle modal close
      const closeButtons = modal.querySelectorAll('.modal-close');
      closeButtons.forEach(button => {
        button.addEventListener('click', () => {
          modal.remove();
          this.helpModalOpen = false;
          A11y.announce('Help closed');
        });
      });

      // Handle more info button
      const moreInfoBtn = modal.querySelector('#help-more-info');
      if (moreInfoBtn) {
        moreInfoBtn.addEventListener('click', () => {
          this.showDetailedHelp();
        });
      }

      // Close on backdrop click
      modal.querySelector('.modal-backdrop').addEventListener('click', () => {
        modal.remove();
        this.helpModalOpen = false;
      });

      // Close on Escape key
      modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          modal.remove();
          this.helpModalOpen = false;
          A11y.announce('Help closed');
        }
      });

      return modal;
    },

    /**
     * Close help modal
     */
    closeHelpModal: function() {
      const modal = document.querySelector('.help-modal');
      if (modal) {
        modal.remove();
        this.helpModalOpen = false;
        A11y.announce('Help closed');
      }
    },

    /**
     * Setup keyboard shortcuts for help system
     */
    setupKeyboardShortcuts: function() {
      document.addEventListener('keydown', (e) => {
        // Alt+H for help overview
        if (e.altKey && (e.key === 'h' || e.key === 'H') && !this.helpModalOpen) {
          e.preventDefault();
          if (window.AutoTest && window.AutoTest.KeyboardNavigation) {
            window.AutoTest.KeyboardNavigation.showKeyboardHelp();
          }
        }

        // Escape to close tooltips
        if (e.key === 'Escape' && this.activeTooltip) {
          this.hideAllTooltips();
        }
      });
    },

    /**
     * Setup help hints system
     */
    setupHelpHints: function() {
      if (!this.settings.enableHelpHints) return;

      // Show help hints for first-time users
      if (!localStorage.getItem('autotest-help-hints-dismissed')) {
        this.showHelpHints();
      }

      // Add help hint triggers
      this.addHelpHintTriggers();
    },

    /**
     * Add help hint triggers to page elements
     */
    addHelpHintTriggers: function() {
      // Add help buttons to complex interfaces
      const complexElements = document.querySelectorAll('form, table, .dashboard-widget');
      
      complexElements.forEach(element => {
        if (!element.querySelector('.help-trigger')) {
          const helpButton = document.createElement('button');
          helpButton.type = 'button';
          helpButton.className = 'help-trigger';
          helpButton.setAttribute('aria-label', 'Get help for this section');
          helpButton.setAttribute('data-tooltip', 'Click for help or press F1');
          helpButton.innerHTML = `
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16">
              <circle cx="8" cy="8" r="7" stroke="currentColor" fill="none" stroke-width="1.5"/>
              <path d="M6.5 6.5A1.5 1.5 0 018 5c.83 0 1.5.67 1.5 1.5 0 .83-.67 1.5-1.5 1.5" stroke="currentColor" fill="none" stroke-width="1.5"/>
              <circle cx="8" cy="11" r="0.5" fill="currentColor"/>
            </svg>
          `;

          // Determine context for help button
          let context = 'general';
          if (element.matches('form')) {
            context = 'forms';
            helpButton.setAttribute('data-help-trigger', 'forms');
          } else if (element.matches('table')) {
            context = 'tables';
            helpButton.setAttribute('data-help-trigger', 'tables');
          } else if (element.matches('.dashboard-widget')) {
            context = 'dashboard';
            helpButton.setAttribute('data-help-trigger', 'dashboard');
          }

          // Position help button
          if (element.matches('form')) {
            const fieldset = element.querySelector('fieldset') || element;
            const legend = fieldset.querySelector('legend') || fieldset.querySelector('h1, h2, h3');
            if (legend) {
              legend.style.position = 'relative';
              helpButton.style.position = 'absolute';
              helpButton.style.right = '0';
              helpButton.style.top = '0';
              legend.appendChild(helpButton);
            }
          } else {
            element.style.position = 'relative';
            helpButton.style.position = 'absolute';
            helpButton.style.top = '8px';
            helpButton.style.right = '8px';
            element.appendChild(helpButton);
          }

          // Initialize tooltip for help button
          this.initializeTooltip(helpButton);
        }
      });
    },

    /**
     * Show initial help hints
     */
    showHelpHints: function() {
      const hint = document.createElement('div');
      hint.className = 'help-hint';
      hint.setAttribute('role', 'dialog');
      hint.setAttribute('aria-labelledby', 'hint-title');
      hint.innerHTML = `
        <div class="hint-content">
          <h3 id="hint-title">Welcome to AutoTest!</h3>
          <p>Here are some ways to get help:</p>
          <ul>
            <li>Press <kbd>F1</kbd> for contextual help</li>
            <li>Press <kbd>Alt+H</kbd> for keyboard shortcuts</li>
            <li>Look for <span class="help-icon">?</span> icons next to complex features</li>
            <li>Hover over elements for helpful tooltips</li>
          </ul>
          <div class="hint-actions">
            <button type="button" class="btn btn-secondary" id="dismiss-hints">Don't show again</button>
            <button type="button" class="btn btn-primary" id="close-hint">Got it</button>
          </div>
        </div>
      `;

      document.body.appendChild(hint);

      // Handle hint actions
      document.getElementById('dismiss-hints').addEventListener('click', () => {
        localStorage.setItem('autotest-help-hints-dismissed', 'true');
        hint.remove();
        A11y.announce('Help hints disabled');
      });

      document.getElementById('close-hint').addEventListener('click', () => {
        hint.remove();
        A11y.announce('Welcome hint closed');
      });

      // Auto-remove after 10 seconds
      setTimeout(() => {
        if (document.contains(hint)) {
          hint.remove();
        }
      }, 10000);

      A11y.announce('Welcome! Help hints are available. Press Alt+H for keyboard shortcuts.');
    },

    /**
     * Show detailed help documentation
     */
    showDetailedHelp: function() {
      // Navigate to comprehensive help page
      window.location.href = '/help';
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => HelpSystem.init());
  } else {
    HelpSystem.init();
  }

  // Export for use by other scripts
  window.AutoTest = window.AutoTest || {};
  window.AutoTest.HelpSystem = HelpSystem;

})();