# AutoTest Multi-Tenant Architecture Design

## Overview

This document outlines the architectural design for transforming AutoTest from a single-tenant application into a comprehensive multi-tenant SaaS platform with complete client isolation.

## Architecture Goals

### Primary Objectives
- **Complete Client Isolation**: Each client's data is completely separated
- **Scalable Multi-Tenancy**: Support hundreds of clients efficiently
- **Enterprise Security**: Role-based access control within each tenant
- **SaaS Management**: Client onboarding, billing, and administration
- **Performance**: Maintain fast response times across all tenants

### Security Requirements
- **Data Isolation**: Zero cross-tenant data access
- **Authentication**: Secure client-scoped login system
- **Authorization**: Role-based permissions within each client
- **Audit Logging**: Complete tenant activity tracking
- **Compliance**: GDPR, SOC 2 compliance ready

## Multi-Tenant Strategy

### Tenant Isolation Model: **Shared Database, Isolated Data**

We'll implement a **Row-Level Security (RLS)** approach where:
- All tenants share the same database instance
- Every table includes a `client_id` foreign key
- All queries are automatically filtered by tenant context
- Application-level middleware enforces tenant isolation

#### Alternative Approaches Considered:
1. **Separate Databases per Tenant** - Too complex for management
2. **Separate Schemas per Tenant** - MongoDB doesn't support schemas
3. **Shared Database, Shared Tables** - ✅ **Selected** - Best balance of isolation and efficiency

## Database Schema Design

### Core Multi-Tenant Models

#### 1. Client/Tenant Model
```javascript
// clients collection
{
    "_id": ObjectId("..."),
    "client_id": "client_abc123",           // Unique client identifier
    "client_name": "Acme Corporation",      // Display name
    "domain": "acme.autotest.com",          // Subdomain or custom domain
    "subscription_plan": "enterprise",      // Plan type
    "status": "active",                     // active, suspended, cancelled
    "created_at": ISODate("..."),
    "updated_at": ISODate("..."),
    
    // Client settings
    "settings": {
        "max_users": 50,
        "max_projects": 100,
        "max_tests_per_month": 10000,
        "branding": {
            "logo_url": "/uploads/clients/abc123/logo.png",
            "primary_color": "#007bff",
            "secondary_color": "#6c757d"
        },
        "features": {
            "api_access": true,
            "scheduled_tests": true,
            "advanced_reports": true,
            "custom_rules": false
        }
    },
    
    // Billing information
    "billing": {
        "plan": "enterprise",
        "monthly_price": 299.00,
        "billing_cycle": "monthly",
        "next_billing_date": ISODate("..."),
        "payment_method": "stripe_pm_...",
        "billing_email": "billing@acme.com"
    },
    
    // Usage tracking
    "usage": {
        "current_users": 15,
        "current_projects": 23,
        "tests_this_month": 1547,
        "storage_used_mb": 2048
    }
}
```

#### 2. Multi-Tenant User Model
```javascript
// users collection
{
    "_id": ObjectId("..."),
    "user_id": "user_xyz789",
    "client_id": "client_abc123",           // ✅ Tenant isolation key
    "email": "john@acme.com",
    "password_hash": "$2b$12$...",
    "role": "project_manager",              // client_admin, project_manager, tester, viewer
    "status": "active",                     // active, suspended, pending_activation
    "created_at": ISODate("..."),
    "last_login": ISODate("..."),
    
    // User profile
    "profile": {
        "first_name": "John",
        "last_name": "Smith",
        "avatar_url": "/uploads/avatars/xyz789.jpg",
        "timezone": "America/New_York",
        "language": "en"
    },
    
    // User preferences
    "preferences": {
        "email_notifications": {
            "test_completion": true,
            "weekly_reports": true,
            "security_alerts": true
        },
        "ui_preferences": {
            "theme": "light",
            "dashboard_layout": "grid",
            "default_wcag_level": "AA"
        }
    },
    
    // Authentication
    "auth": {
        "password_reset_token": null,
        "password_reset_expires": null,
        "email_verification_token": null,
        "email_verified": true,
        "two_factor_enabled": false,
        "failed_login_attempts": 0,
        "locked_until": null
    }
}
```

### Updated Existing Models

#### 3. Multi-Tenant Project Model
```javascript
// projects collection - UPDATED
{
    "_id": ObjectId("..."),
    "project_id": "proj_123",
    "client_id": "client_abc123",           // ✅ NEW: Tenant isolation
    "created_by": "user_xyz789",            // ✅ NEW: User who created it
    "name": "Website Accessibility Testing",
    "description": "Main website testing project",
    "status": "active",
    "created_at": ISODate("..."),
    "updated_at": ISODate("..."),
    
    // Existing fields remain the same
    "settings": { /* ... */ },
    "websites": [ /* ... */ ]
}
```

#### 4. Multi-Tenant Website Model
```javascript
// websites collection - UPDATED
{
    "_id": ObjectId("..."),
    "website_id": "web_456",
    "client_id": "client_abc123",           // ✅ NEW: Tenant isolation
    "project_id": "proj_123",
    "created_by": "user_xyz789",            // ✅ NEW: User who created it
    
    // Existing fields remain the same
    "name": "Main Website",
    "base_url": "https://acme.com",
    /* ... all existing fields ... */
}
```

#### 5. Multi-Tenant Pages and Test Results
```javascript
// pages collection - UPDATED
{
    "_id": ObjectId("..."),
    "page_id": "page_789",
    "client_id": "client_abc123",           // ✅ NEW: Tenant isolation
    "website_id": "web_456",
    /* ... all existing fields ... */
}

// test_results collection - UPDATED
{
    "_id": ObjectId("..."),
    "result_id": "result_101112",
    "client_id": "client_abc123",           // ✅ NEW: Tenant isolation
    "page_id": "page_789",
    "project_id": "proj_123",
    "tested_by": "user_xyz789",             // ✅ NEW: User who ran test
    /* ... all existing fields ... */
}
```

## Tenant Routing Strategy

### Option 1: Subdomain-Based Routing (Recommended)
```
https://acme.autotest.com/       # Acme Corp tenant
https://globex.autotest.com/     # Globex Inc tenant
https://wayneent.autotest.com/   # Wayne Enterprises tenant
```

**Advantages:**
- Clear tenant separation
- Easy to implement
- SEO friendly
- Custom SSL per tenant

**Implementation:**
```python
# Flask subdomain routing
app.config['SERVER_NAME'] = 'autotest.com'

@app.route('/', subdomain='<client_slug>')
def tenant_dashboard(client_slug):
    client = get_client_by_slug(client_slug)
    if not client:
        return render_template('tenant_not_found.html'), 404
    
    # Set tenant context for request
    g.current_client = client
    return render_template('dashboard.html')
```

### Option 2: Path-Based Routing (Fallback)
```
https://autotest.com/client/acme/     # Acme Corp tenant
https://autotest.com/client/globex/   # Globex Inc tenant
```

**Use Case:** When subdomain setup is not feasible

## Authentication & Authorization

### Authentication Flow

#### 1. Client-Scoped Login
```python
# Login process
1. User visits: https://acme.autotest.com/login
2. Extract client from subdomain: "acme"
3. Validate client exists and is active
4. Authenticate user within client context
5. Create session with both user_id and client_id
6. Redirect to client dashboard
```

#### 2. Session Structure
```python
session = {
    'user_id': 'user_xyz789',
    'client_id': 'client_abc123',
    'client_slug': 'acme',
    'user_role': 'project_manager',
    'logged_in_at': datetime.utcnow(),
    'expires_at': datetime.utcnow() + timedelta(hours=8)
}
```

### Authorization Roles

#### Client Admin
- **Permissions**: Full access within their client
- **Can**: Manage users, view all projects, access billing
- **Cannot**: Access other clients' data, system administration

#### Project Manager  
- **Permissions**: Create/manage projects and websites
- **Can**: Create projects, manage team projects, run tests
- **Cannot**: Manage users, access billing, view other managers' private projects

#### Tester
- **Permissions**: Run tests and view results
- **Can**: Execute tests, view assigned projects, generate reports
- **Cannot**: Create projects, manage websites, access administration

#### Viewer
- **Permissions**: Read-only access
- **Can**: View test results, download reports
- **Cannot**: Run tests, modify anything, access administration

## Tenant Isolation Middleware

### Database Query Filtering

#### Automatic Tenant Filtering
```python
class TenantAwareDatabase:
    def __init__(self):
        self.db = get_database_connection()
    
    def find(self, collection, query=None, **kwargs):
        """Automatically add client_id filter to all queries"""
        if not hasattr(g, 'current_client'):
            raise SecurityError("No tenant context set")
        
        query = query or {}
        query['client_id'] = g.current_client.client_id
        
        return self.db[collection].find(query, **kwargs)
    
    def insert_one(self, collection, document):
        """Automatically add client_id to all inserts"""
        if not hasattr(g, 'current_client'):
            raise SecurityError("No tenant context set")
        
        document['client_id'] = g.current_client.client_id
        document['created_at'] = datetime.utcnow()
        
        return self.db[collection].insert_one(document)
```

#### Request Middleware
```python
@app.before_request
def set_tenant_context():
    """Set tenant context for every request"""
    
    # Skip tenant context for system routes
    if request.endpoint in ['health_check', 'system_status', 'admin']:
        return
    
    # Extract tenant from subdomain or path
    client_slug = get_client_slug_from_request(request)
    
    if not client_slug:
        return render_template('no_tenant.html'), 400
    
    # Load and validate client
    client = ClientService.get_by_slug(client_slug)
    if not client or client.status != 'active':
        return render_template('tenant_not_found.html'), 404
    
    # Set global tenant context
    g.current_client = client
    g.client_id = client.client_id
```

## Data Migration Strategy

### Phase 1: Schema Migration
```python
# Migration script: add_client_id_to_existing_collections.py

def migrate_to_multi_tenant():
    """Add client_id to all existing collections"""
    
    # Create default client for existing data
    default_client = {
        'client_id': 'client_default',
        'client_name': 'Default Client',
        'domain': 'default.autotest.com',
        'status': 'active',
        'created_at': datetime.utcnow()
    }
    db.clients.insert_one(default_client)
    
    # Update all existing collections
    collections_to_update = [
        'projects', 'websites', 'pages', 'test_results',
        'scheduled_tests', 'reports', 'snapshots'
    ]
    
    for collection_name in collections_to_update:
        db[collection_name].update_many(
            {'client_id': {'$exists': False}},
            {'$set': {'client_id': 'client_default'}}
        )
        
        # Create index for performance
        db[collection_name].create_index([('client_id', 1)])
```

## Performance Considerations

### Database Indexing Strategy
```javascript
// Essential indexes for multi-tenant performance
db.projects.createIndex({"client_id": 1, "status": 1})
db.projects.createIndex({"client_id": 1, "created_at": -1})

db.websites.createIndex({"client_id": 1, "project_id": 1})
db.pages.createIndex({"client_id": 1, "website_id": 1})

db.test_results.createIndex({"client_id": 1, "test_date": -1})
db.test_results.createIndex({"client_id": 1, "project_id": 1, "test_date": -1})

db.users.createIndex({"client_id": 1, "email": 1}, {"unique": true})
db.users.createIndex({"client_id": 1, "role": 1})
```

### Query Optimization
- **Always filter by client_id first** in compound indexes
- **Use projection** to limit returned fields
- **Implement query result caching** per tenant
- **Monitor query performance** per tenant

### Resource Limits
```python
# Per-tenant resource limits
TENANT_LIMITS = {
    'free': {
        'max_users': 5,
        'max_projects': 10,
        'max_tests_per_month': 1000,
        'storage_limit_mb': 500
    },
    'pro': {
        'max_users': 25,
        'max_projects': 50,
        'max_tests_per_month': 5000,
        'storage_limit_mb': 2000
    },
    'enterprise': {
        'max_users': 100,
        'max_projects': 200,
        'max_tests_per_month': 20000,
        'storage_limit_mb': 10000
    }
}
```

## Security Implementation

### Cross-Tenant Data Protection
```python
class TenantSecurityError(Exception):
    """Raised when cross-tenant access is attempted"""
    pass

def validate_tenant_access(resource_client_id):
    """Ensure user can only access their tenant's resources"""
    if not hasattr(g, 'current_client'):
        raise TenantSecurityError("No tenant context")
    
    if resource_client_id != g.current_client.client_id:
        raise TenantSecurityError(f"Cross-tenant access denied")
```

### Audit Logging
```python
def log_tenant_activity(action, resource_type, resource_id, details=None):
    """Log all tenant activities for compliance"""
    audit_log = {
        'client_id': g.current_client.client_id,
        'user_id': g.current_user.user_id,
        'action': action,  # create, read, update, delete
        'resource_type': resource_type,  # project, website, test, user
        'resource_id': resource_id,
        'timestamp': datetime.utcnow(),
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string,
        'details': details
    }
    
    db.audit_logs.insert_one(audit_log)
```

## API Updates for Multi-Tenancy

### Tenant-Aware Endpoints
```python
# Before: Single-tenant
GET /api/projects

# After: Multi-tenant  
GET /api/projects  # Automatically filtered by tenant context

# API Response includes client context
{
    "success": true,
    "client_id": "client_abc123",
    "data": [...],
    "tenant_info": {
        "client_name": "Acme Corporation",
        "subscription_plan": "enterprise"
    }
}
```

### API Authentication
```python
# API key format includes tenant context
api_key = "at_client_abc123_key_xyz789..."

def authenticate_api_request(api_key):
    """Extract both user and tenant from API key"""
    parts = api_key.split('_')
    if len(parts) < 4 or parts[0] != 'at':
        raise AuthenticationError("Invalid API key format")
    
    client_id = f"{parts[1]}_{parts[2]}"
    key_part = '_'.join(parts[3:])
    
    # Validate API key within tenant context
    api_key_record = db.api_keys.find_one({
        'client_id': client_id,
        'key_hash': hash_api_key(key_part),
        'status': 'active'
    })
    
    if not api_key_record:
        raise AuthenticationError("Invalid API key")
    
    return api_key_record
```

## Implementation Phases

### Phase 11.1: Architecture & Models ✅ (Current)
- [x] Design multi-tenant architecture
- [ ] Create Client/Tenant model
- [ ] Create multi-tenant User model
- [ ] Design database migration strategy

### Phase 11.2: Database Layer
- [ ] Implement tenant-aware database wrapper
- [ ] Create migration scripts
- [ ] Update all existing models
- [ ] Add comprehensive indexing

### Phase 11.3: Authentication System
- [ ] Implement subdomain routing
- [ ] Create client-scoped login system
- [ ] Build session management
- [ ] Add role-based authorization

### Phase 11.4: UI & Administration
- [ ] Create client onboarding flow
- [ ] Build client admin dashboard
- [ ] Implement user management interface
- [ ] Add tenant branding system

### Phase 11.5: API & Integration
- [ ] Update all API endpoints
- [ ] Implement API authentication
- [ ] Add rate limiting per tenant
- [ ] Create webhook system

### Phase 11.6: Testing & Security
- [ ] Comprehensive security testing
- [ ] Cross-tenant isolation verification
- [ ] Performance testing with multiple tenants
- [ ] Compliance audit preparation

## Risk Mitigation

### Data Isolation Risks
- **Risk**: Cross-tenant data leakage
- **Mitigation**: Automated testing, middleware validation, audit logging

### Performance Risks  
- **Risk**: Database performance degradation
- **Mitigation**: Proper indexing, query optimization, tenant-aware caching

### Security Risks
- **Risk**: Authentication bypass
- **Mitigation**: Multi-layer security, session validation, audit trails

## Success Metrics

### Technical Metrics
- **Zero cross-tenant data access** incidents
- **Sub-200ms response times** for 95% of requests
- **99.9% uptime** across all tenants
- **Horizontal scalability** to 1000+ tenants

### Business Metrics
- **Self-service onboarding** for new clients
- **Role-based access control** adoption
- **API usage growth** across tenants
- **Client satisfaction** with isolation and performance

---

This architecture provides a solid foundation for transforming AutoTest into a scalable, secure, multi-tenant SaaS platform while maintaining complete client isolation and enterprise-grade security.

*Multi-Tenant Architecture Design - AutoTest Version 2.0*