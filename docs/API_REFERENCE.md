# AutoTest API Reference

Complete REST API documentation for the AutoTest accessibility testing platform.

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL and Versioning](#base-url-and-versioning)
3. [Response Format](#response-format)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Projects API](#projects-api)
7. [Websites API](#websites-api)
8. [Pages API](#pages-api)
9. [Testing API](#testing-api)
10. [Reports API](#reports-api)
11. [History API](#history-api)
12. [Scheduler API](#scheduler-api)
13. [WebSocket Events](#websocket-events)
14. [SDK Examples](#sdk-examples)

## Authentication

**Note**: Version 1.0 does not include authentication. All endpoints are publicly accessible when running locally. Authentication will be added in version 1.1.

For production deployments, implement authentication at the reverse proxy level (nginx, Apache) or use API gateway authentication.

## Base URL and Versioning

```
Base URL: http://localhost:5000/api
Version: v1 (current)
```

All API endpoints are prefixed with `/api`. Future versions will use `/api/v2`, etc.

## Response Format

### Success Response
```json
{
    "success": true,
    "data": {
        "project_id": "proj_123",
        "name": "Website Testing"
    },
    "message": "Operation completed successfully",
    "timestamp": "2025-01-15T10:30:00Z"
}
```

### Error Response
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input provided",
        "details": {
            "field": "name",
            "constraint": "must be 3-100 characters"
        }
    },
    "timestamp": "2025-01-15T10:30:00Z"
}
```

### Pagination Response
```json
{
    "success": true,
    "data": [...],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 150,
        "pages": 8
    }
}
```

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation failed |
| 500 | Internal Server Error | Server error |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `NOT_FOUND` | Resource not found |
| `ALREADY_EXISTS` | Resource already exists |
| `TEST_IN_PROGRESS` | Test already running |
| `INVALID_URL` | URL format invalid |
| `SCRAPING_ERROR` | Website scraping failed |
| `DATABASE_ERROR` | Database operation failed |

## Rate Limiting

**Version 1.0**: No rate limiting implemented.
**Future versions**: Rate limiting will be based on:
- 1000 requests per hour per IP
- 100 test runs per day per project
- Configurable limits via admin interface

## Projects API

### List Projects

```http
GET /api/projects
```

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Items per page (default: 20, max: 100)
- `search` (string, optional): Search project names
- `status` (string, optional): Filter by status (`active`, `archived`)

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "project_id": "proj_123",
            "name": "Company Website",
            "description": "Main corporate website accessibility testing",
            "status": "active",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-15T10:30:00Z",
            "website_count": 3,
            "last_test_date": "2025-01-14T15:00:00Z",
            "compliance_score": 87.5
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 5,
        "pages": 1
    }
}
```

### Create Project

```http
POST /api/projects
```

**Request Body:**
```json
{
    "name": "New Website Project",
    "description": "Testing accessibility for new website",
    "wcag_level": "AA",
    "notification_emails": ["dev@company.com"]
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "project_id": "proj_456",
        "name": "New Website Project",
        "description": "Testing accessibility for new website",
        "status": "active",
        "created_at": "2025-01-15T10:30:00Z",
        "settings": {
            "wcag_level": "AA",
            "notification_emails": ["dev@company.com"]
        }
    }
}
```

### Get Project

```http
GET /api/projects/{project_id}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "project_id": "proj_123",
        "name": "Company Website",
        "description": "Main corporate website accessibility testing",
        "status": "active",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-15T10:30:00Z",
        "settings": {
            "wcag_level": "AA",
            "test_frequency": "weekly",
            "notification_emails": ["dev@company.com"]
        },
        "websites": [
            {
                "website_id": "web_456",
                "name": "Main Website",
                "base_url": "https://company.com",
                "page_count": 25,
                "last_test_date": "2025-01-14T15:00:00Z"
            }
        ],
        "statistics": {
            "total_tests": 45,
            "total_pages": 125,
            "avg_compliance_score": 87.5,
            "total_violations": 23
        }
    }
}
```

### Update Project

```http
PUT /api/projects/{project_id}
```

**Request Body:**
```json
{
    "name": "Updated Project Name",
    "description": "Updated description",
    "wcag_level": "AAA"
}
```

### Delete Project

```http
DELETE /api/projects/{project_id}
```

**Query Parameters:**
- `force` (boolean, optional): Force delete even if tests exist

## Websites API

### List Project Websites

```http
GET /api/projects/{project_id}/websites
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "website_id": "web_456",
            "project_id": "proj_123",
            "name": "Main Website",
            "base_url": "https://company.com",
            "created_at": "2025-01-01T00:00:00Z",
            "last_crawled": "2025-01-15T09:00:00Z",
            "page_count": 25,
            "status": "active",
            "crawl_settings": {
                "max_pages": 100,
                "follow_external": false,
                "ignore_patterns": ["/admin/*"]
            }
        }
    ]
}
```

### Add Website to Project

```http
POST /api/projects/{project_id}/websites
```

**Request Body:**
```json
{
    "name": "Marketing Site",
    "base_url": "https://marketing.company.com",
    "crawl_settings": {
        "max_pages": 50,
        "follow_external": false,
        "ignore_patterns": ["/admin/*", "/*.pdf"]
    }
}
```

### Get Website Details

```http
GET /api/websites/{website_id}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "website_id": "web_456",
        "project_id": "proj_123",
        "name": "Main Website",
        "base_url": "https://company.com",
        "created_at": "2025-01-01T00:00:00Z",
        "last_crawled": "2025-01-15T09:00:00Z",
        "page_count": 25,
        "status": "active",
        "crawl_settings": {
            "max_pages": 100,
            "follow_external": false,
            "ignore_patterns": ["/admin/*"]
        },
        "pages": [
            {
                "page_id": "page_789",
                "url": "https://company.com/about",
                "title": "About Us - Company",
                "last_tested": "2025-01-15T09:15:00Z",
                "compliance_score": 92.0,
                "violation_count": 2
            }
        ]
    }
}
```

### Update Website

```http
PUT /api/websites/{website_id}
```

### Delete Website

```http
DELETE /api/websites/{website_id}
```

## Pages API

### List Website Pages

```http
GET /api/websites/{website_id}/pages
```

**Query Parameters:**
- `page` (integer): Page number
- `limit` (integer): Items per page
- `status` (string): Filter by status
- `min_score` (float): Minimum compliance score
- `max_score` (float): Maximum compliance score

### Get Page Details

```http
GET /api/pages/{page_id}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "page_id": "page_789",
        "website_id": "web_456",
        "url": "https://company.com/about",
        "title": "About Us - Company",
        "discovered_at": "2025-01-01T00:00:00Z",
        "last_tested": "2025-01-15T09:15:00Z",
        "status": "active",
        "metadata": {
            "content_type": "text/html",
            "status_code": 200,
            "page_size": 15420,
            "load_time": 1.2
        },
        "latest_result": {
            "test_date": "2025-01-15T09:15:00Z",
            "compliance_score": 92.0,
            "violation_count": 2,
            "wcag_level": "AA"
        }
    }
}
```

## Testing API

### Start Accessibility Test

```http
POST /api/testing/run
```

**Request Body:**
```json
{
    "project_id": "proj_123",
    "test_type": "full",
    "wcag_level": "AA",
    "options": {
        "include_warnings": true,
        "check_color_contrast": true,
        "validate_html": true
    }
}
```

**Test Types:**
- `full`: Test all pages in all websites
- `website`: Test specific website
- `page`: Test specific page
- `quick`: Test sample of pages

**Response:**
```json
{
    "success": true,
    "data": {
        "test_id": "test_789012",
        "status": "started",
        "project_id": "proj_123",
        "test_type": "full",
        "started_at": "2025-01-15T10:30:00Z",
        "estimated_duration": "5-10 minutes",
        "pages_to_test": 25
    }
}
```

### Check Test Status

```http
GET /api/testing/status/{test_id}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "test_id": "test_789012",
        "status": "running",
        "progress": {
            "current_page": 15,
            "total_pages": 25,
            "percentage": 60,
            "estimated_remaining": "2 minutes"
        },
        "started_at": "2025-01-15T10:30:00Z",
        "current_activity": "Testing page: /products/overview"
    }
}
```

**Status Values:**
- `queued`: Test queued for execution
- `running`: Test in progress
- `completed`: Test finished successfully
- `failed`: Test failed with errors
- `cancelled`: Test cancelled by user

### Get Test Results

```http
GET /api/testing/results/{test_id}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "test_id": "test_789012",
        "project_id": "proj_123",
        "status": "completed",
        "started_at": "2025-01-15T10:30:00Z",
        "completed_at": "2025-01-15T10:37:00Z",
        "duration": "7 minutes",
        "summary": {
            "total_pages": 25,
            "pages_tested": 25,
            "total_violations": 47,
            "serious": 12,
            "moderate": 28,
            "minor": 7,
            "avg_compliance_score": 87.5
        },
        "violations_by_rule": [
            {
                "rule_id": "color-contrast",
                "rule_name": "Color Contrast",
                "violation_count": 15,
                "affected_pages": 8
            }
        ],
        "pages": [
            {
                "page_id": "page_789",
                "url": "https://company.com/about",
                "compliance_score": 92.0,
                "violation_count": 2,
                "test_duration": 3.2
            }
        ]
    }
}
```

### Cancel Test

```http
DELETE /api/testing/cancel/{test_id}
```

### Test Single Page

```http
POST /api/testing/page
```

**Request Body:**
```json
{
    "url": "https://example.com/page",
    "wcag_level": "AA",
    "wait_time": 5000
}
```

## Reports API

### Generate Report

```http
POST /api/reports/generate
```

**Request Body:**
```json
{
    "project_id": "proj_123",
    "report_type": "detailed",
    "format": "pdf",
    "date_range": {
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-01-15T23:59:59Z"
    },
    "options": {
        "include_screenshots": true,
        "include_fix_suggestions": true,
        "group_by_rule": true
    }
}
```

**Report Types:**
- `executive`: High-level summary for stakeholders
- `detailed`: Complete technical report
- `compliance`: Formal compliance audit report
- `comparison`: Compare multiple time periods

**Formats:**
- `pdf`: PDF document
- `html`: HTML page
- `json`: Raw data
- `csv`: Spreadsheet format

**Response:**
```json
{
    "success": true,
    "data": {
        "report_id": "report_345678",
        "status": "generating",
        "estimated_completion": "2025-01-15T10:35:00Z",
        "download_url": "/api/reports/download/report_345678"
    }
}
```

### Check Report Status

```http
GET /api/reports/status/{report_id}
```

### Download Report

```http
GET /api/reports/download/{report_id}
```

**Response:** Binary file download with appropriate Content-Type header.

### List Reports

```http
GET /api/reports
```

**Query Parameters:**
- `project_id` (string): Filter by project
- `report_type` (string): Filter by report type
- `format` (string): Filter by format

## History API

### Get Historical Data

```http
GET /api/history/{project_id}
```

**Query Parameters:**
- `period` (string): Time period (`day`, `week`, `month`, `year`)
- `start_date` (string): Start date (ISO format)
- `end_date` (string): End date (ISO format)
- `metric` (string): Specific metric (`compliance_score`, `violation_count`)

**Response:**
```json
{
    "success": true,
    "data": {
        "project_id": "proj_123",
        "period": "week",
        "data_points": [
            {
                "date": "2025-01-08",
                "compliance_score": 85.2,
                "total_violations": 52,
                "pages_tested": 25,
                "test_count": 1
            },
            {
                "date": "2025-01-15",
                "compliance_score": 87.5,
                "total_violations": 47,
                "pages_tested": 25,
                "test_count": 2
            }
        ],
        "trends": {
            "compliance_score_change": "+2.3",
            "violation_count_change": "-5",
            "improvement_rate": "4.2%"
        }
    }
}
```

### Create Snapshot

```http
POST /api/history/snapshot
```

**Request Body:**
```json
{
    "project_id": "proj_123",
    "name": "Pre-launch snapshot",
    "description": "Baseline before major release"
}
```

### Compare Snapshots

```http
GET /api/history/compare
```

**Query Parameters:**
- `project_id` (string, required): Project to compare
- `snapshot1` (string, required): First snapshot ID
- `snapshot2` (string, required): Second snapshot ID

## Scheduler API

### List Scheduled Tests

```http
GET /api/scheduler/schedules
```

**Query Parameters:**
- `project_id` (string): Filter by project
- `status` (string): Filter by status (`active`, `paused`)

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "schedule_id": "sched_901234",
            "project_id": "proj_123",
            "name": "Weekly Full Test",
            "frequency": "weekly",
            "next_run": "2025-01-22T09:00:00Z",
            "last_run": "2025-01-15T09:00:00Z",
            "status": "active",
            "test_type": "full",
            "notifications": {
                "email_addresses": ["dev@company.com"],
                "on_completion": true,
                "on_failure": true
            }
        }
    ]
}
```

### Create Schedule

```http
POST /api/scheduler/schedules
```

**Request Body:**
```json
{
    "project_id": "proj_123",
    "name": "Daily Quick Check",
    "frequency": "daily",
    "time": "09:00",
    "timezone": "UTC",
    "test_type": "quick",
    "notifications": {
        "email_addresses": ["dev@company.com"],
        "on_completion": true,
        "on_failure": true
    }
}
```

**Frequency Options:**
- `daily`: Every day at specified time
- `weekly`: Weekly on specified day
- `monthly`: Monthly on specified date
- `custom`: Custom cron expression

### Update Schedule

```http
PUT /api/scheduler/schedules/{schedule_id}
```

### Delete Schedule

```http
DELETE /api/scheduler/schedules/{schedule_id}
```

### Pause/Resume Schedule

```http
POST /api/scheduler/schedules/{schedule_id}/pause
POST /api/scheduler/schedules/{schedule_id}/resume
```

## WebSocket Events

**Connection URL:** `ws://localhost:5000/ws`

### Test Progress Updates

```json
{
    "event": "test_progress",
    "data": {
        "test_id": "test_789012",
        "current_page": 15,
        "total_pages": 25,
        "percentage": 60,
        "current_url": "https://company.com/products"
    }
}
```

### Test Completion

```json
{
    "event": "test_completed",
    "data": {
        "test_id": "test_789012",
        "status": "completed",
        "summary": {
            "total_violations": 47,
            "compliance_score": 87.5
        }
    }
}
```

### Real-time Notifications

```json
{
    "event": "notification",
    "data": {
        "type": "scheduled_test_completed",
        "project_id": "proj_123",
        "message": "Weekly accessibility test completed",
        "timestamp": "2025-01-15T10:45:00Z"
    }
}
```

## SDK Examples

### Python SDK

```python
import requests
from typing import Dict, Any, Optional

class AutoTestAPI:
    def __init__(self, base_url: str = "http://localhost:5000/api"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_project(self, name: str, description: str = "", 
                      wcag_level: str = "AA") -> Dict[str, Any]:
        """Create a new accessibility testing project."""
        data = {
            "name": name,
            "description": description,
            "wcag_level": wcag_level
        }
        response = self.session.post(f"{self.base_url}/projects", json=data)
        response.raise_for_status()
        return response.json()
    
    def start_test(self, project_id: str, test_type: str = "full") -> str:
        """Start accessibility test and return test ID."""
        data = {
            "project_id": project_id,
            "test_type": test_type
        }
        response = self.session.post(f"{self.base_url}/testing/run", json=data)
        response.raise_for_status()
        return response.json()["data"]["test_id"]
    
    def wait_for_test_completion(self, test_id: str, 
                               timeout: int = 600) -> Dict[str, Any]:
        """Wait for test to complete and return results."""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_response = self.session.get(
                f"{self.base_url}/testing/status/{test_id}"
            )
            status_response.raise_for_status()
            status = status_response.json()["data"]["status"]
            
            if status == "completed":
                results_response = self.session.get(
                    f"{self.base_url}/testing/results/{test_id}"
                )
                results_response.raise_for_status()
                return results_response.json()
            elif status == "failed":
                raise Exception(f"Test {test_id} failed")
            
            time.sleep(10)  # Check every 10 seconds
        
        raise TimeoutError(f"Test {test_id} did not complete within {timeout}s")

# Usage example
api = AutoTestAPI()

# Create project
project = api.create_project(
    name="My Website",
    description="Accessibility testing for company website"
)
project_id = project["data"]["project_id"]

# Start test
test_id = api.start_test(project_id, "full")

# Wait for completion
results = api.wait_for_test_completion(test_id)
print(f"Test completed with score: {results['data']['summary']['avg_compliance_score']}")
```

### JavaScript SDK

```javascript
class AutoTestAPI {
    constructor(baseUrl = 'http://localhost:5000/api') {
        this.baseUrl = baseUrl;
    }
    
    async createProject(name, description = '', wcagLevel = 'AA') {
        const response = await fetch(`${this.baseUrl}/projects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                description,
                wcag_level: wcagLevel
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    }
    
    async startTest(projectId, testType = 'full') {
        const response = await fetch(`${this.baseUrl}/testing/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: projectId,
                test_type: testType
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        return result.data.test_id;
    }
    
    async waitForTestCompletion(testId, timeout = 600000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const statusResponse = await fetch(`${this.baseUrl}/testing/status/${testId}`);
            const status = await statusResponse.json();
            
            if (status.data.status === 'completed') {
                const resultsResponse = await fetch(`${this.baseUrl}/testing/results/${testId}`);
                return resultsResponse.json();
            } else if (status.data.status === 'failed') {
                throw new Error(`Test ${testId} failed`);
            }
            
            await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
        }
        
        throw new Error(`Test ${testId} did not complete within ${timeout}ms`);
    }
}

// Usage example
const api = new AutoTestAPI();

async function runAccessibilityTest() {
    try {
        // Create project
        const project = await api.createProject(
            'My Website',
            'Accessibility testing for company website'
        );
        const projectId = project.data.project_id;
        
        // Start test
        const testId = await api.startTest(projectId, 'full');
        console.log(`Test started: ${testId}`);
        
        // Wait for completion
        const results = await api.waitForTestCompletion(testId);
        console.log(`Test completed with score: ${results.data.summary.avg_compliance_score}`);
        
    } catch (error) {
        console.error('Test failed:', error);
    }
}
```

### cURL Examples

```bash
# Create project
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Website",
    "description": "Accessibility testing",
    "wcag_level": "AA"
  }'

# Start test
curl -X POST http://localhost:5000/api/testing/run \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_123",
    "test_type": "full"
  }'

# Check test status
curl http://localhost:5000/api/testing/status/test_789012

# Get test results
curl http://localhost:5000/api/testing/results/test_789012

# Generate report
curl -X POST http://localhost:5000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_123",
    "report_type": "detailed",
    "format": "pdf"
  }'
```

## Integration Examples

### CI/CD Integration (GitHub Actions)

```yaml
name: Accessibility Testing
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  accessibility-test:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v2
      
    - name: Deploy staging
      run: |
        # Deploy your application to staging
        
    - name: Run accessibility tests
      run: |
        curl -X POST http://autotest.company.com/api/testing/page \
          -H "Content-Type: application/json" \
          -d '{
            "url": "https://staging.company.com",
            "wcag_level": "AA"
          }' > test_results.json
        
        # Parse results and fail if score < 90
        score=$(cat test_results.json | jq '.data.compliance_score')
        if (( $(echo "$score < 90" | bc -l) )); then
          echo "Accessibility score $score is below threshold"
          exit 1
        fi
```

### Monitoring Integration

```python
# Monitor accessibility scores with alerts
import requests
import time
from datetime import datetime, timedelta

def monitor_accessibility():
    api_base = "http://autotest.company.com/api"
    
    # Get recent test results
    response = requests.get(f"{api_base}/history/proj_123", params={
        "period": "day",
        "start_date": (datetime.now() - timedelta(days=7)).isoformat()
    })
    
    data = response.json()["data"]
    
    # Check for declining scores
    recent_scores = [point["compliance_score"] for point in data["data_points"][-3:]]
    if len(recent_scores) >= 2:
        trend = recent_scores[-1] - recent_scores[0]
        if trend < -5:  # Score dropped by more than 5 points
            send_alert(f"Accessibility score declined by {abs(trend)} points")

def send_alert(message):
    # Send to Slack, email, or monitoring system
    pass
```

---

This API reference provides comprehensive documentation for integrating with AutoTest. For additional examples or questions, please refer to the GitHub repository or open an issue.

*API Reference - AutoTest Version 1.0*