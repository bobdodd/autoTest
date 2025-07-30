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
Multi-tenant User model for AutoTest application
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import uuid
import re
import hashlib
import secrets
import bcrypt

from autotest.core.database import DatabaseConnection
from autotest.utils.logger import get_logger

logger = get_logger(__name__)


class User:
    """
    Multi-tenant User model with client isolation.
    Each user belongs to exactly one client/tenant.
    """
    
    # User roles within each client
    ROLES = {
        'client_admin': {
            'name': 'Client Administrator',
            'description': 'Full access to client account and user management',
            'permissions': [
                'manage_users', 'manage_billing', 'view_all_projects',
                'create_projects', 'run_tests', 'view_reports',
                'manage_settings', 'export_data'
            ]
        },
        'project_manager': {
            'name': 'Project Manager',
            'description': 'Can create and manage projects and websites',
            'permissions': [
                'create_projects', 'manage_own_projects', 'run_tests',
                'view_reports', 'manage_websites', 'schedule_tests'
            ]
        },
        'tester': {
            'name': 'Tester',
            'description': 'Can run tests and view results',
            'permissions': [
                'run_tests', 'view_assigned_projects', 'view_reports',
                'export_results'
            ]
        },
        'viewer': {
            'name': 'Viewer',
            'description': 'Read-only access to assigned projects',
            'permissions': [
                'view_assigned_projects', 'view_reports'
            ]
        }
    }
    
    def __init__(self, data: Dict[str, Any] = None):
        """Initialize User with data from database or defaults"""
        if data:
            self.user_id = data.get('user_id')
            self.client_id = data.get('client_id')
            self.email = data.get('email')
            self.password_hash = data.get('password_hash')
            self.role = data.get('role', 'viewer')
            self.status = data.get('status', 'pending_activation')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
            self.last_login = data.get('last_login')
            self.profile = data.get('profile', {})
            self.preferences = data.get('preferences', {})
            self.auth = data.get('auth', {})
            self._id = data.get('_id')
        else:
            # Initialize new user with defaults
            self.user_id = None
            self.client_id = None
            self.email = None
            self.password_hash = None
            self.role = 'viewer'
            self.status = 'pending_activation'
            self.created_at = None
            self.updated_at = None
            self.last_login = None
            self.profile = self._default_profile()
            self.preferences = self._default_preferences()
            self.auth = self._default_auth()
            self._id = None
    
    def _default_profile(self) -> Dict[str, Any]:
        """Default user profile"""
        return {
            'first_name': '',
            'last_name': '',
            'avatar_url': None,
            'timezone': 'UTC',
            'language': 'en'
        }
    
    def _default_preferences(self) -> Dict[str, Any]:
        """Default user preferences"""
        return {
            'email_notifications': {
                'test_completion': True,
                'weekly_reports': True,
                'security_alerts': True,
                'project_updates': True
            },
            'ui_preferences': {
                'theme': 'light',
                'dashboard_layout': 'grid',
                'default_wcag_level': 'AA',
                'items_per_page': 20
            },
            'test_preferences': {
                'auto_schedule_frequency': 'weekly',
                'include_warnings': True,
                'detailed_reports': True
            }
        }
    
    def _default_auth(self) -> Dict[str, Any]:
        """Default authentication settings"""
        return {
            'password_reset_token': None,
            'password_reset_expires': None,
            'email_verification_token': None,
            'email_verified': False,
            'two_factor_enabled': False,
            'two_factor_secret': None,
            'failed_login_attempts': 0,
            'locked_until': None,
            'api_keys': []
        }
    
    @staticmethod
    def generate_user_id() -> str:
        """Generate unique user ID"""
        return f"user_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def set_password(self, password: str):
        """Set user password with validation"""
        errors = self.validate_password(password)
        if errors:
            raise ValueError(f"Password validation failed: {', '.join(errors)}")
        
        self.password_hash = self.hash_password(password)
        self.auth['password_reset_token'] = None
        self.auth['password_reset_expires'] = None
    
    def validate_password(self, password: str, client_settings: Dict = None) -> List[str]:
        """Validate password against client password policy"""
        errors = []
        
        # Default password policy
        policy = {
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_symbols': False
        }
        
        # Override with client settings if provided
        if client_settings and 'security' in client_settings:
            policy.update(client_settings['security'].get('password_policy', {}))
        
        if len(password) < policy['min_length']:
            errors.append(f"Password must be at least {policy['min_length']} characters")
        
        if policy['require_uppercase'] and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if policy['require_lowercase'] and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if policy['require_numbers'] and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if policy['require_symbols'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one symbol")
        
        return errors
    
    def validate(self) -> List[str]:
        """Validate user data and return list of errors"""
        errors = []
        
        # Required fields
        if not self.client_id:
            errors.append("Client ID is required")
        
        if not self.email or not self.email.strip():
            errors.append("Email is required")
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
            errors.append("Invalid email format")
        
        # Role validation
        if self.role not in self.ROLES:
            errors.append(f"Invalid role. Must be one of: {', '.join(self.ROLES.keys())}")
        
        # Status validation
        valid_statuses = ['pending_activation', 'active', 'suspended', 'deactivated']
        if self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return errors
    
    def get_role_info(self) -> Dict[str, Any]:
        """Get role information and permissions"""
        return self.ROLES.get(self.role, self.ROLES['viewer'])
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        role_info = self.get_role_info()
        return permission in role_info.get('permissions', [])
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users"""
        return self.has_permission('manage_users')
    
    def can_create_projects(self) -> bool:
        """Check if user can create new projects"""
        return self.has_permission('create_projects')
    
    def can_run_tests(self) -> bool:
        """Check if user can run accessibility tests"""
        return self.has_permission('run_tests')
    
    def can_view_all_projects(self) -> bool:
        """Check if user can view all client projects"""
        return self.has_permission('view_all_projects')
    
    def is_locked(self) -> bool:
        """Check if user account is locked due to failed login attempts"""
        if not self.auth.get('locked_until'):
            return False
        return datetime.utcnow() < self.auth['locked_until']
    
    def lock_account(self, duration_minutes: int = 30):
        """Lock user account for specified duration"""
        self.auth['locked_until'] = datetime.utcnow() + timedelta(minutes=duration_minutes)
        logger.warning(f"User account locked: {self.email} (Client: {self.client_id})")
    
    def unlock_account(self):
        """Unlock user account"""
        self.auth['locked_until'] = None
        self.auth['failed_login_attempts'] = 0
        logger.info(f"User account unlocked: {self.email} (Client: {self.client_id})")
    
    def record_login_attempt(self, success: bool, max_attempts: int = 5):
        """Record login attempt and lock account if necessary"""
        if success:
            self.auth['failed_login_attempts'] = 0
            self.last_login = datetime.utcnow()
            logger.info(f"Successful login: {self.email} (Client: {self.client_id})")
        else:
            self.auth['failed_login_attempts'] = self.auth.get('failed_login_attempts', 0) + 1
            logger.warning(f"Failed login attempt {self.auth['failed_login_attempts']}: {self.email}")
            
            if self.auth['failed_login_attempts'] >= max_attempts:
                self.lock_account()
    
    def generate_password_reset_token(self) -> str:
        """Generate password reset token"""
        token = secrets.token_urlsafe(32)
        self.auth['password_reset_token'] = hashlib.sha256(token.encode()).hexdigest()
        self.auth['password_reset_expires'] = datetime.utcnow() + timedelta(hours=1)
        return token
    
    def verify_password_reset_token(self, token: str) -> bool:
        """Verify password reset token"""
        if not self.auth.get('password_reset_token') or not self.auth.get('password_reset_expires'):
            return False
        
        if datetime.utcnow() > self.auth['password_reset_expires']:
            return False
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash == self.auth['password_reset_token']
    
    def generate_email_verification_token(self) -> str:
        """Generate email verification token"""
        token = secrets.token_urlsafe(32)
        self.auth['email_verification_token'] = hashlib.sha256(token.encode()).hexdigest()
        return token
    
    def verify_email_verification_token(self, token: str) -> bool:
        """Verify email verification token"""
        if not self.auth.get('email_verification_token'):
            return False
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash == self.auth['email_verification_token']:
            self.auth['email_verified'] = True
            self.auth['email_verification_token'] = None
            self.status = 'active'
            return True
        
        return False
    
    def generate_api_key(self, name: str = "Default API Key") -> str:
        """Generate API key for user"""
        key_id = uuid.uuid4().hex[:8]
        key_secret = secrets.token_urlsafe(32)
        
        # Format: at_{client_id}_key_{key_id}_{key_secret}
        api_key = f"at_{self.client_id}_key_{key_id}_{key_secret}"
        
        # Store hashed version
        key_hash = hashlib.sha256(f"{key_id}_{key_secret}".encode()).hexdigest()
        
        api_key_record = {
            'key_id': key_id,
            'key_hash': key_hash,
            'name': name,
            'created_at': datetime.utcnow(),
            'last_used': None,
            'status': 'active'
        }
        
        self.auth['api_keys'].append(api_key_record)
        
        return api_key
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key"""
        for key in self.auth.get('api_keys', []):
            if key['key_id'] == key_id:
                key['status'] = 'revoked'
                return True
        return False
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary for database storage or API response"""
        data = {
            'user_id': self.user_id,
            'client_id': self.client_id,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_login': self.last_login,
            'profile': self.profile,
            'preferences': self.preferences
        }
        
        if include_sensitive:
            data.update({
                'password_hash': self.password_hash,
                'auth': self.auth
            })
        
        return data
    
    def save(self, db_connection: DatabaseConnection = None) -> bool:
        """Save user to database"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            # Validate before saving
            errors = self.validate()
            if errors:
                logger.error(f"User validation failed: {', '.join(errors)}")
                return False
            
            now = datetime.utcnow()
            
            if self._id:
                # Update existing user
                self.updated_at = now
                result = db_connection.db.users.update_one(
                    {'_id': self._id},
                    {'$set': self.to_dict(include_sensitive=True)}
                )
                return result.modified_count > 0
            else:
                # Create new user
                if not self.user_id:
                    self.user_id = self.generate_user_id()
                
                self.created_at = now
                self.updated_at = now
                
                result = db_connection.db.users.insert_one(self.to_dict(include_sensitive=True))
                self._id = result.inserted_id
                return True
                
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False
    
    @classmethod
    def get_by_id(cls, user_id: str, client_id: str = None, db_connection: DatabaseConnection = None) -> Optional['User']:
        """Get user by user_id, optionally scoped to client"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            query = {'user_id': user_id}
            if client_id:
                query['client_id'] = client_id
            
            data = db_connection.db.users.find_one(query)
            return cls(data) if data else None
            
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    @classmethod
    def get_by_email(cls, email: str, client_id: str, db_connection: DatabaseConnection = None) -> Optional['User']:
        """Get user by email within client context"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            data = db_connection.db.users.find_one({
                'email': email.lower().strip(),
                'client_id': client_id
            })
            return cls(data) if data else None
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    @classmethod
    def list_by_client(cls, client_id: str, status: str = None, role: str = None, 
                      db_connection: DatabaseConnection = None) -> List['User']:
        """List users for a specific client"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            query = {'client_id': client_id}
            if status:
                query['status'] = status
            if role:
                query['role'] = role
            
            users = []
            for data in db_connection.db.users.find(query).sort('created_at', -1):
                users.append(cls(data))
            
            return users
            
        except Exception as e:
            logger.error(f"Error listing users for client {client_id}: {e}")
            return []
    
    def delete(self, db_connection: DatabaseConnection = None) -> bool:
        """Delete user (soft delete by setting status to deactivated)"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            if not self._id:
                return False
            
            # Soft delete - just mark as deactivated
            result = db_connection.db.users.update_one(
                {'_id': self._id},
                {
                    '$set': {
                        'status': 'deactivated',
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def __str__(self) -> str:
        return f"User(id={self.user_id}, email={self.email}, client={self.client_id}, role={self.role})"
    
    def __repr__(self) -> str:
        return self.__str__()