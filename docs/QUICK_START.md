# AutoTest Quick Start Guide

Get up and running with AutoTest accessibility testing in under 10 minutes.

## Prerequisites

- Python 3.8+ installed
- MongoDB running on localhost:27017
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Installation (5 minutes)

1. **Clone and Setup**
   ```bash
   git clone https://github.com/bobdodd/autoTest.git
   cd autoTest
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start AutoTest**
   ```bash
   python -m autotest.web.app
   ```

3. **Open in Browser**
   - Navigate to `http://localhost:5000`
   - You should see the AutoTest dashboard

## First Test (5 minutes)

### Step 1: Create a Project
1. Click **"Create Project"** on the dashboard
2. Enter:
   - **Name**: "My First Project"
   - **Description**: "Testing my website accessibility"
3. Click **"Create Project"**

### Step 2: Add a Website
1. In your new project, click **"Add Website"**
2. Configure:
   - **Website Name**: "Main Site"
   - **Base URL**: `https://your-website.com` (or use `https://example.com` for testing)
   - **Max Pages**: 10 (to keep first test quick)
3. Click **"Add Website"**

### Step 3: Run Your First Test
1. Click **"Run All Tests"** in the project dashboard
2. Navigate to **Testing** → **Dashboard** to watch progress
3. Wait for completion (usually 1-5 minutes depending on site size)

### Step 4: View Results
1. Once complete, return to your project dashboard
2. View the test summary showing:
   - Issues found
   - Accessibility score
   - WCAG compliance level
3. Click **"View Details"** for complete analysis

## Generate Your First Report (2 minutes)

1. Navigate to **Reports**
2. Click **"Generate New Report"**
3. Select:
   - **Project**: Your project
   - **Report Type**: Executive Summary
   - **Format**: HTML
4. Click **"Generate Report"**
5. View your professional accessibility report

## What's Next?

### Explore Key Features
- **History**: Track improvements over time with snapshots
- **Scheduling**: Set up automated weekly testing
- **Detailed Results**: Dive deep into specific accessibility violations
- **Multiple Projects**: Organize different websites and environments

### Learn More
- Read the complete [User Manual](USER_MANUAL.md) for comprehensive guidance
- Check the **Help** section in the application for quick tips
- Review the **Testing Dashboard** for ongoing monitoring

### Best Practices
1. **Start Small**: Test with fewer pages initially, then expand
2. **Regular Testing**: Set up weekly schedules for continuous monitoring
3. **Track Progress**: Use snapshots to measure improvements
4. **Share Results**: Generate reports for stakeholders and development teams

## Common First-Time Issues

**Problem**: Tests not starting
- **Solution**: Ensure website URL is accessible and MongoDB is running

**Problem**: No pages found
- **Solution**: Check website URL format and try reducing max depth setting

**Problem**: Application won't start
- **Solution**: Verify Python virtual environment is activated and dependencies installed

## Support

- **Documentation**: Complete user manual in `docs/USER_MANUAL.md`
- **GitHub Issues**: Report bugs or request features
- **Community**: Connect with other AutoTest users

---

**Congratulations!** You've successfully run your first accessibility test with AutoTest. Continue exploring the platform's powerful features for comprehensive accessibility management.

*Quick Start Guide - AutoTest Version 1.0*