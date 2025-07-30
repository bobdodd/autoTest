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
MongoDB database connection and operations for AutoTest
"""

from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from bson import ObjectId
import datetime

from autotest.utils.logger import LoggerMixin
from autotest.utils.config import Config


class DatabaseConnection(LoggerMixin):
    """MongoDB database connection manager"""
    
    def __init__(self, config: Config):
        """
        Initialize database connection
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None
    
    def connect(self) -> None:
        """Establish connection to MongoDB"""
        try:
            mongodb_uri = self.config.get('database.mongodb_uri')
            database_name = self.config.get('database.database_name')
            timeout = self.config.get('database.connection_timeout', 5000)
            
            self.logger.info(f"Connecting to MongoDB at {mongodb_uri}")
            
            self._client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=timeout
            )
            
            # Test connection
            self._client.admin.command('ping')
            
            self._database = self._client[database_name]
            
            # Create indexes for better performance
            self._create_indexes()
            
            self.logger.info(f"Successfully connected to database '{database_name}'")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self.logger.info("Disconnected from MongoDB")
    
    def _create_indexes(self) -> None:
        """Create database indexes for better query performance"""
        if self._database is None:
            return
        
        try:
            # Projects collection indexes
            projects = self._database.projects
            projects.create_index([("name", 1)], unique=True)
            projects.create_index([("created_date", -1)])
            
            # Pages collection indexes
            pages = self._database.pages
            pages.create_index([("project_id", 1), ("website_id", 1)])
            pages.create_index([("url", 1)])
            pages.create_index([("last_tested", -1)])
            
            # Test results collection indexes
            test_results = self._database.test_results
            test_results.create_index([("page_id", 1), ("test_date", -1)])
            test_results.create_index([("test_date", -1)])
            
            self.logger.info("Database indexes created successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to create some indexes: {e}")
    
    @property
    def database(self) -> Database:
        """Get database instance"""
        if self._database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._database
    
    @property
    def client(self) -> MongoClient:
        """Get MongoDB client instance"""
        if self._client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._client
    
    def get_collection(self, name: str) -> Collection:
        """
        Get a collection by name
        
        Args:
            name: Collection name
        
        Returns:
            MongoDB collection
        """
        return self.database[name]


class BaseRepository(LoggerMixin):
    """Base repository class with common CRUD operations"""
    
    def __init__(self, db_connection: DatabaseConnection, collection_name: str):
        """
        Initialize repository
        
        Args:
            db_connection: Database connection instance
            collection_name: Name of the MongoDB collection
        """
        self.db_connection = db_connection
        self.collection_name = collection_name
    
    @property
    def collection(self) -> Collection:
        """Get the MongoDB collection"""
        return self.db_connection.get_collection(self.collection_name)
    
    def create(self, data: Dict[str, Any]) -> str:
        """
        Create a new document
        
        Args:
            data: Document data
        
        Returns:
            Created document ID
        """
        # Add timestamps
        now = datetime.datetime.utcnow()
        data['created_date'] = now
        data['last_modified'] = now
        
        result = self.collection.insert_one(data)
        self.logger.info(f"Created document in {self.collection_name}: {result.inserted_id}")
        return str(result.inserted_id)
    
    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID
        
        Args:
            doc_id: Document ID
        
        Returns:
            Document data or None if not found
        """
        try:
            result = self.collection.find_one({"_id": ObjectId(doc_id)})
            if result:
                result['_id'] = str(result['_id'])
            return result
        except Exception as e:
            self.logger.error(f"Error getting document {doc_id}: {e}")
            return None
    
    def update(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """
        Update document by ID
        
        Args:
            doc_id: Document ID
            data: Updated data
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Add last modified timestamp
            data['last_modified'] = datetime.datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": ObjectId(doc_id)},
                {"$set": data}
            )
            
            success = result.modified_count > 0
            if success:
                self.logger.info(f"Updated document in {self.collection_name}: {doc_id}")
            else:
                self.logger.warning(f"No document updated with ID: {doc_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating document {doc_id}: {e}")
            return False
    
    def delete(self, doc_id: str) -> bool:
        """
        Delete document by ID
        
        Args:
            doc_id: Document ID
        
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(doc_id)})
            success = result.deleted_count > 0
            
            if success:
                self.logger.info(f"Deleted document from {self.collection_name}: {doc_id}")
            else:
                self.logger.warning(f"No document deleted with ID: {doc_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def find_all(self, filter_dict: Optional[Dict[str, Any]] = None, 
                 limit: Optional[int] = None, 
                 sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """
        Find all documents matching filter
        
        Args:
            filter_dict: MongoDB filter dictionary
            limit: Maximum number of documents to return
            sort: Sort specification
        
        Returns:
            List of documents
        """
        try:
            filter_dict = filter_dict or {}
            cursor = self.collection.find(filter_dict)
            
            if sort:
                cursor = cursor.sort(sort)
            
            if limit:
                cursor = cursor.limit(limit)
            
            results = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                results.append(doc)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error finding documents: {e}")
            return []
    
    def count(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching filter
        
        Args:
            filter_dict: MongoDB filter dictionary
        
        Returns:
            Number of matching documents
        """
        try:
            filter_dict = filter_dict or {}
            return self.collection.count_documents(filter_dict)
        except Exception as e:
            self.logger.error(f"Error counting documents: {e}")
            return 0