/*
 * AutoTest - Main JavaScript
 * Accessible interactions and keyboard navigation
 */

(function() {
  'use strict';

  // Feature detection
  const supportsIntersectionObserver = 'IntersectionObserver' in window;
  const supportsCustomElements = 'customElements' in window;
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /**
   * Accessibility utilities
   */
  const A11y = {
    // Announce to screen readers
    announce: function(message, priority = 'polite') {
      const announcer = document.createElement('div');
      announcer.setAttribute('aria-live', priority);
      announcer.setAttribute('aria-atomic', 'true');
      announcer.className = 'sr-only';
      document.body.appendChild(announcer);
      
      announcer.textContent = message;
      
      // Clean up after announcement
      setTimeout(() => {
        document.body.removeChild(announcer);
      }, 1000);
    },

    // Trap focus within an element
    trapFocus: function(element) {
      const focusableElements = element.querySelectorAll(
        'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select, [tabindex]:not([tabindex="-1"])'
      );
      
      if (focusableElements.length === 0) return;
      
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      
      element.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              lastElement.focus();
              e.preventDefault();
            }
          } else {
            if (document.activeElement === lastElement) {
              firstElement.focus();
              e.preventDefault();
            }
          }
        }
      });
      
      // Focus first element
      firstElement.focus();
    },

    // Manage focus for dynamic content
    manageFocus: function(trigger, target) {
      if (target) {
        target.focus();
        
        // Return focus to trigger when target is closed/hidden
        const observer = new MutationObserver(function(mutations) {
          mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && 
                mutation.attributeName === 'hidden' && 
                target.hidden) {
              trigger.focus();
              observer.disconnect();
            }
          });
        });
        
        observer.observe(target, { attributes: true });
      }
    }
  };

  /**
   * Mobile navigation menu
   */
  function initMobileMenu() {
    const menuButton = document.querySelector('.mobile-menu-btn');
    const navigation = document.querySelector('.main-nav');
    
    if (!menuButton || !navigation) return;
    
    menuButton.addEventListener('click', function() {
      const isExpanded = menuButton.getAttribute('aria-expanded') === 'true';
      
      menuButton.setAttribute('aria-expanded', !isExpanded);
      navigation.classList.toggle('nav-open');
      
      if (!isExpanded) {
        // Menu is opening
        A11y.trapFocus(navigation);
        A11y.announce('Navigation menu opened');
      } else {
        // Menu is closing
        A11y.announce('Navigation menu closed');
        menuButton.focus();
      }
    });
    
    // Close menu on Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && navigation.classList.contains('nav-open')) {
        menuButton.setAttribute('aria-expanded', 'false');
        navigation.classList.remove('nav-open');
        menuButton.focus();
        A11y.announce('Navigation menu closed');
      }
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
      if (!navigation.contains(e.target) && 
          !menuButton.contains(e.target) && 
          navigation.classList.contains('nav-open')) {
        menuButton.setAttribute('aria-expanded', 'false');
        navigation.classList.remove('nav-open');
      }
    });
  }

  /**
   * Flash message handling
   */
  function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(function(message) {
      const closeButton = message.querySelector('.flash-close');
      
      if (closeButton) {
        closeButton.addEventListener('click', function() {
          message.style.opacity = '0';
          message.style.transform = 'translateY(-10px)';
          
          setTimeout(function() {
            message.remove();
          }, prefersReducedMotion ? 0 : 300);
        });
      }
      
      // Auto-dismiss success messages after 5 seconds
      if (message.classList.contains('flash-success')) {
        setTimeout(function() {
          if (message.parentNode) {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            
            setTimeout(function() {
              message.remove();
            }, prefersReducedMotion ? 0 : 300);
          }
        }, 5000);
      }
    });
  }

  /**
   * Enhanced keyboard navigation
   */
  function initKeyboardNavigation() {
    // Add visible focus indicators for keyboard users
    let isTabbing = false;
    
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Tab') {
        isTabbing = true;
        document.body.classList.add('using-keyboard');
      }
    });
    
    document.addEventListener('mousedown', function() {
      isTabbing = false;
      document.body.classList.remove('using-keyboard');
    });
    
    // Skip link functionality
    const skipLink = document.querySelector('.skip-link');
    if (skipLink) {
      skipLink.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(skipLink.getAttribute('href'));
        if (target) {
          target.focus();
          target.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth' });
        }
      });
    }
    
    // Card keyboard interaction
    document.querySelectorAll('.project-card, .action-card').forEach(function(card) {
      const link = card.querySelector('a');
      
      if (link) {
        card.setAttribute('tabindex', '0');
        card.setAttribute('role', 'button');
        
        card.addEventListener('keydown', function(e) {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            link.click();
          }
        });
        
        // Visual feedback
        card.addEventListener('focus', function() {
          card.style.boxShadow = 'var(--shadow-md)';
          card.style.transform = 'translateY(-1px)';
        });
        
        card.addEventListener('blur', function() {
          card.style.boxShadow = '';
          card.style.transform = '';
        });
      }
    });
  }

  /**
   * Form enhancements
   */
  function initFormEnhancements() {
    // Enhanced form validation
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
      // Live validation feedback
      const inputs = form.querySelectorAll('input, textarea, select');
      
      inputs.forEach(function(input) {
        input.addEventListener('blur', function() {
          validateField(input);
        });
        
        input.addEventListener('input', function() {
          // Clear previous errors on input
          clearFieldError(input);
        });
      });
      
      // Enhanced form submission
      form.addEventListener('submit', function(e) {
        let isValid = true;
        
        inputs.forEach(function(input) {
          if (!validateField(input)) {
            isValid = false;
          }
        });
        
        if (!isValid) {
          e.preventDefault();
          
          // Focus first error field
          const firstError = form.querySelector('.field-error');
          if (firstError) {
            const errorField = firstError.previousElementSibling;
            if (errorField) {
              errorField.focus();
              A11y.announce('Form has errors. Please correct them and try again.', 'assertive');
            }
          }
        }
      });
    });
    
    function validateField(field) {
      const value = field.value.trim();
      const isRequired = field.hasAttribute('required');
      let isValid = true;
      let errorMessage = '';
      
      // Clear previous errors
      clearFieldError(field);
      
      // Required field validation
      if (isRequired && !value) {
        isValid = false;
        errorMessage = 'This field is required.';
      }
      
      // Email validation
      if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          isValid = false;
          errorMessage = 'Please enter a valid email address.';
        }
      }
      
      // URL validation
      if (field.type === 'url' && value) {
        try {
          new URL(value);
        } catch {
          isValid = false;
          errorMessage = 'Please enter a valid URL starting with http:// or https://';
        }
      }
      
      // Show error if invalid
      if (!isValid) {
        showFieldError(field, errorMessage);
      }
      
      return isValid;
    }
    
    function showFieldError(field, message) {
      field.setAttribute('aria-invalid', 'true');
      field.classList.add('field-invalid');
      
      const errorId = field.id + '-error';
      let errorElement = document.getElementById(errorId);
      
      if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.id = errorId;
        errorElement.className = 'field-error';
        errorElement.setAttribute('role', 'alert');
        field.parentNode.insertBefore(errorElement, field.nextSibling);
      }
      
      errorElement.textContent = message;
      field.setAttribute('aria-describedby', errorId);
    }
    
    function clearFieldError(field) {
      field.removeAttribute('aria-invalid');
      field.classList.remove('field-invalid');
      
      const errorId = field.id + '-error';
      const errorElement = document.getElementById(errorId);
      
      if (errorElement) {
        errorElement.remove();
        field.removeAttribute('aria-describedby');
      }
    }
  }

  /**
   * Progressive enhancement for data tables
   */
  function initDataTables() {
    const tables = document.querySelectorAll('table');
    
    tables.forEach(function(table) {
      // Add responsive wrapper
      if (!table.parentNode.classList.contains('table-responsive')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-responsive';
        wrapper.setAttribute('tabindex', '0');
        wrapper.setAttribute('role', 'region');
        wrapper.setAttribute('aria-label', 'Data table');
        
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
      }
      
      // Enhance sortable tables
      const sortableHeaders = table.querySelectorAll('th[data-sort]');
      
      sortableHeaders.forEach(function(header) {
        header.setAttribute('tabindex', '0');
        header.setAttribute('role', 'button');
        header.style.cursor = 'pointer';
        
        header.addEventListener('click', function() {
          sortTable(table, header);
        });
        
        header.addEventListener('keydown', function(e) {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            sortTable(table, header);
          }
        });
      });
    });
  }

  /**
   * Animation and motion utilities
   */
  function initAnimations() {
    if (prefersReducedMotion) {
      // Disable animations for users who prefer reduced motion
      document.documentElement.style.setProperty('--transition-fast', '0ms');
      document.documentElement.style.setProperty('--transition-base', '0ms');
      document.documentElement.style.setProperty('--transition-slow', '0ms');
      return;
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function(link) {
      link.addEventListener('click', function(e) {
        const targetId = this.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
          e.preventDefault();
          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
          
          // Update focus
          if (targetElement.tabIndex === -1) {
            targetElement.tabIndex = -1;
          }
          targetElement.focus();
        }
      });
    });
    
    // Fade in animation for new content
    if (supportsIntersectionObserver) {
      const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('fade-in');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1 });
      
      document.querySelectorAll('.fade-on-scroll').forEach(function(element) {
        observer.observe(element);
      });
    }
  }

  /**
   * Initialize all components
   */
  function init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
      return;
    }
    
    try {
      initMobileMenu();
      initFlashMessages();
      initKeyboardNavigation();
      initFormEnhancements();
      initDataTables();
      initAnimations();
      
      // Announce app is ready for screen reader users
      setTimeout(function() {
        A11y.announce('AutoTest application is ready');
      }, 1000);
      
    } catch (error) {
      console.error('Error initializing AutoTest:', error);
    }
  }

  // Start initialization
  init();

  // Export utilities for other scripts
  window.AutoTest = {
    A11y: A11y,
    prefersReducedMotion: prefersReducedMotion
  };

})();