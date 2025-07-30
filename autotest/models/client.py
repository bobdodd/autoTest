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
Client/Tenant model for multi-tenant AutoTest application
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import uuid
import re

from autotest.core.database import DatabaseConnection
from autotest.utils.logger import get_logger

logger = get_logger(__name__)


class Client:
    """
    Client/Tenant model for multi-tenant architecture.
    Each client represents an isolated tenant with their own users and data.
    """
    
    # Subscription plans and their limits
    SUBSCRIPTION_PLANS = {
        'free': {
            'name': 'Free Plan',
            'monthly_price': 0.00,
            'max_users': 3,
            'max_projects': 5,
            'max_tests_per_month': 500,
            'storage_limit_mb': 100,
            'features': {
                'api_access': False,
                'scheduled_tests': False,
                'advanced_reports': False,
                'custom_rules': False,
                'priority_support': False
            }
        },
        'pro': {
            'name': 'Professional Plan',
            'monthly_price': 49.00,
            'max_users': 15,
            'max_projects': 25,
            'max_tests_per_month': 2500,
            'storage_limit_mb': 1000,
            'features': {
                'api_access': True,
                'scheduled_tests': True,
                'advanced_reports': True,
                'custom_rules': False,
                'priority_support': False
            }
        },
        'enterprise': {
            'name': 'Enterprise Plan',
            'monthly_price': 199.00,
            'max_users': 100,
            'max_projects': 100,
            'max_tests_per_month': 10000,
            'storage_limit_mb': 5000,
            'features': {
                'api_access': True,
                'scheduled_tests': True,
                'advanced_reports': True,
                'custom_rules': True,
                'priority_support': True
            }
        }
    }
    
    def __init__(self, data: Dict[str, Any] = None):
        """Initialize Client with data from database or defaults"""
        if data:
            self.client_id = data.get('client_id')
            self.client_name = data.get('client_name')
            self.client_slug = data.get('client_slug')
            self.domain = data.get('domain')
            self.subscription_plan = data.get('subscription_plan', 'free')
            self.status = data.get('status', 'active')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
            self.settings = data.get('settings', {})
            self.billing = data.get('billing', {})
            self.usage = data.get('usage', {})
            self._id = data.get('_id')
        else:
            # Initialize new client with defaults
            self.client_id = None
            self.client_name = None
            self.client_slug = None
            self.domain = None
            self.subscription_plan = 'free'
            self.status = 'pending'
            self.created_at = None
            self.updated_at = None
            self.settings = self._default_settings()
            self.billing = self._default_billing()
            self.usage = self._default_usage()
            self._id = None
    
    def _default_settings(self) -> Dict[str, Any]:
        """Default client settings"""
        return {
            'branding': {
                'logo_url': None,
                'primary_color': '#007bff',
                'secondary_color': '#6c757d',
                'favicon_url': None
            },
            'features': self.SUBSCRIPTION_PLANS['free']['features'].copy(),
            'security': {
                'require_2fa': False,
                'session_timeout_hours': 8,
                'password_policy': {
                    'min_length': 8,
                    'require_uppercase': True,
                    'require_lowercase': True,
                    'require_numbers': True,
                    'require_symbols': False
                }
            },
            'notifications': {
                'admin_email': None,
                'test_completion_notifications': True,
                'weekly_reports': True,
                'security_alerts': True
            }
        }
    
    def _default_billing(self) -> Dict[str, Any]:
        """Default billing information"""
        return {
            'plan': 'free',
            'monthly_price': 0.00,
            'billing_cycle': 'monthly',
            'next_billing_date': None,
            'payment_method': None,
            'billing_email': None,
            'billing_address': {},
            'payment_status': 'current'
        }
    
    def _default_usage(self) -> Dict[str, Any]:
        """Default usage tracking"""
        return {
            'current_users': 0,
            'current_projects': 0,
            'tests_this_month': 0,
            'storage_used_mb': 0,
            'last_activity': None,
            'monthly_reset_date': self._get_monthly_reset_date()
        }
    
    def _get_monthly_reset_date(self) -> datetime:
        """Get the next monthly usage reset date"""
        now = datetime.utcnow()
        if now.day <= 1:
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if next_month.month == 12:
                next_month = next_month.replace(year=next_month.year + 1, month=1)
            else:
                next_month = next_month.replace(month=next_month.month + 1)
            return next_month
    
    @staticmethod
    def generate_client_id() -> str:
        """Generate unique client ID"""
        return f"client_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def generate_client_slug(client_name: str) -> str:
        """Generate URL-safe client slug from name"""
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        slug = re.sub(r'[^\w\s-]', '', client_name.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        
        # Ensure it's not empty and not too long
        if not slug:
            slug = f"client-{uuid.uuid4().hex[:8]}"
        elif len(slug) > 50:
            slug = slug[:50].rstrip('-')
        
        return slug
    
    def validate(self) -> List[str]:
        """Validate client data and return list of errors"""
        errors = []
        
        # Required fields
        if not self.client_name or len(self.client_name.strip()) < 2:
            errors.append("Client name must be at least 2 characters")
        
        if not self.client_slug:
            errors.append("Client slug is required")
        elif not re.match(r'^[a-z0-9-]+$', self.client_slug):
            errors.append("Client slug can only contain lowercase letters, numbers, and hyphens")
        
        # Subscription plan validation
        if self.subscription_plan not in self.SUBSCRIPTION_PLANS:
            errors.append(f"Invalid subscription plan: {self.subscription_plan}")
        
        # Status validation
        valid_statuses = ['pending', 'active', 'suspended', 'cancelled']
        if self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        # Domain validation if provided
        if self.domain:
            domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$'
            if not re.match(domain_pattern, self.domain):
                errors.append("Invalid domain format")
        
        return errors
    
    def get_plan_limits(self) -> Dict[str, Any]:
        """Get limits for current subscription plan"""
        return self.SUBSCRIPTION_PLANS.get(self.subscription_plan, self.SUBSCRIPTION_PLANS['free'])
    
    def is_within_limits(self, limit_type: str, proposed_increase: int = 1) -> tuple[bool, str]:
        """
        Check if client is within subscription limits
        Returns (is_within_limits, error_message)
        """
        limits = self.get_plan_limits()
        current_usage = self.usage
        
        if limit_type == 'users':
            current = current_usage.get('current_users', 0)
            max_allowed = limits.get('max_users', 0)
            if current + proposed_increase > max_allowed:
                return False, f"User limit exceeded. Plan allows {max_allowed} users, you have {current}"
        
        elif limit_type == 'projects':
            current = current_usage.get('current_projects', 0)
            max_allowed = limits.get('max_projects', 0)
            if current + proposed_increase > max_allowed:
                return False, f"Project limit exceeded. Plan allows {max_allowed} projects, you have {current}"
        
        elif limit_type == 'tests':
            current = current_usage.get('tests_this_month', 0)
            max_allowed = limits.get('max_tests_per_month', 0)
            if current + proposed_increase > max_allowed:
                return False, f"Monthly test limit exceeded. Plan allows {max_allowed} tests, you have used {current}"
        
        elif limit_type == 'storage':
            current = current_usage.get('storage_used_mb', 0)
            max_allowed = limits.get('storage_limit_mb', 0)
            if current + proposed_increase > max_allowed:
                return False, f"Storage limit exceeded. Plan allows {max_allowed}MB, you have used {current}MB"
        
        return True, ""
    
    def has_feature(self, feature_name: str) -> bool:
        """Check if client has access to a specific feature"""
        plan_features = self.get_plan_limits().get('features', {})
        return plan_features.get(feature_name, False)
    
    def update_usage(self, usage_type: str, increment: int = 1):
        """Update usage statistics"""
        if usage_type == 'tests':
            self.usage['tests_this_month'] = self.usage.get('tests_this_month', 0) + increment
        elif usage_type == 'storage':
            self.usage['storage_used_mb'] = self.usage.get('storage_used_mb', 0) + increment
        
        self.usage['last_activity'] = datetime.utcnow()
    
    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        self.usage['tests_this_month'] = 0
        self.usage['monthly_reset_date'] = self._get_monthly_reset_date()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert client to dictionary for database storage"""
        return {
            'client_id': self.client_id,
            'client_name': self.client_name,
            'client_slug': self.client_slug,
            'domain': self.domain,
            'subscription_plan': self.subscription_plan,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'settings': self.settings,
            'billing': self.billing,
            'usage': self.usage
        }
    
    def save(self, db_connection: DatabaseConnection = None) -> bool:
        """Save client to database"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            # Validate before saving
            errors = self.validate()
            if errors:
                logger.error(f"Client validation failed: {', '.join(errors)}")
                return False
            
            now = datetime.utcnow()
            
            if self._id:
                # Update existing client
                self.updated_at = now
                result = db_connection.db.clients.update_one(
                    {'_id': self._id},
                    {'$set': self.to_dict()}
                )
                return result.modified_count > 0
            else:
                # Create new client
                if not self.client_id:
                    self.client_id = self.generate_client_id()
                if not self.client_slug:
                    self.client_slug = self.generate_client_slug(self.client_name)
                
                self.created_at = now
                self.updated_at = now
                
                result = db_connection.db.clients.insert_one(self.to_dict())
                self._id = result.inserted_id
                return True
                
        except Exception as e:
            logger.error(f"Error saving client: {e}")
            return False
    
    @classmethod
    def get_by_id(cls, client_id: str, db_connection: DatabaseConnection = None) -> Optional['Client']:
        """Get client by client_id"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            data = db_connection.db.clients.find_one({'client_id': client_id})
            return cls(data) if data else None
            
        except Exception as e:
            logger.error(f"Error getting client by ID {client_id}: {e}")
            return None
    
    @classmethod
    def get_by_slug(cls, client_slug: str, db_connection: DatabaseConnection = None) -> Optional['Client']:
        """Get client by client_slug"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            data = db_connection.db.clients.find_one({'client_slug': client_slug})
            return cls(data) if data else None
            
        except Exception as e:
            logger.error(f"Error getting client by slug {client_slug}: {e}")
            return None
    
    @classmethod
    def get_by_domain(cls, domain: str, db_connection: DatabaseConnection = None) -> Optional['Client']:
        """Get client by custom domain"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            data = db_connection.db.clients.find_one({'domain': domain})
            return cls(data) if data else None
            
        except Exception as e:
            logger.error(f"Error getting client by domain {domain}: {e}")
            return None
    
    @classmethod
    def list_all(cls, status: str = None, db_connection: DatabaseConnection = None) -> List['Client']:
        """List all clients, optionally filtered by status"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            query = {}
            if status:
                query['status'] = status
            
            clients = []
            for data in db_connection.db.clients.find(query).sort('created_at', -1):
                clients.append(cls(data))
            
            return clients
            
        except Exception as e:
            logger.error(f"Error listing clients: {e}")
            return []
    
    def delete(self, db_connection: DatabaseConnection = None) -> bool:
        """Delete client and all associated data"""
        try:
            if not db_connection:
                from autotest.utils.config import Config
                config = Config()
                db_connection = DatabaseConnection(config)
                db_connection.connect()
            
            if not self._id:
                return False
            
            # TODO: In production, this should cascade delete all tenant data
            # For now, just mark as deleted
            result = db_connection.db.clients.update_one(
                {'_id': self._id},
                {'$set': {'status': 'deleted', 'updated_at': datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting client: {e}")
            return False
    
    def __str__(self) -> str:
        return f"Client(id={self.client_id}, name={self.client_name}, plan={self.subscription_plan})"
    
    def __repr__(self) -> str:
        return self.__str__()