"""
Session Management System for Personality Assessment Application

This module implements Task 7 requirements:
- Workflow state management
- Automatic progress saving
- Session recovery after interruptions
- Pending task tracking
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib


class SessionManager:
    """
    Manages user sessions, auto-saves progress, and enables recovery.
    
    Features:
    - Automatic state persistence every 30 seconds
    - Session recovery after browser refresh/crash
    - Pending task tracking
    - Workflow state management
    """
    
    def __init__(self, session_dir: str = "sessions"):
        """
        Initialize session manager.
        
        Args:
            session_dir: Directory to store session files
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.current_session_id = None
        self.session_data = {}
        self.last_save_time = None
        self.auto_save_interval = 30  # seconds
        
    def create_session(self, user_id: str = "default") -> str:
        """
        Create a new session or resume existing one.
        
        Args:
            user_id: User identifier
            
        Returns:
            Session ID
        """
        # Generate session ID from user and timestamp
        session_id = self._generate_session_id(user_id)
        self.current_session_id = session_id
        
        # Try to load existing session
        if self._session_exists(session_id):
            self.load_session(session_id)
        else:
            # Initialize new session
            self.session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'workflow_state': {},
                'pending_tasks': [],
                'completed_tasks': [],
                'batch_progress': {},
                'upload_history': []
            }
            self.save_session()
        
        return session_id
    
    def save_session(self, force: bool = False) -> bool:
        """
        Save current session state to disk.
        
        Args:
            force: Force save even if auto-save interval hasn't elapsed
            
        Returns:
            True if saved, False if skipped
        """
        if not self.current_session_id:
            return False
        
        # Check if we should auto-save
        if not force and self.last_save_time:
            elapsed = (datetime.now() - self.last_save_time).total_seconds()
            if elapsed < self.auto_save_interval:
                return False
        
        # Update timestamp
        self.session_data['last_updated'] = datetime.now().isoformat()
        
        # Save to file
        session_file = self.session_dir / f"{self.current_session_id}.json"
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
            
            self.last_save_time = datetime.now()
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def load_session(self, session_id: str) -> bool:
        """
        Load session from disk.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if loaded successfully
        """
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return False
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                self.session_data = json.load(f)
            
            self.current_session_id = session_id
            return True
        except Exception as e:
            print(f"Error loading session: {e}")
            return False
    
    def update_workflow_state(self, state_key: str, state_value: Any):
        """
        Update workflow state.
        
        Args:
            state_key: State identifier
            state_value: State value
        """
        if 'workflow_state' not in self.session_data:
            self.session_data['workflow_state'] = {}
        
        self.session_data['workflow_state'][state_key] = state_value
        self.save_session()
    
    def get_workflow_state(self, state_key: str, default: Any = None) -> Any:
        """
        Get workflow state value.
        
        Args:
            state_key: State identifier
            default: Default value if not found
            
        Returns:
            State value or default
        """
        return self.session_data.get('workflow_state', {}).get(state_key, default)
    
    def add_pending_task(self, task: Dict[str, Any]):
        """
        Add a pending task to track.
        
        Args:
            task: Task dictionary with 'id', 'type', 'description', 'created_at'
        """
        if 'pending_tasks' not in self.session_data:
            self.session_data['pending_tasks'] = []
        
        task['created_at'] = datetime.now().isoformat()
        self.session_data['pending_tasks'].append(task)
        self.save_session()
    
    def complete_task(self, task_id: str):
        """
        Mark a task as completed.
        
        Args:
            task_id: Task identifier
        """
        if 'pending_tasks' not in self.session_data:
            return
        
        # Find and remove from pending
        for i, task in enumerate(self.session_data['pending_tasks']):
            if task.get('id') == task_id:
                task['completed_at'] = datetime.now().isoformat()
                
                # Move to completed
                if 'completed_tasks' not in self.session_data:
                    self.session_data['completed_tasks'] = []
                self.session_data['completed_tasks'].append(task)
                
                # Remove from pending
                self.session_data['pending_tasks'].pop(i)
                self.save_session()
                break
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all pending tasks.
        
        Returns:
            List of pending tasks
        """
        return self.session_data.get('pending_tasks', [])
    
    def update_batch_progress(self, batch_id: str, progress: Dict[str, Any]):
        """
        Update batch processing progress.
        
        Args:
            batch_id: Batch identifier
            progress: Progress dictionary with 'current', 'total', 'status'
        """
        if 'batch_progress' not in self.session_data:
            self.session_data['batch_progress'] = {}
        
        progress['last_updated'] = datetime.now().isoformat()
        self.session_data['batch_progress'][batch_id] = progress
        self.save_session()
    
    def get_batch_progress(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get batch processing progress.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Progress dictionary or None
        """
        return self.session_data.get('batch_progress', {}).get(batch_id)
    
    def add_upload_history(self, filename: str, file_hash: str, metadata: Dict[str, Any]):
        """
        Add file upload to history.
        
        Args:
            filename: Uploaded filename
            file_hash: File content hash
            metadata: Additional metadata
        """
        if 'upload_history' not in self.session_data:
            self.session_data['upload_history'] = []
        
        upload_record = {
            'filename': filename,
            'file_hash': file_hash,
            'uploaded_at': datetime.now().isoformat(),
            'metadata': metadata
        }
        
        self.session_data['upload_history'].append(upload_record)
        self.save_session()
    
    def check_recent_upload(self, file_hash: str, hours: int = 24) -> Optional[Dict[str, Any]]:
        """
        Check if file was recently uploaded.
        
        Args:
            file_hash: File content hash
            hours: Hours to look back
            
        Returns:
            Upload record if found, None otherwise
        """
        if 'upload_history' not in self.session_data:
            return None
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for upload in reversed(self.session_data['upload_history']):
            upload_time = datetime.fromisoformat(upload['uploaded_at'])
            if upload_time < cutoff_time:
                break
            
            if upload['file_hash'] == file_hash:
                return upload
        
        return None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get session summary statistics.
        
        Returns:
            Summary dictionary
        """
        if not self.session_data:
            return {}
        
        return {
            'session_id': self.session_data.get('session_id'),
            'created_at': self.session_data.get('created_at'),
            'last_updated': self.session_data.get('last_updated'),
            'pending_tasks_count': len(self.session_data.get('pending_tasks', [])),
            'completed_tasks_count': len(self.session_data.get('completed_tasks', [])),
            'active_batches': len(self.session_data.get('batch_progress', {})),
            'total_uploads': len(self.session_data.get('upload_history', []))
        }
    
    def cleanup_old_sessions(self, days: int = 7):
        """
        Remove session files older than specified days.
        
        Args:
            days: Number of days to keep
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                
                last_updated = datetime.fromisoformat(data.get('last_updated', data.get('created_at')))
                
                if last_updated < cutoff_time:
                    session_file.unlink()
            except Exception as e:
                print(f"Error cleaning up {session_file}: {e}")
    
    def _generate_session_id(self, user_id: str) -> str:
        """Generate session ID from user ID and date"""
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{user_id}_{date_str}"
    
    def _session_exists(self, session_id: str) -> bool:
        """Check if session file exists"""
        session_file = self.session_dir / f"{session_id}.json"
        return session_file.exists()
    
    def has_recoverable_state(self) -> bool:
        """
        Check if there's a recoverable state from previous session.
        
        Returns:
            True if recoverable state exists
        """
        # Check session data for pending tasks or incomplete batches
        if self.session_data:
            has_pending = len(self.session_data.get('pending_tasks', [])) > 0
            has_incomplete_batches = any(
                batch.get('status') != 'completed'
                for batch in self.session_data.get('batch_progress', {}).values()
            )
            
            if has_pending or has_incomplete_batches:
                return True
        
        # Check for actual checkpoint files in assessments directory
        assessments_dir = Path("assessments")
        if assessments_dir.exists():
            import glob
            checkpoint_files = glob.glob("assessments/checkpoint_*.csv")
            return len(checkpoint_files) > 0
        
        return False
    
    def get_recovery_info(self) -> Dict[str, Any]:
        """
        Get information about recoverable state.
        
        Returns:
            Recovery information dictionary
        """
        recovery_info = {
            'pending_tasks': self.get_pending_tasks(),
            'incomplete_batches': [],
            'completed_batches': [],
            'last_activity': self.session_data.get('last_updated') if self.session_data else None
        }
        
        # Check session data for tracked batches
        session_batches = []
        if self.session_data:
            for bid, progress in self.session_data.get('batch_progress', {}).items():
                if (progress.get('status') != 'completed' or 
                    self._has_pending_review_task(bid)):
                    session_batches.append({'batch_id': bid, **progress})
        
        # Scan for actual checkpoint files in assessments directory
        assessments_dir = Path("assessments")
        if assessments_dir.exists():
            import glob
            import pandas as pd
            
            # Find all checkpoint files
            checkpoint_files = glob.glob("assessments/checkpoint_*.csv")
            
            for checkpoint_file in checkpoint_files:
                try:
                    # Extract batch_id from filename
                    filename = os.path.basename(checkpoint_file)
                    batch_id = filename.replace('checkpoint_', '').replace('.csv', '')
                    
                    # Check if we already have this batch from session data
                    already_tracked = any(b['batch_id'] == batch_id for b in session_batches)
                    if already_tracked:
                        continue
                    
                    # Load checkpoint to get info
                    df = pd.read_csv(checkpoint_file)
                    total_rows = len(df)
                    
                    # Count completed assessments (rows with VALID assessment data)
                    completed_rows = 0
                    for _, row in df.iterrows():
                        has_valid_assessment = False
                        
                        # Check for assessment data
                        assessment_column = None
                        if 'assessment' in row and pd.notna(row['assessment']) and str(row['assessment']).strip():
                            assessment_column = 'assessment'
                        elif 'Assessment_Result' in row and pd.notna(row['Assessment_Result']) and str(row['Assessment_Result']).strip():
                            assessment_column = 'Assessment_Result'
                        
                        if assessment_column:
                            try:
                                # Validate that the assessment contains actual data, not dummy data
                                assessment_str = str(row[assessment_column]).strip()
                                
                                # Skip obviously dummy or empty data
                                if (assessment_str.lower() in ['nan', 'none', '', 'null'] or
                                    'dummy' in assessment_str.lower() or
                                    'placeholder' in assessment_str.lower()):
                                    continue
                                
                                # Try to parse as Python literal to validate structure
                                import ast
                                assessment_data = ast.literal_eval(assessment_str)
                                
                                # Validate that assessment has meaningful content
                                if isinstance(assessment_data, dict):
                                    assessments = assessment_data.get('assessments', [])
                                    if assessments and len(assessments) > 0:
                                        # Check if any assessment has actual quality/level data
                                        for assessment in assessments:
                                            if isinstance(assessment, dict):
                                                # Handle both formats
                                                if assessment.get('quality') and assessment.get('level'):
                                                    has_valid_assessment = True
                                                    break
                                                else:
                                                    # Check nested format
                                                    for key, value in assessment.items():
                                                        if isinstance(value, dict) and value.get('quality') and value.get('level'):
                                                            has_valid_assessment = True
                                                            break
                                                if has_valid_assessment:
                                                    break
                                
                            except Exception as e:
                                print(f"Error validating assessment data for row: {e}")
                                continue
                        
                        if has_valid_assessment:
                            completed_rows += 1
                    
                    # Only mark as completed if ALL rows have valid assessments
                    if completed_rows == total_rows and total_rows > 0:
                        status = 'completed'
                        # Add to completed batches for review
                        recovery_info['completed_batches'].append({
                            'batch_id': batch_id,
                            'current': completed_rows,
                            'total': total_rows,
                            'status': status,
                            'checkpoint_file': checkpoint_file
                        })
                    elif completed_rows > 0:
                        status = 'in_progress'
                        # Add to incomplete batches
                        recovery_info['incomplete_batches'].append({
                            'batch_id': batch_id,
                            'current': completed_rows,
                            'total': total_rows,
                            'status': status,
                            'checkpoint_file': checkpoint_file
                        })
                    else:
                        # No valid assessments found - remove this checkpoint file
                        print(f"Removing invalid checkpoint file with no valid assessments: {checkpoint_file}")
                        try:
                            os.remove(checkpoint_file)
                        except Exception as e:
                            print(f"Error removing invalid checkpoint file: {e}")
                        
                except Exception as e:
                    print(f"Error processing checkpoint file {checkpoint_file}: {e}")
                    # Remove corrupted checkpoint files
                    try:
                        os.remove(checkpoint_file)
                        print(f"Removed corrupted checkpoint file: {checkpoint_file}")
                    except:
                        pass
                    continue
        
        # Add session-tracked batches to appropriate categories
        for batch in session_batches:
            batch_status = batch.get('status')
            if batch_status == 'completed' or batch_status == 'ready_for_review':
                recovery_info['completed_batches'].append(batch)
            else:
                recovery_info['incomplete_batches'].append(batch)
        
        return recovery_info
    
    def _has_pending_review_task(self, batch_id: str) -> bool:
        """Check if there's a pending review task for the given batch ID"""
        pending_tasks = self.get_pending_tasks()
        return any(
            task.get('type') == 'batch_review' and task.get('batch_id') == batch_id
            for task in pending_tasks
        )
    
    def validate_checkpoint_file(self, checkpoint_file: str) -> Dict[str, Any]:
        """
        Validate checkpoint file integrity and return validation results.
        
        Args:
            checkpoint_file: Path to checkpoint file
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': False,
            'total_rows': 0,
            'valid_assessments': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            import pandas as pd
            import ast
            
            # Check if file exists
            if not os.path.exists(checkpoint_file):
                validation_result['errors'].append(f"Checkpoint file does not exist: {checkpoint_file}")
                return validation_result
            
            # Load and validate CSV structure
            try:
                df = pd.read_csv(checkpoint_file)
            except Exception as e:
                validation_result['errors'].append(f"Failed to read CSV file: {str(e)}")
                return validation_result
            
            validation_result['total_rows'] = len(df)
            
            if len(df) == 0:
                validation_result['errors'].append("Checkpoint file is empty")
                return validation_result
            
            # Check required columns
            required_columns = ['name', 'observations']
            missing_columns = [col for col in required_columns if col not in df.columns and col.title() not in df.columns]
            if missing_columns:
                validation_result['errors'].append(f"Missing required columns: {missing_columns}")
            
            # Validate each row
            valid_count = 0
            for idx, row in df.iterrows():
                row_errors = []
                
                # Check name
                name = row.get('name', row.get('Name', ''))
                if not name or pd.isna(name) or not str(name).strip():
                    row_errors.append(f"Row {idx+1}: Missing or empty name")
                
                # Check observations
                observations = row.get('observations', row.get('Observations', ''))
                if not observations or pd.isna(observations) or not str(observations).strip():
                    row_errors.append(f"Row {idx+1}: Missing or empty observations")
                
                # Check assessment data
                assessment_column = None
                if 'assessment' in row and pd.notna(row['assessment']):
                    assessment_column = 'assessment'
                elif 'Assessment_Result' in row and pd.notna(row['Assessment_Result']):
                    assessment_column = 'Assessment_Result'
                
                if assessment_column:
                    try:
                        assessment_str = str(row[assessment_column]).strip()
                        
                        # Skip obviously invalid data
                        if (assessment_str.lower() in ['nan', 'none', '', 'null'] or
                            'dummy' in assessment_str.lower() or
                            'placeholder' in assessment_str.lower()):
                            row_errors.append(f"Row {idx+1}: Invalid assessment data (dummy/placeholder)")
                        else:
                            # Try to parse assessment data
                            try:
                                assessment_data = ast.literal_eval(assessment_str)
                                if isinstance(assessment_data, dict):
                                    assessments = assessment_data.get('assessments', [])
                                    if not assessments or len(assessments) == 0:
                                        row_errors.append(f"Row {idx+1}: Assessment data contains no assessments")
                                    else:
                                        # Validate assessment structure
                                        has_valid_assessment = False
                                        for assessment in assessments:
                                            if isinstance(assessment, dict):
                                                if assessment.get('quality') and assessment.get('level'):
                                                    has_valid_assessment = True
                                                    break
                                                else:
                                                    # Check nested format
                                                    for key, value in assessment.items():
                                                        if isinstance(value, dict) and value.get('quality') and value.get('level'):
                                                            has_valid_assessment = True
                                                            break
                                                if has_valid_assessment:
                                                    break
                                        
                                        if not has_valid_assessment:
                                            row_errors.append(f"Row {idx+1}: Assessment data has no valid quality/level pairs")
                                else:
                                    row_errors.append(f"Row {idx+1}: Assessment data is not a dictionary")
                            except Exception as e:
                                row_errors.append(f"Row {idx+1}: Failed to parse assessment data - {str(e)}")
                    except Exception as e:
                        row_errors.append(f"Row {idx+1}: Error processing assessment column - {str(e)}")
                else:
                    row_errors.append(f"Row {idx+1}: No assessment data found")
                
                if not row_errors:
                    valid_count += 1
                else:
                    validation_result['warnings'].extend(row_errors)
            
            validation_result['valid_assessments'] = valid_count
            validation_result['is_valid'] = valid_count > 0 and len(validation_result['errors']) == 0
            
            # Add summary
            if validation_result['is_valid']:
                if valid_count == validation_result['total_rows']:
                    validation_result['summary'] = f"All {valid_count} rows are valid"
                else:
                    validation_result['summary'] = f"{valid_count}/{validation_result['total_rows']} rows are valid"
            else:
                validation_result['summary'] = f"File is invalid: {len(validation_result['errors'])} errors found"
            
        except Exception as e:
            validation_result['errors'].append(f"Unexpected error during validation: {str(e)}")
        
        return validation_result
