import pandas as pd
import json
import os
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import streamlit as st

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
    Manages storage of assessment results in a structured CSV format.
    Student names are in the first column, followed by date-based columns
    containing observations and assessments for each date.
    """
    
    def __init__(self, storage_file: str = "assessments/student_assessments.csv"):
        self.storage_file = storage_file
        self.ensure_storage_directory()
    
    def ensure_storage_directory(self):
        """Ensure the storage directory exists"""
        directory = os.path.dirname(self.storage_file)
        if directory:  # Only create directory if there is one
            os.makedirs(directory, exist_ok=True)
    
    def load_existing_data(self) -> pd.DataFrame:
        """Load existing assessment data from CSV file"""
        if os.path.exists(self.storage_file):
            try:
                df = pd.read_csv(self.storage_file, index_col=0)
                return df
            except Exception as e:
                st.warning(f"Could not load existing data: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
    
    def save_data(self, df: pd.DataFrame):
        """Save DataFrame to CSV file using atomic write pattern"""
        try:
            # Ensure directory exists
            self.ensure_storage_directory()
            
            # Write to temporary file first
            fd, temp_path = tempfile.mkstemp(suffix='.csv', dir=os.path.dirname(self.storage_file) or '.')
            try:
                os.close(fd)  # Close the file descriptor
                df.to_csv(temp_path, index=True)
                # Atomic rename (on same filesystem)
                shutil.move(temp_path, self.storage_file)
                st.success(f"Assessment data saved to {self.storage_file}")
            except Exception as e:
                # Clean up temp file on failure
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise e
        except Exception as e:
            st.error(f"Failed to save data: {e}")
    
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
        Add a new assessment to the storage system
        Returns True if successfully added, False otherwise
        """
        if assessment_date is None:
            assessment_date = datetime.now().strftime("%Y-%m-%d")
        
        # Check for duplicates
        is_duplicate, existing_data = self.check_duplicate_assessments(student_name, assessment_date)
        
        if is_duplicate:
            # This should be handled by the UI before calling this method
            st.error("Duplicate assessment detected. Please handle through the UI first.")
            return False
        
        # Load existing data
        df = self.load_existing_data()
        
        # Prepare new assessment data
        formatted_assessment = self.format_assessment_data(assessment_result)
        new_data = f"Observations: {observations}\n\nAssessment:\n{formatted_assessment}"
        
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
        
        return df[student_mask].iloc[0]
    
    def get_all_students(self) -> List[str]:
        """Get list of all student names in the system"""
        df = self.load_existing_data()
        
        if df.empty or 'Student_Name' not in df.columns:
            return []
        
        return df['Student_Name'].tolist()
    
    def export_to_csv(self, output_file: Optional[str] = None) -> str:
        """Export current data to a CSV file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"assessments/export_{timestamp}.csv"
        
        df = self.load_existing_data()
        df.to_csv(output_file, index=False)
        return output_file
