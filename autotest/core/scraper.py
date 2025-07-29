"""
Web scraping module using Selenium WebDriver for AutoTest application
"""

import time
import re
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import requests

from autotest.core.database import DatabaseConnection
from autotest.core.website_manager import WebsiteManager
from autotest.models.project import ProjectRepository
from autotest.utils.logger import LoggerMixin
from autotest.utils.config import Config


class WebScraper(LoggerMixin):
    """Web scraper using Selenium WebDriver for page discovery"""
    
    def __init__(self, config: Config, db_connection: DatabaseConnection):
        """
        Initialize web scraper
        
        Args:
            config: Application configuration
            db_connection: Database connection instance
        """
        self.config = config
        self.db_connection = db_connection
        self.project_repo = ProjectRepository(db_connection)
        self.website_manager = WebsiteManager(db_connection)
        self.driver: Optional[webdriver.Chrome | webdriver.Firefox] = None
        
        # Scraping configuration
        self.request_delay = config.get('scraping.request_delay', 1.0)
        self.user_agent = config.get('scraping.user_agent', 'AutoTest Accessibility Scanner/1.0')
        self.timeout = config.get('testing.timeout', 30)
        self.website_config = {}
    
    def configure(self, website_config: Dict[str, Any]) -> None:
        """
        Configure scraper with website-specific settings
        
        Args:
            website_config: Website scraping configuration dictionary
        """
        self.website_config = website_config
        self.logger.debug(f"Scraper configured with: {website_config}")
    
    def _setup_driver(self, browser: str = 'chrome', headless: bool = True) -> bool:
        """
        Set up Selenium WebDriver
        
        Args:
            browser: Browser to use ('chrome' or 'firefox')
            headless: Run browser in headless mode
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            if browser.lower() == 'chrome':
                options = ChromeOptions()
                if headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument(f'--user-agent={self.user_agent}')
                options.add_argument('--window-size=1920,1080')
                
                self.driver = webdriver.Chrome(options=options)
                
            elif browser.lower() == 'firefox':
                options = FirefoxOptions()
                if headless:
                    options.add_argument('--headless')
                options.set_preference("general.useragent.override", self.user_agent)
                
                self.driver = webdriver.Firefox(options=options)
                
            else:
                self.logger.error(f"Unsupported browser: {browser}")
                return False
            
            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(self.timeout)
            
            self.logger.info(f"WebDriver setup successful: {browser}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            return False
    
    def _cleanup_driver(self) -> None:
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Error cleaning up WebDriver: {e}")
            finally:
                self.driver = None
    
    def _can_fetch_url(self, base_url: str, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt
        
        Args:
            base_url: Base URL of the website
            url: URL to check
        
        Returns:
            True if URL can be fetched, False otherwise
        """
        try:
            parsed_base = urlparse(base_url)
            robots_url = f"{parsed_base.scheme}://{parsed_base.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch(self.user_agent, url)
            
        except Exception as e:
            self.logger.warning(f"Error checking robots.txt for {url}: {e}")
            # If we can't check robots.txt, assume we can fetch
            return True
    
    def _is_valid_page_url(self, url: str, base_domain: str, include_external: bool = False) -> bool:
        """
        Check if URL is valid for scraping
        
        Args:
            url: URL to validate
            base_domain: Base domain of the website
            include_external: Whether to include external links
        
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            
            # Skip non-HTTP(S) URLs
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Skip common non-HTML files
            path = parsed.path.lower()
            excluded_extensions = [
                '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.zip', '.rar', '.tar', '.gz',
                '.css', '.js', '.xml', '.json',
                '.mp3', '.mp4', '.avi', '.mov', '.wmv'
            ]
            
            if any(path.endswith(ext) for ext in excluded_extensions):
                return False
            
            # Check domain restrictions
            if not include_external:
                parsed_base = urlparse(base_domain)
                if parsed.netloc != parsed_base.netloc:
                    return False
            
            # Skip common patterns that are not content pages
            excluded_patterns = [
                r'/admin/', r'/wp-admin/', r'/login/', r'/logout/',
                r'/api/', r'/ajax/', r'/rpc/',
                r'/feed/', r'/rss/', r'/atom/',
                r'\.php\?', r'\.asp\?', r'\.jsp\?'
            ]
            
            if any(re.search(pattern, url, re.IGNORECASE) for pattern in excluded_patterns):
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Error validating URL {url}: {e}")
            return False
    
    def _extract_links_from_page(self, url: str, base_url: str) -> List[str]:
        """
        Extract all links from a page
        
        Args:
            url: URL of the page
            base_url: Base URL for resolving relative links
        
        Returns:
            List of discovered URLs
        """
        links = []
        
        try:
            self.logger.debug(f"Extracting links from: {url}")
            
            # Navigate to the page
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page title
            title = self.driver.title
            
            # Find all anchor tags with href attributes
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href]")
            
            for element in link_elements:
                try:
                    href = element.get_attribute('href')
                    if href:
                        # Resolve relative URLs
                        absolute_url = urljoin(base_url, href)
                        
                        # Clean up the URL (remove fragments)
                        parsed = urlparse(absolute_url)
                        clean_url = urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, parsed.query, ''
                        ))
                        
                        links.append(clean_url)
                        
                except Exception as e:
                    self.logger.debug(f"Error processing link element: {e}")
                    continue
            
            self.logger.debug(f"Extracted {len(links)} links from {url}")
            return links
            
        except TimeoutException:
            self.logger.warning(f"Timeout loading page: {url}")
            return []
        except WebDriverException as e:
            self.logger.warning(f"WebDriver error loading page {url}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error extracting links from {url}: {e}")
            return []
    
    def _get_page_title(self, url: str) -> str:
        """
        Get the title of a page
        
        Args:
            url: URL of the page
        
        Returns:
            Page title or empty string if not found
        """
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "title"))
            )
            return self.driver.title
        except Exception as e:
            self.logger.debug(f"Could not get title for {url}: {e}")
            return ""
    
    def scrape_website(self, project_id: str, website_id: str, 
                      max_pages: int = 100, depth_limit = 'unlimited',
                      include_external: bool = False) -> Dict[str, Any]:
        """
        Scrape a website to discover pages
        
        Args:
            project_id: Project ID
            website_id: Website ID
            max_pages: Maximum number of pages to discover
            depth_limit: Maximum crawling depth ('unlimited' or integer)
            include_external: Include external links
        
        Returns:
            Dictionary with scraping results
        """
        try:
            # Get project and website info
            project = self.project_repo.get_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
            
            website = project.get_website(website_id)
            if not website:
                return {
                    'success': False,
                    'error': 'Website not found'
                }
            
            base_url = website.url
            self.logger.info(f"Starting website scrape: {base_url}")
            
            # Setup WebDriver
            if not self._setup_driver():
                return {
                    'success': False,
                    'error': 'Failed to setup web browser'
                }
            
            try:
                # Initialize tracking variables
                discovered_urls: Set[str] = set()
                processed_urls: Set[str] = set()
                url_queue: List[tuple] = [(base_url, 0)]  # (url, depth)
                results = {
                    'added': [],
                    'skipped': [],
                    'errors': []
                }
                
                while url_queue and len(discovered_urls) < max_pages:
                    current_url, depth = url_queue.pop(0)
                    
                    # Skip if already processed or depth exceeded
                    if current_url in processed_urls or (depth_limit != 'unlimited' and depth > depth_limit):
                        continue
                    
                    processed_urls.add(current_url)
                    
                    # Check robots.txt
                    if not self._can_fetch_url(base_url, current_url):
                        self.logger.debug(f"Robots.txt disallows: {current_url}")
                        continue
                    
                    # Extract links from current page
                    links = self._extract_links_from_page(current_url, base_url)
                    
                    # Add current URL to discovered set
                    if self._is_valid_page_url(current_url, base_url, include_external):
                        discovered_urls.add(current_url)
                    
                    # Process discovered links
                    for link in links:
                        if len(discovered_urls) >= max_pages:
                            break
                            
                        if link not in processed_urls and link not in [u for u, d in url_queue]:
                            if self._is_valid_page_url(link, base_url, include_external):
                                discovered_urls.add(link)
                                
                                # Add to queue for further crawling if within depth limit
                                if depth_limit == 'unlimited' or depth < depth_limit:
                                    url_queue.append((link, depth + 1))
                    
                    # Add delay between requests
                    time.sleep(self.request_delay)
                
                # Add discovered URLs to database
                discovered_list = list(discovered_urls)[:max_pages]
                
                for url in discovered_list:
                    try:
                        # Get page title
                        title = self._get_page_title(url)
                        
                        # Add page to website
                        result = self.website_manager.add_page_to_website(
                            project_id, website_id, url, title, "scraping"
                        )
                        
                        if result['success']:
                            results['added'].append({
                                'url': url,
                                'title': title,
                                'page_id': result['page_id']
                            })
                        else:
                            if 'already exists' in result['error']:
                                results['skipped'].append({
                                    'url': url,
                                    'reason': result['error']
                                })
                            else:
                                results['errors'].append({
                                    'url': url,
                                    'error': result['error']
                                })
                    
                    except Exception as e:
                        results['errors'].append({
                            'url': url,
                            'error': str(e)
                        })
                
                self.logger.info(f"Website scraping completed. Added {len(results['added'])} pages")
                
                return {
                    'success': True,
                    'results': results,
                    'summary': {
                        'total_discovered': len(discovered_urls),
                        'total_processed': len(processed_urls),
                        'pages_added': len(results['added']),
                        'pages_skipped': len(results['skipped']),
                        'errors': len(results['errors']),
                        'max_pages_reached': len(discovered_urls) >= max_pages
                    }
                }
                
            finally:
                self._cleanup_driver()
                
        except Exception as e:
            self.logger.error(f"Error during website scraping: {e}")
            self._cleanup_driver()
            return {
                'success': False,
                'error': f'Scraping failed: {str(e)}'
            }
    
    def validate_page_accessibility(self, url: str) -> Dict[str, Any]:
        """
        Basic validation that a page is accessible for testing
        
        Args:
            url: URL to validate
        
        Returns:
            Dictionary with validation results
        """
        try:
            if not self._setup_driver():
                return {
                    'success': False,
                    'error': 'Failed to setup web browser'
                }
            
            try:
                self.driver.get(url)
                
                # Wait for page to load
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check if page loaded successfully
                title = self.driver.title
                current_url = self.driver.current_url
                
                # Basic accessibility checks
                has_title = bool(title.strip())
                has_h1 = len(self.driver.find_elements(By.TAG_NAME, "h1")) > 0
                has_main = len(self.driver.find_elements(By.TAG_NAME, "main")) > 0
                
                return {
                    'success': True,
                    'accessible': True,
                    'title': title,
                    'current_url': current_url,
                    'basic_checks': {
                        'has_title': has_title,
                        'has_h1': has_h1,
                        'has_main': has_main
                    }
                }
                
            finally:
                self._cleanup_driver()
                
        except TimeoutException:
            self._cleanup_driver()
            return {
                'success': True,
                'accessible': False,
                'error': 'Page load timeout'
            }
        except WebDriverException as e:
            self._cleanup_driver()
            return {
                'success': True,
                'accessible': False,
                'error': f'WebDriver error: {str(e)}'
            }
        except Exception as e:
            self._cleanup_driver()
            self.logger.error(f"Error validating page accessibility: {e}")
            return {
                'success': False,
                'error': f'Validation failed: {str(e)}'
            }