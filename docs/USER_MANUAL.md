# AutoTest User Manual - Version 1.0

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Project Management](#project-management)
4. [Website Management](#website-management)
5. [Running Tests](#running-tests)
6. [Understanding Test Results](#understanding-test-results)
7. [Generating Reports](#generating-reports)
8. [History and Snapshots](#history-and-snapshots)
9. [Scheduling Automated Tests](#scheduling-automated-tests)
10. [Troubleshooting](#troubleshooting)
11. [API Reference](#api-reference)
12. [FAQ](#faq)

---

## Introduction

AutoTest is a comprehensive web-based accessibility testing platform designed to help organizations ensure their websites comply with WCAG (Web Content Accessibility Guidelines) standards. The platform provides automated testing, detailed reporting, historical tracking, and scheduling capabilities to streamline accessibility compliance efforts.

### Key Features

- **Automated Accessibility Testing**: Run comprehensive WCAG compliance checks
- **Project & Website Management**: Organize testing across multiple projects and sites
- **Detailed Reporting**: Generate executive summaries, technical reports, and compliance audits
- **Historical Tracking**: Monitor accessibility improvements over time with snapshots
- **Scheduled Testing**: Automate regular accessibility checks
- **User-Friendly Interface**: Intuitive web interface designed with accessibility in mind

### System Requirements

- **Server**: Linux/macOS/Windows with Python 3.8+
- **Database**: MongoDB 4.4+
- **Browser**: Modern web browser (Chrome, Firefox, Safari, Edge)
- **Memory**: Minimum 4GB RAM recommended
- **Storage**: 1GB+ for test results and reports

---

## Getting Started

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/bobdodd/autoTest.git
   cd autoTest
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Database**
   - Ensure MongoDB is running on `localhost:27017`
   - The application will create the `autotest` database automatically

5. **Start the Application**
   ```bash
   python -m autotest.web.app
   ```

6. **Access the Web Interface**
   - Open your browser to `http://localhost:5000`
   - You should see the AutoTest dashboard

### Initial Setup

Upon first accessing AutoTest, you'll see the main dashboard. To begin testing:

1. **Create Your First Project** - Click "Create Project" to organize your websites
2. **Add a Website** - Add the website you want to test to your project  
3. **Run Your First Test** - Use "Run All Tests" to scan your website
4. **View Results** - Review findings in the dashboard and generate reports

---

## Project Management

Projects in AutoTest serve as containers for organizing related websites and their accessibility testing efforts. This is particularly useful for organizations managing multiple websites or different development environments.

### Creating a Project

1. Navigate to **Projects** in the main menu
2. Click **"Create New Project"**
3. Fill in the project details:
   - **Name**: Descriptive name for your project (e.g., "Corporate Website", "E-commerce Platform")
   - **Description**: Optional detailed description of the project's scope and goals
4. Click **"Create Project"**

### Managing Projects

#### Viewing Projects
- The **Projects** page lists all your projects with key statistics
- Click on any project name to view detailed information
- Each project shows: creation date, number of websites, recent test activity

#### Editing Projects
1. Go to the project detail page
2. Click **"Edit Project"**
3. Modify the name or description as needed
4. Save your changes

#### Deleting Projects
⚠️ **Warning**: Deleting a project will remove all associated websites, test results, and reports.

1. Go to the project detail page
2. Click **"Delete Project"**
3. Confirm the deletion when prompted

### Project Dashboard

Each project has its own dashboard showing:
- **Website Overview**: All websites in the project
- **Recent Test Results**: Latest accessibility findings
- **Testing Progress**: Status of ongoing or scheduled tests
- **Quick Actions**: Run tests, generate reports, manage websites

---

## Website Management

Websites are the individual web properties you want to test for accessibility compliance. Each website belongs to a project and contains multiple pages that will be tested.

### Adding a Website

1. Navigate to your project's detail page
2. Click **"Add Website"**
3. Configure the website settings:

#### Basic Information
- **Website Name**: Human-readable name (e.g., "Main Company Site")
- **Base URL**: The root URL to start testing from (e.g., `https://example.com`)
- **Description**: Optional notes about the website

#### Scraping Configuration
- **Max Depth**: How many link levels to follow (default: 3)
- **Max Pages**: Maximum number of pages to discover (default: 100)
- **Respect robots.txt**: Whether to follow robots.txt restrictions
- **Follow External Links**: Whether to test external links (usually disabled)

#### Testing Parameters
- **Custom Rules**: Enable additional accessibility rules beyond WCAG
- **Screenshot on Error**: Capture screenshots when violations are found
- **Test Timeout**: Maximum time to spend testing each page

### Managing Websites

#### Viewing Website Details
- Click on any website name to see its detailed information
- The website detail page shows:
  - All discovered pages
  - Recent test results
  - Configuration settings
  - Test history

#### Editing Websites
1. Go to the website detail page
2. Click **"Edit Website"**
3. Modify settings as needed
4. **Note**: Changing the base URL will require re-discovering pages

#### Removing Websites
1. Go to the website detail page
2. Click **"Remove Website"**
3. Confirm removal (this deletes all associated test data)

### Page Discovery

AutoTest automatically discovers pages on your website by:
1. Starting at the base URL
2. Following internal links up to the specified depth
3. Respecting the maximum page limit
4. Filtering out duplicate URLs and external links

You can view all discovered pages in the website detail view, where each page shows:
- **URL**: The full page address
- **Title**: The page title as discovered
- **Last Tested**: When accessibility tests were last run
- **Issues Found**: Number of accessibility violations detected

---

## Running Tests

AutoTest provides several ways to run accessibility tests depending on your needs:

### Test Types

#### Full Project Testing
- Tests all websites and pages within a project
- Most comprehensive option for complete accessibility audits
- Recommended for initial assessments and major releases

#### Single Website Testing  
- Tests all pages within one specific website
- Useful for focused testing after website updates
- Faster than full project testing

#### Individual Page Testing
- Tests a single specific page
- Ideal for debugging specific accessibility issues
- Quick validation after fixing problems

### Starting Tests

#### From Project Dashboard
1. Navigate to your project
2. Click **"Run All Tests"** for comprehensive testing
3. Monitor progress in the testing dashboard

#### From Website Details
1. Go to the specific website page
2. Click **"Test Website"** to test all pages in that site
3. Or click **"Test Page"** next to individual pages

#### From Testing Dashboard
1. Navigate to **Testing** in the main menu
2. Use the **"Run New Test"** section to configure:
   - Project or website selection
   - Test type (accessibility, performance, full suite)
   - Priority level (normal, high, urgent)

### Monitoring Test Progress

#### Testing Dashboard
The testing dashboard provides real-time information about:
- **Active Tests**: Currently running test jobs
- **Queue Status**: Tests waiting to be executed
- **Recent Results**: Completed tests with summary statistics
- **System Status**: Overall testing system health

#### Test Job Details
Click on any active test to see:
- **Progress**: Percentage completed and pages tested
- **Current Activity**: Which page is being tested
- **Estimated Time**: Remaining time to completion
- **Partial Results**: Issues found so far

### Test Results

#### Immediate Results
- Basic statistics appear in the dashboard as tests complete
- **Issues Found**: Total number of accessibility violations
- **Pages Tested**: Number of pages successfully scanned
- **Test Duration**: Time taken to complete the testing

#### Detailed Analysis
For comprehensive results analysis:
1. Navigate to **Testing** → **Results**
2. Select your project or website
3. Review detailed findings including:
   - Violation severity breakdown (Critical, Serious, Moderate, Minor)
   - WCAG guideline compliance status
   - Specific element-level issues
   - Recommendations for fixes

### Understanding Test Output

#### Violation Severity Levels
- **Critical**: Serious barriers that prevent access for users with disabilities
- **Serious**: Significant issues that severely impact usability
- **Moderate**: Problems that create difficulties but don't completely block access
- **Minor**: Best practice violations that should be addressed for optimal accessibility

#### WCAG Compliance Levels
- **Level A**: Basic accessibility features
- **Level AA**: Standard level for most legal requirements
- **Level AAA**: Enhanced accessibility (not required for general compliance)

---

## Understanding Test Results

AutoTest provides comprehensive accessibility analysis with detailed explanations to help you understand and fix issues.

### Results Dashboard

After tests complete, the results dashboard shows:

#### Summary Statistics
- **Total Violations**: Complete count of accessibility issues found
- **Compliance Score**: Overall accessibility percentage (0-100%)
- **WCAG Level**: Highest compliance level achieved (A, AA, AAA)
- **Pages Tested**: Number of pages successfully analyzed

#### Violation Breakdown
- **By Severity**: Critical, Serious, Moderate, and Minor issues
- **By WCAG Guideline**: Issues organized by accessibility principles
- **By Page**: Which pages have the most problems
- **By Element Type**: Common problem areas (images, forms, navigation)

### Detailed Violation Analysis

#### Individual Violation Details
Each accessibility issue includes:

**Problem Description**
- Clear explanation of what the violation means
- Why it impacts users with disabilities
- Which WCAG guidelines are affected

**Location Information**  
- Specific page URL where the issue occurs
- HTML element selector for precise identification
- Screenshot highlighting the problematic element (when available)

**Remediation Guidance**
- Step-by-step instructions to fix the issue
- Code examples showing correct implementation
- Links to relevant WCAG documentation

#### Common Violation Types

**Missing Alt Text**
- Images without alternative text descriptions
- Impact: Screen readers cannot describe images to blind users
- Fix: Add meaningful `alt` attributes to all images

**Color Contrast Issues**
- Text that doesn't have sufficient contrast against backgrounds  
- Impact: Users with low vision cannot read the content
- Fix: Increase color contrast to meet WCAG standards (4.5:1 for normal text)

**Keyboard Navigation Problems**
- Interactive elements not accessible via keyboard
- Impact: Users who cannot use a mouse are blocked from functionality
- Fix: Ensure all interactive elements can be reached and activated with keyboard

**Missing Form Labels**
- Form inputs without associated labels
- Impact: Screen reader users cannot understand form fields
- Fix: Associate every form input with a descriptive label

**Heading Structure Issues**
- Improper heading hierarchy (h1, h2, h3, etc.)
- Impact: Screen readers rely on headings for page navigation
- Fix: Use headings in logical order without skipping levels

### Filtering and Sorting Results

#### Filter Options
- **By Severity**: Show only Critical, Serious, Moderate, or Minor issues
- **By WCAG Level**: Filter to A, AA, or AAA compliance issues
- **By Page**: View issues for specific pages only
- **By Guideline**: Focus on particular WCAG principles

#### Sorting Options
- **By Impact**: Most severe issues first
- **By Frequency**: Most common problems across pages
- **By Page**: Group all issues by page location
- **By Fix Complexity**: Simple fixes first, then complex ones

### Exporting Results

#### Available Formats
- **PDF Report**: Professional document for stakeholders
- **CSV Export**: Spreadsheet format for tracking and analysis
- **JSON Data**: Raw data for integration with other tools
- **HTML Summary**: Web-friendly overview for sharing

#### Export Options
1. Go to the test results page
2. Click **"Export Results"**
3. Choose your preferred format
4. Select which data to include:
   - Summary statistics only
   - Detailed violation list
   - Screenshots and evidence
   - Remediation recommendations

---

## Generating Reports

AutoTest provides multiple report formats tailored for different audiences and purposes.

### Report Types

#### Executive Summary
**Audience**: Leadership, stakeholders, project managers
**Purpose**: High-level overview of accessibility status

**Contents**:
- Overall compliance score and WCAG level achieved
- Key statistics and trends
- Risk assessment and legal implications
- High-level recommendations and next steps
- Budget and timeline estimates for remediation

#### Technical Detailed Report  
**Audience**: Developers, QA engineers, accessibility specialists
**Purpose**: Comprehensive technical analysis for implementation

**Contents**:
- Complete violation inventory with technical details
- Code examples and fix instructions
- Element-level analysis with selectors
- Testing methodology and configuration details
- Detailed remediation guidelines

#### Compliance Audit Report
**Audience**: Legal teams, compliance officers, auditors
**Purpose**: Formal compliance assessment for legal/regulatory purposes

**Contents**:
- WCAG compliance checklist with pass/fail status
- Legal risk assessment and compliance gaps
- Certification readiness evaluation
- Recommended remediation timeline
- Documentation for compliance records

### Generating Reports

#### Quick Report Generation
1. Navigate to **Reports** in the main menu
2. Click **"Generate New Report"**
3. Select report configuration:
   - **Project**: Choose which project to report on
   - **Report Type**: Executive, Technical, or Compliance
   - **Time Range**: Data period to include (last 30 days, etc.)
   - **Format**: HTML for web viewing or PDF for distribution

#### Advanced Report Configuration

**Data Sources**
- **Current Test Results**: Latest accessibility findings
- **Historical Trends**: Changes over time
- **Comparison Data**: Before/after analysis
- **Custom Filters**: Specific pages, severity levels, or guidelines

**Customization Options**
- **Company Branding**: Add your organization's logo and colors
- **Executive Summary**: Include/exclude high-level overview
- **Technical Details**: Control level of technical information
- **Screenshots**: Include visual evidence of issues
- **Remediation Guidance**: Add fix instructions and timelines

### Report Management

#### Viewing Generated Reports
- The **Reports** dashboard lists all generated reports
- Each report shows: generation date, report type, project, status
- Click on any report to view or download

#### Report Formats

**HTML Reports**
- Interactive web-based format
- Clickable sections and navigation
- Embedded charts and visualizations  
- Easy sharing via URL
- Mobile-friendly responsive design

**PDF Reports**
- Professional print-ready format
- Consistent formatting and branding
- Suitable for formal documentation
- Easy email distribution
- Archival quality for long-term storage

#### Sharing and Distribution

**Direct Links**
- HTML reports generate shareable URLs
- Access control ensures only authorized viewing
- Links remain active until report is deleted

**Download Options**
- PDF reports can be downloaded immediately
- Bulk download multiple reports
- Integration with cloud storage services

**Email Distribution**
- Send reports directly from the platform
- Include custom message and context
- Automatic PDF attachment for stakeholders

### Report Customization

#### Templates
- **Standard Templates**: Pre-configured report layouts
- **Custom Templates**: Create organization-specific formats
- **Template Library**: Save and reuse successful configurations

#### Branding Options
- **Logo Integration**: Add company logo to reports
- **Color Schemes**: Match organizational brand colors
- **Header/Footer**: Custom headers with contact information
- **Watermarks**: Add confidentiality or draft markings

---

## History and Snapshots

The History module provides powerful tools for tracking accessibility improvements over time and comparing different testing periods.

### Understanding Snapshots

#### What are Snapshots?
Snapshots are point-in-time captures of your website's accessibility status, including:
- Total violations found
- Breakdown by severity level (Critical, Serious, Moderate, Minor)
- Accessibility score calculation
- WCAG compliance percentage
- Number of pages tested
- Testing date and configuration

#### Automatic Snapshot Creation
AutoTest automatically creates snapshots when:
- Test runs complete successfully
- Significant changes in violation counts are detected
- Scheduled tests execute
- Manual test runs finish

#### Manual Snapshot Creation
You can also create snapshots manually:
1. Navigate to **History** → **Snapshots**
2. Click **"Create Snapshot"**
3. Select the project to capture
4. Add optional notes describing the snapshot context
5. The system will gather current test data and create the snapshot

### Viewing Historical Data

#### Snapshots Dashboard
The snapshots dashboard provides:
- **Timeline View**: Chronological list of all snapshots
- **Filtering Options**: By project, date range, or results per page
- **Summary Statistics**: Accessibility scores, violation counts, compliance status
- **Trend Indicators**: Visual indicators showing improvement or regression

#### Snapshot Details
Each snapshot displays:
- **Date and Time**: When the snapshot was created
- **Project Information**: Which project was captured
- **Accessibility Metrics**: Score, violations, compliance level
- **Test Coverage**: Number of pages included
- **Notes**: Any comments added during creation

### Comparing Periods

#### Snapshot Comparison Tool
The comparison tool helps identify changes between different time periods:

1. Navigate to **History** → **Compare Periods**
2. Choose comparison method:
   - **Date Range Comparison**: Compare two specific time periods
   - **Specific Snapshots**: Compare two individual snapshots

#### Date Range Comparison
- Select two time periods (start and end dates for each)
- System automatically finds representative data for each period
- Shows aggregated changes across the date ranges
- Useful for comparing "before/after" major updates

#### Specific Snapshot Comparison  
- Choose exactly two snapshots to compare
- Shows precise differences between those specific points in time
- Ideal for detailed analysis of specific changes
- Best for comparing known good/bad states

### Analyzing Trends

#### Trend Visualization
The history system tracks several key metrics over time:

**Accessibility Score Trends**
- Overall accessibility percentage changes
- Identifies improvement or degradation patterns
- Highlights periods of significant change

**Violation Count Trends**
- Total violations over time
- Breakdown by severity level
- Shows which types of issues are being addressed

**WCAG Compliance Progress**
- Compliance level changes (A, AA, AAA)
- Progress toward specific compliance goals
- Identification of compliance regression

#### Historical Insights
AutoTest provides automated insights based on historical data:

**Improvement Detection**
- Identifies periods of significant accessibility improvements
- Highlights successful remediation efforts
- Recognizes positive trends worth continuing

**Regression Alerts**
- Detects when accessibility scores decline
- Identifies new violations introduced
- Flags potential compliance concerns

**Pattern Recognition**
- Seasonal or cyclical patterns in accessibility metrics  
- Correlation between testing frequency and improvements
- Impact analysis of major site changes

### Exporting Historical Data

#### Export Options
Historical data can be exported in multiple formats:

**JSON Export**
- Complete historical dataset
- Suitable for integration with other tools
- Preserves all metadata and relationships

**CSV Export**  
- Spreadsheet-compatible format
- Ideal for analysis in Excel or Google Sheets
- Customizable column selection

**Report Integration**
- Historical data can be included in generated reports
- Trend analysis in executive summaries
- Before/after comparisons in technical reports

---

## Scheduling Automated Tests

The Scheduler module enables automated, recurring accessibility testing to ensure continuous compliance monitoring.

### Understanding Scheduled Tests

#### Benefits of Automation
- **Continuous Monitoring**: Regular testing catches new issues quickly
- **Consistency**: Standardized testing approach across all sites
- **Efficiency**: Reduces manual testing workload
- **Early Detection**: Problems identified before they impact users
- **Compliance Maintenance**: Ongoing verification of accessibility standards

#### Schedule Types
- **Regular Intervals**: Daily, weekly, or monthly testing
- **Custom Timing**: Specific days/times based on your workflow
- **Event-Triggered**: Tests after deployments or content updates
- **Compliance Cycles**: Aligned with audit or reporting requirements

### Creating Schedules

#### Basic Schedule Creation
1. Navigate to **Scheduler** in the main menu
2. Click **"Create Schedule"**
3. Configure the schedule:

**Schedule Information**
- **Name**: Descriptive name for the schedule (e.g., "Weekly Homepage Check")
- **Description**: Optional details about the schedule's purpose

**Testing Scope**
- **Project**: Which project to test
- **Test Type**: Accessibility, performance, or full test suite
- **Frequency**: How often to run (daily, weekly, monthly, custom)

#### Advanced Configuration

**Custom Intervals**
- **Specific Days**: Choose which days of the week
- **Time Preferences**: Set preferred execution times
- **Timezone Settings**: Configure for your local timezone
- **Holiday Handling**: Skip tests during holidays or maintenance periods

**Notification Settings**
- **Email Recipients**: Who should receive test completion notifications
- **Alert Conditions**: When to send special alerts (new violations, failures)
- **Report Delivery**: Automatically generate and send reports

**Test Parameters**
- **Page Limits**: Maximum pages to test in each run
- **Timeout Settings**: How long to wait for page responses
- **Screenshot Options**: When to capture visual evidence
- **Custom Rules**: Additional accessibility rules to enforce

### Managing Schedules

#### Schedule Dashboard
The scheduler dashboard shows:
- **Active Schedules**: Currently running automated tests
- **Upcoming Tests**: Next scheduled executions with times
- **Recent Results**: Outcomes from recent automated tests
- **Schedule Statistics**: Success rates and performance metrics

#### Schedule Status Types
- **Active**: Schedule is running according to configuration
- **Paused**: Temporarily disabled but can be resumed
- **Completed**: Finished schedules that ran for a specific period
- **Failed**: Schedules with configuration or execution problems

### Schedule Operations

#### Running Schedules Manually
- Click **"Run Now"** on any schedule to execute immediately
- Useful for testing schedule configuration
- Does not affect the regular schedule timing

#### Editing Schedules
1. Go to the schedule detail page
2. Click **"Edit Schedule"**
3. Modify any configuration parameters
4. Save changes (affects future executions only)

#### Pausing and Resuming
- **Pause**: Temporarily stop a schedule without deleting it
- **Resume**: Reactivate a paused schedule
- Useful during maintenance periods or major site changes

#### Deleting Schedules
⚠️ **Warning**: Deleting removes all schedule history and configuration
1. Navigate to the schedule detail page
2. Click **"Delete Schedule"**
3. Confirm deletion when prompted

### Schedule Execution

#### Execution Process
When a schedule runs:
1. **Initialization**: System prepares testing environment
2. **Page Discovery**: Identifies pages to test (if website structure changed)
3. **Testing**: Runs accessibility checks on all pages
4. **Analysis**: Processes results and compares to previous runs
5. **Notification**: Sends configured alerts and reports
6. **Storage**: Saves results and updates historical data

#### Execution History
Each schedule maintains detailed execution history:
- **Execution Time**: When the test ran
- **Duration**: How long the test took to complete
- **Results Summary**: Issues found, pages tested, success status
- **Changes Detected**: New violations or improvements since last run
- **System Status**: Any errors or warnings during execution

### Notifications and Alerts

#### Email Notifications
Configure email alerts for:
- **Schedule Completion**: Test finished successfully
- **New Violations**: Accessibility issues discovered
- **Score Changes**: Significant improvements or regressions
- **System Errors**: Technical problems during testing

#### Alert Conditions
Set specific conditions that trigger notifications:
- **Violation Thresholds**: Alert when violations exceed limits
- **Score Drops**: Notification if accessibility score decreases
- **Compliance Changes**: Alert if WCAG compliance level changes
- **Page Errors**: Notification if pages become inaccessible

#### Report Integration
Scheduled tests can automatically generate reports:
- **Regular Reports**: Weekly or monthly accessibility reports
- **Exception Reports**: Special reports when issues are found
- **Stakeholder Updates**: Executive summaries for leadership
- **Technical Briefings**: Detailed reports for development teams

---

## Troubleshooting

This section helps resolve common issues you might encounter while using AutoTest.

### Installation and Setup Issues

#### "ModuleNotFoundError" when starting
**Problem**: Python cannot find AutoTest modules
**Solutions**:
1. Ensure you're in the correct directory: `cd autoTest`
2. Activate the virtual environment: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Verify Python path: `python -c "import sys; print(sys.path)"`

#### Database Connection Errors
**Problem**: "Database not connected" or MongoDB connection failures
**Solutions**:
1. Check MongoDB status: `sudo systemctl status mongod`
2. Start MongoDB if stopped: `sudo systemctl start mongod`
3. Verify connection string in configuration
4. Check firewall settings blocking port 27017

#### Port Already in Use
**Problem**: "Address already in use" when starting the web server
**Solutions**:
1. Find process using port 5000: `lsof -i :5000`
2. Kill the process: `kill -9 <process_id>`
3. Or use a different port: `export AUTOTEST_PORT=5001`

### Testing Issues

#### Tests Not Running
**Problem**: "Run All Tests" button doesn't start testing
**Symptoms**: Button appears to work but no tests execute

**Debugging Steps**:
1. Check browser console for JavaScript errors (F12)
2. Verify project has websites added
3. Ensure websites have pages discovered
4. Check testing service status in system logs

**Solutions**:
- Refresh the page and try again
- Clear browser cache and cookies
- Verify the testing service is initialized properly
- Check that MongoDB is accessible and has proper permissions

#### No Pages Found During Testing
**Problem**: "No pages found in project" error during test execution
**Causes**:
- Website URL is inaccessible
- Robots.txt blocking access
- Network connectivity issues
- Incorrect base URL configuration

**Solutions**:
1. Verify website URL is accessible in browser
2. Check "Respect robots.txt" setting in website configuration
3. Test with simpler URL (remove www, https, etc.)  
4. Review website scraping configuration settings

#### Tests Timing Out
**Problem**: Tests start but never complete or take extremely long
**Solutions**:
1. Reduce max pages setting in website configuration
2. Decrease max depth to limit page discovery
3. Check for slow-loading pages that cause timeouts
4. Increase timeout values in testing configuration

### Report Generation Issues

#### "Invalid PDF data" Error
**Problem**: PDF downloads fail with invalid data error
**Cause**: Report generation or PDF encoding issues

**Solutions**:
1. Try generating HTML report first to verify data
2. Check available disk space for temporary files
3. Clear browser cache and cookies
4. Restart the AutoTest application

#### Empty Reports
**Problem**: Reports generate but contain no data or show "0 tests executed"
**Debugging**:
1. Verify tests have actually been completed
2. Check that test results are stored in database
3. Confirm report is configured for correct project/time range

**Solutions**:
- Ensure tests have completed successfully before generating reports
- Select correct project and time range in report configuration
- Check database connectivity and permissions

#### Missing Report Templates
**Problem**: "Unknown report template" errors
**Solution**: Verify all template files exist in the templates directory and restart the application

### Interface Issues

#### "Error loading" Messages
**Problem**: Various pages show "Error loading" instead of content
**Common Causes**:
- Missing template files
- Database connectivity issues
- Service initialization problems

**General Solutions**:
1. Check browser console for specific error messages
2. Restart the AutoTest application
3. Verify database connection is working
4. Clear browser cache and reload

#### Snapshots Not Loading
**Problem**: Historical snapshots page shows "Loading snapshots..." indefinitely
**Solutions**:
1. Check browser console for JavaScript errors
2. Verify API endpoints are responding
3. Ensure project selection is working properly
4. Test with different browser or incognito mode

#### Form Submissions Not Working
**Problem**: Forms appear to submit but nothing happens
**Debugging**:
1. Check browser console for JavaScript errors
2. Verify network requests are being made (Network tab in dev tools)
3. Check for popup blockers interfering with notifications

### Performance Issues

#### Slow Page Loading
**Solutions**:
1. Check database performance and indexing
2. Reduce number of concurrent tests
3. Optimize page discovery settings
4. Consider running on more powerful hardware

#### High Memory Usage
**Solutions**:
1. Reduce max concurrent jobs setting
2. Limit max pages per website
3. Clear old test results and reports periodically
4. Monitor and restart application if needed

### Data Issues

#### Missing Historical Data
**Problem**: Previous test results or snapshots are missing
**Debugging**:
1. Check database for data integrity
2. Verify backup procedures are working
3. Review application logs for errors

**Prevention**:
- Implement regular database backups
- Monitor disk space usage
- Set up data retention policies

#### Incorrect Test Results
**Problem**: Test results seem inaccurate or inconsistent
**Solutions**:
1. Verify website hasn't changed between tests
2. Check for browser compatibility issues
3. Review test configuration settings
4. Compare with manual accessibility testing

### Getting Help

#### Log Files
Check application logs for detailed error information:
- Application logs: Usually in `/var/log/autotest/` or similar
- Web server logs: Check your web server configuration
- Database logs: MongoDB logs for database-related issues

#### Support Resources
1. **Documentation**: Review this user manual thoroughly
2. **GitHub Issues**: Check existing issues or create new ones
3. **Community Forums**: Connect with other AutoTest users
4. **Professional Support**: Contact for enterprise support options

#### Reporting Bugs
When reporting issues, include:
- AutoTest version number
- Operating system and browser details
- Steps to reproduce the problem
- Error messages or screenshots
- Relevant log file excerpts

---

## API Reference

AutoTest provides REST API endpoints for integration with other tools and automated workflows.

### Authentication

Currently, AutoTest operates without authentication in development mode. For production deployments, implement appropriate security measures.

### Base URL
All API endpoints are relative to your AutoTest installation:
```
http://localhost:5000/api/
```

### Common Response Format
```json
{
    "success": true,
    "data": {...},
    "message": "Operation completed successfully",
    "timestamp": "2025-07-29T10:00:00Z"
}
```

Error responses:
```json
{
    "success": false,
    "error": "Error description",
    "code": "ERROR_CODE",
    "timestamp": "2025-07-29T10:00:00Z"
}
```

### Projects API

#### List Projects
```http
GET /api/projects
```
Returns all projects with basic information.

#### Get Project Details
```http
GET /api/projects/{project_id}
```
Returns detailed information about a specific project.

#### Create Project
```http
POST /api/projects
Content-Type: application/json

{
    "name": "Project Name",
    "description": "Project description"
}
```

#### Update Project
```http
PUT /api/projects/{project_id}
Content-Type: application/json

{
    "name": "Updated Name",
    "description": "Updated description"
}
```

#### Delete Project
```http
DELETE /api/projects/{project_id}
```

### Testing API

#### Start Test
```http
POST /api/testing/run
Content-Type: application/json

{
    "project_id": "project-uuid",
    "test_type": "accessibility",
    "priority": "normal"
}
```

#### Get Test Status
```http
GET /api/testing/jobs/{job_id}
```

#### Get Test Results
```http
GET /api/testing/results?project_id={project_id}&limit=10
```

### Reports API

#### Generate Report
```http
POST /api/reports/generate
Content-Type: application/json

{
    "template_id": "executive_summary",
    "project_id": "project-uuid",
    "format": "pdf"
}
```

#### List Reports
```http
GET /api/reports?project_id={project_id}
```

#### Download Report
```http
GET /api/reports/{report_id}/download
```

### History API

#### Get Snapshots
```http
GET /api/history/snapshots?project_id={project_id}&limit=50
```

#### Create Snapshot
```http
POST /api/history/snapshots
Content-Type: application/json

{
    "project_id": "project-uuid",
    "notes": "Manual snapshot after fixes"
}
```

#### Compare Snapshots
```http
POST /api/history/compare
Content-Type: application/json

{
    "snapshot1_id": "snapshot-uuid-1",
    "snapshot2_id": "snapshot-uuid-2"
}
```

### Scheduler API

#### List Schedules
```http
GET /api/scheduler/schedules
```

#### Create Schedule
```http
POST /api/scheduler/schedules
Content-Type: application/json

{
    "name": "Weekly Test",
    "project_id": "project-uuid",
    "frequency": "weekly",
    "test_type": "accessibility"
}
```

#### Run Schedule Immediately
```http
POST /api/scheduler/schedules/{schedule_id}/run
```

---

## FAQ

### General Questions

**Q: What accessibility standards does AutoTest check?**
A: AutoTest primarily focuses on WCAG 2.1 guidelines at levels A, AA, and AAA. It also includes additional best practices and common accessibility patterns.

**Q: How many pages can AutoTest handle?**
A: The system can handle thousands of pages, but performance depends on your hardware. For large sites, consider using the page limits and depth restrictions in website configuration.

**Q: Can I test websites that require authentication?**
A: Currently, AutoTest tests publicly accessible pages only. Authentication-protected pages require manual testing or specialized configuration.

**Q: Is AutoTest suitable for production use?**
A: Version 1.0 is designed for internal use and testing environments. For production deployment, additional security and performance optimizations are recommended.

### Technical Questions

**Q: What browsers does AutoTest use for testing?**
A: AutoTest uses headless Chrome/Chromium for automated testing, providing consistent results across different environments.

**Q: Can I customize the accessibility rules?**
A: Yes, AutoTest supports custom rules and can be extended with additional accessibility checks beyond the standard WCAG guidelines.

**Q: How accurate are the test results?**
A: Automated testing catches many accessibility issues but cannot detect all problems. Manual testing and user feedback remain important for comprehensive accessibility assessment.

**Q: Can I integrate AutoTest with CI/CD pipelines?**
A: Yes, the REST API enables integration with continuous integration systems. You can trigger tests automatically after deployments.

### Troubleshooting Questions

**Q: Why are my tests taking so long?**
A: Long test times usually result from testing too many pages or slow website responses. Try reducing the max pages setting or increasing timeout values.

**Q: What do I do if the application won't start?**
A: Check that MongoDB is running, all dependencies are installed, and you're using the correct Python virtual environment.

**Q: Can I recover deleted projects or test results?**
A: AutoTest doesn't include built-in backup/recovery features. Implement regular database backups to protect against data loss.

---

## Appendix

### WCAG Guidelines Reference
- **Principle 1: Perceivable** - Information must be presentable in ways users can perceive
- **Principle 2: Operable** - Interface components must be operable by all users  
- **Principle 3: Understandable** - Information and UI operation must be understandable
- **Principle 4: Robust** - Content must be robust enough for various assistive technologies

### Keyboard Shortcuts
- **Ctrl+/** - Toggle help system
- **Alt+M** - Navigate to main menu
- **Alt+S** - Skip to main content
- **Esc** - Close modal dialogs

### File Locations
- **Configuration**: `autotest/config/`
- **Templates**: `autotest/web/templates/`
- **Static Files**: `autotest/web/static/`
- **Logs**: `/var/log/autotest/` (or configured location)

---

*AutoTest User Manual - Version 1.0*  
*Last Updated: July 29, 2025*