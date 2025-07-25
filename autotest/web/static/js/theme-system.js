/*
 * AutoTest - Theme System
 * Dark mode, high contrast, and user preference management
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
   * Theme System Manager
   */
  const ThemeSystem = {
    // Available themes
    themes: {
      light: 'Light Theme',
      dark: 'Dark Theme',
      'high-contrast': 'High Contrast Theme',
      'high-contrast-dark': 'High Contrast Dark Theme'
    },

    // Current theme
    currentTheme: 'light',

    // Theme preferences
    preferences: {
      theme: 'auto',
      reducedMotion: null,
      reducedData: false,
      fontSize: 'normal',
      lineHeight: 'normal'
    },

    // Theme change observers
    observers: [],

    /**
     * Initialize theme system
     */
    init: function() {
      this.loadPreferences();
      this.detectSystemPreferences();
      this.applyTheme();
      this.setupThemeControls();
      this.setupSystemPreferenceListeners();
      this.setupKeyboardShortcuts();
      
      // Announce theme system is ready
      setTimeout(() => {
        A11y.announce(`Theme system activated. Current theme: ${this.themes[this.currentTheme]}. Press Alt+T to toggle themes.`);
      }, 2000);
    },

    /**
     * Load saved preferences from localStorage
     */
    loadPreferences: function() {
      try {
        const saved = localStorage.getItem('autotest-theme-preferences');
        if (saved) {
          this.preferences = { ...this.preferences, ...JSON.parse(saved) };
        }
      } catch (e) {
        console.warn('Failed to load theme preferences:', e);
      }
    },

    /**
     * Save preferences to localStorage
     */
    savePreferences: function() {
      try {
        localStorage.setItem('autotest-theme-preferences', JSON.stringify(this.preferences));
      } catch (e) {
        console.warn('Failed to save theme preferences:', e);
      }
    },

    /**
     * Detect system preferences
     */
    detectSystemPreferences: function() {
      // Detect color scheme preference
      if (this.preferences.theme === 'auto') {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
          this.currentTheme = 'dark';
        } else {
          this.currentTheme = 'light';
        }
      } else {
        this.currentTheme = this.preferences.theme;
      }

      // Detect high contrast preference
      if (window.matchMedia && window.matchMedia('(prefers-contrast: high)').matches) {
        if (this.currentTheme === 'dark') {
          this.currentTheme = 'high-contrast-dark';
        } else {
          this.currentTheme = 'high-contrast';
        }
      }

      // Detect reduced motion preference
      if (this.preferences.reducedMotion === null) {
        this.preferences.reducedMotion = window.matchMedia && 
          window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      }
    },

    /**
     * Apply current theme
     */
    applyTheme: function() {
      const html = document.documentElement;
      
      // Remove existing theme classes
      Object.keys(this.themes).forEach(theme => {
        html.classList.remove(`theme-${theme}`);
      });

      // Add current theme class
      html.classList.add(`theme-${this.currentTheme}`);

      // Apply additional preferences
      this.applyAccessibilityPreferences();

      // Update theme color meta tag for mobile browsers
      this.updateThemeColorMeta();

      // Notify observers
      this.notifyThemeChange();

      // Update theme controls
      this.updateThemeControls();
    },

    /**
     * Apply accessibility preferences
     */
    applyAccessibilityPreferences: function() {
      const html = document.documentElement;

      // Apply reduced motion preference
      if (this.preferences.reducedMotion) {
        html.classList.add('reduce-motion');
      } else {
        html.classList.remove('reduce-motion');
      }

      // Apply font size preference
      html.classList.remove('font-size-small', 'font-size-large', 'font-size-extra-large');
      if (this.preferences.fontSize !== 'normal') {
        html.classList.add(`font-size-${this.preferences.fontSize}`);
      }

      // Apply line height preference
      html.classList.remove('line-height-tight', 'line-height-loose');
      if (this.preferences.lineHeight !== 'normal') {
        html.classList.add(`line-height-${this.preferences.lineHeight}`);
      }

      // Apply reduced data preference
      if (this.preferences.reducedData) {
        html.classList.add('reduce-data');
      } else {
        html.classList.remove('reduce-data');
      }
    },

    /**
     * Update theme color meta tag
     */
    updateThemeColorMeta: function() {
      let themeColor = '#ffffff'; // light theme default

      switch (this.currentTheme) {
        case 'dark':
          themeColor = '#212529';
          break;
        case 'high-contrast':
          themeColor = '#ffffff';
          break;
        case 'high-contrast-dark':
          themeColor = '#000000';
          break;
      }

      let metaTag = document.querySelector('meta[name="theme-color"]');
      if (!metaTag) {
        metaTag = document.createElement('meta');
        metaTag.name = 'theme-color';
        document.head.appendChild(metaTag);
      }
      metaTag.content = themeColor;
    },

    /**
     * Setup theme controls
     */
    setupThemeControls: function() {
      this.createThemeToggle();
      this.createThemeSelector();
      this.createAccessibilityControls();
    },

    /**
     * Create theme toggle button
     */
    createThemeToggle: function() {
      // Check if theme toggle already exists
      if (document.querySelector('.theme-toggle')) return;

      const toggle = document.createElement('button');
      toggle.className = 'theme-toggle';
      toggle.setAttribute('aria-label', 'Toggle theme');
      toggle.setAttribute('data-tooltip', 'Switch between light and dark themes (Alt+T)');
      toggle.innerHTML = this.getThemeIcon();

      // Position in header
      const header = document.querySelector('.site-header .header-content');
      if (header) {
        toggle.style.marginLeft = 'auto';
        toggle.style.marginRight = 'var(--spacing-md)';
        header.appendChild(toggle);
      }

      // Handle click
      toggle.addEventListener('click', () => {
        this.toggleTheme();
      });

      // Store reference
      this.themeToggle = toggle;
    },

    /**
     * Get theme icon HTML
     */
    getThemeIcon: function() {
      switch (this.currentTheme) {
        case 'dark':
        case 'high-contrast-dark':
          return `
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 20 20">
              <path d="M10 2L13 9L20 9L14.5 13.5L17 20L10 16L3 20L5.5 13.5L0 9L7 9L10 2Z" fill="currentColor"/>
            </svg>
          `;
        case 'high-contrast':
          return `
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 20 20">
              <circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" stroke-width="2"/>
              <path d="M10 2 L10 18 M2 10 L18 10" stroke="currentColor" stroke-width="2"/>
            </svg>
          `;
        default:
          return `
            <svg aria-hidden="true" width="20" height="20" viewBox="0 0 20 20">
              <path d="M10 15C7.24 15 5 12.76 5 10C5 7.24 7.24 5 10 5C12.76 5 15 7.24 15 10C15 12.76 12.76 15 10 15ZM10 0L10 3M10 17L10 20M3.5 3.5L5.6 5.6M14.4 14.4L16.5 16.5M0 10L3 10M17 10L20 10M3.5 16.5L5.6 14.4M14.4 5.6L16.5 3.5" fill="currentColor"/>
            </svg>
          `;
      }
    },

    /**
     * Create theme selector modal
     */
    createThemeSelector: function() {
      // Add theme selector button to help modal or settings
      const createSelectorModal = () => {
        const modal = document.createElement('div');
        modal.className = 'theme-selector-modal';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-labelledby', 'theme-selector-title');
        modal.setAttribute('aria-modal', 'true');

        modal.innerHTML = `
          <div class="modal-backdrop"></div>
          <div class="modal-content">
            <div class="modal-header">
              <h2 id="theme-selector-title">Theme & Accessibility Settings</h2>
              <button type="button" class="modal-close" aria-label="Close settings">×</button>
            </div>
            <div class="modal-body">
              <div class="setting-group">
                <h3>Color Theme</h3>
                <fieldset class="theme-options">
                  <legend class="sr-only">Choose color theme</legend>
                  ${Object.entries(this.themes).map(([key, name]) => `
                    <label class="theme-option">
                      <input type="radio" name="theme" value="${key}" ${this.currentTheme === key ? 'checked' : ''}>
                      <span class="theme-preview theme-preview-${key}"></span>
                      <span class="theme-name">${name}</span>
                    </label>
                  `).join('')}
                  <label class="theme-option">
                    <input type="radio" name="theme" value="auto" ${this.preferences.theme === 'auto' ? 'checked' : ''}>
                    <span class="theme-preview theme-preview-auto"></span>
                    <span class="theme-name">Auto (System)</span>
                  </label>
                </fieldset>
              </div>

              <div class="setting-group">
                <h3>Accessibility Options</h3>
                
                <label class="setting-option">
                  <input type="checkbox" ${this.preferences.reducedMotion ? 'checked' : ''} data-setting="reducedMotion">
                  <span>Reduce motion and animations</span>
                </label>

                <label class="setting-option">
                  <input type="checkbox" ${this.preferences.reducedData ? 'checked' : ''} data-setting="reducedData">
                  <span>Reduce data usage (simplified interface)</span>
                </label>

                <div class="setting-option">
                  <label for="font-size-select">Font Size:</label>
                  <select id="font-size-select" data-setting="fontSize">
                    <option value="small" ${this.preferences.fontSize === 'small' ? 'selected' : ''}>Small</option>
                    <option value="normal" ${this.preferences.fontSize === 'normal' ? 'selected' : ''}>Normal</option>
                    <option value="large" ${this.preferences.fontSize === 'large' ? 'selected' : ''}>Large</option>
                    <option value="extra-large" ${this.preferences.fontSize === 'extra-large' ? 'selected' : ''}>Extra Large</option>
                  </select>
                </div>

                <div class="setting-option">
                  <label for="line-height-select">Line Height:</label>
                  <select id="line-height-select" data-setting="lineHeight">
                    <option value="tight" ${this.preferences.lineHeight === 'tight' ? 'selected' : ''}>Tight</option>
                    <option value="normal" ${this.preferences.lineHeight === 'normal' ? 'selected' : ''}>Normal</option>
                    <option value="loose" ${this.preferences.lineHeight === 'loose' ? 'selected' : ''}>Loose</option>
                  </select>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" id="reset-themes">Reset to Default</button>
              <button type="button" class="btn btn-primary modal-close">Apply Settings</button>
            </div>
          </div>
        `;

        // Handle theme selection
        const themeRadios = modal.querySelectorAll('input[name="theme"]');
        themeRadios.forEach(radio => {
          radio.addEventListener('change', (e) => {
            if (e.target.checked) {
              this.setTheme(e.target.value);
            }
          });
        });

        // Handle accessibility settings
        const settingInputs = modal.querySelectorAll('[data-setting]');
        settingInputs.forEach(input => {
          input.addEventListener('change', (e) => {
            const setting = e.target.dataset.setting;
            let value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
            this.updatePreference(setting, value);
          });
        });

        // Handle reset button
        modal.querySelector('#reset-themes').addEventListener('click', () => {
          this.resetToDefaults();
          modal.remove();
        });

        // Handle close
        const closeButtons = modal.querySelectorAll('.modal-close');
        closeButtons.forEach(button => {
          button.addEventListener('click', () => {
            modal.remove();
            A11y.announce('Theme settings closed');
          });
        });

        modal.querySelector('.modal-backdrop').addEventListener('click', () => {
          modal.remove();
        });

        return modal;
      };

      // Store function for later use
      this.showThemeSelector = () => {
        const modal = createSelectorModal();
        document.body.appendChild(modal);
        
        const firstRadio = modal.querySelector('input[type="radio"]:checked');
        if (firstRadio) {
          firstRadio.focus();
        }
        
        A11y.trapFocus(modal);
        A11y.announce('Theme settings opened');
      };
    },

    /**
     * Create accessibility controls
     */
    createAccessibilityControls: function() {
      // Quick accessibility toolbar
      const toolbar = document.createElement('div');
      toolbar.className = 'accessibility-toolbar';
      toolbar.setAttribute('role', 'toolbar');
      toolbar.setAttribute('aria-label', 'Accessibility controls');

      toolbar.innerHTML = `
        <button class="a11y-control" data-action="increase-font" aria-label="Increase font size" data-tooltip="Make text larger">A+</button>
        <button class="a11y-control" data-action="decrease-font" aria-label="Decrease font size" data-tooltip="Make text smaller">A-</button>
        <button class="a11y-control" data-action="toggle-contrast" aria-label="Toggle high contrast" data-tooltip="Toggle high contrast mode">◐</button>
        <button class="a11y-control" data-action="settings" aria-label="Theme settings" data-tooltip="Open theme and accessibility settings">⚙</button>
      `;

      // Position toolbar
      toolbar.style.position = 'fixed';
      toolbar.style.top = '50%';
      toolbar.style.right = '0';
      toolbar.style.transform = 'translateY(-50%)';
      toolbar.style.zIndex = '1000';

      document.body.appendChild(toolbar);

      // Handle toolbar actions
      toolbar.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (action) {
          this.handleAccessibilityAction(action);
        }
      });

      this.accessibilityToolbar = toolbar;
    },

    /**
     * Handle accessibility toolbar actions
     */
    handleAccessibilityAction: function(action) {
      switch (action) {
        case 'increase-font':
          this.adjustFontSize(1);
          break;
        case 'decrease-font':
          this.adjustFontSize(-1);
          break;
        case 'toggle-contrast':
          this.toggleHighContrast();
          break;
        case 'settings':
          this.showThemeSelector();
          break;
      }
    },

    /**
     * Adjust font size
     */
    adjustFontSize: function(direction) {
      const sizes = ['small', 'normal', 'large', 'extra-large'];
      const currentIndex = sizes.indexOf(this.preferences.fontSize);
      const newIndex = Math.max(0, Math.min(sizes.length - 1, currentIndex + direction));
      
      if (newIndex !== currentIndex) {
        this.updatePreference('fontSize', sizes[newIndex]);
        A11y.announce(`Font size: ${sizes[newIndex].replace('-', ' ')}`);
      }
    },

    /**
     * Toggle high contrast mode
     */
    toggleHighContrast: function() {
      if (this.currentTheme.includes('high-contrast')) {
        // Switch back to regular theme
        const newTheme = this.currentTheme.includes('dark') ? 'dark' : 'light';
        this.setTheme(newTheme);
      } else {
        // Switch to high contrast
        const newTheme = this.currentTheme === 'dark' ? 'high-contrast-dark' : 'high-contrast';
        this.setTheme(newTheme);
      }
    },

    /**
     * Setup system preference listeners
     */
    setupSystemPreferenceListeners: function() {
      // Listen for system color scheme changes
      if (window.matchMedia) {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        darkModeQuery.addListener((e) => {
          if (this.preferences.theme === 'auto') {
            this.currentTheme = e.matches ? 'dark' : 'light';
            this.applyTheme();
            A11y.announce(`Theme automatically changed to ${this.themes[this.currentTheme]} based on system preference`);
          }
        });

        // Listen for contrast preference changes
        const contrastQuery = window.matchMedia('(prefers-contrast: high)');
        contrastQuery.addListener((e) => {
          if (e.matches && !this.currentTheme.includes('high-contrast')) {
            const newTheme = this.currentTheme === 'dark' ? 'high-contrast-dark' : 'high-contrast';
            this.setTheme(newTheme);
            A11y.announce('High contrast mode enabled automatically');
          }
        });

        // Listen for reduced motion changes
        const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        motionQuery.addListener((e) => {
          if (this.preferences.reducedMotion === null) {
            this.updatePreference('reducedMotion', e.matches);
            A11y.announce(e.matches ? 'Reduced motion enabled' : 'Motion animations enabled');
          }
        });
      }
    },

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts: function() {
      document.addEventListener('keydown', (e) => {
        // Alt+T to toggle theme
        if (e.altKey && (e.key === 't' || e.key === 'T')) {
          e.preventDefault();
          this.toggleTheme();
        }

        // Alt+Shift+T to open theme settings
        if (e.altKey && e.shiftKey && (e.key === 't' || e.key === 'T')) {
          e.preventDefault();
          this.showThemeSelector();
        }

        // Ctrl+Plus/Minus for font size
        if (e.ctrlKey && (e.key === '=' || e.key === '+')) {
          e.preventDefault();
          this.adjustFontSize(1);
        }
        if (e.ctrlKey && e.key === '-') {
          e.preventDefault();
          this.adjustFontSize(-1);
        }
      });
    },

    /**
     * Toggle between light and dark themes
     */
    toggleTheme: function() {
      let nextTheme;
      
      switch (this.currentTheme) {
        case 'light':
          nextTheme = 'dark';
          break;
        case 'dark':
          nextTheme = 'light';
          break;
        case 'high-contrast':
          nextTheme = 'high-contrast-dark';
          break;
        case 'high-contrast-dark':
          nextTheme = 'high-contrast';
          break;
        default:
          nextTheme = 'dark';
      }

      this.setTheme(nextTheme);
      A11y.announce(`Theme changed to ${this.themes[nextTheme]}`);
    },

    /**
     * Set specific theme
     */
    setTheme: function(theme) {
      if (this.themes[theme]) {
        this.currentTheme = theme;
        this.preferences.theme = theme;
        this.applyTheme();
        this.savePreferences();
      }
    },

    /**
     * Update a preference
     */
    updatePreference: function(key, value) {
      this.preferences[key] = value;
      this.applyTheme();
      this.savePreferences();
    },

    /**
     * Reset to default preferences
     */
    resetToDefaults: function() {
      this.preferences = {
        theme: 'auto',
        reducedMotion: null,
        reducedData: false,
        fontSize: 'normal',
        lineHeight: 'normal'
      };
      this.detectSystemPreferences();
      this.applyTheme();
      this.savePreferences();
      A11y.announce('Theme and accessibility settings reset to defaults');
    },

    /**
     * Update theme controls
     */
    updateThemeControls: function() {
      if (this.themeToggle) {
        this.themeToggle.innerHTML = this.getThemeIcon();
        this.themeToggle.setAttribute('aria-label', `Current theme: ${this.themes[this.currentTheme]}. Click to toggle.`);
      }
    },

    /**
     * Add theme change observer
     */
    onThemeChange: function(callback) {
      this.observers.push(callback);
    },

    /**
     * Notify theme change observers
     */
    notifyThemeChange: function() {
      this.observers.forEach(callback => {
        try {
          callback(this.currentTheme, this.preferences);
        } catch (e) {
          console.warn('Theme change observer error:', e);
        }
      });
    },

    /**
     * Get current theme info
     */
    getCurrentTheme: function() {
      return {
        theme: this.currentTheme,
        themeName: this.themes[this.currentTheme],
        preferences: { ...this.preferences }
      };
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => ThemeSystem.init());
  } else {
    ThemeSystem.init();
  }

  // Export for use by other scripts
  window.AutoTest = window.AutoTest || {};
  window.AutoTest.ThemeSystem = ThemeSystem;

})();