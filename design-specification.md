# AutoTest - Automated Accessibility Testing Tool
## Design Specification v1.0

### Overview
AutoTest is a Python-based automated accessibility testing tool with a graphical user interface that uses MongoDB for storing configuration and test results. The tool enables comprehensive accessibility testing across multiple websites within organized projects.

### Architecture

#### Technology Stack
- **Backend**: Python 3.8+
- **GUI Framework**: tkinter or PyQt6
- **Database**: MongoDB
- **Web Scraping**: Selenium WebDriver, BeautifulSoup
- **Accessibility Testing**: Custom accessibility testing engine (no external dependencies)
- **HTTP Client**: requests, aiohttp

#### Information Architecture

##### Projects
- **Purpose**: Top-level organizational unit for accessibility testing
- **Attributes**:
  - `project_id`: Unique identifier (ObjectId)
  - `name`: Project name (string, required)
  - `description`: Optional project description
  - `created_date`: Timestamp of creation
  - `last_modified`: Timestamp of last modification
  - `websites`: Array of website objects

##### Websites
- **Purpose**: Individual websites within a project
- **Attributes**:
  - `website_id`: Unique identifier (ObjectId)
  - `name`: Optional website name (defaults to domain)
  - `url`: Base URL of the website (string, required)
  - `created_date`: Timestamp of creation
  - `pages`: Array of page objects
  - `scraping_config`: Configuration for web scraping

##### Pages
- **Purpose**: Individual pages/URLs to be tested within a website
- **Attributes**:
  - `page_id`: Unique identifier (ObjectId)
  - `url`: Full URL of the page (string, required)
  - `title`: Page title (extracted during scraping)
  - `discovered_method`: Manual or scraping
  - `last_tested`: Timestamp of last accessibility test
  - `test_results`: Array of test result objects

##### Test Results
- **Purpose**: Store accessibility test results for each page
- **Attributes**:
  - `result_id`: Unique identifier (ObjectId)
  - `test_date`: Timestamp of test execution
  - `test_engine`: Accessibility testing engine used
  - `violations`: Array of accessibility violations
  - `passes`: Array of accessibility checks that passed
  - `incomplete`: Array of incomplete/needs review items
  - `summary`: Test summary statistics

### Database Schema (MongoDB Collections)

#### Projects Collection
```json
{
  "_id": ObjectId,
  "name": "string",
  "description": "string",
  "created_date": Date,
  "last_modified": Date,
  "websites": [
    {
      "website_id": ObjectId,
      "name": "string",
      "url": "string",
      "created_date": Date,
      "scraping_config": {
        "max_pages": 100,
        "depth_limit": 3,
        "include_external": false
      }
    }
  ]
}
```

#### Pages Collection
```json
{
  "_id": ObjectId,
  "project_id": ObjectId,
  "website_id": ObjectId,
  "url": "string",
  "title": "string",
  "discovered_method": "manual|scraping",
  "created_date": Date,
  "last_tested": Date
}
```

#### Test Results Collection
```json
{
  "_id": ObjectId,
  "page_id": ObjectId,
  "test_date": Date,
  "test_engine": "string",
  "violations": [
    {
      "id": "string",
      "impact": "minor|moderate|serious|critical",
      "description": "string",
      "help": "string",
      "helpUrl": "string",
      "nodes": []
    }
  ],
  "passes": [],
  "incomplete": [],
  "summary": {
    "violations": 0,
    "passes": 0,
    "incomplete": 0
  }
}
```

### Core Features

#### Project Management
- **Create Project**: Add new accessibility testing project
- **Edit Project**: Modify project name and description
- **Delete Project**: Remove project and all associated data
- **List Projects**: Display all projects with summary information

#### Website Management
- **Add Website**: Add website to project with URL and optional name
- **Edit Website**: Modify website URL and name
- **Delete Website**: Remove website and all associated pages
- **Configure Scraping**: Set scraping parameters (max pages, depth, etc.)

#### Page Discovery and Management
- **Manual Page Addition**: Manually add specific URLs to test
- **Website Scraping**: Automatically discover pages within a website
  - Configurable maximum number of pages (default: 100)
  - Depth-limited crawling
  - Respect robots.txt
  - Filter by content type (HTML pages only)
- **Page List Management**: View, edit, and remove discovered pages

#### Accessibility Testing
- **Single Page Testing**: Run accessibility tests on individual pages
- **Batch Testing**: Run tests on multiple pages or entire websites
- **Scheduled Testing**: Configure automated testing schedules
- **Custom Testing Engine**: Built-in accessibility testing with configurable rules

#### Results and Reporting
- **Test Results Viewer**: Display accessibility violations and passes
- **Historical Results**: Track test results over time
- **Export Functionality**: Export results to CSV, JSON, or PDF
- **Dashboard**: Overview of project health and statistics

### User Interface Design

#### Main Window
- Menu bar with File, Edit, View, Tools, Help
- Toolbar with common actions (New Project, Run Test, Export)
- Left sidebar: Project tree view
- Main content area: Context-sensitive panels
- Status bar: Current operation status

#### Project Tree Structure
```
├── Project 1
│   ├── Website 1 (example.com)
│   │   ├── Page 1 (/home)
│   │   ├── Page 2 (/about)
│   │   └── Page 3 (/contact)
│   └── Website 2 (test.com)
└── Project 2
```

#### Key Dialogs
- **New Project Dialog**: Project name and description
- **Add Website Dialog**: URL, name, scraping configuration
- **Scraping Progress Dialog**: Real-time scraping status
- **Test Results Dialog**: Detailed accessibility test results
- **Export Dialog**: Format selection and configuration

### Technical Implementation

#### Application Structure
```
autotest/
├── main.py                 # Application entry point
├── gui/
│   ├── __init__.py
│   ├── main_window.py      # Main application window
│   ├── dialogs/            # Dialog classes
│   └── widgets/            # Custom widgets
├── core/
│   ├── __init__.py
│   ├── project_manager.py  # Project CRUD operations
│   ├── scraper.py          # Web scraping functionality
│   ├── accessibility_tester.py # Custom accessibility testing engine
│   └── database.py         # MongoDB interface
├── testing/
│   ├── __init__.py
│   ├── rules/              # Custom accessibility rules
│   ├── checkers/           # Individual accessibility checkers
│   └── reporters/          # Test result formatters
├── models/
│   ├── __init__.py
│   ├── project.py          # Project data model
│   ├── website.py          # Website data model
│   └── page.py             # Page data model
├── utils/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   └── logger.py           # Logging utilities
└── requirements.txt        # Python dependencies
```

#### Configuration
- MongoDB connection settings
- Default scraping parameters
- Accessibility testing engine preferences
- UI preferences and themes

### Security Considerations
- Input validation for all URLs and user inputs
- Safe handling of web scraping (rate limiting, respectful crawling)
- Secure MongoDB connection configuration
- Protection against malicious website content

### Future Enhancements
- Plugin architecture for additional accessibility testing engines
- API for external integrations
- Advanced reporting and analytics
- Multi-user support with authentication
- Cloud deployment options
- Integration with CI/CD pipelines

### Installation and Setup
1. Install Python 3.8+ and MongoDB
2. Install required Python packages: `pip install -r requirements.txt`
3. Configure MongoDB connection in config file
4. Run application: `python main.py`

### Dependencies
- pymongo: MongoDB Python driver
- selenium: Web browser automation
- beautifulsoup4: HTML parsing
- requests: HTTP client library
- tkinter/PyQt6: GUI framework
- Custom accessibility testing modules (no external dependencies)