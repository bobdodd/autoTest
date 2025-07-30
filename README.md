# AutoTest - Accessibility Testing Platform

![AutoTest Logo](docs/assets/logo.png)

[![Version](https://img.shields.io/badge/version-1.0-blue.svg)](https://github.com/bobdodd/autoTest/releases/tag/Version-1)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![WCAG](https://img.shields.io/badge/WCAG-2.1%20AA-orange.svg)](https://www.w3.org/WAI/WCAG21/quickref/)
[![License](https://img.shields.io/badge/license-GPL%203.0-blue.svg)](LICENSE)

AutoTest is a comprehensive web-based platform for automated accessibility testing, designed to help organizations ensure their websites comply with WCAG (Web Content Accessibility Guidelines) standards.

## ✨ Features

### 🔍 **Comprehensive Testing**
- Automated WCAG 2.1 compliance checking (A, AA, AAA levels)
- Multi-page website crawling and testing
- Real-time testing progress monitoring
- Detailed violation analysis with fix recommendations

### 📊 **Professional Reporting**
- Executive summaries for stakeholders
- Technical detailed reports for developers
- Compliance audit reports for legal teams
- PDF and HTML export formats

### 📈 **Historical Tracking**
- Accessibility progress monitoring over time
- Snapshot comparison between different periods
- Trend analysis and improvement tracking
- Automated snapshot creation

### ⏰ **Automated Scheduling**
- Recurring accessibility tests (daily, weekly, monthly)
- Automated report generation and distribution
- Email notifications for new issues
- Integration-ready REST API

### 🎯 **User-Friendly Interface**
- Intuitive web-based dashboard
- Responsive design for all devices
- Built-in accessibility features
- Comprehensive help system

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Modern web browser

### Installation
```bash
# Clone repository
git clone https://github.com/bobdodd/autoTest.git
cd autoTest

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start AutoTest
python -m autotest.web.app
```

### First Test
1. Open `http://localhost:5000` in your browser
2. Create a new project
3. Add a website to test
4. Click "Run All Tests"
5. View results and generate reports

📖 **Detailed Instructions**: See [Quick Start Guide](docs/QUICK_START.md)

## 📚 Documentation

### User Guides
- **[Quick Start Guide](docs/QUICK_START.md)** - Get running in 10 minutes
- **[Installation Guide](docs/INSTALLATION.md)** - Complete setup instructions
- **[User Manual](docs/USER_MANUAL.md)** - Comprehensive feature documentation

### Technical Documentation
- **[API Reference](docs/USER_MANUAL.md#api-reference)** - REST API endpoints
- **[Troubleshooting](docs/USER_MANUAL.md#troubleshooting)** - Common issues and solutions
- **[FAQ](docs/USER_MANUAL.md#faq)** - Frequently asked questions

## 🏗️ Architecture

AutoTest is built with a modern, scalable architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Interface │    │   Core Services  │    │    Database     │
│                 │    │                  │    │                 │
│ • Dashboard     │◄──►│ • Testing Engine │◄──►│ • MongoDB       │
│ • Reports       │    │ • Report Gen     │    │ • Test Results  │
│ • History       │    │ • Scheduler      │    │ • Projects      │
│ • API           │    │ • History        │    │ • Schedules     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Components
- **Flask Web Framework** - Modern Python web application
- **MongoDB Database** - Document storage for flexible data models
- **Selenium WebDriver** - Browser automation for accessibility testing
- **ReportLab** - Professional PDF report generation
- **Bootstrap-free UI** - Custom accessible interface components

## 🎯 Use Cases

### For Development Teams
- **Continuous Integration**: Integrate accessibility testing into CI/CD pipelines
- **Code Quality**: Catch accessibility issues before deployment
- **Developer Training**: Learn accessibility best practices through detailed feedback

### For QA Teams
- **Automated Testing**: Reduce manual accessibility testing workload
- **Regression Testing**: Ensure accessibility improvements don't regress
- **Comprehensive Coverage**: Test entire websites systematically

### For Compliance Officers
- **Legal Compliance**: Generate formal compliance audit reports
- **Risk Assessment**: Identify and prioritize accessibility risks
- **Documentation**: Maintain records for accessibility compliance

### For Project Managers
- **Progress Tracking**: Monitor accessibility improvements over time
- **Resource Planning**: Understand remediation effort required
- **Stakeholder Reporting**: Professional reports for leadership

## 🛠️ Contributing

We welcome contributions to AutoTest! Here's how to get involved:

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/bobdodd/autoTest.git
cd autoTest
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest autotest/tests/

# Start development server
python -m autotest.web.app
```

### Contribution Guidelines
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards
- Follow PEP 8 Python style guidelines
- Include tests for new functionality
- Update documentation for user-facing changes
- Ensure accessibility in all UI components

## 📊 Project Stats

- **4,200+ lines** of Python code
- **Comprehensive test coverage** with automated testing
- **Professional documentation** with user manual and API docs
- **Production-ready** with Docker support
- **Active development** with regular updates

## 🔒 Security

AutoTest takes security seriously:

- **Input Validation**: All user inputs are validated and sanitized
- **Secure Database**: MongoDB with proper access controls
- **HTTPS Ready**: SSL/TLS support for production deployments
- **No Data Collection**: Your website data stays on your servers

For security issues, please email security@autotest.com.

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

### GPL v3.0 Summary
- **Freedom to use**: Use AutoTest for any purpose
- **Freedom to study**: Access and examine the source code
- **Freedom to modify**: Make changes and improvements
- **Freedom to distribute**: Share copies and modifications
- **Copyleft requirement**: Derivative works must also be GPL licensed

## 🙏 Acknowledgments

- **Web Content Accessibility Guidelines (WCAG)** - W3C accessibility standards
- **axe-core** - Accessibility testing engine inspiration
- **Flask Community** - Excellent web framework and ecosystem
- **MongoDB** - Flexible document database platform

## 📞 Support

### Community Support
- **GitHub Issues**: [Report bugs and request features](https://github.com/bobdodd/autoTest/issues)
- **Discussions**: [Community Q&A and discussions](https://github.com/bobdodd/autoTest/discussions)
- **Documentation**: [Comprehensive user guides](docs/)

### Professional Support
For enterprise deployments and professional support:
- Email: support@autotest.com
- Consulting: Custom implementations and training
- SLA Support: Priority support with guaranteed response times

## 🗺️ Roadmap

### Version 1.1 (Planned)
- [ ] User authentication and role-based access
- [ ] Advanced custom rule creation
- [ ] Performance testing integration
- [ ] Enhanced API with webhooks

### Version 2.0 (Future)
- [ ] Multi-tenant architecture
- [ ] Machine learning for issue prioritization
- [ ] Mobile app testing support
- [ ] Advanced analytics and insights

### Community Requests
- [ ] JIRA integration
- [ ] Slack notifications
- [ ] Custom branding options
- [ ] Bulk website management

## 📈 Version History

### Version 1.0 (Current)
- ✅ Complete web-based accessibility testing platform
- ✅ Project and website management
- ✅ Comprehensive reporting system
- ✅ Historical tracking and snapshots
- ✅ Automated scheduling
- ✅ REST API
- ✅ Professional documentation

---

<div align="center">

**[Get Started](docs/QUICK_START.md)** •
**[Documentation](docs/USER_MANUAL.md)** •
**[API Reference](docs/USER_MANUAL.md#api-reference)** •
**[Contributing](#contributing)** •
**[Support](#support)**

**Made with ❤️ for web accessibility**

</div>