"""
Enhanced CSV Processor for Personality Assessment System
Addresses user feedback issues with robust CSV parsing, validation, and duplicate detection
"""

import pandas as pd
import hashlib
import os
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class ValidationIssue:
    """Represents a validation issue found in CSV processing"""
    row_number: int
    column: str
    issue_type: str
    description: str
    suggested_fix: str


@dataclass
class ValidationResult:
    """Result of CSV validation"""
    is_valid: bool
    total_rows: int
    valid_rows: int
    blank_rows_skipped: int
    issues: List[ValidationIssue]
    processed_data: pd.DataFrame


@dataclass
class DuplicateEntry:
    """Represents a duplicate entry found in CSV"""
    row_numbers: List[int]
    student_name: str
    duplicate_type: str  # 'exact_match', 'name_similarity', 'content_similarity'
    similarity_score: float


@dataclass
class DuplicateReport:
    """Report of duplicate detection results"""
    duplicates_found: List[DuplicateEntry]
    total_duplicates: int
    unique_students: int


class EnhancedCSVProcessor:
    """Enhanced CSV processor with robust validation and duplicate detection"""
    
    def __init__(self):
        self.upload_history = {}  # Track uploaded files to prevent reprocessing
    
    @staticmethod
    def sanitize_csv_cell(value) -> str:
        """
        Sanitize CSV cell values to prevent CSV injection attacks.
        
        CSV injection (also known as Formula Injection) occurs when spreadsheet applications
        like Excel interpret cell values starting with special characters (=, +, -, @, tab, 
        carriage return) as formulas, which can lead to code execution vulnerabilities.
        
        This function prefixes dangerous characters with a single quote to prevent formula
        interpretation while preserving the original data for display purposes.
        
        Args:
            value: Cell value of any type (str, int, float, None, NaN)
        
        Returns:
            Sanitized string value safe for CSV export
        
        Security Note:
            This addresses OWASP recommendations for CSV injection prevention.
            Reference: https://owasp.org/www-community/attacks/CSV_Injection
        
        Examples:
            >>> sanitize_csv_cell("=SUM(A1:A10)")
            "'=SUM(A1:A10)"
            >>> sanitize_csv_cell("Normal text")
            "Normal text"
            >>> sanitize_csv_cell(123)
            "123"
            >>> sanitize_csv_cell(None)
            ""
        """
        # Handle None
        if value is None:
            return ""
        
        # Handle pandas NA and NaN values
        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            # If pd.isna() fails, continue with string conversion
            pass
        
        # Convert to string
        str_value = str(value)
        
        # Define dangerous characters that could trigger formula execution
        dangerous_chars = ('=', '+', '-', '@', '\t', '\r')
        
        # Check if the first character is dangerous (before any stripping)
        if str_value and str_value[0] in dangerous_chars:
            # Prefix with single quote to prevent formula interpretation
            # Keep the original value intact (don't strip)
            return f"'{str_value}"
        
        # For safe values, strip whitespace normally
        str_value = str_value.strip()
        
        # Empty strings are safe
        if not str_value:
            return ""
        
        return str_value
    
    def sanitize_dataframe_for_export(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Sanitize all cells in a DataFrame to prevent CSV injection attacks.
        
        This method should be called before any DataFrame.to_csv() operation
        to ensure all cell values are safe from formula injection.
        
        Args:
            df: DataFrame to sanitize
        
        Returns:
            New DataFrame with all cells sanitized
        """
        if df.empty:
            return df
        
        # Create a copy to avoid modifying the original
        sanitized_df = df.copy()
        
        # Apply sanitization to all columns
        for column in sanitized_df.columns:
            sanitized_df[column] = sanitized_df[column].apply(self.sanitize_csv_cell)
        
        return sanitized_df
        
    def validate_and_process_csv(self, file_content: str, filename: str = None) -> ValidationResult:
        """
        Main method to validate and process CSV content
        Addresses Requirements 8.1, 8.2, 8.3, 8.4, 8.5
        """
        try:
            # Try different encodings to handle various file formats
            df = self._read_csv_with_encoding(file_content)
            
            # Normalize column names
            df = self._normalize_columns(df)
            
            # Validate basic structure
            structure_issues = self._validate_csv_structure(df)
            
            # Skip blank rows and validate data
            cleaned_df, validation_issues = self._clean_and_validate_data(df)
            
            # Combine all issues
            all_issues = structure_issues + validation_issues
            
            # Calculate statistics
            total_rows = len(df)
            valid_rows = len(cleaned_df)
            invalid_data_issues = len([i for i in all_issues if i.issue_type == 'invalid_data'])
            blank_rows_skipped = max(0, total_rows - valid_rows - invalid_data_issues)
            
            return ValidationResult(
                is_valid=len([i for i in all_issues if i.issue_type == 'critical']) == 0,
                total_rows=total_rows,
                valid_rows=valid_rows,
                blank_rows_skipped=blank_rows_skipped,
                issues=all_issues,
                processed_data=cleaned_df
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                total_rows=0,
                valid_rows=0,
                blank_rows_skipped=0,
                issues=[ValidationIssue(
                    row_number=0,
                    column="file",
                    issue_type="critical",
                    description=f"Failed to read CSV file: {str(e)}",
                    suggested_fix="Check file format and encoding. Ensure it's a valid CSV file."
                )],
                processed_data=pd.DataFrame()
            )
    
    def _read_csv_with_encoding(self, file_content: str) -> pd.DataFrame:
        """Try different encodings to read CSV content"""
        encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                if isinstance(file_content, str):
                    # If it's already a string, create a StringIO object
                    from io import StringIO
                    # Force all columns to be read as strings to preserve original data
                    return pd.read_csv(StringIO(file_content), dtype=str, keep_default_na=False)
                else:
                    # If it's bytes, try with encoding
                    from io import StringIO
                    content_str = file_content.decode(encoding)
                    # Force all columns to be read as strings to preserve original data
                    return pd.read_csv(StringIO(content_str), dtype=str, keep_default_na=False)
            except (UnicodeDecodeError, pd.errors.EmptyDataError):
                continue
        
        raise ValueError("Could not read CSV with any supported encoding")
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to handle case variations and whitespace"""
        # Strip whitespace and convert to title case for consistency
        df.columns = df.columns.str.strip().str.title()
        return df
    
    def _validate_csv_structure(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate basic CSV structure and required columns"""
        issues = []
        
        # Check for required columns - support both old and new formats
        # New format: Name, School, Class, Session, Observations
        # Old format: Name, Observations (for backward compatibility)
        required_columns_new = ['Name', 'School', 'Class', 'Session', 'Observations']
        required_columns_old = ['Name', 'Observations']
        
        # Check if it's the new 5-column format
        has_new_format = all(col in df.columns for col in required_columns_new)
        has_old_format = all(col in df.columns for col in required_columns_old)
        
        if not has_new_format and not has_old_format:
            # Neither format is complete, check what's missing
            if 'Name' not in df.columns:
                issues.append(ValidationIssue(
                    row_number=0,
                    column='Name',
                    issue_type="critical",
                    description="Required column 'Name' is missing",
                    suggested_fix="Add a column named 'Name' to your CSV file"
                ))
            
            if 'Observations' not in df.columns:
                issues.append(ValidationIssue(
                    row_number=0,
                    column='Observations',
                    issue_type="critical",
                    description="Required column 'Observations' is missing",
                    suggested_fix="Add a column named 'Observations' to your CSV file"
                ))
            
            # If has Name and Observations but missing other columns, suggest new format
            if has_old_format:
                missing_cols = [col for col in required_columns_new if col not in df.columns]
                if missing_cols:
                    issues.append(ValidationIssue(
                        row_number=0,
                        column="format",
                        issue_type="warning",
                        description=f"Using legacy 2-column format. Missing columns for new format: {', '.join(missing_cols)}",
                        suggested_fix="Consider upgrading to 5-column format: Name, School, Class, Session, Observations"
                    ))
        
        # Check for empty DataFrame
        if df.empty:
            issues.append(ValidationIssue(
                row_number=0,
                column="file",
                issue_type="critical",
                description="CSV file is empty",
                suggested_fix="Add data rows to your CSV file"
            ))
        
        return issues
    
    def _clean_and_validate_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[ValidationIssue]]:
        """
        Clean data by removing blank rows and validate content
        Addresses Requirement 8.1: Skip completely blank rows and rows with only whitespace
        Supports both legacy (Name, Observations) and new (Name, School, Class, Session, Observations) formats
        """
        issues = []
        valid_rows = []
        
        # Determine format
        has_new_format = all(col in df.columns for col in ['Name', 'School', 'Class', 'Session', 'Observations'])
        
        for idx, row in df.iterrows():
            row_number = idx + 2  # +2 because pandas is 0-indexed and we skip header
            
            # Check if row is completely blank
            if self._is_blank_row(row):
                continue  # Skip blank rows silently
            
            # Validate required fields and sanitize for CSV injection
            name = self.sanitize_csv_cell(row.get('Name', ''))
            observations = self.sanitize_csv_cell(row.get('Observations', ''))
            
            row_issues = []
            
            # Validate Name field
            if not name or name.lower() in ['nan', 'none', '']:
                row_issues.append(ValidationIssue(
                    row_number=row_number,
                    column="Name",
                    issue_type="invalid_data",
                    description="Student name is empty or invalid",
                    suggested_fix="Provide a valid student name"
                ))
            
            # Validate Observations field
            if not observations or observations.lower() in ['nan', 'none', '']:
                row_issues.append(ValidationIssue(
                    row_number=row_number,
                    column="Observations",
                    issue_type="invalid_data",
                    description="Observations field is empty",
                    suggested_fix="Provide observation notes for this student"
                ))
            
            # Validate new format fields if present
            if has_new_format:
                school = self.sanitize_csv_cell(row.get('School', ''))
                class_name = self.sanitize_csv_cell(row.get('Class', ''))
                session = self.sanitize_csv_cell(row.get('Session', ''))
                
                # School validation (optional but recommended)
                if not school or school.lower() in ['nan', 'none', '']:
                    row_issues.append(ValidationIssue(
                        row_number=row_number,
                        column="School",
                        issue_type="warning",
                        description="School name is empty",
                        suggested_fix="Provide school name for better organization"
                    ))
                
                # Class validation (optional but recommended)
                if not class_name or class_name.lower() in ['nan', 'none', '']:
                    row_issues.append(ValidationIssue(
                        row_number=row_number,
                        column="Class",
                        issue_type="warning",
                        description="Class is empty",
                        suggested_fix="Provide class information for better organization"
                    ))
                
                # Session validation (optional but recommended)
                if not session or session.lower() in ['nan', 'none', '']:
                    row_issues.append(ValidationIssue(
                        row_number=row_number,
                        column="Session",
                        issue_type="warning",
                        description="Session is empty",
                        suggested_fix="Provide session information for tracking over time"
                    ))
            
            # If row has valid required data (Name and Observations), include it
            # Warnings don't prevent inclusion
            critical_issues = [issue for issue in row_issues if issue.issue_type in ['critical', 'invalid_data']]
            if not critical_issues:
                # Create sanitized row with CSV injection protection
                sanitized_row = row.copy()
                sanitized_row['Name'] = name
                sanitized_row['Observations'] = observations
                if has_new_format:
                    sanitized_row['School'] = school
                    sanitized_row['Class'] = class_name
                    sanitized_row['Session'] = session
                valid_rows.append(sanitized_row)
            
            # Add all issues (including warnings) to the issues list
            issues.extend(row_issues)
        
        # Create cleaned DataFrame
        cleaned_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
        
        return cleaned_df, issues
    
    def _is_blank_row(self, row: pd.Series) -> bool:
        """
        Check if a row is completely blank or contains only whitespace
        Addresses Requirement 8.1: Skip completely blank rows and rows with only whitespace
        """
        for value in row:
            if pd.notna(value):
                str_value = str(value).strip()
                if str_value and str_value.lower() not in ['nan', 'none', '']:
                    return False
        return True
    
    def detect_duplicates(self, df: pd.DataFrame) -> DuplicateReport:
        """
        Detect duplicate entries within the CSV
        Addresses Requirement 5.3: Identify duplicate student entries within uploaded files
        """
        duplicates = []
        processed_names = {}
        
        for idx, row in df.iterrows():
            name = str(row.get('Name', '')).strip()
            observations = str(row.get('Observations', '')).strip()
            
            # Skip only truly empty names or standard null values
            # But allow special characters like null bytes that might be valid test data
            if not name or name.lower() in ['nan', 'none', '']:
                continue
            
            name_lower = name.lower()
            
            # Check for exact name matches
            if name_lower in processed_names:
                # Check if this is a new duplicate group or addition to existing
                existing_duplicate = None
                for dup in duplicates:
                    if dup.student_name.lower() == name_lower:
                        existing_duplicate = dup
                        break
                
                if existing_duplicate:
                    existing_duplicate.row_numbers.append(idx + 2)
                else:
                    duplicates.append(DuplicateEntry(
                        row_numbers=[processed_names[name_lower], idx + 2],
                        student_name=name if name else f"Student_{idx+2}",  # Handle edge cases better
                        duplicate_type="exact_match",
                        similarity_score=1.0
                    ))
            else:
                processed_names[name_lower] = idx + 2
        
        # Check for similar names (fuzzy matching)
        similar_duplicates = self._find_similar_names(df)
        duplicates.extend(similar_duplicates)
        
        return DuplicateReport(
            duplicates_found=duplicates,
            total_duplicates=len(duplicates),
            unique_students=len(df) - sum(len(dup.row_numbers) - 1 for dup in duplicates)
        )
    
    def _find_similar_names(self, df: pd.DataFrame) -> List[DuplicateEntry]:
        """Find names that are similar but not exact matches"""
        from difflib import SequenceMatcher
        
        similar_duplicates = []
        names = [(idx, str(row.get('Name', '')).strip()) for idx, row in df.iterrows()]
        
        for i, (idx1, name1) in enumerate(names):
            if not name1:
                continue
                
            for j, (idx2, name2) in enumerate(names[i+1:], i+1):
                if not name2:
                    continue
                
                similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
                
                if similarity > 0.8:  # 80% similarity threshold
                    similar_duplicates.append(DuplicateEntry(
                        row_numbers=[idx1 + 2, idx2 + 2],
                        student_name=f"{name1} / {name2}",
                        duplicate_type="name_similarity",
                        similarity_score=similarity
                    ))
        
        return similar_duplicates
    
    def check_file_duplicate(self, file_content: str, filename: str) -> bool:
        """
        Check if this file has been uploaded before
        Addresses Requirement 5.5: Maintain upload history to prevent accidental re-processing
        """
        # Create content hash
        content_hash = hashlib.md5(file_content.encode()).hexdigest()
        
        # Check against upload history
        if filename in self.upload_history:
            stored_info = self.upload_history[filename]
            # Only consider it a duplicate if:
            # 1. Same content hash AND
            # 2. File was successfully processed AND
            # 3. Upload was recent (within last hour to allow for legitimate re-uploads)
            if (stored_info['hash'] == content_hash and 
                stored_info.get('processed', False)):
                
                # Check if upload was recent (within 1 hour)
                time_diff = datetime.now() - stored_info['timestamp']
                if time_diff.total_seconds() < 3600:  # 1 hour
                    return True
        
        # Store in history (always update to latest upload)
        self.upload_history[filename] = {
            'hash': content_hash,
            'timestamp': datetime.now(),
            'processed': False
        }
        
        return False
    
    def clear_upload_history(self):
        """Clear the upload history to allow fresh uploads"""
        self.upload_history = {}
    
    def remove_file_from_history(self, filename: str):
        """Remove a specific file from upload history"""
        if filename in self.upload_history:
            del self.upload_history[filename]
    
    def mark_file_processed(self, filename: str):
        """Mark a file as successfully processed"""
        if filename in self.upload_history:
            self.upload_history[filename]['processed'] = True
    
    def generate_validation_report(self, validation_result: ValidationResult) -> str:
        """
        Generate a detailed validation report
        Addresses Requirement 8.4: Provide detailed validation reports showing skipped rows and reasons
        """
        report = []
        report.append("📋 CSV Validation Report")
        report.append("=" * 50)
        report.append(f"Total rows in file: {validation_result.total_rows}")
        report.append(f"Valid student records: {validation_result.valid_rows}")
        report.append(f"Blank rows skipped: {validation_result.blank_rows_skipped}")
        report.append(f"Invalid rows with issues: {len([i for i in validation_result.issues if i.issue_type == 'invalid_data'])}")
        report.append("")
        
        if validation_result.issues:
            report.append("⚠️ Issues Found:")
            report.append("-" * 30)
            
            # Group issues by type
            critical_issues = [i for i in validation_result.issues if i.issue_type == 'critical']
            data_issues = [i for i in validation_result.issues if i.issue_type == 'invalid_data']
            
            if critical_issues:
                report.append("🚨 Critical Issues (must be fixed):")
                for issue in critical_issues:
                    report.append(f"  • {issue.description}")
                    report.append(f"    Fix: {issue.suggested_fix}")
                report.append("")
            
            if data_issues:
                report.append("⚠️ Data Issues:")
                for issue in data_issues:
                    report.append(f"  • Row {issue.row_number}, Column '{issue.column}': {issue.description}")
                    report.append(f"    Fix: {issue.suggested_fix}")
                report.append("")
        
        if validation_result.is_valid:
            report.append("✅ File is ready for processing!")
        else:
            report.append("❌ File has critical issues that must be resolved before processing.")
        
        return "\n".join(report)
    
    def get_processing_summary(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Get a summary suitable for UI display"""
        return {
            'total_rows': validation_result.total_rows,
            'valid_students': validation_result.valid_rows,
            'blank_rows_skipped': validation_result.blank_rows_skipped,
            'issues_count': len(validation_result.issues),
            'critical_issues': len([i for i in validation_result.issues if i.issue_type == 'critical']),
            'is_processable': validation_result.is_valid and validation_result.valid_rows > 0,
            'processed_data': validation_result.processed_data
        }

    @staticmethod
    def sanitize_csv_cell(value) -> str:
        """
        Sanitize CSV cell values to prevent CSV injection attacks.

        CSV injection (also known as Formula Injection) occurs when spreadsheet applications
        like Excel interpret cell values starting with special characters (=, +, -, @, tab,
        carriage return) as formulas, which can lead to code execution vulnerabilities.

        This function prefixes dangerous characters with a single quote to prevent formula
        interpretation while preserving the original data for display purposes.

        Args:
            value: Cell value of any type (str, int, float, None, NaN)

        Returns:
            Sanitized string value safe for CSV export

        Security Note:
            This addresses OWASP recommendations for CSV injection prevention.
            Reference: https://owasp.org/www-community/attacks/CSV_Injection

        Examples:
            >>> sanitize_csv_cell("=SUM(A1:A10)")
            "'=SUM(A1:A10)"
            >>> sanitize_csv_cell("Normal text")
            "Normal text"
            >>> sanitize_csv_cell(123)
            "123"
            >>> sanitize_csv_cell(None)
            ""
        """
        # Handle None and NaN values
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""

        # Convert to string
        str_value = str(value).strip()

        # Empty strings are safe
        if not str_value:
            return ""

        # Define dangerous characters that could trigger formula execution
        dangerous_chars = ('=', '+', '-', '@', '\t', '\r')

        # Check if the first character is dangerous
        if str_value[0] in dangerous_chars:
            # Prefix with single quote to prevent formula interpretation
            return f"'{str_value}"

        return str_value



def create_sample_csv_with_issues():
    """Create a sample CSV for testing that includes the issues mentioned in user feedback"""
    sample_data = [
        ['Name', 'Observations'],
        ['John Doe', 'Very active student, participates well in class'],
        ['', ''],  # Blank row
        ['Jane Smith', 'Quiet but attentive, completes work on time'],
        ['   ', '   '],  # Whitespace only row
        ['Bob Johnson', ''],  # Missing observations
        ['', 'Some observations without a name'],  # Missing name
        ['Alice Brown', 'Creative and enthusiastic student'],
        ['', ''],  # Another blank row
        ['Charlie Wilson', 'Shows leadership qualities'],
        ['', ''],  # Final blank row
    ]
    
    # Convert to proper CSV string
    csv_lines = []
    for row in sample_data:
        csv_lines.append(','.join([f'"{cell}"' if ',' in str(cell) else str(cell) for cell in row]))
    
    return '\n'.join(csv_lines)


if __name__ == "__main__":
    # Test the enhanced CSV processor
    processor = EnhancedCSVProcessor()
    
    # Test with sample data that has issues
    sample_csv = create_sample_csv_with_issues()
    result = processor.validate_and_process_csv(sample_csv, "test_file.csv")
    
    print(processor.generate_validation_report(result))
    print("\nProcessing Summary:")
    summary = processor.get_processing_summary(result)
    for key, value in summary.items():
        if key != 'processed_data':
            print(f"{key}: {value}")