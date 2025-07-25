/*
 * AutoTest - Enhanced Keyboard Navigation
 * Advanced keyboard navigation features and shortcuts
 */

(function() {
  'use strict';

  // Check if AutoTest utilities are available
  if (!window.AutoTest || !window.AutoTest.A11y) {
    console.error('AutoTest utilities not available');
    return;
  }

  const A11y = window.AutoTest.A11y;
  const prefersReducedMotion = window.AutoTest.prefersReducedMotion;

  /**
   * Enhanced Keyboard Navigation Manager
   */
  const KeyboardNavigation = {
    // Track current navigation mode
    currentMode: 'normal', // normal, search, menu, modal, form
    
    // Navigation history for breadcrumb-style navigation
    navigationHistory: [],
    
    // Currently focused roving tabindex group
    currentRovingGroup: null,
    
    // Keyboard shortcuts registry
    shortcuts: new Map(),
    
    // Navigation landmarks
    landmarks: [],

    /**
     * Initialize enhanced keyboard navigation
     */
    init: function() {
      this.setupGlobalKeyboardHandlers();
      this.setupRovingTabindex();
      this.setupKeyboardShortcuts();
      this.setupLandmarkNavigation();
      this.setupAdvancedFocus();
      this.setupContextualHelp();
      
      // Announce navigation is ready
      A11y.announce('Enhanced keyboard navigation is active. Press Alt+H for help.');
    },

    /**
     * Setup global keyboard event handlers
     */
    setupGlobalKeyboardHandlers: function() {
      document.addEventListener('keydown', (e) => {
        // Global keyboard shortcuts
        if (e.altKey && !e.ctrlKey && !e.shiftKey) {
          switch(e.key) {
            case 'h':
            case 'H':
              e.preventDefault();
              this.showKeyboardHelp();
              break;
            case 'm':
            case 'M':
              e.preventDefault();
              this.jumpToMainContent();
              break;
            case 'n':
            case 'N':
              e.preventDefault();
              this.jumpToNavigation();
              break;
            case 's':
            case 'S':
              e.preventDefault();
              this.jumpToSearch();
              break;
            case '1':
              e.preventDefault();
              this.jumpToLandmark('main');
              break;
            case '2':
              e.preventDefault();
              this.jumpToLandmark('navigation');
              break;
            case '3':
              e.preventDefault();
              this.jumpToLandmark('search');
              break;
            case '4':
              e.preventDefault();
              this.jumpToLandmark('complementary');
              break;
          }
        }
        
        // Navigation mode specific handlers
        this.handleModeSpecificKeys(e);
        
        // Escape key handling
        if (e.key === 'Escape') {
          this.handleEscape(e);
        }
      });

      // Track navigation state changes
      document.addEventListener('focusin', (e) => {
        this.updateNavigationState(e.target);
      });
    },

    /**
     * Setup roving tabindex for complex widgets
     */
    setupRovingTabindex: function() {
      // Find all roving tabindex groups
      const rovingGroups = document.querySelectorAll('[data-roving-tabindex]');
      
      rovingGroups.forEach(group => {
        const items = group.querySelectorAll('[role="tab"], [role="option"], [role="menuitem"], [role="gridcell"], .nav-item');
        
        if (items.length === 0) return;
        
        // Set initial tabindex states
        items.forEach((item, index) => {
          item.setAttribute('tabindex', index === 0 ? '0' : '-1');
        });
        
        // Handle arrow key navigation
        group.addEventListener('keydown', (e) => {
          if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) {
            return;
          }
          
          e.preventDefault();
          
          const currentIndex = Array.from(items).indexOf(e.target);
          let nextIndex = currentIndex;
          
          const isVertical = group.getAttribute('aria-orientation') === 'vertical' || 
                           group.classList.contains('vertical-navigation');
          
          switch(e.key) {
            case 'ArrowUp':
              if (isVertical) {
                nextIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
              }
              break;
            case 'ArrowDown':
              if (isVertical) {
                nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
              }
              break;
            case 'ArrowLeft':
              if (!isVertical) {
                nextIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
              }
              break;
            case 'ArrowRight':
              if (!isVertical) {
                nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
              }
              break;
            case 'Home':
              nextIndex = 0;
              break;
            case 'End':
              nextIndex = items.length - 1;
              break;
          }
          
          if (nextIndex !== currentIndex) {
            items[currentIndex].setAttribute('tabindex', '-1');
            items[nextIndex].setAttribute('tabindex', '0');
            items[nextIndex].focus();
            
            // Announce position if there are many items
            if (items.length > 5) {
              A11y.announce(`${nextIndex + 1} of ${items.length}`);
            }
          }
        });
      });
    },

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts: function() {
      // Register common shortcuts
      this.registerShortcut('/', () => this.jumpToSearch(), 'Jump to search');
      this.registerShortcut('?', () => this.showKeyboardHelp(), 'Show keyboard shortcuts');
      this.registerShortcut('g h', () => this.goToHome(), 'Go to homepage');
      this.registerShortcut('g p', () => this.goToProjects(), 'Go to projects');
      this.registerShortcut('g t', () => this.goToTesting(), 'Go to testing');
      this.registerShortcut('g r', () => this.goToReports(), 'Go to reports');
      
      // Sequential key handling for multi-key shortcuts
      let keySequence = [];
      let sequenceTimer = null;
      
      document.addEventListener('keydown', (e) => {
        // Skip if user is typing in form fields
        if (this.isTypingInInput(e.target)) return;
        
        // Clear sequence timer
        if (sequenceTimer) {
          clearTimeout(sequenceTimer);
        }
        
        // Add key to sequence
        keySequence.push(e.key.toLowerCase());
        
        // Check for matches
        const sequence = keySequence.join(' ');
        const shortcut = this.shortcuts.get(sequence);
        
        if (shortcut) {
          e.preventDefault();
          shortcut.action();
          keySequence = [];
          return;
        }
        
        // Check for partial matches
        const hasPartialMatch = Array.from(this.shortcuts.keys()).some(key => 
          key.startsWith(sequence)
        );
        
        if (!hasPartialMatch) {
          keySequence = [e.key.toLowerCase()];
        }
        
        // Clear sequence after timeout
        sequenceTimer = setTimeout(() => {
          keySequence = [];
        }, 1000);
      });
    },

    /**
     * Setup landmark navigation
     */
    setupLandmarkNavigation: function() {
      this.landmarks = [
        { element: document.querySelector('main'), name: 'Main content', key: '1' },
        { element: document.querySelector('nav[role="navigation"]'), name: 'Navigation', key: '2' },
        { element: document.querySelector('[role="search"]'), name: 'Search', key: '3' },
        { element: document.querySelector('aside'), name: 'Sidebar', key: '4' },
        { element: document.querySelector('footer'), name: 'Footer', key: '5' }
      ].filter(landmark => landmark.element);
      
      // Add landmark navigation shortcut
      document.addEventListener('keydown', (e) => {
        if (e.altKey && e.key >= '1' && e.key <= '5') {
          const landmark = this.landmarks[parseInt(e.key) - 1];
          if (landmark) {
            e.preventDefault();
            this.focusLandmark(landmark);
          }
        }
      });
    },

    /**
     * Setup advanced focus management
     */
    setupAdvancedFocus: function() {
      // Enhanced focus indicators
      document.addEventListener('focusin', (e) => {
        const element = e.target;
        
        // Add context-aware focus styling
        if (element.matches('button, [role="button"]')) {
          element.classList.add('button-focused');
        } else if (element.matches('a')) {
          element.classList.add('link-focused');
        } else if (element.matches('input, textarea, select')) {
          element.classList.add('input-focused');
        }
        
        // Scroll focused element into view if needed
        this.ensureElementVisible(element);
      });
      
      document.addEventListener('focusout', (e) => {
        const element = e.target;
        element.classList.remove('button-focused', 'link-focused', 'input-focused');
      });
      
      // Focus restoration for dynamic content
      this.setupFocusRestoration();
    },

    /**
     * Setup contextual help system
     */
    setupContextualHelp: function() {
      // F1 key for contextual help
      document.addEventListener('keydown', (e) => {
        if (e.key === 'F1') {
          e.preventDefault();
          this.showContextualHelp(e.target);
        }
      });
    },

    /**
     * Handle mode-specific keyboard navigation
     */
    handleModeSpecificKeys: function(e) {
      switch(this.currentMode) {
        case 'search':
          this.handleSearchMode(e);
          break;
        case 'menu':
          this.handleMenuMode(e);
          break;
        case 'modal':
          this.handleModalMode(e);
          break;
        case 'form':
          this.handleFormMode(e);
          break;
        case 'table':
          this.handleTableMode(e);
          break;
      }
    },

    /**
     * Handle search mode navigation
     */
    handleSearchMode: function(e) {
      if (e.key === 'Enter' && e.target.matches('input[type="search"]')) {
        // Enhanced search submission
        const searchResults = document.querySelector('[role="region"][aria-label*="search" i]');
        if (searchResults) {
          setTimeout(() => {
            const firstResult = searchResults.querySelector('a, button, [tabindex="0"]');
            if (firstResult) {
              firstResult.focus();
              A11y.announce(`Search completed. ${searchResults.children.length} results found.`);
            }
          }, 100);
        }
      }
    },

    /**
     * Handle menu mode navigation
     */
    handleMenuMode: function(e) {
      const menu = document.querySelector('[role="menu"]:not([hidden])');
      if (!menu) return;
      
      switch(e.key) {
        case 'ArrowDown':
          e.preventDefault();
          this.focusNextMenuItem(menu, 1);
          break;
        case 'ArrowUp':
          e.preventDefault();
          this.focusNextMenuItem(menu, -1);
          break;
        case 'Home':
          e.preventDefault();
          this.focusFirstMenuItem(menu);
          break;
        case 'End':
          e.preventDefault();
          this.focusLastMenuItem(menu);
          break;
      }
    },

    /**
     * Handle table navigation
     */
    handleTableMode: function(e) {
      const table = e.target.closest('table');
      if (!table) return;
      
      const cell = e.target.closest('td, th');
      if (!cell) return;
      
      switch(e.key) {
        case 'ArrowRight':
          if (e.ctrlKey) {
            e.preventDefault();
            this.navigateTableCell(cell, 'right');
          }
          break;
        case 'ArrowLeft':
          if (e.ctrlKey) {
            e.preventDefault();
            this.navigateTableCell(cell, 'left');
          }
          break;
        case 'ArrowUp':
          if (e.ctrlKey) {
            e.preventDefault();
            this.navigateTableCell(cell, 'up');
          }
          break;
        case 'ArrowDown':
          if (e.ctrlKey) {
            e.preventDefault();
            this.navigateTableCell(cell, 'down');
          }
          break;
      }
    },

    /**
     * Handle escape key
     */
    handleEscape: function(e) {
      // Close modals
      const modal = document.querySelector('[role="dialog"]:not([hidden])');
      if (modal) {
        const closeButton = modal.querySelector('[data-dismiss="modal"], .modal-close');
        if (closeButton) {
          closeButton.click();
        }
        return;
      }
      
      // Close menus
      const openMenu = document.querySelector('[role="menu"]:not([hidden])');
      if (openMenu) {
        const menuButton = document.querySelector('[aria-expanded="true"][aria-controls]');
        if (menuButton) {
          menuButton.click();
        }
        return;
      }
      
      // Clear search
      const searchInput = document.querySelector('input[type="search"]:focus');
      if (searchInput && searchInput.value) {
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input', { bubbles: true }));
        A11y.announce('Search cleared');
        return;
      }
      
      // Return to main content
      const mainContent = document.querySelector('main');
      if (mainContent && !mainContent.contains(document.activeElement)) {
        mainContent.focus();
        A11y.announce('Returned to main content');
      }
    },

    /**
     * Update navigation state based on current focus
     */
    updateNavigationState: function(element) {
      const previousMode = this.currentMode;
      
      if (element.matches('input[type="search"]')) {
        this.currentMode = 'search';
      } else if (element.closest('[role="menu"]')) {
        this.currentMode = 'menu';
      } else if (element.closest('[role="dialog"]')) {
        this.currentMode = 'modal';
      } else if (element.closest('form')) {
        this.currentMode = 'form';
      } else if (element.closest('table')) {
        this.currentMode = 'table';
      } else {
        this.currentMode = 'normal';
      }
      
      // Announce mode changes
      if (previousMode !== this.currentMode && this.currentMode !== 'normal') {
        A11y.announce(`Entered ${this.currentMode} mode`);
      }
    },

    /**
     * Jump to specific elements
     */
    jumpToMainContent: function() {
      const main = document.querySelector('main');
      if (main) {
        main.focus();
        A11y.announce('Jumped to main content');
      }
    },

    jumpToNavigation: function() {
      const nav = document.querySelector('nav[role="navigation"]');
      if (nav) {
        const firstLink = nav.querySelector('a, button');
        if (firstLink) {
          firstLink.focus();
          A11y.announce('Jumped to navigation');
        }
      }
    },

    jumpToSearch: function() {
      const searchInput = document.querySelector('input[type="search"]');
      if (searchInput) {
        searchInput.focus();
        A11y.announce('Jumped to search');
      } else {
        A11y.announce('Search not available on this page');
      }
    },

    jumpToLandmark: function(landmarkType) {
      const landmark = document.querySelector(`[role="${landmarkType}"], ${landmarkType}`);
      if (landmark) {
        landmark.focus();
        A11y.announce(`Jumped to ${landmarkType}`);
      }
    },

    /**
     * Navigation shortcuts
     */
    goToHome: function() {
      window.location.href = '/';
    },

    goToProjects: function() {
      window.location.href = '/projects';
    },

    goToTesting: function() {
      window.location.href = '/testing';
    },

    goToReports: function() {
      window.location.href = '/reports';
    },

    /**
     * Show keyboard help modal
     */
    showKeyboardHelp: function() {
      const helpModal = this.createHelpModal();
      document.body.appendChild(helpModal);
      
      // Focus the modal
      const firstButton = helpModal.querySelector('button');
      if (firstButton) {
        firstButton.focus();
      }
      
      A11y.trapFocus(helpModal);
      A11y.announce('Keyboard shortcuts help opened');
    },

    /**
     * Create help modal
     */
    createHelpModal: function() {
      const modal = document.createElement('div');
      modal.className = 'keyboard-help-modal';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-labelledby', 'help-modal-title');
      modal.setAttribute('aria-modal', 'true');
      
      modal.innerHTML = `
        <div class="modal-backdrop"></div>
        <div class="modal-content">
          <div class="modal-header">
            <h2 id="help-modal-title">Keyboard Shortcuts</h2>
            <button type="button" class="modal-close" aria-label="Close help">×</button>
          </div>
          <div class="modal-body">
            <div class="shortcut-groups">
              <div class="shortcut-group">
                <h3>Navigation</h3>
                <dl class="shortcut-list">
                  <dt>Alt + M</dt>
                  <dd>Jump to main content</dd>
                  <dt>Alt + N</dt>
                  <dd>Jump to navigation</dd>
                  <dt>Alt + S</dt>
                  <dd>Jump to search</dd>
                  <dt>Alt + 1-5</dt>
                  <dd>Jump to landmarks</dd>
                </dl>
              </div>
              <div class="shortcut-group">
                <h3>Quick Actions</h3>
                <dl class="shortcut-list">
                  <dt>/</dt>
                  <dd>Focus search</dd>
                  <dt>?</dt>
                  <dd>Show this help</dd>
                  <dt>Escape</dt>
                  <dd>Close modal/menu or return to main</dd>
                </dl>
              </div>
              <div class="shortcut-group">
                <h3>Page Navigation</h3>
                <dl class="shortcut-list">
                  <dt>G H</dt>
                  <dd>Go to homepage</dd>
                  <dt>G P</dt>
                  <dd>Go to projects</dd>
                  <dt>G T</dt>
                  <dd>Go to testing</dd>
                  <dt>G R</dt>
                  <dd>Go to reports</dd>
                </dl>
              </div>
              <div class="shortcut-group">
                <h3>Context Help</h3>
                <dl class="shortcut-list">
                  <dt>F1</dt>
                  <dd>Show contextual help</dd>
                  <dt>Alt + H</dt>
                  <dd>Show keyboard shortcuts</dd>
                </dl>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary modal-close">Got it</button>
          </div>
        </div>
      `;
      
      // Handle modal close
      const closeButtons = modal.querySelectorAll('.modal-close');
      closeButtons.forEach(button => {
        button.addEventListener('click', () => {
          modal.remove();
          A11y.announce('Keyboard shortcuts help closed');
        });
      });
      
      // Close on backdrop click
      modal.querySelector('.modal-backdrop').addEventListener('click', () => {
        modal.remove();
      });
      
      return modal;
    },

    /**
     * Show contextual help
     */
    showContextualHelp: function(element) {
      let helpText = '';
      
      if (element.matches('input[type="search"]')) {
        helpText = 'Search field. Type to search, press Enter to submit, Escape to clear.';
      } else if (element.matches('table')) {
        helpText = 'Data table. Use Ctrl+Arrow keys to navigate between cells.';
      } else if (element.matches('[role="button"], button')) {
        helpText = 'Button. Press Enter or Space to activate.';
      } else if (element.matches('a')) {
        helpText = 'Link. Press Enter to follow.';
      } else if (element.matches('form')) {
        helpText = 'Form. Tab between fields, press Enter to submit.';
      } else {
        helpText = 'Press Alt+H for keyboard shortcuts, F1 for contextual help.';
      }
      
      A11y.announce(helpText, 'assertive');
    },

    /**
     * Utility functions
     */
    registerShortcut: function(keys, action, description) {
      this.shortcuts.set(keys, { action, description });
    },

    isTypingInInput: function(element) {
      return element.matches('input, textarea, select, [contenteditable="true"]');
    },

    ensureElementVisible: function(element) {
      if (element.scrollIntoViewIfNeeded) {
        element.scrollIntoViewIfNeeded();
      } else {
        element.scrollIntoView({
          behavior: prefersReducedMotion ? 'auto' : 'smooth',
          block: 'nearest'
        });
      }
    },

    focusLandmark: function(landmark) {
      if (landmark.element.tabIndex === -1) {
        landmark.element.tabIndex = -1;
      }
      landmark.element.focus();
      A11y.announce(`Navigated to ${landmark.name}`);
    },

    navigateTableCell: function(currentCell, direction) {
      const table = currentCell.closest('table');
      const rows = Array.from(table.querySelectorAll('tr'));
      const currentRow = currentCell.closest('tr');
      const currentRowIndex = rows.indexOf(currentRow);
      const cells = Array.from(currentRow.querySelectorAll('td, th'));
      const currentCellIndex = cells.indexOf(currentCell);
      
      let targetCell = null;
      
      switch(direction) {
        case 'right':
          targetCell = cells[currentCellIndex + 1];
          break;
        case 'left':
          targetCell = cells[currentCellIndex - 1];
          break;
        case 'up':
          if (currentRowIndex > 0) {
            const targetRow = rows[currentRowIndex - 1];
            const targetCells = targetRow.querySelectorAll('td, th');
            targetCell = targetCells[Math.min(currentCellIndex, targetCells.length - 1)];
          }
          break;
        case 'down':
          if (currentRowIndex < rows.length - 1) {
            const targetRow = rows[currentRowIndex + 1];
            const targetCells = targetRow.querySelectorAll('td, th');
            targetCell = targetCells[Math.min(currentCellIndex, targetCells.length - 1)];
          }
          break;
      }
      
      if (targetCell) {
        targetCell.focus();
        A11y.announce(`${targetCell.textContent.trim()} cell`);
      }
    },

    focusNextMenuItem: function(menu, direction) {
      const items = menu.querySelectorAll('[role="menuitem"]');
      const currentIndex = Array.from(items).indexOf(document.activeElement);
      let nextIndex = currentIndex + direction;
      
      if (nextIndex < 0) nextIndex = items.length - 1;
      if (nextIndex >= items.length) nextIndex = 0;
      
      items[nextIndex].focus();
    },

    focusFirstMenuItem: function(menu) {
      const firstItem = menu.querySelector('[role="menuitem"]');
      if (firstItem) firstItem.focus();
    },

    focusLastMenuItem: function(menu) {
      const items = menu.querySelectorAll('[role="menuitem"]');
      const lastItem = items[items.length - 1];
      if (lastItem) lastItem.focus();
    },

    setupFocusRestoration: function() {
      // Store focus before page changes
      let lastFocusedElement = null;
      
      document.addEventListener('focusout', (e) => {
        lastFocusedElement = e.target;
      });
      
      // Restore focus after dynamic content changes
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            // Check if focused element was removed
            if (lastFocusedElement && !document.contains(lastFocusedElement)) {
              // Try to restore focus to a similar element
              this.restoreFocusToSimilarElement(lastFocusedElement);
            }
          }
        });
      });
      
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    },

    restoreFocusToSimilarElement: function(originalElement) {
      // Try to find a similar element to restore focus to
      const tagName = originalElement.tagName.toLowerCase();
      const className = originalElement.className;
      const id = originalElement.id;
      
      let targetElement = null;
      
      // Try by ID first
      if (id) {
        targetElement = document.getElementById(id);
      }
      
      // Try by class and tag
      if (!targetElement && className) {
        targetElement = document.querySelector(`${tagName}.${className.split(' ')[0]}`);
      }
      
      // Try by tag name
      if (!targetElement) {
        targetElement = document.querySelector(tagName);
      }
      
      // Fallback to main content
      if (!targetElement) {
        targetElement = document.querySelector('main');
      }
      
      if (targetElement) {
        targetElement.focus();
        A11y.announce('Focus restored after content change');
      }
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => KeyboardNavigation.init());
  } else {
    KeyboardNavigation.init();
  }

  // Export for use by other scripts
  window.AutoTest = window.AutoTest || {};
  window.AutoTest.KeyboardNavigation = KeyboardNavigation;

})();