/*
 * AutoTest - Screen Reader Announcements
 * Enhanced screen reader support for dynamic content and interactions
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
   * Enhanced Screen Reader Manager
   */
  const ScreenReader = {
    // Live regions for different types of announcements
    liveRegions: {
      polite: null,
      assertive: null,
      status: null
    },

    // Queue for managing announcements
    announcementQueue: [],
    isProcessingQueue: false,

    // Settings
    settings: {
      enableDynamicAnnouncements: true,
      enableNavigationAnnouncements: true,
      enableFormAnnouncements: true,
      enableProgressAnnouncements: true,
      enableErrorAnnouncements: true,
      announcementDelay: 100,
      queueDelay: 1500
    },

    /**
     * Initialize screen reader enhancements
     */
    init: function() {
      this.createLiveRegions();
      this.setupDynamicContentObserver();
      this.setupFormAnnouncements();
      this.setupNavigationAnnouncements();
      this.setupProgressAnnouncements();
      this.setupErrorAnnouncements();
      this.setupLoadingAnnouncements();
      this.setupDataTableAnnouncements();
      
      // Announce that screen reader enhancements are active
      setTimeout(() => {
        this.announce('Screen reader enhancements activated', 'polite');
      }, 1000);
    },

    /**
     * Create permanent live regions for announcements
     */
    createLiveRegions: function() {
      // Polite announcements (non-interrupting)
      this.liveRegions.polite = document.createElement('div');
      this.liveRegions.polite.setAttribute('aria-live', 'polite');
      this.liveRegions.polite.setAttribute('aria-atomic', 'true');
      this.liveRegions.polite.className = 'sr-only';
      this.liveRegions.polite.id = 'sr-live-polite';
      document.body.appendChild(this.liveRegions.polite);

      // Assertive announcements (interrupting)
      this.liveRegions.assertive = document.createElement('div');
      this.liveRegions.assertive.setAttribute('aria-live', 'assertive');
      this.liveRegions.assertive.setAttribute('aria-atomic', 'true');
      this.liveRegions.assertive.className = 'sr-only';
      this.liveRegions.assertive.id = 'sr-live-assertive';
      document.body.appendChild(this.liveRegions.assertive);

      // Status announcements
      this.liveRegions.status = document.createElement('div');
      this.liveRegions.status.setAttribute('role', 'status');
      this.liveRegions.status.setAttribute('aria-atomic', 'true');
      this.liveRegions.status.className = 'sr-only';
      this.liveRegions.status.id = 'sr-status';
      document.body.appendChild(this.liveRegions.status);
    },

    /**
     * Enhanced announcement method with queueing
     */
    announce: function(message, priority = 'polite', options = {}) {
      if (!this.settings.enableDynamicAnnouncements) return;

      const announcement = {
        message: this.sanitizeMessage(message),
        priority: priority,
        timestamp: Date.now(),
        options: {
          delay: options.delay || this.settings.announcementDelay,
          clearPrevious: options.clearPrevious || false,
          context: options.context || null
        }
      };

      // Add to queue
      this.announcementQueue.push(announcement);
      
      // Process queue if not already processing
      if (!this.isProcessingQueue) {
        this.processAnnouncementQueue();
      }
    },

    /**
     * Process the announcement queue
     */
    processAnnouncementQueue: function() {
      if (this.announcementQueue.length === 0) {
        this.isProcessingQueue = false;
        return;
      }

      this.isProcessingQueue = true;
      const announcement = this.announcementQueue.shift();

      setTimeout(() => {
        this.makeAnnouncement(announcement);
        
        // Process next announcement after delay
        setTimeout(() => {
          this.processAnnouncementQueue();
        }, this.settings.queueDelay);
        
      }, announcement.options.delay);
    },

    /**
     * Make the actual announcement
     */
    makeAnnouncement: function(announcement) {
      const region = this.liveRegions[announcement.priority] || this.liveRegions.polite;
      
      if (announcement.options.clearPrevious) {
        region.textContent = '';
        // Force screen reader to notice the change
        setTimeout(() => {
          region.textContent = announcement.message;
        }, 10);
      } else {
        region.textContent = announcement.message;
      }

      // Log for debugging
      console.log(`[SR] ${announcement.priority.toUpperCase()}: ${announcement.message}`);
    },

    /**
     * Setup dynamic content observer
     */
    setupDynamicContentObserver: function() {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList') {
            this.handleContentChanges(mutation);
          } else if (mutation.type === 'attributes') {
            this.handleAttributeChanges(mutation);
          }
        });
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['aria-expanded', 'aria-selected', 'aria-checked', 'hidden', 'disabled']
      });
    },

    /**
     * Handle content changes
     */
    handleContentChanges: function(mutation) {
      // Check for new content additions
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          this.announceNewContent(node);
        }
      });

      // Check for content removals
      if (mutation.removedNodes.length > 0) {
        const removedCount = Array.from(mutation.removedNodes).filter(
          node => node.nodeType === Node.ELEMENT_NODE
        ).length;
        
        if (removedCount > 0) {
          this.announce(`${removedCount} item${removedCount === 1 ? '' : 's'} removed`, 'polite');
        }
      }
    },

    /**
     * Handle attribute changes
     */
    handleAttributeChanges: function(mutation) {
      const element = mutation.target;
      const attributeName = mutation.attributeName;

      switch(attributeName) {
        case 'aria-expanded':
          this.announceExpandedChange(element);
          break;
        case 'aria-selected':
          this.announceSelectedChange(element);
          break;
        case 'aria-checked':
          this.announceCheckedChange(element);
          break;
        case 'hidden':
          this.announceVisibilityChange(element);
          break;
        case 'disabled':
          this.announceDisabledChange(element);
          break;
      }
    },

    /**
     * Announce new content
     */
    announceNewContent: function(element) {
      // Skip if element is not visible or is for screen readers only
      if (element.classList && (element.classList.contains('sr-only') || 
          element.offsetParent === null)) {
        return;
      }

      // Specific content type announcements
      if (element.matches('.flash-message, .alert')) {
        this.announceAlert(element);
      } else if (element.matches('[role="dialog"], .modal')) {
        this.announceModal(element);
      } else if (element.matches('.search-results, [role="region"]')) {
        this.announceRegion(element);
      } else if (element.matches('table')) {
        this.announceTable(element);
      } else if (element.matches('.pagination')) {
        this.announcePagination(element);
      } else if (element.matches('.test-results, .violation-list')) {
        this.announceResults(element);
      }
    },

    /**
     * Announce alerts and flash messages
     */
    announceAlert: function(element) {
      const type = this.getAlertType(element);
      const message = this.getTextContent(element);
      
      this.announce(`${type}: ${message}`, 'assertive', {
        context: 'alert',
        clearPrevious: true
      });
    },

    /**
     * Announce modal dialogs
     */
    announceModal: function(element) {
      const title = element.querySelector('h1, h2, h3, [role="heading"]');
      const titleText = title ? this.getTextContent(title) : 'Dialog';
      
      this.announce(`${titleText} dialog opened`, 'assertive', {
        context: 'modal'
      });
    },

    /**
     * Announce regions and search results
     */
    announceRegion: function(element) {
      const label = element.getAttribute('aria-label') || 
                   element.getAttribute('aria-labelledby') ||
                   'Content region';
      
      const itemCount = element.querySelectorAll('li, tr, .item, .result').length;
      
      if (itemCount > 0) {
        this.announce(`${label} updated with ${itemCount} item${itemCount === 1 ? '' : 's'}`, 'polite', {
          context: 'region'
        });
      } else {
        this.announce(`${label} updated`, 'polite', {
          context: 'region'
        });
      }
    },

    /**
     * Announce tables
     */
    announceTable: function(element) {
      const caption = element.querySelector('caption');
      const rows = element.querySelectorAll('tbody tr').length;
      const cols = element.querySelectorAll('thead th').length;
      
      let announcement = caption ? 
        `Table: ${this.getTextContent(caption)}` : 
        'Data table';
      
      if (rows > 0) {
        announcement += ` with ${rows} row${rows === 1 ? '' : 's'}`;
      }
      
      if (cols > 0) {
        announcement += ` and ${cols} column${cols === 1 ? '' : 's'}`;
      }
      
      this.announce(announcement, 'polite', {
        context: 'table'
      });
    },

    /**
     * Setup form announcements
     */
    setupFormAnnouncements: function() {
      if (!this.settings.enableFormAnnouncements) return;

      // Form submission announcements
      document.addEventListener('submit', (e) => {
        const form = e.target;
        const formName = form.getAttribute('aria-label') || 
                        form.querySelector('h1, h2, legend')?.textContent || 
                        'Form';
        
        this.announce(`${formName} submitted`, 'assertive', {
          context: 'form'
        });
      });

      // Form validation announcements
      document.addEventListener('invalid', (e) => {
        const field = e.target;
        const label = this.getFieldLabel(field);
        const validationMessage = field.validationMessage;
        
        this.announce(`${label}: ${validationMessage}`, 'assertive', {
          context: 'validation'
        });
      });

      // Field change announcements for complex widgets
      document.addEventListener('change', (e) => {
        const element = e.target;
        
        if (element.matches('select')) {
          this.announceSelectChange(element);
        } else if (element.matches('input[type="checkbox"]')) {
          this.announceCheckboxChange(element);
        } else if (element.matches('input[type="radio"]')) {
          this.announceRadioChange(element);
        }
      });
    },

    /**
     * Setup navigation announcements
     */
    setupNavigationAnnouncements: function() {
      if (!this.settings.enableNavigationAnnouncements) return;

      // Page navigation
      let currentPath = window.location.pathname;
      
      // Listen for programmatic navigation
      const originalPushState = history.pushState;
      const originalReplaceState = history.replaceState;
      
      history.pushState = function(...args) {
        originalPushState.apply(history, args);
        ScreenReader.announcePageChange();
      };
      
      history.replaceState = function(...args) {
        originalReplaceState.apply(history, args);
        ScreenReader.announcePageChange();
      };
      
      window.addEventListener('popstate', () => {
        this.announcePageChange();
      });

      // Breadcrumb navigation
      const breadcrumbObserver = new MutationObserver(() => {
        const breadcrumbs = document.querySelector('.breadcrumb, [aria-label*="breadcrumb" i]');
        if (breadcrumbs) {
          this.announceBreadcrumbChange(breadcrumbs);
        }
      });

      const breadcrumbContainer = document.querySelector('.breadcrumb, [aria-label*="breadcrumb" i]');
      if (breadcrumbContainer) {
        breadcrumbObserver.observe(breadcrumbContainer, {
          childList: true,
          subtree: true
        });
      }
    },

    /**
     * Setup progress announcements
     */
    setupProgressAnnouncements: function() {
      if (!this.settings.enableProgressAnnouncements) return;

      // Progress bars
      const progressElements = document.querySelectorAll('[role="progressbar"], progress');
      
      progressElements.forEach((progress) => {
        const observer = new MutationObserver(() => {
          this.announceProgressChange(progress);
        });
        
        observer.observe(progress, {
          attributes: true,
          attributeFilter: ['aria-valuenow', 'value']
        });
      });

      // Loading states
      const loadingObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.target.matches('.loading, [aria-busy="true"]')) {
            this.announceLoadingState(mutation.target);
          }
        });
      });

      loadingObserver.observe(document.body, {
        attributes: true,
        attributeFilter: ['aria-busy', 'class'],
        subtree: true
      });
    },

    /**
     * Setup error announcements
     */
    setupErrorAnnouncements: function() {
      if (!this.settings.enableErrorAnnouncements) return;

      // AJAX error handling
      document.addEventListener('ajaxError', (e) => {
        this.announce('An error occurred while loading content. Please try again.', 'assertive', {
          context: 'error'
        });
      });

      // JavaScript errors
      window.addEventListener('error', (e) => {
        // Only announce user-facing errors, not development errors
        if (e.error && e.error.userFacing) {
          this.announce(e.error.message || 'An unexpected error occurred', 'assertive', {
            context: 'error'
          });
        }
      });
    },

    /**
     * Setup loading announcements
     */
    setupLoadingAnnouncements: function() {
      // Monitor AJAX requests
      const originalFetch = window.fetch;
      
      window.fetch = function(...args) {
        ScreenReader.announce('Loading content', 'polite', {
          context: 'loading'
        });
        
        return originalFetch.apply(this, args)
          .then(response => {
            if (response.ok) {
              ScreenReader.announce('Content loaded', 'polite', {
                context: 'loading'
              });
            } else {
              ScreenReader.announce('Failed to load content', 'assertive', {
                context: 'error'
              });
            }
            return response;
          })
          .catch(error => {
            ScreenReader.announce('Failed to load content', 'assertive', {
              context: 'error'
            });
            throw error;
          });
      };
    },

    /**
     * Setup data table announcements
     */
    setupDataTableAnnouncements: function() {
      // Sort announcements
      document.addEventListener('click', (e) => {
        if (e.target.matches('th[data-sort], [role="columnheader"][tabindex]')) {
          const sortDirection = e.target.getAttribute('aria-sort');
          const columnName = this.getTextContent(e.target);
          
          if (sortDirection) {
            this.announce(`Table sorted by ${columnName}, ${sortDirection}`, 'polite', {
              context: 'table'
            });
          }
        }
      });

      // Row selection announcements
      document.addEventListener('change', (e) => {
        if (e.target.matches('input[type="checkbox"]') && 
            e.target.closest('table')) {
          const isSelectAll = e.target.closest('thead') !== null;
          const isChecked = e.target.checked;
          
          if (isSelectAll) {
            this.announce(`${isChecked ? 'All' : 'No'} rows selected`, 'polite', {
              context: 'selection'
            });
          } else {
            const selectedCount = e.target.closest('table')
              .querySelectorAll('tbody input[type="checkbox"]:checked').length;
            
            this.announce(`${selectedCount} row${selectedCount === 1 ? '' : 's'} selected`, 'polite', {
              context: 'selection'
            });
          }
        }
      });
    },

    /**
     * Utility methods for specific announcements
     */
    announceExpandedChange: function(element) {
      const isExpanded = element.getAttribute('aria-expanded') === 'true';
      const label = this.getElementLabel(element);
      
      this.announce(`${label} ${isExpanded ? 'expanded' : 'collapsed'}`, 'polite', {
        context: 'interaction'
      });
    },

    announceSelectedChange: function(element) {
      const isSelected = element.getAttribute('aria-selected') === 'true';
      const label = this.getElementLabel(element);
      
      this.announce(`${label} ${isSelected ? 'selected' : 'deselected'}`, 'polite', {
        context: 'selection'
      });
    },

    announceCheckedChange: function(element) {
      const isChecked = element.getAttribute('aria-checked') === 'true';
      const label = this.getElementLabel(element);
      
      this.announce(`${label} ${isChecked ? 'checked' : 'unchecked'}`, 'polite', {
        context: 'form'
      });
    },

    announceVisibilityChange: function(element) {
      const isHidden = element.hasAttribute('hidden');
      const label = this.getElementLabel(element);
      
      this.announce(`${label} ${isHidden ? 'hidden' : 'shown'}`, 'polite', {
        context: 'visibility'
      });
    },

    announcePageChange: function() {
      const title = document.title;
      const main = document.querySelector('main h1, h1');
      const heading = main ? this.getTextContent(main) : title;
      
      this.announce(`Page changed to ${heading}`, 'assertive', {
        context: 'navigation',
        clearPrevious: true
      });
    },

    announceProgressChange: function(progressElement) {
      const value = progressElement.getAttribute('aria-valuenow') || 
                   progressElement.value;
      const max = progressElement.getAttribute('aria-valuemax') || 
                 progressElement.max || 100;
      const label = this.getElementLabel(progressElement);
      
      const percentage = Math.round((value / max) * 100);
      
      this.announce(`${label}: ${percentage}% complete`, 'polite', {
        context: 'progress'
      });
    },

    /**
     * Helper methods
     */
    sanitizeMessage: function(message) {
      return message.replace(/\s+/g, ' ').trim();
    },

    getTextContent: function(element) {
      if (!element) return '';
      return element.textContent.replace(/\s+/g, ' ').trim();
    },

    getElementLabel: function(element) {
      // Try various labeling methods
      const ariaLabel = element.getAttribute('aria-label');
      if (ariaLabel) return ariaLabel;

      const ariaLabelledBy = element.getAttribute('aria-labelledby');
      if (ariaLabelledBy) {
        const labelElement = document.getElementById(ariaLabelledBy);
        if (labelElement) return this.getTextContent(labelElement);
      }

      const label = element.closest('label') || 
                   document.querySelector(`label[for="${element.id}"]`);
      if (label) return this.getTextContent(label);

      return this.getTextContent(element) || 'Element';
    },

    getFieldLabel: function(field) {
      return this.getElementLabel(field) || field.name || field.placeholder || 'Field';
    },

    getAlertType: function(element) {
      if (element.classList.contains('flash-success') || 
          element.classList.contains('alert-success')) return 'Success';
      if (element.classList.contains('flash-error') || 
          element.classList.contains('alert-error')) return 'Error';
      if (element.classList.contains('flash-warning') || 
          element.classList.contains('alert-warning')) return 'Warning';
      return 'Notice';
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => ScreenReader.init());
  } else {
    ScreenReader.init();
  }

  // Export for use by other scripts
  window.AutoTest = window.AutoTest || {};
  window.AutoTest.ScreenReader = ScreenReader;

})();