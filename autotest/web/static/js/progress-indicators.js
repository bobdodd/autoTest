/*
 * AutoTest - Progress Indicators
 * Accessible progress indication for long-running operations
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
   * Progress Indicators Manager
   */
  const ProgressIndicators = {
    // Active progress operations
    activeOperations: new Map(),
    
    // Progress indicator elements
    indicators: new Map(),
    
    // Global progress overlay
    globalOverlay: null,
    
    // Settings
    settings: {
      announceProgressSteps: true,
      announceCompletion: true,
      announceFailures: true,
      progressUpdateInterval: 1000,
      estimateTimeRemaining: true,
      showPercentage: true
    },

    /**
     * Initialize progress indicators system
     */
    init: function() {
      this.createGlobalOverlay();
      this.setupProgressObservers();
      this.setupFormSubmissionIndicators();
      this.setupAjaxIndicators();
      this.setupFileUploadIndicators();
      this.setupTestProgressIndicators();
      
      // Announce progress system is ready
      setTimeout(() => {
        A11y.announce('Progress indication system activated');
      }, 2500);
    },

    /**
     * Create global progress overlay
     */
    createGlobalOverlay: function() {
      this.globalOverlay = document.createElement('div');
      this.globalOverlay.className = 'global-progress-overlay';
      this.globalOverlay.setAttribute('role', 'dialog');
      this.globalOverlay.setAttribute('aria-modal', 'true');
      this.globalOverlay.setAttribute('aria-labelledby', 'global-progress-title');
      this.globalOverlay.style.display = 'none';

      this.globalOverlay.innerHTML = `
        <div class="progress-backdrop"></div>
        <div class="progress-content">
          <div class="progress-header">
            <h2 id="global-progress-title">Processing...</h2>
            <button type="button" class="progress-cancel" aria-label="Cancel operation" style="display: none;">Cancel</button>
          </div>
          <div class="progress-body">
            <div class="progress-bar-container">
              <div class="progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
                <div class="progress-fill"></div>
              </div>
              <div class="progress-percentage">0%</div>
            </div>
            <div class="progress-details">
              <div class="progress-status">Initializing...</div>
              <div class="progress-substeps"></div>
              <div class="progress-time">
                <span class="time-elapsed">0s</span>
                <span class="time-remaining" style="display: none;">Est. 0s remaining</span>
              </div>
            </div>
          </div>
        </div>
      `;

      document.body.appendChild(this.globalOverlay);
    },

    /**
     * Setup progress observers for existing elements
     */
    setupProgressObservers: function() {
      // Observe existing progress bars
      const progressBars = document.querySelectorAll('[role="progressbar"], progress');
      progressBars.forEach(bar => {
        this.enhanceProgressBar(bar);
      });

      // Observe for new progress bars
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const progressBars = node.querySelectorAll('[role="progressbar"], progress');
              progressBars.forEach(bar => {
                this.enhanceProgressBar(bar);
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
     * Enhance existing progress bar with accessibility features
     */
    enhanceProgressBar: function(progressBar) {
      // Skip if already enhanced
      if (progressBar.dataset.enhanced === 'true') return;

      progressBar.dataset.enhanced = 'true';

      // Ensure proper ARIA attributes
      if (!progressBar.hasAttribute('role')) {
        progressBar.setAttribute('role', 'progressbar');
      }
      if (!progressBar.hasAttribute('aria-valuemin')) {
        progressBar.setAttribute('aria-valuemin', '0');
      }
      if (!progressBar.hasAttribute('aria-valuemax')) {
        progressBar.setAttribute('aria-valuemax', '100');
      }

      // Add percentage display if not present
      if (!progressBar.querySelector('.progress-percentage')) {
        const percentage = document.createElement('div');
        percentage.className = 'progress-percentage';
        percentage.setAttribute('aria-live', 'polite');
        progressBar.parentNode.insertBefore(percentage, progressBar.nextSibling);
      }

      // Monitor progress changes
      const observer = new MutationObserver(() => {
        this.updateProgressAnnouncements(progressBar);
      });

      observer.observe(progressBar, {
        attributes: true,
        attributeFilter: ['aria-valuenow', 'value']
      });
    },

    /**
     * Update progress announcements
     */
    updateProgressAnnouncements: function(progressBar) {
      const value = progressBar.getAttribute('aria-valuenow') || progressBar.value || 0;
      const max = progressBar.getAttribute('aria-valuemax') || progressBar.max || 100;
      const percentage = Math.round((value / max) * 100);

      // Update percentage display
      const percentageDisplay = progressBar.parentNode.querySelector('.progress-percentage');
      if (percentageDisplay) {
        percentageDisplay.textContent = `${percentage}%`;
      }

      // Announce progress at certain intervals
      if (this.settings.announceProgressSteps && percentage % 25 === 0 && percentage > 0) {
        const label = progressBar.getAttribute('aria-label') || 'Progress';
        A11y.announce(`${label}: ${percentage}% complete`, 'polite');
      }
    },

    /**
     * Setup form submission indicators
     */
    setupFormSubmissionIndicators: function() {
      document.addEventListener('submit', (e) => {
        const form = e.target;
        
        // Skip if form has data-no-progress attribute
        if (form.hasAttribute('data-no-progress')) return;

        // Show progress for forms that might take time
        if (form.matches('.ajax-form, [data-ajax], .file-upload-form')) {
          this.showFormProgress(form);
        }
      });
    },

    /**
     * Show form submission progress
     */
    showFormProgress: function(form) {
      const formName = form.getAttribute('aria-label') || 
                     form.querySelector('h1, h2, h3, legend')?.textContent || 
                     'Form';

      const operationId = this.startOperation(`Submitting ${formName}`, {
        type: 'form-submission',
        element: form,
        cancellable: false
      });

      // Simulate progress for forms without explicit progress tracking
      this.simulateProgress(operationId, {
        duration: 3000,
        steps: [
          { progress: 20, status: 'Validating form data...' },
          { progress: 50, status: 'Sending data...' },
          { progress: 80, status: 'Processing response...' },
          { progress: 100, status: 'Complete!' }
        ]
      });
    },

    /**
     * Setup AJAX request indicators
     */
    setupAjaxIndicators: function() {
      // Monitor fetch requests
      const originalFetch = window.fetch;
      
      window.fetch = function(...args) {
        const url = args[0];
        const options = args[1] || {};
        
        // Skip progress for certain requests
        if (options.skipProgress) {
          return originalFetch.apply(this, args);
        }

        const operationId = ProgressIndicators.startOperation('Loading data...', {
          type: 'ajax-request',
          url: url,
          method: options.method || 'GET'
        });

        return originalFetch.apply(this, args)
          .then(response => {
            ProgressIndicators.completeOperation(operationId, 'Data loaded successfully');
            return response;
          })
          .catch(error => {
            ProgressIndicators.failOperation(operationId, 'Failed to load data');
            throw error;
          });
      };

      // Monitor XMLHttpRequest
      const originalXHROpen = XMLHttpRequest.prototype.open;
      const originalXHRSend = XMLHttpRequest.prototype.send;

      XMLHttpRequest.prototype.open = function(method, url, ...args) {
        this._progressData = { method, url };
        return originalXHROpen.apply(this, [method, url, ...args]);
      };

      XMLHttpRequest.prototype.send = function(...args) {
        if (!this._skipProgress && this._progressData) {
          const operationId = ProgressIndicators.startOperation('Loading...', {
            type: 'xhr-request',
            url: this._progressData.url,
            method: this._progressData.method
          });

          this.addEventListener('load', () => {
            ProgressIndicators.completeOperation(operationId, 'Request completed');
          });

          this.addEventListener('error', () => {
            ProgressIndicators.failOperation(operationId, 'Request failed');
          });

          this.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
              const percentage = (e.loaded / e.total) * 100;
              ProgressIndicators.updateProgress(operationId, percentage, 'Downloading...');
            }
          });
        }

        return originalXHRSend.apply(this, args);
      };
    },

    /**
     * Setup file upload indicators
     */
    setupFileUploadIndicators: function() {
      document.addEventListener('change', (e) => {
        if (e.target.matches('input[type="file"]')) {
          const fileInput = e.target;
          const files = fileInput.files;
          
          if (files.length > 0) {
            this.showFileUploadProgress(fileInput, files);
          }
        }
      });
    },

    /**
     * Show file upload progress
     */
    showFileUploadProgress: function(fileInput, files) {
      const totalFiles = files.length;
      const totalSize = Array.from(files).reduce((sum, file) => sum + file.size, 0);
      
      const operationId = this.startOperation(`Uploading ${totalFiles} file${totalFiles > 1 ? 's' : ''}`, {
        type: 'file-upload',
        element: fileInput,
        totalFiles: totalFiles,
        totalSize: totalSize,
        cancellable: true
      });

      // Show file details
      const fileList = Array.from(files).map(file => 
        `${file.name} (${this.formatFileSize(file.size)})`
      ).join(', ');

      this.updateProgress(operationId, 0, `Preparing to upload: ${fileList}`);

      // Simulate upload progress (in real implementation, this would track actual upload)
      this.simulateProgress(operationId, {
        duration: 5000 + (totalSize / 1000), // Scale with file size
        steps: [
          { progress: 10, status: 'Validating files...' },
          { progress: 30, status: 'Starting upload...' },
          { progress: 70, status: 'Uploading files...' },
          { progress: 90, status: 'Processing uploaded files...' },
          { progress: 100, status: 'Upload complete!' }
        ]
      });
    },

    /**
     * Setup test progress indicators
     */
    setupTestProgressIndicators: function() {
      // Listen for test start events
      document.addEventListener('testStarted', (e) => {
        const testData = e.detail;
        this.showTestProgress(testData);
      });

      // Listen for test progress events
      document.addEventListener('testProgress', (e) => {
        const { operationId, progress, status, substeps } = e.detail;
        this.updateProgress(operationId, progress, status, substeps);
      });

      // Listen for test completion events
      document.addEventListener('testCompleted', (e) => {
        const { operationId, success, message } = e.detail;
        if (success) {
          this.completeOperation(operationId, message);
        } else {
          this.failOperation(operationId, message);
        }
      });
    },

    /**
     * Show test progress
     */
    showTestProgress: function(testData) {
      const { testType, websiteUrl, totalPages } = testData;
      
      const operationId = this.startOperation(`Running ${testType} test`, {
        type: 'accessibility-test',
        websiteUrl: websiteUrl,
        totalPages: totalPages,
        cancellable: true
      });

      this.updateProgress(operationId, 0, `Starting test for ${websiteUrl}`, [
        'Initializing browser...',
        'Loading page...',
        'Running accessibility checks...'
      ]);

      return operationId;
    },

    /**
     * Start a new progress operation
     */
    startOperation: function(title, options = {}) {
      const operationId = 'op_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      
      const operation = {
        id: operationId,
        title: title,
        progress: 0,
        status: 'Starting...',
        substeps: [],
        startTime: Date.now(),
        estimatedDuration: options.estimatedDuration || null,
        type: options.type || 'generic',
        cancellable: options.cancellable || false,
        cancelled: false,
        element: options.element || null,
        ...options
      };

      this.activeOperations.set(operationId, operation);
      this.showProgress(operation);
      
      // Announce operation start
      A11y.announce(`${title} started`, 'polite');

      return operationId;
    },

    /**
     * Update progress for an operation
     */
    updateProgress: function(operationId, progress, status = null, substeps = null) {
      const operation = this.activeOperations.get(operationId);
      if (!operation || operation.cancelled) return;

      operation.progress = Math.min(100, Math.max(0, progress));
      if (status) operation.status = status;
      if (substeps) operation.substeps = substeps;

      this.updateProgressDisplay(operation);

      // Update estimated time remaining
      if (this.settings.estimateTimeRemaining && operation.progress > 10) {
        const elapsed = Date.now() - operation.startTime;
        const estimatedTotal = (elapsed / operation.progress) * 100;
        operation.estimatedTimeRemaining = estimatedTotal - elapsed;
      }
    },

    /**
     * Complete an operation successfully
     */
    completeOperation: function(operationId, message = 'Operation completed successfully') {
      const operation = this.activeOperations.get(operationId);
      if (!operation) return;

      operation.progress = 100;
      operation.status = message;
      operation.completed = true;

      this.updateProgressDisplay(operation);

      // Announce completion
      if (this.settings.announceCompletion) {
        A11y.announce(message, 'polite');
      }

      // Hide progress after delay
      setTimeout(() => {
        this.hideProgress(operationId);
      }, 2000);
    },

    /**
     * Fail an operation
     */
    failOperation: function(operationId, message = 'Operation failed') {
      const operation = this.activeOperations.get(operationId);
      if (!operation) return;

      operation.failed = true;
      operation.status = message;

      this.updateProgressDisplay(operation);

      // Announce failure
      if (this.settings.announceFailures) {
        A11y.announce(message, 'assertive');
      }

      // Hide progress after delay
      setTimeout(() => {
        this.hideProgress(operationId);
      }, 5000);
    },

    /**
     * Cancel an operation
     */
    cancelOperation: function(operationId) {
      const operation = this.activeOperations.get(operationId);
      if (!operation || !operation.cancellable) return;

      operation.cancelled = true;
      operation.status = 'Operation cancelled';

      this.updateProgressDisplay(operation);
      A11y.announce('Operation cancelled', 'polite');

      // Hide progress after delay
      setTimeout(() => {
        this.hideProgress(operationId);
      }, 1000);
    },

    /**
     * Show progress display
     */
    showProgress: function(operation) {
      // Use global overlay for important operations
      if (operation.type === 'accessibility-test' || operation.type === 'file-upload') {
        this.showGlobalProgress(operation);
      } else {
        this.showInlineProgress(operation);
      }
    },

    /**
     * Show global progress overlay
     */
    showGlobalProgress: function(operation) {
      const overlay = this.globalOverlay;
      
      overlay.querySelector('#global-progress-title').textContent = operation.title;
      
      const cancelBtn = overlay.querySelector('.progress-cancel');
      if (operation.cancellable) {
        cancelBtn.style.display = 'block';
        cancelBtn.onclick = () => this.cancelOperation(operation.id);
      } else {
        cancelBtn.style.display = 'none';
      }

      overlay.style.display = 'flex';
      this.currentGlobalOperation = operation.id;

      // Focus trap in overlay
      A11y.trapFocus(overlay);
    },

    /**
     * Show inline progress indicator
     */
    showInlineProgress: function(operation) {
      // Create inline progress indicator near the triggering element
      if (operation.element) {
        const indicator = this.createInlineIndicator(operation);
        operation.element.parentNode.insertBefore(indicator, operation.element.nextSibling);
        this.indicators.set(operation.id, indicator);
      }
    },

    /**
     * Create inline progress indicator
     */
    createInlineIndicator: function(operation) {
      const indicator = document.createElement('div');
      indicator.className = 'inline-progress-indicator';
      indicator.innerHTML = `
        <div class="progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="${operation.title}">
          <div class="progress-fill"></div>
        </div>
        <div class="progress-status">${operation.status}</div>
      `;
      return indicator;
    },

    /**
     * Update progress display
     */
    updateProgressDisplay: function(operation) {
      if (this.currentGlobalOperation === operation.id) {
        this.updateGlobalProgressDisplay(operation);
      }

      const inlineIndicator = this.indicators.get(operation.id);
      if (inlineIndicator) {
        this.updateInlineProgressDisplay(operation, inlineIndicator);
      }
    },

    /**
     * Update global progress display
     */
    updateGlobalProgressDisplay: function(operation) {
      const overlay = this.globalOverlay;
      
      const progressBar = overlay.querySelector('.progress-bar');
      const progressFill = overlay.querySelector('.progress-fill');
      const percentage = overlay.querySelector('.progress-percentage');
      const status = overlay.querySelector('.progress-status');
      const substeps = overlay.querySelector('.progress-substeps');
      const timeElapsed = overlay.querySelector('.time-elapsed');
      const timeRemaining = overlay.querySelector('.time-remaining');

      // Update progress bar
      progressBar.setAttribute('aria-valuenow', operation.progress);
      progressFill.style.width = `${operation.progress}%`;
      percentage.textContent = `${Math.round(operation.progress)}%`;

      // Update status
      status.textContent = operation.status;

      // Update substeps
      if (operation.substeps && operation.substeps.length > 0) {
        substeps.innerHTML = operation.substeps.map(step => `<div class="substep">${step}</div>`).join('');
      }

      // Update time information
      const elapsed = Math.round((Date.now() - operation.startTime) / 1000);
      timeElapsed.textContent = `${elapsed}s`;

      if (operation.estimatedTimeRemaining && operation.estimatedTimeRemaining > 0) {
        const remaining = Math.round(operation.estimatedTimeRemaining / 1000);
        timeRemaining.textContent = `Est. ${remaining}s remaining`;
        timeRemaining.style.display = 'block';
      }

      // Add completion or error styling
      if (operation.completed) {
        overlay.classList.add('progress-completed');
      } else if (operation.failed) {
        overlay.classList.add('progress-failed');
      }
    },

    /**
     * Update inline progress display
     */
    updateInlineProgressDisplay: function(operation, indicator) {
      const progressBar = indicator.querySelector('.progress-bar');
      const progressFill = indicator.querySelector('.progress-fill');
      const status = indicator.querySelector('.progress-status');

      progressBar.setAttribute('aria-valuenow', operation.progress);
      progressFill.style.width = `${operation.progress}%`;
      status.textContent = operation.status;

      if (operation.completed) {
        indicator.classList.add('progress-completed');
      } else if (operation.failed) {
        indicator.classList.add('progress-failed');
      }
    },

    /**
     * Hide progress display
     */
    hideProgress: function(operationId) {
      const operation = this.activeOperations.get(operationId);
      if (!operation) return;

      if (this.currentGlobalOperation === operationId) {
        this.globalOverlay.style.display = 'none';
        this.globalOverlay.classList.remove('progress-completed', 'progress-failed');
        this.currentGlobalOperation = null;
      }

      const inlineIndicator = this.indicators.get(operationId);
      if (inlineIndicator) {
        inlineIndicator.remove();
        this.indicators.delete(operationId);
      }

      this.activeOperations.delete(operationId);
    },

    /**
     * Simulate progress for operations without real progress tracking
     */
    simulateProgress: function(operationId, options) {
      const { duration, steps } = options;
      const operation = this.activeOperations.get(operationId);
      if (!operation) return;

      let currentStep = 0;
      const stepDuration = duration / steps.length;

      const updateStep = () => {
        if (operation.cancelled || currentStep >= steps.length) return;

        const step = steps[currentStep];
        this.updateProgress(operationId, step.progress, step.status);

        currentStep++;
        
        if (currentStep < steps.length) {
          setTimeout(updateStep, stepDuration);
        } else {
          this.completeOperation(operationId);
        }
      };

      setTimeout(updateStep, stepDuration);
    },

    /**
     * Format file size
     */
    formatFileSize: function(bytes) {
      const units = ['B', 'KB', 'MB', 'GB'];
      let size = bytes;
      let unitIndex = 0;

      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }

      return `${size.toFixed(1)} ${units[unitIndex]}`;
    },

    /**
     * Get active operations
     */
    getActiveOperations: function() {
      return Array.from(this.activeOperations.values());
    },

    /**
     * Cancel all operations
     */
    cancelAllOperations: function() {
      this.activeOperations.forEach((operation, id) => {
        if (operation.cancellable) {
          this.cancelOperation(id);
        }
      });
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => ProgressIndicators.init());
  } else {
    ProgressIndicators.init();
  }

  // Export for use by other scripts
  window.AutoTest = window.AutoTest || {};
  window.AutoTest.ProgressIndicators = ProgressIndicators;

})();