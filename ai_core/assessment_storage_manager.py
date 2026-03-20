import pandas as pd
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import streamlit as st
from .data_consolidator import DataConsolidator, Observation, Assessment, ConsolidatedProfile
import uuid
import re
import logging
import hashlib
from pathlib import Path
import time

def format_date_column(date_str: str) -> str:
    """
    Convert a date string (YYYY-MM-DD) to Excel-safe column format (Session_DDMmmYYYY).
    Example: '2025-12-07' -> 'Session_07Dec2025'
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return f"Session_{date_obj.strftime('%d%b%Y')}"
    except ValueError:
        # If parsing fails, return a safe default format
        return f"Session_{date_str.replace('-', '_')}"

def normalize_name(name: str) -> str:
    """Normalize student name by stripping whitespace and converting to lowercase for matching."""
    return ' '.join(name.strip().lower().split())

class AssessmentStorageManager:
    """
    Enhanced storage manager for assessment results with comprehensive metadata tracking.
    
    Features:
    - Automatic timestamping for all observations with monotonic validation
    - Detailed activity logging and audit trails
    - Backup and versioning system for data protection
    - Observation count and date tracking
    - Data consolidation capabilities
    
    Student names are in the first column, followed by date-based columns
    containing observations and assessments for each date.
    """
    
    def __init__(self, storage_file: str = "assessments/student_assessments.csv"):
        self.storage_file = storage_file
        self.data_consolidator = DataConsolidator()
        self.ensure_storage_directory()
        
        # Initialize metadata tracking
        self.metadata_file = self._get_metadata_file_path()
        self.audit_log_file = self._get_audit_log_path()
        self.backup_dir = self._get_backup_directory()
        
        # Initialize logging
        self._setup_logging()
        
        # Load or initialize metadata
        self.metadata = self._load_metadata()
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Track last operation timestamp for monotonicity
        self.last_operation_timestamp = self._get_last_operation_timestamp()
    
    def _get_metadata_file_path(self) -> str:
        """Get path for metadata file"""
        base_dir = os.path.dirname(self.storage_file) or "assessments"
        return os.path.join(base_dir, "metadata.json")
    
    def _get_audit_log_path(self) -> str:
        """Get path for audit log file"""
        base_dir = os.path.dirname(self.storage_file) or "assessments"
        return os.path.join(base_dir, "audit_log.json")
    
    def _get_backup_directory(self) -> str:
        """Get backup directory path"""
        base_dir = os.path.dirname(self.storage_file) or "assessments"
        return os.path.join(base_dir, "backups")
    
    def _setup_logging(self):
        """Setup logging for audit trail"""
        # Create logger for this storage manager
        self.logger = logging.getLogger(f"storage_manager_{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            # Create file handler for audit log
            handler = logging.FileHandler(self.audit_log_file)
            handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            self.logger.addHandler(handler)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file or create default with error handling"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                self.logger.warning(f"Corrupted metadata file, creating new: {e}")
            except PermissionError:
                self.logger.warning(f"Permission denied reading metadata file: {self.metadata_file}")
            except IOError as e:
                self.logger.warning(f"I/O error reading metadata: {e}")
            except OSError as e:
                self.logger.warning(f"OS error reading metadata: {e}")
        
        # Default metadata structure
        return {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'version': '1.0.0',
            'student_counts': {},
            'observation_counts': {},
            'last_backup': None,
            'total_observations': 0,
            'total_students': 0,
            'last_operation_timestamp': None
        }
    
    def _save_metadata(self):
        """Save metadata to file with comprehensive error handling"""
        try:
            self.metadata['last_updated'] = datetime.now().isoformat()
            
            # Ensure directory exists
            metadata_dir = os.path.dirname(self.metadata_file)
            if metadata_dir:
                os.makedirs(metadata_dir, exist_ok=True)
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except PermissionError:
            self.logger.error(f"Permission denied saving metadata to: {self.metadata_file}")
        except IOError as e:
            self.logger.error(f"I/O error saving metadata: {e}")
        except TypeError as e:
            self.logger.error(f"Data serialization error saving metadata: {e}")
        except OSError as e:
            self.logger.error(f"OS error saving metadata: {e}")
    
    def _get_last_operation_timestamp(self) -> Optional[datetime]:
        """Get timestamp of last operation for monotonicity checking"""
        if self.metadata.get('last_operation_timestamp'):
            try:
                return datetime.fromisoformat(self.metadata['last_operation_timestamp'])
            except ValueError:
                return None
        return None
    
    def _validate_timestamp_monotonicity(self, new_timestamp: datetime) -> bool:
        """
        Validate that new timestamp maintains monotonicity.
        Returns True if timestamp is valid (greater than or equal to last timestamp).
        """
        if self.last_operation_timestamp is None:
            return True
        
        # Allow equal timestamps (same millisecond) but not earlier ones
        return new_timestamp >= self.last_operation_timestamp
    
    def _update_operation_timestamp(self, timestamp: datetime):
        """Update the last operation timestamp"""
        self.last_operation_timestamp = timestamp
        self.metadata['last_operation_timestamp'] = timestamp.isoformat()
        self._save_metadata()
    
    def _log_activity(self, action: str, details: Dict[str, Any]):
        """Log activity for audit trail"""
        timestamp = datetime.now()
        
        # Validate timestamp monotonicity
        if not self._validate_timestamp_monotonicity(timestamp):
            # If timestamp would violate monotonicity, adjust it slightly
            if self.last_operation_timestamp:
                timestamp = self.last_operation_timestamp + timedelta(microseconds=1)
        
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'action': action,
            'details': convert_numpy_types(details)
        }
        
        # Log to file
        self.logger.info(json.dumps(log_entry))
        
        # Update operation timestamp
        self._update_operation_timestamp(timestamp)
    
    def _create_backup(self) -> Optional[str]:
        """
        Create backup of current data.
        Returns backup file path if successful, None otherwise.
        """
        if not os.path.exists(self.storage_file):
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.csv"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy main data file
            shutil.copy2(self.storage_file, backup_path)
            
            # Also backup metadata
            metadata_backup = os.path.join(self.backup_dir, f"metadata_{timestamp}.json")
            if os.path.exists(self.metadata_file):
                shutil.copy2(self.metadata_file, metadata_backup)
            
            # Update metadata
            self.metadata['last_backup'] = timestamp
            self._save_metadata()
            
            self._log_activity("backup_created", {
                "backup_path": backup_path,
                "metadata_backup": metadata_backup,
                "timestamp": timestamp
            })
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Keep only the most recent backups"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("backup_") and file.endswith(".csv"):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getctime(file_path)))
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups
            for file_path, _ in backup_files[keep_count:]:
                os.remove(file_path)
                # Also remove corresponding metadata backup
                metadata_file = file_path.replace("backup_", "metadata_").replace(".csv", ".json")
                if os.path.exists(metadata_file):
                    os.remove(metadata_file)
            
            if len(backup_files) > keep_count:
                self._log_activity("backup_cleanup", {
                    "removed_count": len(backup_files) - keep_count,
                    "kept_count": keep_count
                })
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
    
    def _update_student_metadata(self, student_name: str, action: str):
        """Update metadata for student operations"""
        normalized_name = normalize_name(student_name)
        
        if normalized_name not in self.metadata['student_counts']:
            self.metadata['student_counts'][normalized_name] = {
                'original_name': student_name,
                'observation_count': 0,
                'first_observed': datetime.now().isoformat(),
                'last_observed': datetime.now().isoformat()
            }
            self.metadata['total_students'] += 1
        
        student_meta = self.metadata['student_counts'][normalized_name]
        
        if action == 'add_observation':
            student_meta['observation_count'] += 1
            student_meta['last_observed'] = datetime.now().isoformat()
            self.metadata['total_observations'] += 1
        
        self._save_metadata()
    
    def ensure_storage_directory(self):
        """Ensure the storage directory exists"""
        directory = os.path.dirname(self.storage_file)
        if directory:  # Only create directory if there is one
            os.makedirs(directory, exist_ok=True)
    
    def load_existing_data(self) -> pd.DataFrame:
        """Load existing assessment data from CSV file with comprehensive error handling"""
        if not os.path.exists(self.storage_file):
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(self.storage_file, index_col=0, encoding='utf-8')
            return df
        except pd.errors.EmptyDataError:
            self.logger.warning(f"Storage file is empty: {self.storage_file}")
            return pd.DataFrame()
        except pd.errors.ParserError as e:
            self.logger.error(f"Error parsing CSV file: {e}")
            st.error(f"❌ Corrupted data file. Please check: {self.storage_file}")
            return pd.DataFrame()
        except UnicodeDecodeError:
            # Try alternative encodings
            try:
                df = pd.read_csv(self.storage_file, index_col=0, encoding='latin-1')
                return df
            except Exception as e:
                self.logger.error(f"Encoding error loading data: {e}")
                st.error(f"❌ File encoding error. Please ensure UTF-8 encoding.")
                return pd.DataFrame()
        except PermissionError:
            self.logger.error(f"Permission denied accessing: {self.storage_file}")
            st.error(f"❌ Permission denied accessing data file")
            return pd.DataFrame()
        except IOError as e:
            self.logger.error(f"I/O error loading data: {e}")
            st.error(f"❌ Error reading data file: {str(e)}")
            return pd.DataFrame()
        except (OSError, ValueError) as e:
            self.logger.error(f"Error loading existing data: {e}")
            st.warning(f"⚠️ Could not load existing data: {str(e)}")
            return pd.DataFrame()
    
    def save_data(self, df: pd.DataFrame):
        """Save DataFrame to CSV file using atomic write pattern with backup and logging"""
        try:
            # Validate DataFrame
            if df is None:
                raise ValueError("Cannot save None DataFrame")
            
            # Create backup before saving
            backup_path = self._create_backup()
            
            # Ensure directory exists
            self.ensure_storage_directory()
            
            # Write to temporary file first
            storage_dir = os.path.dirname(self.storage_file) or '.'
            fd, temp_path = tempfile.mkstemp(suffix='.csv', dir=storage_dir)
            
            try:
                os.close(fd)  # Close the file descriptor
                df.to_csv(temp_path, index=True, encoding='utf-8')
                # Atomic rename (on same filesystem)
                shutil.move(temp_path, self.storage_file)
                
                # Log successful save
                self._log_activity("data_saved", {
                    "storage_file": self.storage_file,
                    "backup_created": backup_path is not None,
                    "backup_path": backup_path,
                    "row_count": len(df),
                    "column_count": len(df.columns)
                })
                
                # Cleanup old backups
                self._cleanup_old_backups()
                
            except PermissionError:
                # Clean up temp file on failure
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                raise PermissionError(f"Permission denied writing to: {self.storage_file}")
            except IOError as e:
                # Clean up temp file on failure
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                raise IOError(f"I/O error saving data: {e}")
            except OSError as e:
                # Clean up temp file on failure
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                raise OSError(f"OS error saving data: {e}")
                
        except ValueError as e:
            self._log_activity("save_failed", {
                "error": str(e),
                "error_type": "ValueError",
                "storage_file": self.storage_file
            })
            st.error(f"❌ Invalid data: {str(e)}")
        except PermissionError as e:
            self._log_activity("save_failed", {
                "error": str(e),
                "error_type": "PermissionError",
                "storage_file": self.storage_file
            })
            st.error(f"❌ Permission denied saving data")
            st.info("💡 Please check file permissions and ensure the file is not open in another program")
        except IOError as e:
            self._log_activity("save_failed", {
                "error": str(e),
                "error_type": "IOError",
                "storage_file": self.storage_file
            })
            st.error(f"❌ Error saving data: {str(e)}")
        except OSError as e:
            self._log_activity("save_failed", {
                "error": str(e),
                "error_type": "OSError",
                "storage_file": self.storage_file
            })
            st.error(f"❌ System error saving data: {str(e)}")
    
    def get_date_columns(self, df: pd.DataFrame) -> List[str]:
        """Get all date-based columns from the DataFrame"""
        date_columns = []
        for col in df.columns:
            # Support both old 'Date_' format and new 'Session_' format
            if (col.startswith('Date_') or col.startswith('Session_')) and col != 'Student_Name':
                date_columns.append(col)
        return sorted(date_columns)
    
    def format_assessment_data(self, assessment_result: Dict) -> str:
        """Format assessment result into a readable string"""
        if not assessment_result or 'assessments' not in assessment_result:
            return "No assessment data"
        
        formatted_data = []
        for assessment in assessment_result['assessments']:
            quality = assessment.get('quality', 'Unknown')
            level = assessment.get('level', 'Unknown')
            reasoning = assessment.get('reasoning', '')
            
            formatted_data.append(f"{quality}: {level}")
            if reasoning:
                formatted_data.append(f"  ({reasoning})")
        
        return "\n".join(formatted_data)
    
    def check_duplicate_assessments(self, student_name: str, assessment_date: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check if student already has assessment on the given date
        Returns (is_duplicate, existing_data)
        """
        df = self.load_existing_data()
        
        if df.empty or 'Student_Name' not in df.columns:
            return False, None
        
        # Find student row with normalized name matching
        df['_normalized_name'] = df['Student_Name'].apply(lambda x: normalize_name(str(x)) if pd.notna(x) else '')
        normalized_input = normalize_name(student_name)
        student_row = df[df['_normalized_name'] == normalized_input]
        df.drop('_normalized_name', axis=1, inplace=True)
        if student_row.empty:
            return False, None
        
        # Check for existing data on this date
        date_col = format_date_column(assessment_date)
        # Also check legacy Date_ format for backward compatibility
        legacy_date_col = f"Date_{assessment_date}"
        if date_col in df.columns or legacy_date_col in df.columns:
            actual_col = date_col if date_col in df.columns else legacy_date_col
            # Safely access DataFrame value with null check
            if not student_row.empty and actual_col in student_row.columns:
                existing_data = student_row[actual_col].iloc[0]
                if pd.notna(existing_data) and str(existing_data).strip():
                    return True, {
                        'date': assessment_date,
                        'data': existing_data,
                        'column': actual_col
                    }
        
        return False, None
    
    def _check_duplicate_legacy(self, student_row, assessment_date, df):
        """Legacy duplicate check - kept for reference"""
        date_col = format_date_column(assessment_date)
        if date_col in df.columns:
            pass  # Handled above
        return False, None
    
    def handle_duplicate_assessment(self, student_name: str, assessment_date: str, 
                                  new_observations: str, new_assessment: Dict) -> str:
        """
        Handle duplicate assessment scenario with user choice
        Returns the action taken: 'replace', 'append', or 'cancel'
        """
        is_duplicate, existing_data = self.check_duplicate_assessments(student_name, assessment_date)
        
        if not is_duplicate:
            return 'new'
        
        # Show duplicate warning and get user choice
        st.warning(f"⚠️ Student '{student_name}' already has assessment data for {assessment_date}")
        st.write("**Existing data:**")
        st.text(str(existing_data['data']))
        
        st.write("**New data:**")
        st.text(f"Observations: {new_observations}")
        st.text(f"Assessment: {self.format_assessment_data(new_assessment)}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Replace", key=f"replace_{student_name}_{assessment_date}"):
                return 'replace'
        
        with col2:
            if st.button("➕ Append", key=f"append_{student_name}_{assessment_date}"):
                return 'append'
        
        with col3:
            if st.button("❌ Cancel", key=f"cancel_{student_name}_{assessment_date}"):
                return 'cancel'
        
        return 'pending'
    
    def add_assessment(self, student_name: str, observations: str, assessment_result: Dict, 
                      assessment_date: Optional[str] = None) -> bool:
        """
        Add a new assessment to the storage system with automatic timestamping and metadata tracking.
        Returns True if successfully added, False otherwise
        """
        if assessment_date is None:
            assessment_date = datetime.now().strftime("%Y-%m-%d")
        
        # Log the operation start
        operation_timestamp = datetime.now()
        self._log_activity("add_assessment_start", {
            "student_name": student_name,
            "assessment_date": assessment_date,
            "observations_length": len(observations) if observations else 0
        })
        
        # Check for duplicates
        is_duplicate, existing_data = self.check_duplicate_assessments(student_name, assessment_date)
        
        if is_duplicate:
            # This should be handled by the UI before calling this method
            self._log_activity("add_assessment_duplicate", {
                "student_name": student_name,
                "assessment_date": assessment_date,
                "existing_data_preview": str(existing_data)[:100] if existing_data else None
            })
            st.error("Duplicate assessment detected. Please handle through the UI first.")
            return False
        
        # Load existing data
        df = self.load_existing_data()
        
        # Prepare new assessment data with timestamp
        formatted_assessment = self.format_assessment_data(assessment_result)
        timestamp_str = operation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        new_data = f"Timestamp: {timestamp_str}\nObservations: {observations}\n\nAssessment:\n{formatted_assessment}"
        
        # Create or update student row
        if df.empty or 'Student_Name' not in df.columns:
            # Create new DataFrame
            df = pd.DataFrame(columns=['Student_Name'])
        
        # Find or create student row with normalized matching
        df['_normalized_name'] = df['Student_Name'].apply(lambda x: normalize_name(str(x)) if pd.notna(x) else '')
        normalized_input = normalize_name(student_name)
        student_mask = df['_normalized_name'] == normalized_input
        df.drop('_normalized_name', axis=1, inplace=True)
        
        if student_mask.any():
            # Update existing student
            student_idx = df[student_mask].index[0]
        else:
            # Add new student
            new_row = {'Student_Name': student_name}
            for col in df.columns:
                if col != 'Student_Name':
                    new_row[col] = ''
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            student_idx = len(df) - 1
        
        # Add date column if it doesn't exist
        date_col = format_date_column(assessment_date)
        if date_col not in df.columns:
            df[date_col] = ''
        
        # Update the data
        df.at[student_idx, date_col] = new_data
        
        # Save the updated data
        self.save_data(df)
        
        # Update metadata
        self._update_student_metadata(student_name, 'add_observation')
        
        # Log successful completion
        self._log_activity("add_assessment_complete", {
            "student_name": student_name,
            "assessment_date": assessment_date,
            "date_column": date_col,
            "student_index": student_idx,
            "success": True
        })
        
        return True
    
    def replace_assessment(self, student_name: str, observations: str, assessment_result: Dict,
                          assessment_date: str) -> bool:
        """Replace existing assessment data for a student on a specific date"""
        df = self.load_existing_data()
        
        if df.empty or 'Student_Name' not in df.columns:
            return False
        
        # Find student with normalized matching
        df['_normalized_name'] = df['Student_Name'].apply(lambda x: normalize_name(str(x)) if pd.notna(x) else '')
        normalized_input = normalize_name(student_name)
        student_mask = df['_normalized_name'] == normalized_input
        df.drop('_normalized_name', axis=1, inplace=True)
        
        if not student_mask.any():
            return False
        
        student_idx = df[student_mask].index[0]
        date_col = format_date_column(assessment_date)
        
        if date_col not in df.columns:
            df[date_col] = ''
        
        # Replace the data
        formatted_assessment = self.format_assessment_data(assessment_result)
        new_data = f"Observations: {observations}\n\nAssessment:\n{formatted_assessment}"
        df.at[student_idx, date_col] = new_data
        
        self.save_data(df)
        return True
    
    def append_assessment(self, student_name: str, observations: str, assessment_result: Dict,
                         assessment_date: str) -> bool:
        """Append new assessment data to existing data for a student on a specific date"""
        df = self.load_existing_data()
        
        if df.empty or 'Student_Name' not in df.columns:
            return False
        
        # Find student with normalized matching
        df['_normalized_name'] = df['Student_Name'].apply(lambda x: normalize_name(str(x)) if pd.notna(x) else '')
        normalized_input = normalize_name(student_name)
        student_mask = df['_normalized_name'] == normalized_input
        df.drop('_normalized_name', axis=1, inplace=True)
        
        if not student_mask.any():
            return False
        
        student_idx = df[student_mask].index[0]
        date_col = format_date_column(assessment_date)
        
        if date_col not in df.columns:
            df[date_col] = ''
        
        # Get existing data
        existing_data = df.at[student_idx, date_col]
        
        # Append new data
        formatted_assessment = self.format_assessment_data(assessment_result)
        new_data = f"Observations: {observations}\n\nAssessment:\n{formatted_assessment}"
        
        if pd.notna(existing_data) and str(existing_data).strip():
            combined_data = f"{existing_data}\n\n--- Additional Assessment ---\n{new_data}"
        else:
            combined_data = new_data
        
        df.at[student_idx, date_col] = combined_data
        
        self.save_data(df)
        return True
    
    def get_student_data(self, student_name: str) -> Optional[pd.Series]:
        """Get all assessment data for a specific student"""
        df = self.load_existing_data()
        
        if df.empty or 'Student_Name' not in df.columns:
            return None
        
        student_mask = df['Student_Name'] == student_name
        if not student_mask.any():
            return None
        
        # Safely access DataFrame with check
        student_rows = df[student_mask]
        if student_rows.empty:
            return None
        
        return student_rows.iloc[0]
    
    def get_all_students(self) -> List[str]:
        """Get list of all student names in the system"""
        df = self.load_existing_data()
        
        if df.empty or 'Student_Name' not in df.columns:
            return []
        
        return df['Student_Name'].tolist()
    
    def get_all_assessments(self) -> List[Dict[str, Any]]:
        """
        Get all assessments in the system in a standardized format.
        
        Returns:
            List of assessment dictionaries with student info and assessment data
        """
        df = self.load_existing_data()
        
        if df.empty or 'Student_Name' not in df.columns:
            return []
        
        assessments = []
        
        for idx, row in df.iterrows():
            student_name = row['Student_Name']
            
            # Get all date columns for this student
            date_columns = self.get_date_columns(df)
            
            for date_col in date_columns:
                if pd.notna(row[date_col]) and str(row[date_col]).strip():
                    # Parse date from column name
                    assessment_date = self._parse_date_from_column(date_col)
                    
                    # Extract content
                    content = str(row[date_col])
                    
                    # Extract school and class from content if present
                    school = 'Unknown'
                    class_name = 'Unknown'
                    
                    import re
                    school_match = re.search(r'\[School:\s*([^\]]+)\]', content)
                    class_match = re.search(r'\[Class:\s*([^\]]+)\]', content)
                    
                    if school_match:
                        school = school_match.group(1).strip()
                    if class_match:
                        class_name = class_match.group(1).strip()
                    
                    # Extract observations
                    observations = self._extract_observation_text(content)
                    
                    # Create assessment record
                    assessment_record = {
                        'student_name': student_name,
                        'school': school,
                        'class': class_name,
                        'assessment_date': assessment_date.strftime('%Y-%m-%d'),
                        'observations': observations,
                        'content': content,
                        'date_column': date_col
                    }
                    
                    assessments.append(assessment_record)
        
        # Sort by date (newest first)
        assessments.sort(key=lambda x: x['assessment_date'], reverse=True)
        
        return assessments
    
    def export_to_csv(self, output_file: Optional[str] = None) -> str:
        """Export current data to a CSV file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"assessments/export_{timestamp}.csv"
        
        df = self.load_existing_data()
        df.to_csv(output_file, index=False)
        return output_file
    
    def extract_observations_from_storage(self, student_name: str) -> List[Observation]:
        """
        Extract all observations for a student from the storage format.
        
        Args:
            student_name: Name of the student
            
        Returns:
            List of Observation objects parsed from stored data
        """
        df = self.load_existing_data()
        
        if df.empty or 'Student_Name' not in df.columns:
            return []
        
        # Find student with normalized matching
        df['_normalized_name'] = df['Student_Name'].apply(lambda x: normalize_name(str(x)) if pd.notna(x) else '')
        normalized_input = normalize_name(student_name)
        student_row = df[df['_normalized_name'] == normalized_input]
        df.drop('_normalized_name', axis=1, inplace=True)
        
        if student_row.empty:
            return []
        
        # Safely access DataFrame with check
        if len(student_row) == 0:
            return []
        
        observations = []
        student_data = student_row.iloc[0]
        student_id = self._generate_student_id(student_name)
        
        # Extract observations from date columns
        date_columns = self.get_date_columns(df)
        for date_col in date_columns:
            if pd.notna(student_data[date_col]) and str(student_data[date_col]).strip():
                # Parse date from column name
                observation_date = self._parse_date_from_column(date_col)
                
                # Extract observation content
                content = str(student_data[date_col])
                observation_text = self._extract_observation_text(content)
                
                # Extract school and class from observation text if present
                school = 'Unknown'
                class_name = 'Unknown'
                
                if observation_text:
                    # Check for school/class markers at the beginning
                    import re
                    school_match = re.search(r'\[School:\s*([^\]]+)\]', observation_text)
                    class_match = re.search(r'\[Class:\s*([^\]]+)\]', observation_text)
                    
                    if school_match:
                        school = school_match.group(1).strip()
                        # Remove the marker from observation text
                        observation_text = re.sub(r'\[School:\s*[^\]]+\]\s*', '', observation_text)
                    
                    if class_match:
                        class_name = class_match.group(1).strip()
                        # Remove the marker from observation text
                        observation_text = re.sub(r'\[Class:\s*[^\]]+\]\s*', '', observation_text)
                
                if observation_text:
                    observation = Observation(
                        observation_id=str(uuid.uuid4()),
                        student_id=student_id,
                        student_name=student_name,
                        content=observation_text,
                        timestamp=observation_date,
                        source="csv_upload",
                        metadata={
                            'original_column': date_col,
                            'school': school,
                            'class': class_name
                        }
                    )
                    observations.append(observation)
        
        return observations
    
    def extract_assessments_from_storage(self, student_name: str) -> List[Assessment]:
        """
        Extract all assessments for a student from the storage format.
        
        Args:
            student_name: Name of the student
            
        Returns:
            List of Assessment objects parsed from stored data
        """
        df = self.load_existing_data()
        
        if df.empty or 'Student_Name' not in df.columns:
            return []
        
        # Find student with normalized matching
        df['_normalized_name'] = df['Student_Name'].apply(lambda x: normalize_name(str(x)) if pd.notna(x) else '')
        normalized_input = normalize_name(student_name)
        student_row = df[df['_normalized_name'] == normalized_input]
        df.drop('_normalized_name', axis=1, inplace=True)
        
        if student_row.empty:
            return []
        
        # Safely access DataFrame with check
        if len(student_row) == 0:
            return []
        
        assessments = []
        student_data = student_row.iloc[0]
        student_id = self._generate_student_id(student_name)
        
        # Extract assessments from date columns
        date_columns = self.get_date_columns(df)
        for date_col in date_columns:
            if pd.notna(student_data[date_col]) and str(student_data[date_col]).strip():
                # Parse date from column name
                assessment_date = self._parse_date_from_column(date_col)
                
                # Extract assessment content
                content = str(student_data[date_col])
                assessment_data = self._extract_assessment_data(content)
                
                if assessment_data:
                    assessment = Assessment(
                        assessment_id=str(uuid.uuid4()),
                        student_id=student_id,
                        qualities=assessment_data,
                        timestamp=assessment_date,
                        source_observations=[],  # Could be enhanced to track
                        metadata={
                            'original_column': date_col,
                            'extraction_method': 'storage_parser'
                        }
                    )
                    assessments.append(assessment)
        
        return assessments
    
    def get_consolidated_student_profile(self, student_name: str) -> Optional[ConsolidatedProfile]:
        """
        Get consolidated profile for a student including all observations and assessments.
        
        Args:
            student_name: Name of the student
            
        Returns:
            ConsolidatedProfile object or None if student not found
        """
        observations = self.extract_observations_from_storage(student_name)
        assessments = self.extract_assessments_from_storage(student_name)
        
        if not observations:
            return None
        
        student_id = self._generate_student_id(student_name)
        
        try:
            consolidated_profile = self.data_consolidator.consolidate_student_observations(
                student_id, observations, assessments
            )
            return consolidated_profile
        except Exception as e:
            st.error(f"Error consolidating data for {student_name}: {e}")
            return None
    
    def get_all_consolidated_profiles(self, limit: int = None) -> List[ConsolidatedProfile]:
        """
        Get consolidated profiles for all students in the system.
        
        Args:
            limit: Optional limit on number of profiles to return (for performance)
        
        Returns:
            List of ConsolidatedProfile objects
        """
        all_students = self.get_all_students()
        
        # Apply limit if specified
        if limit and limit > 0:
            all_students = all_students[:limit]
        
        profiles = []
        
        for student_name in all_students:
            profile = self.get_consolidated_student_profile(student_name)
            if profile:
                profiles.append(profile)
        
        return profiles
    
    def get_student_observation_summary(self, student_name: str) -> Dict[str, Any]:
        """
        Get summary information about a student's observations and assessments.
        
        Args:
            student_name: Name of the student
            
        Returns:
            Dictionary with summary statistics
        """
        profile = self.get_consolidated_student_profile(student_name)
        
        if not profile:
            return {
                'student_name': student_name,
                'observation_count': 0,
                'assessment_count': 0,
                'first_observed': None,
                'last_observed': None,
                'data_quality_score': 0.0,
                'has_consolidated_assessment': False
            }
        
        return {
            'student_name': profile.student_name,
            'observation_count': profile.observation_count,
            'assessment_count': profile.assessment_count,
            'first_observed': profile.first_observed,
            'last_observed': profile.last_observed,
            'data_quality_score': profile.data_quality_score,
            'has_consolidated_assessment': profile.consolidated_assessment is not None,
            'school': profile.school,
            'class': profile.class_name
        }
    
    def _generate_student_id(self, student_name: str) -> str:
        """Generate consistent student ID from name"""
        normalized_name = normalize_name(student_name)
        # Use hash for consistent ID generation
        import hashlib
        return hashlib.md5(normalized_name.encode()).hexdigest()[:12]
    
    def _parse_date_from_column(self, column_name: str) -> datetime:
        """Parse date from column name (Session_DDMmmYYYY or Date_YYYY-MM-DD format)"""
        try:
            if column_name.startswith('Session_'):
                # Format: Session_07Dec2025
                date_part = column_name.replace('Session_', '')
                return datetime.strptime(date_part, '%d%b%Y')
            elif column_name.startswith('Date_'):
                # Format: Date_2025-12-07
                date_part = column_name.replace('Date_', '')
                return datetime.strptime(date_part, '%Y-%m-%d')
            else:
                # Fallback to current date
                return datetime.now()
        except ValueError:
            # If parsing fails, return current date
            return datetime.now()
    
    def _extract_observation_text(self, content: str) -> str:
        """Extract observation text from stored content, including school/class markers"""
        if not content or not content.strip():
            return ""
        
        # Look for "Observations:" section
        lines = content.split('\n')
        observation_lines = []
        in_observations = False
        
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('Observations:'):
                in_observations = True
                # Include the text after "Observations:" if any
                obs_text = line_stripped.replace('Observations:', '').strip()
                if obs_text:
                    observation_lines.append(obs_text)
            elif in_observations and line_stripped.startswith('Assessment:'):
                # Stop when we hit the assessment section
                break
            elif in_observations and line_stripped:
                observation_lines.append(line_stripped)
        
        return '\n'.join(observation_lines).strip()
    
    def _extract_assessment_data(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Extract assessment data from stored content"""
        if not content or not content.strip():
            return {}
        
        # Look for "Assessment:" section
        lines = content.split('\n')
        assessment_lines = []
        in_assessment = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('Assessment:'):
                in_assessment = True
                # Include the text after "Assessment:" if any
                assess_text = line.replace('Assessment:', '').strip()
                if assess_text:
                    assessment_lines.append(assess_text)
            elif in_assessment and line:
                assessment_lines.append(line)
        
        if not assessment_lines:
            return {}
        
        # Parse assessment text into structured format
        assessment_text = '\n'.join(assessment_lines)
        qualities = {}
        
        # Simple parsing - look for "Quality: Level" patterns
        # This is a basic parser and could be enhanced based on actual data format
        for line in assessment_lines:
            if ':' in line and not line.startswith('('):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    quality = parts[0].strip()
                    level = parts[1].strip()
                    
                    # Extract reasoning if it's on the next line in parentheses
                    reasoning = ""
                    # This is simplified - could be enhanced for better parsing
                    
                    qualities[quality] = {
                        'level': level,
                        'reasoning': reasoning,
                        'confidence': 0.8  # Default confidence
                    }
        
        return qualities

    def get_observation_metadata(self, student_name: str) -> Dict[str, Any]:
        """
        Get comprehensive metadata for a student's observations.
        
        Args:
            student_name: Name of the student
            
        Returns:
            Dictionary with observation metadata including counts, dates, history, school, class, and quality metrics
        """
        normalized_name = normalize_name(student_name)
        
        # Get metadata from storage
        student_meta = self.metadata['student_counts'].get(normalized_name, {})
        
        # Get detailed observation history from storage
        observations = self.extract_observations_from_storage(student_name)
        assessments = self.extract_assessments_from_storage(student_name)
        
        # Extract school and class from observations
        school = 'Unknown'
        class_name = 'Unknown'
        if observations:
            # Get school and class from the first observation's metadata
            school = observations[0].metadata.get('school', 'Unknown')
            class_name = observations[0].metadata.get('class', 'Unknown')
        
        # Calculate data quality score directly
        data_quality_score = 0.0
        has_consolidated_assessment = False
        
        if observations:
            # Calculate data quality using the same logic as DataConsolidator
            data_quality_score = self.data_consolidator._calculate_data_quality_score(
                observations, assessments
            )
            # Check if we have assessments (which means consolidated assessment exists)
            has_consolidated_assessment = len(assessments) > 0
        
        return {
            'student_name': student_name,
            'normalized_name': normalized_name,
            'observation_count': student_meta.get('observation_count', len(observations)),
            'assessment_count': len(assessments),
            'first_observed': student_meta.get('first_observed'),
            'last_observed': student_meta.get('last_observed'),
            'observation_dates': [obs.timestamp.strftime('%Y-%m-%d') for obs in observations],
            'assessment_dates': [assess.timestamp.strftime('%Y-%m-%d') for assess in assessments],
            'data_sources': list(set(obs.source for obs in observations)),
            'metadata_last_updated': self.metadata.get('last_updated'),
            'school': school,
            'class': class_name,
            'data_quality_score': data_quality_score,
            'has_consolidated_assessment': has_consolidated_assessment
        }
    
    def get_system_metadata(self) -> Dict[str, Any]:
        """
        Get comprehensive system metadata and statistics.
        Recalculates statistics from actual data to ensure accuracy.
        
        Returns:
            Dictionary with system-wide metadata and statistics
        """
        # Recalculate statistics from actual data
        try:
            df = self.load_existing_data()
            total_students = len(df) if not df.empty else 0
            
            # Count total observations (date columns)
            date_columns = self.get_date_columns(df)
            total_observations = 0
            for col in date_columns:
                total_observations += df[col].notna().sum()
            
            # Update metadata with fresh counts
            self.metadata['total_students'] = total_students
            self.metadata['total_observations'] = total_observations
            
        except Exception as e:
            self.logger.warning(f"Could not recalculate metadata: {e}")
            # Fall back to cached values
            total_students = self.metadata.get('total_students', 0)
            total_observations = self.metadata.get('total_observations', 0)
        
        return {
            'storage_file': self.storage_file,
            'created_at': self.metadata.get('created_at'),
            'last_updated': self.metadata.get('last_updated'),
            'version': self.metadata.get('version'),
            'total_students': total_students,
            'total_observations': total_observations,
            'last_backup': self.metadata.get('last_backup'),
            'backup_directory': self.backup_dir,
            'audit_log_file': self.audit_log_file,
            'metadata_file': self.metadata_file,
            'last_operation_timestamp': self.metadata.get('last_operation_timestamp')
        }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups with metadata.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        try:
            for file in os.listdir(self.backup_dir):
                if file.startswith("backup_") and file.endswith(".csv"):
                    file_path = os.path.join(self.backup_dir, file)
                    
                    # Extract timestamp from filename
                    timestamp_str = file.replace("backup_", "").replace(".csv", "")
                    
                    # Get file stats
                    stat = os.stat(file_path)
                    
                    backup_info = {
                        'filename': file,
                        'path': file_path,
                        'timestamp': timestamp_str,
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'size_bytes': stat.st_size,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2)
                    }
                    
                    # Check for corresponding metadata backup
                    metadata_file = os.path.join(self.backup_dir, f"metadata_{timestamp_str}.json")
                    backup_info['has_metadata'] = os.path.exists(metadata_file)
                    
                    backups.append(backup_info)
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def restore_from_backup(self, backup_filename: str) -> bool:
        """
        Restore data from a specific backup.
        
        Args:
            backup_filename: Name of the backup file to restore from
            
        Returns:
            True if restoration was successful, False otherwise
        """
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            self.logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Create a backup of current state before restoring
            current_backup = self._create_backup()
            
            # Copy backup to main storage file
            shutil.copy2(backup_path, self.storage_file)
            
            # Try to restore metadata if available
            timestamp_str = backup_filename.replace("backup_", "").replace(".csv", "")
            metadata_backup = os.path.join(self.backup_dir, f"metadata_{timestamp_str}.json")
            
            if os.path.exists(metadata_backup):
                shutil.copy2(metadata_backup, self.metadata_file)
                # Reload metadata
                self.metadata = self._load_metadata()
            
            # Log the restoration
            self._log_activity("restore_from_backup", {
                "backup_filename": backup_filename,
                "backup_path": backup_path,
                "current_backup_created": current_backup,
                "metadata_restored": os.path.exists(metadata_backup)
            })
            
            st.success(f"Successfully restored from backup: {backup_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore from backup {backup_filename}: {e}")
            st.error(f"Failed to restore from backup: {e}")
            return False
    
    def delete_backup(self, backup_filename: str) -> bool:
        """
        Delete a specific backup file and its associated metadata.
        
        Args:
            backup_filename: Name of the backup file to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            self.logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Delete the backup CSV file
            os.remove(backup_path)
            
            # Try to delete associated metadata backup
            timestamp_str = backup_filename.replace("backup_", "").replace(".csv", "")
            metadata_backup = os.path.join(self.backup_dir, f"metadata_{timestamp_str}.json")
            
            if os.path.exists(metadata_backup):
                os.remove(metadata_backup)
            
            # Log the deletion
            self._log_activity("delete_backup", {
                "backup_filename": backup_filename,
                "backup_path": backup_path,
                "metadata_deleted": os.path.exists(metadata_backup)
            })
            
            self.logger.info(f"Successfully deleted backup: {backup_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete backup {backup_filename}: {e}")
            return False
    
    def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent audit trail entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audit trail entries
        """
        audit_entries = []
        
        if not os.path.exists(self.audit_log_file):
            return audit_entries
        
        try:
            with open(self.audit_log_file, 'r') as f:
                lines = f.readlines()
            
            # Get the most recent entries
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in recent_lines:
                try:
                    # Parse log line to extract JSON
                    # Format: timestamp - level - json_data
                    parts = line.strip().split(' - ', 2)
                    if len(parts) >= 3:
                        json_data = json.loads(parts[2])
                        audit_entries.append(json_data)
                except json.JSONDecodeError:
                    continue
            
            # Sort by timestamp (newest first)
            audit_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to read audit trail: {e}")
        
        return audit_entries
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """
        Validate the integrity of stored data and metadata.
        
        Returns:
            Dictionary with validation results and any issues found
        """
        validation_results = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # Check if main storage file exists and is readable
            if not os.path.exists(self.storage_file):
                validation_results['issues'].append("Main storage file does not exist")
                validation_results['is_valid'] = False
                return validation_results
            
            # Load and validate DataFrame
            df = self.load_existing_data()
            
            if df.empty:
                validation_results['warnings'].append("Storage file is empty")
            else:
                # Validate DataFrame structure
                if 'Student_Name' not in df.columns:
                    validation_results['issues'].append("Missing Student_Name column")
                    validation_results['is_valid'] = False
                
                # Check for duplicate student names
                if 'Student_Name' in df.columns:
                    duplicates = df['Student_Name'].duplicated()
                    if duplicates.any():
                        duplicate_names = df[duplicates]['Student_Name'].tolist()
                        validation_results['warnings'].append(f"Duplicate student names found: {duplicate_names}")
                
                # Validate date columns
                date_columns = self.get_date_columns(df)
                validation_results['statistics']['date_columns'] = len(date_columns)
                validation_results['statistics']['total_students'] = len(df)
                
                # Check metadata consistency
                metadata_student_count = self.metadata.get('total_students', 0)
                actual_student_count = len(df)
                
                if metadata_student_count != actual_student_count:
                    validation_results['warnings'].append(
                        f"Metadata student count ({metadata_student_count}) doesn't match actual count ({actual_student_count})"
                    )
            
            # Check backup directory
            if os.path.exists(self.backup_dir):
                backups = self.list_backups()
                validation_results['statistics']['backup_count'] = len(backups)
            else:
                validation_results['warnings'].append("Backup directory does not exist")
            
            # Check audit log
            if os.path.exists(self.audit_log_file):
                audit_entries = self.get_audit_trail(10)
                validation_results['statistics']['recent_audit_entries'] = len(audit_entries)
            else:
                validation_results['warnings'].append("Audit log file does not exist")
            
            # Log validation
            self._log_activity("data_validation", {
                "is_valid": validation_results['is_valid'],
                "issue_count": len(validation_results['issues']),
                "warning_count": len(validation_results['warnings']),
                "statistics": validation_results['statistics']
            })
            
        except Exception as e:
            validation_results['issues'].append(f"Validation failed with error: {str(e)}")
            validation_results['is_valid'] = False
            self.logger.error(f"Data validation failed: {e}")
        
        return validation_results
