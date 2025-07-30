# AutoTest - Accessibility Testing Platform
# Copyright (C) 2025 Bob Dodd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Tenant-aware database layer for multi-tenant AutoTest application.
Automatically handles client isolation for all database operations.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from flask import g, has_request_context
import pymongo
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.results import InsertOneResult, InsertManyResult, UpdateResult, DeleteResult

from autotest.core.database import DatabaseConnection
from autotest.utils.logger import get_logger

logger = get_logger(__name__)


class TenantSecurityError(Exception):
    """Raised when tenant security is violated"""
    pass


class TenantAwareDatabase:
    """
    Database wrapper that automatically enforces tenant isolation.
    All queries are automatically filtered by client_id.
    """
    
    # Collections that don't require tenant filtering (system collections)
    SYSTEM_COLLECTIONS = {
        'clients',  # Client/tenant data itself
        'system_config',
        'audit_logs',
        'migrations'
    }
    
    # Collections that require tenant isolation
    TENANT_COLLECTIONS = {
        'users',
        'projects', 
        'websites',
        'pages',
        'test_results',
        'scheduled_tests',
        'reports',
        'snapshots',
        'api_keys'
    }
    
    def __init__(self, db_connection: DatabaseConnection = None):
        """Initialize tenant-aware database"""
        if db_connection:
            self.db_connection = db_connection
        else:
            from autotest.utils.config import Config
            config = Config()
            self.db_connection = DatabaseConnection(config)
            self.db_connection.connect()
        
        self.db = self.db_connection.db
    
    def _get_current_client_id(self) -> str:
        """Get current client ID from Flask global context"""
        if not has_request_context():
            # No request context - this might be a system operation
            if hasattr(g, 'system_mode') and g.system_mode:
                return None  # System mode allows cross-tenant access
            raise TenantSecurityError("No request context available for tenant isolation")
        
        if not hasattr(g, 'current_client') or not g.current_client:
            raise TenantSecurityError("No tenant context set in request")
        
        return g.current_client.client_id
    
    def _add_tenant_filter(self, collection_name: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """Add tenant filter to query if required"""
        if collection_name in self.SYSTEM_COLLECTIONS:
            return query  # No tenant filtering for system collections
        
        if collection_name not in self.TENANT_COLLECTIONS:
            logger.warning(f"Unknown collection {collection_name} - applying tenant filter by default")
        
        client_id = self._get_current_client_id()
        if client_id:
            query = query.copy()
            query['client_id'] = client_id
        
        return query
    
    def _add_tenant_data(self, collection_name: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Add tenant data to document if required"""
        if collection_name in self.SYSTEM_COLLECTIONS:
            return document  # No tenant data for system collections
        
        client_id = self._get_current_client_id()
        if client_id:
            document = document.copy()
            document['client_id'] = client_id
            
            # Add audit fields
            now = datetime.utcnow()
            if 'created_at' not in document:
                document['created_at'] = now
            document['updated_at'] = now
        
        return document
    
    def _validate_tenant_access(self, collection_name: str, document: Dict[str, Any]):
        """Validate that document belongs to current tenant"""
        if collection_name in self.SYSTEM_COLLECTIONS:
            return  # No validation for system collections
        
        client_id = self._get_current_client_id()
        if client_id and document.get('client_id') != client_id:
            raise TenantSecurityError(
                f"Cross-tenant access denied: document belongs to {document.get('client_id')}, "
                f"current tenant is {client_id}"
            )
    
    # Collection access methods
    def get_collection(self, collection_name: str) -> 'TenantAwareCollection':
        """Get tenant-aware collection wrapper"""
        return TenantAwareCollection(self, collection_name)
    
    def __getattr__(self, collection_name: str) -> 'TenantAwareCollection':
        """Allow direct collection access like db.projects"""
        return self.get_collection(collection_name)
    
    def __getitem__(self, collection_name: str) -> 'TenantAwareCollection':
        """Allow bracket notation like db['projects']"""
        return self.get_collection(collection_name)
    
    # System operations (bypass tenant filtering)
    def system_operation(self, operation_func):
        """Execute operation in system mode (bypasses tenant filtering)"""
        def wrapper(*args, **kwargs):
            # Set system mode flag
            old_system_mode = getattr(g, 'system_mode', False)
            g.system_mode = True
            
            try:
                return operation_func(*args, **kwargs)
            finally:
                g.system_mode = old_system_mode
        
        return wrapper
    
    # Aggregation pipeline helpers
    def add_tenant_match_stage(self, pipeline: List[Dict], collection_name: str) -> List[Dict]:
        """Add tenant filtering stage to aggregation pipeline"""
        if collection_name in self.SYSTEM_COLLECTIONS:
            return pipeline
        
        client_id = self._get_current_client_id()
        if client_id:
            # Insert tenant filter as first stage
            match_stage = {'$match': {'client_id': client_id}}
            return [match_stage] + pipeline
        
        return pipeline


class TenantAwareCollection:
    """
    Tenant-aware collection wrapper that automatically applies tenant filtering.
    """
    
    def __init__(self, tenant_db: TenantAwareDatabase, collection_name: str):
        self.tenant_db = tenant_db
        self.collection_name = collection_name
        self.collection: Collection = tenant_db.db[collection_name]
    
    # Read operations
    def find_one(self, query: Dict[str, Any] = None, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Find one document with tenant filtering"""
        query = query or {}
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        
        result = self.collection.find_one(query, *args, **kwargs)
        if result:
            self.tenant_db._validate_tenant_access(self.collection_name, result)
        
        return result
    
    def find(self, query: Dict[str, Any] = None, *args, **kwargs) -> Cursor:
        """Find documents with tenant filtering"""
        query = query or {}
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        
        return self.collection.find(query, *args, **kwargs)
    
    def count_documents(self, query: Dict[str, Any] = None, **kwargs) -> int:
        """Count documents with tenant filtering"""
        query = query or {}
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        
        return self.collection.count_documents(query, **kwargs)
    
    def distinct(self, field: str, query: Dict[str, Any] = None, **kwargs) -> List:
        """Get distinct values with tenant filtering"""
        query = query or {}
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        
        return self.collection.distinct(field, query, **kwargs)
    
    # Write operations
    def insert_one(self, document: Dict[str, Any], **kwargs) -> InsertOneResult:
        """Insert one document with tenant data"""
        document = self.tenant_db._add_tenant_data(self.collection_name, document)
        
        return self.collection.insert_one(document, **kwargs)
    
    def insert_many(self, documents: List[Dict[str, Any]], **kwargs) -> InsertManyResult:
        """Insert many documents with tenant data"""
        tenant_documents = []
        for doc in documents:
            tenant_documents.append(
                self.tenant_db._add_tenant_data(self.collection_name, doc)
            )
        
        return self.collection.insert_many(tenant_documents, **kwargs)
    
    def update_one(self, query: Dict[str, Any], update: Dict[str, Any], **kwargs) -> UpdateResult:
        """Update one document with tenant filtering"""
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        
        # Add updated_at to update operations
        if '$set' in update:
            update['$set']['updated_at'] = datetime.utcnow()
        elif '$inc' in update or '$push' in update or '$pull' in update:
            # For non-$set operations, use $currentDate
            if '$currentDate' not in update:
                update['$currentDate'] = {}
            update['$currentDate']['updated_at'] = True
        
        return self.collection.update_one(query, update, **kwargs)
    
    def update_many(self, query: Dict[str, Any], update: Dict[str, Any], **kwargs) -> UpdateResult:
        """Update many documents with tenant filtering"""
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        
        # Add updated_at to update operations
        if '$set' in update:
            update['$set']['updated_at'] = datetime.utcnow()
        elif '$inc' in update or '$push' in update or '$pull' in update:
            if '$currentDate' not in update:
                update['$currentDate'] = {}
            update['$currentDate']['updated_at'] = True
        
        return self.collection.update_many(query, update, **kwargs)
    
    def replace_one(self, query: Dict[str, Any], replacement: Dict[str, Any], **kwargs) -> UpdateResult:
        """Replace one document with tenant filtering and data"""
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        replacement = self.tenant_db._add_tenant_data(self.collection_name, replacement)
        
        return self.collection.replace_one(query, replacement, **kwargs)
    
    def delete_one(self, query: Dict[str, Any], **kwargs) -> DeleteResult:
        """Delete one document with tenant filtering"""
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        
        return self.collection.delete_one(query, **kwargs)
    
    def delete_many(self, query: Dict[str, Any], **kwargs) -> DeleteResult:
        """Delete many documents with tenant filtering"""
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        
        return self.collection.delete_many(query, **kwargs)
    
    # Aggregation operations
    def aggregate(self, pipeline: List[Dict], **kwargs) -> Cursor:
        """Run aggregation pipeline with tenant filtering"""
        pipeline = self.tenant_db.add_tenant_match_stage(pipeline, self.collection_name)
        
        return self.collection.aggregate(pipeline, **kwargs)
    
    # Index operations (pass through to underlying collection)
    def create_index(self, keys, **kwargs):
        """Create index on underlying collection"""
        return self.collection.create_index(keys, **kwargs)
    
    def create_indexes(self, indexes, **kwargs):
        """Create multiple indexes on underlying collection"""
        return self.collection.create_indexes(indexes, **kwargs)
    
    def drop_index(self, index, **kwargs):
        """Drop index on underlying collection"""
        return self.collection.drop_index(index, **kwargs)
    
    def list_indexes(self):
        """List indexes on underlying collection"""
        return self.collection.list_indexes()
    
    # Utility methods
    def find_one_and_update(self, query: Dict[str, Any], update: Dict[str, Any], 
                           **kwargs) -> Optional[Dict[str, Any]]:
        """Find one document and update with tenant filtering"""
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        
        # Add updated_at to update operations
        if '$set' in update:
            update['$set']['updated_at'] = datetime.utcnow()
        
        return self.collection.find_one_and_update(query, update, **kwargs)
    
    def find_one_and_replace(self, query: Dict[str, Any], replacement: Dict[str, Any], 
                            **kwargs) -> Optional[Dict[str, Any]]:
        """Find one document and replace with tenant filtering"""
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        replacement = self.tenant_db._add_tenant_data(self.collection_name, replacement)
        
        return self.collection.find_one_and_replace(query, replacement, **kwargs)
    
    def find_one_and_delete(self, query: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """Find one document and delete with tenant filtering"""
        query = self.tenant_db._add_tenant_filter(self.collection_name, query)
        
        return self.collection.find_one_and_delete(query, **kwargs)


class TenantDatabaseService:
    """
    Service class for managing tenant database operations
    """
    
    @staticmethod
    def get_tenant_db() -> TenantAwareDatabase:
        """Get tenant-aware database instance"""
        return TenantAwareDatabase()
    
    @staticmethod
    def create_tenant_indexes():
        """Create essential indexes for multi-tenant collections"""
        db = TenantAwareDatabase()
        
        # Use system mode to create indexes
        @db.system_operation
        def create_indexes():
            # Client indexes
            db.clients.create_index([('client_id', 1)], unique=True)
            db.clients.create_index([('client_slug', 1)], unique=True)
            db.clients.create_index([('domain', 1)], sparse=True)
            db.clients.create_index([('status', 1)])
            
            # User indexes
            db.users.create_index([('client_id', 1), ('email', 1)], unique=True)
            db.users.create_index([('client_id', 1), ('user_id', 1)], unique=True)
            db.users.create_index([('client_id', 1), ('role', 1)])
            db.users.create_index([('client_id', 1), ('status', 1)])
            
            # Project indexes
            db.projects.create_index([('client_id', 1), ('project_id', 1)], unique=True)
            db.projects.create_index([('client_id', 1), ('status', 1)])
            db.projects.create_index([('client_id', 1), ('created_at', -1)])
            
            # Website indexes
            db.websites.create_index([('client_id', 1), ('website_id', 1)], unique=True)
            db.websites.create_index([('client_id', 1), ('project_id', 1)])
            
            # Page indexes
            db.pages.create_index([('client_id', 1), ('page_id', 1)], unique=True)
            db.pages.create_index([('client_id', 1), ('website_id', 1)])
            db.pages.create_index([('client_id', 1), ('url', 1)])
            
            # Test result indexes
            db.test_results.create_index([('client_id', 1), ('result_id', 1)], unique=True)
            db.test_results.create_index([('client_id', 1), ('project_id', 1), ('test_date', -1)])
            db.test_results.create_index([('client_id', 1), ('page_id', 1), ('test_date', -1)])
            
            # Scheduled test indexes
            db.scheduled_tests.create_index([('client_id', 1), ('schedule_id', 1)], unique=True)
            db.scheduled_tests.create_index([('client_id', 1), ('next_run', 1), ('status', 1)])
            
            logger.info("Multi-tenant database indexes created successfully")
        
        create_indexes()
    
    @staticmethod
    def migrate_existing_data_to_multitenant(default_client_id: str = "client_default"):
        """
        Migrate existing single-tenant data to multi-tenant structure.
        This should be run once during the upgrade to v2.0.
        """
        db = TenantAwareDatabase()
        
        @db.system_operation
        def migrate_data():
            logger.info("Starting migration to multi-tenant structure...")
            
            # Create default client if it doesn't exist
            existing_client = db.clients.find_one({'client_id': default_client_id})
            if not existing_client:
                default_client = {
                    'client_id': default_client_id,
                    'client_name': 'Default Client',
                    'client_slug': 'default',
                    'domain': None,
                    'subscription_plan': 'enterprise',
                    'status': 'active',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'settings': {
                        'branding': {
                            'logo_url': None,
                            'primary_color': '#007bff',
                            'secondary_color': '#6c757d'
                        },
                        'features': {
                            'api_access': True,
                            'scheduled_tests': True,
                            'advanced_reports': True,
                            'custom_rules': True,
                            'priority_support': True
                        }
                    },
                    'billing': {'plan': 'enterprise', 'monthly_price': 0.00},
                    'usage': {'current_users': 0, 'current_projects': 0}
                }
                db.clients.insert_one(default_client)
                logger.info(f"Created default client: {default_client_id}")
            
            # Migrate each collection
            collections_to_migrate = [
                'projects', 'websites', 'pages', 'test_results',
                'scheduled_tests', 'reports', 'snapshots'
            ]
            
            for collection_name in collections_to_migrate:
                collection = db.db[collection_name]
                
                # Count documents without client_id
                count = collection.count_documents({'client_id': {'$exists': False}})
                if count > 0:
                    logger.info(f"Migrating {count} documents in {collection_name}")
                    
                    # Add client_id to all documents without it
                    result = collection.update_many(
                        {'client_id': {'$exists': False}},
                        {
                            '$set': {
                                'client_id': default_client_id,
                                'updated_at': datetime.utcnow()
                            }
                        }
                    )
                    
                    logger.info(f"Updated {result.modified_count} documents in {collection_name}")
                else:
                    logger.info(f"No migration needed for {collection_name}")
            
            logger.info("Multi-tenant migration completed successfully")
        
        migrate_data()
    
    @staticmethod
    def validate_tenant_isolation(client_id: str) -> Dict[str, Any]:
        """
        Validate that tenant isolation is working correctly.
        Returns report of any issues found.
        """
        db = TenantAwareDatabase()
        issues = []
        
        @db.system_operation
        def validate_isolation():
            # Check each tenant collection for cross-tenant data
            for collection_name in db.TENANT_COLLECTIONS:
                collection = db.db[collection_name]
                
                # Find documents that don't belong to the specified client
                cross_tenant_docs = list(collection.find({
                    'client_id': {'$ne': client_id}
                }))
                
                if cross_tenant_docs:
                    issues.append({
                        'collection': collection_name,
                        'issue': 'cross_tenant_data_found',
                        'count': len(cross_tenant_docs),
                        'sample_ids': [str(doc['_id']) for doc in cross_tenant_docs[:5]]
                    })
                
                # Check for documents without client_id
                missing_client_id = collection.count_documents({
                    'client_id': {'$exists': False}
                })
                
                if missing_client_id > 0:
                    issues.append({
                        'collection': collection_name,
                        'issue': 'missing_client_id',
                        'count': missing_client_id
                    })
        
        validate_isolation()
        
        return {
            'client_id': client_id,
            'validation_date': datetime.utcnow(),
            'issues_found': len(issues),
            'issues': issues,
            'status': 'clean' if len(issues) == 0 else 'issues_found'
        }