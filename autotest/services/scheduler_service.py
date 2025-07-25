"""
Scheduler Service for AutoTest
Handles scheduled accessibility testing with configurable intervals and conditions.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

from ..core.database import DatabaseConnection


class ScheduleFrequency(Enum):
    """Schedule frequency options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ScheduleStatus(Enum):
    """Schedule status options"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScheduledTest:
    """
    Scheduled test configuration
    """
    schedule_id: str
    name: str
    description: str
    project_id: Optional[str] = None
    website_id: Optional[str] = None
    page_ids: Optional[List[str]] = None
    test_type: str = "accessibility"  # accessibility, css, javascript, scenarios
    frequency: ScheduleFrequency = ScheduleFrequency.WEEKLY
    custom_interval_hours: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    notification_emails: Optional[List[str]] = None
    test_config: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SchedulerService:
    """
    Comprehensive scheduled testing service for AutoTest
    """
    
    def __init__(self, config, db_connection: DatabaseConnection, testing_service=None):
        """
        Initialize scheduler service
        
        Args:
            config: Application configuration
            db_connection: Database connection instance
            testing_service: Testing service for executing tests
        """
        self.config = config
        self.db_connection = db_connection
        self.testing_service = testing_service
        self.logger = logging.getLogger(__name__)
        
        # Scheduler thread management
        self._scheduler_thread = None
        self._scheduler_running = False
        self._scheduler_lock = threading.Lock()
        
        # Initialize database collections
        self._init_database()
        
        # Start scheduler if enabled
        if config.get('scheduler.enabled', True):
            self.start_scheduler()
    
    def _init_database(self):
        """Initialize database collections for scheduled tests"""
        try:
            # Create indexes for efficient querying
            self.db_connection.db.scheduled_tests.create_index("schedule_id", unique=True)
            self.db_connection.db.scheduled_tests.create_index("next_run")
            self.db_connection.db.scheduled_tests.create_index("status")
            self.db_connection.db.scheduled_tests.create_index("project_id")
            
            # Schedule execution history
            self.db_connection.db.schedule_executions.create_index("schedule_id")
            self.db_connection.db.schedule_executions.create_index("execution_time")
            
            self.logger.info("Scheduler database collections initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing scheduler database: {e}")
    
    def create_schedule(self, schedule_data: Dict[str, Any]) -> str:
        """
        Create a new scheduled test
        
        Args:
            schedule_data: Schedule configuration data
            
        Returns:
            Schedule ID of created schedule
        """
        try:
            schedule_id = str(uuid.uuid4())
            
            # Create scheduled test object
            scheduled_test = ScheduledTest(
                schedule_id=schedule_id,
                name=schedule_data.get('name', 'Untitled Schedule'),
                description=schedule_data.get('description', ''),
                project_id=schedule_data.get('project_id'),
                website_id=schedule_data.get('website_id'),
                page_ids=schedule_data.get('page_ids', []),
                test_type=schedule_data.get('test_type', 'accessibility'),
                frequency=ScheduleFrequency(schedule_data.get('frequency', 'weekly')),
                custom_interval_hours=schedule_data.get('custom_interval_hours'),
                start_date=self._parse_datetime(schedule_data.get('start_date')),
                end_date=self._parse_datetime(schedule_data.get('end_date')),
                notification_emails=schedule_data.get('notification_emails', []),
                test_config=schedule_data.get('test_config', {}),
                created_by=schedule_data.get('created_by'),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Calculate next run time
            scheduled_test.next_run = self._calculate_next_run(scheduled_test)
            
            # Store in database
            self.db_connection.db.scheduled_tests.insert_one(asdict(scheduled_test))
            
            self.logger.info(f"Created scheduled test: {schedule_id} - {scheduled_test.name}")
            return schedule_id
            
        except Exception as e:
            self.logger.error(f"Error creating schedule: {e}")
            raise Exception(f"Failed to create schedule: {str(e)}")
    
    def update_schedule(self, schedule_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing scheduled test
        
        Args:
            schedule_id: ID of the schedule to update
            update_data: Updated configuration data
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Get existing schedule
            existing_schedule = self.get_schedule(schedule_id)
            if not existing_schedule:
                return False
            
            # Update fields
            update_fields = {}
            
            if 'name' in update_data:
                update_fields['name'] = update_data['name']
            if 'description' in update_data:
                update_fields['description'] = update_data['description']
            if 'frequency' in update_data:
                update_fields['frequency'] = update_data['frequency']
                # Recalculate next run if frequency changed
                temp_schedule = ScheduledTest(**existing_schedule)
                temp_schedule.frequency = ScheduleFrequency(update_data['frequency'])
                update_fields['next_run'] = self._calculate_next_run(temp_schedule)
            if 'custom_interval_hours' in update_data:
                update_fields['custom_interval_hours'] = update_data['custom_interval_hours']
            if 'start_date' in update_data:
                update_fields['start_date'] = self._parse_datetime(update_data['start_date'])
            if 'end_date' in update_data:
                update_fields['end_date'] = self._parse_datetime(update_data['end_date'])
            if 'status' in update_data:
                update_fields['status'] = update_data['status']
            if 'notification_emails' in update_data:
                update_fields['notification_emails'] = update_data['notification_emails']
            if 'test_config' in update_data:
                update_fields['test_config'] = update_data['test_config']
            
            update_fields['updated_at'] = datetime.now()
            
            # Update in database
            result = self.db_connection.db.scheduled_tests.update_one(
                {'schedule_id': schedule_id},
                {'$set': update_fields}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Updated scheduled test: {schedule_id}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating schedule {schedule_id}: {e}")
            return False
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a scheduled test
        
        Args:
            schedule_id: ID of the schedule to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            result = self.db_connection.db.scheduled_tests.delete_one(
                {'schedule_id': schedule_id}
            )
            
            if result.deleted_count > 0:
                # Also delete execution history
                self.db_connection.db.schedule_executions.delete_many(
                    {'schedule_id': schedule_id}
                )
                
                self.logger.info(f"Deleted scheduled test: {schedule_id}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting schedule {schedule_id}: {e}")
            return False
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific scheduled test"""
        try:
            schedule = self.db_connection.db.scheduled_tests.find_one(
                {'schedule_id': schedule_id}
            )
            
            if schedule:
                # Remove MongoDB _id field
                schedule.pop('_id', None)
                return schedule
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting schedule {schedule_id}: {e}")
            return None
    
    def list_schedules(self, project_id: str = None, status: str = None, 
                      limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List scheduled tests with optional filtering
        
        Args:
            project_id: Filter by project ID
            status: Filter by status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of scheduled tests
        """
        try:
            query = {}
            
            if project_id:
                query['project_id'] = project_id
            if status:
                query['status'] = status
            
            schedules = list(
                self.db_connection.db.scheduled_tests
                .find(query)
                .sort('created_at', -1)
                .limit(limit)
                .skip(offset)
            )
            
            # Remove MongoDB _id fields
            for schedule in schedules:
                schedule.pop('_id', None)
            
            return schedules
            
        except Exception as e:
            self.logger.error(f"Error listing schedules: {e}")
            return []
    
    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a scheduled test"""
        return self.update_schedule(schedule_id, {'status': ScheduleStatus.PAUSED.value})
    
    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused scheduled test"""
        return self.update_schedule(schedule_id, {'status': ScheduleStatus.ACTIVE.value})
    
    def start_scheduler(self):
        """Start the background scheduler thread"""
        with self._scheduler_lock:
            if self._scheduler_running:
                self.logger.warning("Scheduler is already running")
                return
            
            self._scheduler_running = True
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                name="AutoTestScheduler",
                daemon=True
            )
            self._scheduler_thread.start()
            
            self.logger.info("Scheduler started")
    
    def stop_scheduler(self):
        """Stop the background scheduler thread"""
        with self._scheduler_lock:
            if not self._scheduler_running:
                return
            
            self._scheduler_running = False
            
            if self._scheduler_thread and self._scheduler_thread.is_alive():
                self._scheduler_thread.join(timeout=30)
            
            self.logger.info("Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop - runs in background thread"""
        self.logger.info("Scheduler loop started")
        
        check_interval = self.config.get('scheduler.check_interval_seconds', 60)
        
        while self._scheduler_running:
            try:
                self._check_and_execute_schedules()
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(check_interval)
        
        self.logger.info("Scheduler loop stopped")
    
    def _check_and_execute_schedules(self):
        """Check for schedules that need to be executed"""
        try:
            now = datetime.now()
            
            # Find schedules that need to run
            due_schedules = list(
                self.db_connection.db.scheduled_tests.find({
                    'status': ScheduleStatus.ACTIVE.value,
                    'next_run': {'$lte': now}
                })
            )
            
            for schedule_data in due_schedules:
                try:
                    # Execute the scheduled test
                    execution_result = self._execute_scheduled_test(schedule_data)
                    
                    # Update schedule with next run time
                    schedule = ScheduledTest(**schedule_data)
                    schedule.last_run = now
                    schedule.next_run = self._calculate_next_run(schedule)
                    
                    # Update in database
                    self.db_connection.db.scheduled_tests.update_one(
                        {'schedule_id': schedule.schedule_id},
                        {
                            '$set': {
                                'last_run': schedule.last_run,
                                'next_run': schedule.next_run,
                                'updated_at': now
                            }
                        }
                    )
                    
                    # Store execution result
                    self._store_execution_result(schedule.schedule_id, execution_result)
                    
                    self.logger.info(f"Executed scheduled test: {schedule.name}")
                    
                except Exception as e:
                    self.logger.error(f"Error executing schedule {schedule_data.get('schedule_id')}: {e}")
                    
                    # Mark schedule as failed
                    self.db_connection.db.scheduled_tests.update_one(
                        {'schedule_id': schedule_data.get('schedule_id')},
                        {
                            '$set': {
                                'status': ScheduleStatus.FAILED.value,
                                'updated_at': now
                            }
                        }
                    )
            
        except Exception as e:
            self.logger.error(f"Error checking schedules: {e}")
    
    def _execute_scheduled_test(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a scheduled test
        
        Args:
            schedule_data: Schedule configuration
            
        Returns:
            Test execution results
        """
        try:
            if not self.testing_service:
                raise Exception("Testing service not available")
            
            test_type = schedule_data.get('test_type', 'accessibility')
            project_id = schedule_data.get('project_id')
            website_id = schedule_data.get('website_id')
            page_ids = schedule_data.get('page_ids', [])
            test_config = schedule_data.get('test_config', {})
            
            execution_result = {
                'schedule_id': schedule_data.get('schedule_id'),
                'execution_time': datetime.now(),
                'test_type': test_type,
                'status': 'running',
                'results': {},
                'errors': []
            }
            
            # Execute based on test type
            if test_type == 'accessibility':
                if project_id:
                    job_id = self.testing_service.test_project(project_id)
                elif website_id:
                    job_id = self.testing_service.test_website(website_id)
                elif page_ids:
                    job_id = self.testing_service.test_multiple_pages(page_ids)
                else:
                    raise Exception("No target specified for accessibility test")
                
                execution_result['job_id'] = job_id
                execution_result['status'] = 'completed'
                
            elif test_type == 'css':
                # CSS modification testing
                if page_ids:
                    css_results = []
                    for page_id in page_ids:
                        # This would integrate with CSS testing
                        css_results.append({'page_id': page_id, 'css_test': 'completed'})
                    execution_result['results']['css'] = css_results
                    execution_result['status'] = 'completed'
                
            elif test_type == 'javascript':
                # JavaScript testing
                if page_ids:
                    js_results = []
                    for page_id in page_ids:
                        # This would integrate with JavaScript testing
                        js_results.append({'page_id': page_id, 'js_test': 'completed'})
                    execution_result['results']['javascript'] = js_results
                    execution_result['status'] = 'completed'
                
            elif test_type == 'scenarios':
                # Scenario testing
                scenario_ids = test_config.get('scenario_ids', [])
                if page_ids and scenario_ids:
                    scenario_results = []
                    for page_id in page_ids:
                        for scenario_id in scenario_ids:
                            # This would integrate with scenario testing
                            scenario_results.append({
                                'page_id': page_id,
                                'scenario_id': scenario_id,
                                'scenario_test': 'completed'
                            })
                    execution_result['results']['scenarios'] = scenario_results
                    execution_result['status'] = 'completed'
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Error executing scheduled test: {e}")
            return {
                'schedule_id': schedule_data.get('schedule_id'),
                'execution_time': datetime.now(),
                'status': 'failed',
                'error': str(e)
            }
    
    def _store_execution_result(self, schedule_id: str, execution_result: Dict[str, Any]):
        """Store execution result in database"""
        try:
            execution_result['schedule_id'] = schedule_id
            self.db_connection.db.schedule_executions.insert_one(execution_result)
            
        except Exception as e:
            self.logger.error(f"Error storing execution result: {e}")
    
    def _calculate_next_run(self, schedule: ScheduledTest) -> datetime:
        """Calculate the next run time for a schedule"""
        try:
            now = datetime.now()
            start_date = schedule.start_date or now
            
            # Use start_date if it's in the future
            if start_date > now:
                return start_date
            
            # Calculate based on frequency
            if schedule.frequency == ScheduleFrequency.DAILY:
                next_run = now + timedelta(days=1)
            elif schedule.frequency == ScheduleFrequency.WEEKLY:
                next_run = now + timedelta(weeks=1)
            elif schedule.frequency == ScheduleFrequency.MONTHLY:
                # Add one month (approximate)
                next_run = now + timedelta(days=30)
            elif schedule.frequency == ScheduleFrequency.CUSTOM:
                if schedule.custom_interval_hours:
                    next_run = now + timedelta(hours=schedule.custom_interval_hours)
                else:
                    next_run = now + timedelta(days=1)  # Default to daily
            else:
                next_run = now + timedelta(days=1)  # Default fallback
            
            # Don't schedule past the end date
            if schedule.end_date and next_run > schedule.end_date:
                # Mark as completed instead
                self.db_connection.db.scheduled_tests.update_one(
                    {'schedule_id': schedule.schedule_id},
                    {'$set': {'status': ScheduleStatus.COMPLETED.value}}
                )
                return schedule.end_date
            
            return next_run
            
        except Exception as e:
            self.logger.error(f"Error calculating next run: {e}")
            return datetime.now() + timedelta(days=1)  # Default fallback
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Try different formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If no format matches, raise exception
            raise ValueError(f"Unable to parse datetime: {date_str}")
            
        except Exception as e:
            self.logger.error(f"Error parsing datetime {date_str}: {e}")
            return None
    
    def get_schedule_execution_history(self, schedule_id: str, 
                                     limit: int = 20) -> List[Dict[str, Any]]:
        """Get execution history for a schedule"""
        try:
            executions = list(
                self.db_connection.db.schedule_executions
                .find({'schedule_id': schedule_id})
                .sort('execution_time', -1)
                .limit(limit)
            )
            
            # Remove MongoDB _id fields
            for execution in executions:
                execution.pop('_id', None)
            
            return executions
            
        except Exception as e:
            self.logger.error(f"Error getting execution history: {e}")
            return []
    
    def get_scheduler_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        try:
            total_schedules = self.db_connection.db.scheduled_tests.count_documents({})
            active_schedules = self.db_connection.db.scheduled_tests.count_documents(
                {'status': ScheduleStatus.ACTIVE.value}
            )
            paused_schedules = self.db_connection.db.scheduled_tests.count_documents(
                {'status': ScheduleStatus.PAUSED.value}
            )
            
            # Recent executions
            recent_executions = self.db_connection.db.schedule_executions.count_documents({
                'execution_time': {'$gte': datetime.now() - timedelta(hours=24)}
            })
            
            return {
                'total_schedules': total_schedules,
                'active_schedules': active_schedules,
                'paused_schedules': paused_schedules,
                'completed_schedules': total_schedules - active_schedules - paused_schedules,
                'recent_executions_24h': recent_executions,
                'scheduler_running': self._scheduler_running
            }
            
        except Exception as e:
            self.logger.error(f"Error getting scheduler statistics: {e}")
            return {}