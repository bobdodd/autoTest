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
Proper unit tests for AutoTest core modules based on actual implementations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

# Import actual core modules
from autotest.core.database import DatabaseConnection, BaseRepository
from autotest.core.project_manager import ProjectManager
from autotest.core.website_manager import WebsiteManager
from autotest.core.scraper import WebScraper
from autotest.core.accessibility_tester import AccessibilityTester


class TestDatabaseConnection:
    """Test cases for DatabaseConnection module"""
    
    def test_initialization(self):
        """Test DatabaseConnection initialization"""
        config = Mock()
        db = DatabaseConnection(config)
        
        assert db.config == config
        assert db._client is None
        assert db._database is None
    
    @patch('autotest.core.database.MongoClient')
    def test_connect_success(self, mock_mongo_client):
        """Test successful database connection"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            'database.mongodb_uri': 'mongodb://localhost:27017',
            'database.database_name': 'test_db',
            'database.connection_timeout': 5000
        }.get(key, default)
        
        mock_client = Mock()
        mock_database = Mock()
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_database
        
        # Mock collection methods for index creation
        mock_collection = Mock()
        mock_database.__getitem__.return_value = mock_collection
        mock_database.projects = mock_collection
        mock_database.pages = mock_collection
        mock_database.test_results = mock_collection
        
        db = DatabaseConnection(config)
        db.connect()
        
        assert db._client == mock_client
        assert db._database == mock_database
        mock_client.admin.command.assert_called_with('ping')
    
    def test_disconnect(self):
        """Test database disconnection"""
        config = Mock()
        db = DatabaseConnection(config)
        
        mock_client = Mock()
        db._client = mock_client
        db._database = Mock()
        
        db.disconnect()
        
        assert db._client is None
        assert db._database is None
        mock_client.close.assert_called_once()
    
    def test_database_property_when_connected(self):
        """Test database property when connected"""
        config = Mock()
        db = DatabaseConnection(config)
        
        mock_database = Mock()
        db._database = mock_database
        
        assert db.database == mock_database
    
    def test_database_property_when_not_connected(self):
        """Test database property when not connected"""
        config = Mock()
        db = DatabaseConnection(config)
        
        with pytest.raises(RuntimeError, match="Database not connected"):
            _ = db.database
    
    def test_client_property_when_connected(self):
        """Test client property when connected"""
        config = Mock()
        db = DatabaseConnection(config)
        
        mock_client = Mock()
        db._client = mock_client
        
        assert db.client == mock_client
    
    def test_client_property_when_not_connected(self):
        """Test client property when not connected"""
        config = Mock()
        db = DatabaseConnection(config)
        
        with pytest.raises(RuntimeError, match="Database not connected"):
            _ = db.client
    
    def test_get_collection(self):
        """Test getting a collection"""
        config = Mock()
        db = DatabaseConnection(config)
        
        mock_database = Mock()
        mock_collection = Mock()
        db._database = mock_database
        mock_database.__getitem__.return_value = mock_collection
        
        result = db.get_collection('test_collection')
        
        assert result == mock_collection
        mock_database.__getitem__.assert_called_with('test_collection')


class TestBaseRepository:
    """Test cases for BaseRepository module"""
    
    def test_initialization(self):
        """Test BaseRepository initialization"""
        mock_db_conn = Mock()
        repo = BaseRepository(mock_db_conn, 'test_collection')
        
        assert repo.db_connection == mock_db_conn
        assert repo.collection_name == 'test_collection'
    
    def test_collection_property(self):
        """Test collection property"""
        mock_db_conn = Mock()
        mock_collection = Mock()
        mock_db_conn.get_collection.return_value = mock_collection
        
        repo = BaseRepository(mock_db_conn, 'test_collection')
        
        assert repo.collection == mock_collection
        mock_db_conn.get_collection.assert_called_with('test_collection')
    
    @patch('autotest.core.database.datetime')
    def test_create_document(self, mock_datetime):
        """Test creating a document"""
        mock_now = datetime(2025, 1, 1, 12, 0, 0)
        mock_datetime.datetime.utcnow.return_value = mock_now
        
        mock_db_conn = Mock()
        mock_collection = Mock()
        mock_db_conn.get_collection.return_value = mock_collection
        
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        mock_collection.insert_one.return_value = mock_result
        
        repo = BaseRepository(mock_db_conn, 'test_collection')
        
        test_data = {'name': 'test', 'value': 123}
        result = repo.create(test_data)
        
        assert result == str(mock_result.inserted_id)
        
        # Verify the data was modified with timestamps
        expected_data = {
            'name': 'test',
            'value': 123,
            'created_date': mock_now,
            'last_modified': mock_now
        }
        mock_collection.insert_one.assert_called_with(expected_data)
    
    def test_get_by_id_success(self):
        """Test getting document by ID successfully"""
        mock_db_conn = Mock()
        mock_collection = Mock()
        mock_db_conn.get_collection.return_value = mock_collection
        
        test_id = ObjectId()
        mock_doc = {'_id': test_id, 'name': 'test'}
        mock_collection.find_one.return_value = mock_doc
        
        repo = BaseRepository(mock_db_conn, 'test_collection')
        
        result = repo.get_by_id(str(test_id))
        
        assert result['_id'] == str(test_id)
        assert result['name'] == 'test'
        mock_collection.find_one.assert_called_with({"_id": test_id})
    
    def test_get_by_id_not_found(self):
        """Test getting document by ID when not found"""
        mock_db_conn = Mock()
        mock_collection = Mock()
        mock_db_conn.get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = None
        
        repo = BaseRepository(mock_db_conn, 'test_collection')
        
        result = repo.get_by_id('507f1f77bcf86cd799439011')
        
        assert result is None
    
    @patch('autotest.core.database.datetime')
    def test_update_document_success(self, mock_datetime):
        """Test updating a document successfully"""
        mock_now = datetime(2025, 1, 1, 12, 0, 0)
        mock_datetime.datetime.utcnow.return_value = mock_now
        
        mock_db_conn = Mock()
        mock_collection = Mock()
        mock_db_conn.get_collection.return_value = mock_collection
        
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_collection.update_one.return_value = mock_result
        
        repo = BaseRepository(mock_db_conn, 'test_collection')
        
        test_id = '507f1f77bcf86cd799439011'
        update_data = {'name': 'updated'}
        
        result = repo.update(test_id, update_data)
        
        assert result is True
        
        expected_update = {
            'name': 'updated',
            'last_modified': mock_now
        }
        mock_collection.update_one.assert_called_with(
            {"_id": ObjectId(test_id)},
            {"$set": expected_update}
        )
    
    def test_delete_document_success(self):
        """Test deleting a document successfully"""
        mock_db_conn = Mock()
        mock_collection = Mock()
        mock_db_conn.get_collection.return_value = mock_collection
        
        mock_result = Mock()
        mock_result.deleted_count = 1
        mock_collection.delete_one.return_value = mock_result
        
        repo = BaseRepository(mock_db_conn, 'test_collection')
        
        test_id = '507f1f77bcf86cd799439011'
        result = repo.delete(test_id)
        
        assert result is True
        mock_collection.delete_one.assert_called_with({"_id": ObjectId(test_id)})
    
    def test_find_all_with_filter(self):
        """Test finding all documents with filter"""
        mock_db_conn = Mock()
        mock_collection = Mock()
        mock_db_conn.get_collection.return_value = mock_collection
        
        mock_cursor = Mock()
        mock_docs = [
            {'_id': ObjectId(), 'name': 'doc1'},
            {'_id': ObjectId(), 'name': 'doc2'}
        ]
        mock_cursor.__iter__.return_value = iter(mock_docs)
        mock_collection.find.return_value = mock_cursor
        
        repo = BaseRepository(mock_db_conn, 'test_collection')
        
        filter_dict = {'active': True}
        result = repo.find_all(filter_dict)
        
        assert len(result) == 2
        assert all(isinstance(doc['_id'], str) for doc in result)
        mock_collection.find.assert_called_with(filter_dict)
    
    def test_count_documents(self):
        """Test counting documents"""
        mock_db_conn = Mock()
        mock_collection = Mock()
        mock_db_conn.get_collection.return_value = mock_collection
        mock_collection.count_documents.return_value = 5
        
        repo = BaseRepository(mock_db_conn, 'test_collection')
        
        filter_dict = {'active': True}
        result = repo.count(filter_dict)
        
        assert result == 5
        mock_collection.count_documents.assert_called_with(filter_dict)


class TestProjectManager:
    """Test cases for ProjectManager module"""
    
    @patch('autotest.core.project_manager.ProjectRepository')
    def test_initialization(self, mock_project_repo_class):
        """Test ProjectManager initialization"""
        mock_db_conn = Mock()
        mock_project_repo = Mock()
        mock_project_repo_class.return_value = mock_project_repo
        
        pm = ProjectManager(mock_db_conn)
        
        assert pm.db_connection == mock_db_conn
        mock_project_repo_class.assert_called_with(mock_db_conn)


class TestWebsiteManager:
    """Test cases for WebsiteManager module"""
    
    def test_initialization(self):
        """Test WebsiteManager initialization"""
        mock_db_conn = Mock()
        wm = WebsiteManager(mock_db_conn)
        
        assert wm.db_connection == mock_db_conn


class TestWebScraper:
    """Test cases for WebScraper module"""
    
    @patch('autotest.core.scraper.ProjectRepository')
    @patch('autotest.core.scraper.WebsiteManager')
    def test_initialization(self, mock_website_manager_class, mock_project_repo_class):
        """Test WebScraper initialization"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            'scraping.request_delay': 1.0,
            'scraping.user_agent': 'AutoTest/1.0',
            'testing.timeout': 30
        }.get(key, default)
        
        mock_db_conn = Mock()
        mock_project_repo = Mock()
        mock_website_manager = Mock()
        mock_project_repo_class.return_value = mock_project_repo
        mock_website_manager_class.return_value = mock_website_manager
        
        scraper = WebScraper(config, mock_db_conn)
        
        assert scraper.config == config
        assert scraper.db_connection == mock_db_conn
        assert scraper.driver is None
        assert scraper.request_delay == 1.0
        assert scraper.user_agent == 'AutoTest/1.0'
        assert scraper.timeout == 30


class TestAccessibilityTester:
    """Test cases for AccessibilityTester module"""
    
    @patch('autotest.core.accessibility_tester.PageRepository')
    @patch('autotest.core.accessibility_tester.TestResultRepository')
    @patch('autotest.core.accessibility_tester.WCAGRules')
    @patch('autotest.core.accessibility_tester.CSSAccessibilityRules')
    @patch('autotest.core.accessibility_tester.JSAccessibilityChecker')
    def test_initialization(self, mock_js_checker, mock_css_rules, mock_wcag_rules, 
                          mock_test_result_repo, mock_page_repo):
        """Test AccessibilityTester initialization"""
        config = Mock()
        mock_db_conn = Mock()
        
        # Mock the repository classes
        mock_page_repo.return_value = Mock()
        mock_test_result_repo.return_value = Mock()
        
        tester = AccessibilityTester(config, mock_db_conn)
        
        assert tester.config == config
        assert tester.db_connection == mock_db_conn