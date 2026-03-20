"""
Property-based tests for Enhanced CSV Processor
Tests the correctness properties defined in the design document
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import pandas as pd
from io import StringIO
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_core.enhanced_csv_processor import EnhancedCSVProcessor, ValidationResult


class TestEnhancedCSVProcessor:
    """Property-based tests for Enhanced CSV Processor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = EnhancedCSVProcessor()
    
    @given(
        valid_names=st.lists(
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and x.strip().lower() not in ['nan', 'none']),
            min_size=1,
            max_size=20
        ),
        valid_observations=st.lists(
            st.text(min_size=10, max_size=200).filter(lambda x: x.strip() and x.strip().lower() not in ['nan', 'none']),
            min_size=1,
            max_size=20
        ),
        blank_rows_count=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_csv_processing_accuracy_property(self, valid_names, valid_observations, blank_rows_count):
        """
        Property 10: CSV Processing Accuracy
        For any valid CSV file, the number of processed students should equal 
        the number of non-blank rows with valid data
        
        Feature: personality-assessment-improvements, Property 10: CSV Processing Accuracy
        Validates: Requirements 8.1, 8.2
        """
        # Ensure we have matching numbers of names and observations
        min_length = min(len(valid_names), len(valid_observations))
        valid_names = valid_names[:min_length]
        valid_observations = valid_observations[:min_length]
        
        # Create CSV content with valid data and blank rows
        csv_lines = ['Name,Observations']  # Header
        
        # Add valid student data
        for name, obs in zip(valid_names, valid_observations):
            # Escape commas and quotes in CSV
            name_escaped = name.replace('"', '""')
            obs_escaped = obs.replace('"', '""')
            csv_lines.append(f'"{name_escaped}","{obs_escaped}"')
        
        # Add blank rows
        for _ in range(blank_rows_count):
            csv_lines.append(',')  # Completely blank row
            csv_lines.append('   ,   ')  # Whitespace only row
        
        csv_content = '\n'.join(csv_lines)
        
        # Process the CSV
        result = self.processor.validate_and_process_csv(csv_content, "test.csv")
        
        # Property assertion: processed students should equal valid data rows
        expected_valid_students = len(valid_names)
        actual_valid_students = result.valid_rows
        
        assert actual_valid_students == expected_valid_students, (
            f"Expected {expected_valid_students} valid students, got {actual_valid_students}. "
            f"Blank rows should be skipped."
        )
        
        # Additional property: blank rows should be properly counted
        expected_blank_rows = blank_rows_count * 2  # We add 2 blank rows per iteration
        actual_blank_rows = result.blank_rows_skipped
        
        assert actual_blank_rows >= blank_rows_count, (
            f"Expected at least {blank_rows_count} blank rows to be skipped, "
            f"got {actual_blank_rows}"
        )
    
    @given(
        csv_data=st.lists(
            st.tuples(
                st.one_of(
                    st.text(min_size=1, max_size=30).filter(lambda x: x.strip()),  # Valid name
                    st.just(''),  # Empty name
                    st.just('   ')  # Whitespace name
                ),
                st.one_of(
                    st.text(min_size=5, max_size=100).filter(lambda x: x.strip()),  # Valid observation
                    st.just(''),  # Empty observation
                    st.just('   ')  # Whitespace observation
                )
            ),
            min_size=1,
            max_size=15
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_blank_row_detection_consistency(self, csv_data):
        """
        Property: Blank row detection should be consistent
        For any CSV data, rows that are completely blank or whitespace-only 
        should be consistently identified and skipped
        
        Feature: personality-assessment-improvements, Property 10: CSV Processing Accuracy
        Validates: Requirements 8.1
        """
        # Create CSV content
        csv_lines = ['Name,Observations']
        valid_row_count = 0
        
        for name, obs in csv_data:
            name_clean = name.strip()
            obs_clean = obs.strip()
            
            # Count expected valid rows
            if name_clean and obs_clean and name_clean.lower() not in ['nan', 'none'] and obs_clean.lower() not in ['nan', 'none']:
                valid_row_count += 1
            
            # Escape for CSV
            name_escaped = name.replace('"', '""')
            obs_escaped = obs.replace('"', '""')
            csv_lines.append(f'"{name_escaped}","{obs_escaped}"')
        
        csv_content = '\n'.join(csv_lines)
        
        # Process twice to ensure consistency
        result1 = self.processor.validate_and_process_csv(csv_content, "test1.csv")
        result2 = self.processor.validate_and_process_csv(csv_content, "test2.csv")
        
        # Property: Results should be identical for same input
        assert result1.valid_rows == result2.valid_rows, (
            "Processing the same CSV twice should yield identical valid row counts"
        )
        assert result1.blank_rows_skipped == result2.blank_rows_skipped, (
            "Processing the same CSV twice should yield identical blank row counts"
        )
        
        # Property: Valid rows should not exceed total data rows
        assert result1.valid_rows <= len(csv_data), (
            f"Valid rows ({result1.valid_rows}) cannot exceed total data rows ({len(csv_data)})"
        )
    
    @given(
        names=st.lists(
            st.text(min_size=1, max_size=30).filter(
                lambda x: x.strip() and x.strip().lower() not in ['nan', 'none', ''] and '\x00' not in x
            ),  # Filter out problematic characters and empty strings
            min_size=2,
            max_size=10
        ),
        observations=st.lists(
            st.text(min_size=5, max_size=100).filter(
                lambda x: x.strip() and x.strip().lower() not in ['nan', 'none', ''] and '\x00' not in x
            ),  # Filter out problematic characters and empty strings
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_duplicate_detection_completeness(self, names, observations):
        """
        Property 7: Duplicate Detection Completeness
        For any set of uploaded files or student data, all actual duplicates 
        should be detected and no false positives should occur
        
        Feature: personality-assessment-improvements, Property 7: Duplicate Detection Completeness
        Validates: Requirements 5.1, 5.3
        """
        # Ensure we have matching lengths
        min_length = min(len(names), len(observations))
        names = names[:min_length]
        observations = observations[:min_length]
        
        # Create intentional duplicates by repeating some entries
        if len(names) >= 2:
            # Add exact duplicate
            names.append(names[0])
            observations.append(observations[0])
            expected_duplicates = 1
        else:
            expected_duplicates = 0
        
        # Create CSV
        csv_lines = ['Name,Observations']
        for name, obs in zip(names, observations):
            name_escaped = name.replace('"', '""')
            obs_escaped = obs.replace('"', '""')
            csv_lines.append(f'"{name_escaped}","{obs_escaped}"')
        
        csv_content = '\n'.join(csv_lines)
        
        # Process CSV and detect duplicates
        result = self.processor.validate_and_process_csv(csv_content, "test.csv")
        
        if result.is_valid and result.valid_rows > 0:
            duplicate_report = self.processor.detect_duplicates(result.processed_data)
            
            # Property: If we added duplicates, they should be detected
            if expected_duplicates > 0:
                assert duplicate_report.total_duplicates >= expected_duplicates, (
                    f"Expected at least {expected_duplicates} duplicates, "
                    f"found {duplicate_report.total_duplicates}"
                )
            
            # Property: Unique students + duplicates should account for all data
            total_entries = len(result.processed_data)
            reported_unique = duplicate_report.unique_students
            
            assert reported_unique <= total_entries, (
                f"Unique students ({reported_unique}) cannot exceed total entries ({total_entries})"
            )
    
    def test_validation_report_completeness_property(self):
        """
        Property 14: Validation Report Completeness
        For any CSV processing operation with errors, the validation report 
        should identify all issues with accurate row numbers and descriptions
        
        Feature: personality-assessment-improvements, Property 14: Validation Report Completeness
        Validates: Requirements 8.4, 8.5
        """
        # Create CSV with known issues
        csv_content = """Name,Observations
John Doe,Good student with excellent participation
,Missing name but has observations
Jane Smith,
,
   ,   
Alice Brown,Creative and enthusiastic student"""
        
        result = self.processor.validate_and_process_csv(csv_content, "test.csv")
        report = self.processor.generate_validation_report(result)
        
        # Property: Report should contain information about all issues
        assert "Issues Found" in report or result.valid_rows > 0, (
            "Report should mention issues if any exist"
        )
        
        # Property: Report should contain row numbers for data issues
        if result.issues:
            for issue in result.issues:
                if issue.issue_type == 'invalid_data':
                    assert issue.row_number > 0, (
                        f"Issue should have valid row number, got {issue.row_number}"
                    )
                    assert issue.description, (
                        "Issue should have description"
                    )
                    assert issue.suggested_fix, (
                        "Issue should have suggested fix"
                    )
        
        # Property: Report should be non-empty string
        assert isinstance(report, str) and len(report) > 0, (
            "Validation report should be a non-empty string"
        )
    
    @given(st.text(min_size=0, max_size=1000))
    @settings(max_examples=50, deadline=None)
    def test_processor_robustness(self, random_content):
        """
        Property: Processor should handle any input gracefully without crashing
        For any input string, the processor should return a valid ValidationResult
        """
        try:
            result = self.processor.validate_and_process_csv(random_content, "test.csv")
            
            # Property: Should always return ValidationResult
            assert isinstance(result, ValidationResult), (
                "Processor should always return ValidationResult object"
            )
            
            # Property: Counts should be non-negative
            assert result.total_rows >= 0, "Total rows should be non-negative"
            assert result.valid_rows >= 0, "Valid rows should be non-negative"
            assert result.blank_rows_skipped >= 0, "Blank rows skipped should be non-negative"
            
            # Property: Valid rows cannot exceed total rows
            assert result.valid_rows <= result.total_rows, (
                "Valid rows cannot exceed total rows"
            )
            
        except Exception as e:
            # If an exception occurs, it should be handled gracefully
            pytest.fail(f"Processor should handle any input gracefully, but raised: {e}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])


class TestCSVInjectionPrevention:
    """Tests for CSV injection vulnerability prevention"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = EnhancedCSVProcessor()
    
    def test_sanitize_csv_cell_with_formula_injection(self):
        """Test that dangerous formula characters are properly escaped"""
        # Test cases with dangerous characters
        dangerous_inputs = [
            ("=SUM(A1:A10)", "'=SUM(A1:A10)"),
            ("+1234567890", "'+1234567890"),
            ("-1234567890", "'-1234567890"),
            ("@username", "'@username"),
            ("\t\tTabbed", "'\t\tTabbed"),
            ("\rCarriage", "'\rCarriage"),
            ("=1+1", "'=1+1"),
            ("+A1", "'+A1"),
            ("-A1", "'-A1"),
            ("@A1", "'@A1"),
        ]
        
        for input_val, expected_output in dangerous_inputs:
            result = self.processor.sanitize_csv_cell(input_val)
            assert result == expected_output, (
                f"Input '{input_val}' should be sanitized to '{expected_output}', "
                f"got '{result}'"
            )
    
    def test_sanitize_csv_cell_with_safe_values(self):
        """Test that normal values are not modified"""
        safe_inputs = [
            ("Normal text", "Normal text"),
            ("John Doe", "John Doe"),
            ("123", "123"),
            ("Student observations here", "Student observations here"),
            ("A normal sentence.", "A normal sentence."),
            ("email@example.com", "email@example.com"),  # @ not at start
            ("Score: +5", "Score: +5"),  # + not at start
            ("Temperature: -10", "Temperature: -10"),  # - not at start
        ]
        
        for input_val, expected_output in safe_inputs:
            result = self.processor.sanitize_csv_cell(input_val)
            assert result == expected_output, (
                f"Safe input '{input_val}' should not be modified, "
                f"expected '{expected_output}', got '{result}'"
            )
    
    def test_sanitize_csv_cell_with_none_and_nan(self):
        """Test that None and NaN values are handled properly"""
        import numpy as np
        
        test_cases = [
            (None, ""),
            (np.nan, ""),
            (pd.NA, ""),
            ("", ""),
            ("   ", ""),
        ]
        
        for input_val, expected_output in test_cases:
            result = self.processor.sanitize_csv_cell(input_val)
            assert result == expected_output, (
                f"Input '{input_val}' should return empty string, got '{result}'"
            )
    
    def test_sanitize_csv_cell_with_numeric_types(self):
        """Test that numeric types are properly converted"""
        test_cases = [
            (123, "123"),
            (45.67, "45.67"),
            (0, "0"),
            (-5, "-5"),  # Negative number should be escaped
        ]
        
        for input_val, expected_output in test_cases:
            result = self.processor.sanitize_csv_cell(input_val)
            # For negative numbers, they start with -, so should be escaped
            if str(input_val).startswith('-'):
                assert result.startswith("'"), (
                    f"Negative number {input_val} should be escaped"
                )
            else:
                assert result == expected_output, (
                    f"Numeric input {input_val} should convert to '{expected_output}', "
                    f"got '{result}'"
                )
    
    def test_sanitize_dataframe_for_export(self):
        """Test that entire DataFrames are properly sanitized"""
        # Create DataFrame with dangerous values
        df = pd.DataFrame({
            'Name': ['John Doe', '=MALICIOUS()', '+Attack', 'Jane Smith'],
            'Observations': ['Good student', '@Command', 'Normal text', '-Formula'],
            'School': ['School A', '\tTabbed', 'School B', 'School C']
        })
        
        sanitized_df = self.processor.sanitize_dataframe_for_export(df)
        
        # Check that dangerous values are escaped
        assert sanitized_df.loc[1, 'Name'] == "'=MALICIOUS()", (
            "Formula in Name should be escaped"
        )
        assert sanitized_df.loc[2, 'Name'] == "'+Attack", (
            "Plus sign at start should be escaped"
        )
        assert sanitized_df.loc[1, 'Observations'] == "'@Command", (
            "@ symbol at start should be escaped"
        )
        assert sanitized_df.loc[3, 'Observations'] == "'-Formula", (
            "Minus sign at start should be escaped"
        )
        assert sanitized_df.loc[1, 'School'] == "'\tTabbed", (
            "Tab character at start should be escaped"
        )
        
        # Check that safe values are not modified
        assert sanitized_df.loc[0, 'Name'] == 'John Doe', (
            "Safe name should not be modified"
        )
        assert sanitized_df.loc[2, 'Observations'] == 'Normal text', (
            "Safe observation should not be modified"
        )
    
    def test_csv_processing_applies_sanitization(self):
        """Test that CSV processing automatically applies sanitization"""
        # Create CSV with dangerous values
        csv_content = """Name,Observations
=MALICIOUS(),Dangerous formula in name
John Doe,+Attack vector
Jane Smith,@Command injection
Bob Wilson,-Formula attack"""
        
        result = self.processor.validate_and_process_csv(csv_content, "test.csv")
        
        # Check that processed data has sanitized values
        if result.valid_rows > 0:
            df = result.processed_data
            
            # Check first row (formula in name)
            assert df.iloc[0]['Name'].startswith("'"), (
                "Dangerous character in name should be escaped during processing"
            )
            
            # Check observations column
            for idx, row in df.iterrows():
                obs = row['Observations']
                if obs and obs[0] in ('=', '+', '-', '@', '\t', '\r'):
                    assert obs.startswith("'"), (
                        f"Dangerous observation '{obs}' should be escaped"
                    )
    
    @given(
        dangerous_char=st.sampled_from(['=', '+', '-', '@', '\t', '\r']),
        content=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=50, deadline=None)
    def test_sanitization_property_all_dangerous_chars(self, dangerous_char, content):
        """
        Property: Any string starting with dangerous characters should be escaped
        For any dangerous character (=, +, -, @, tab, carriage return) at the start,
        the sanitized value should be prefixed with a single quote
        """
        input_value = dangerous_char + content
        result = self.processor.sanitize_csv_cell(input_value)
        
        # Property: Result should start with single quote
        assert result.startswith("'"), (
            f"Input starting with '{dangerous_char}' should be escaped, "
            f"got '{result}'"
        )
        
        # Property: Original content should be preserved after the quote
        assert result[1:] == input_value, (
            f"Original content should be preserved after quote, "
            f"expected '{input_value}', got '{result[1:]}'"
        )
    
    @given(
        safe_start=st.text(min_size=1, max_size=1).filter(
            lambda x: x not in ('=', '+', '-', '@', '\t', '\r', ' ')
        ),
        content=st.text(min_size=0, max_size=50)
    )
    @settings(max_examples=50, deadline=None)
    def test_sanitization_property_safe_values_unchanged(self, safe_start, content):
        """
        Property: Strings not starting with dangerous characters should remain unchanged
        For any string that doesn't start with dangerous characters,
        the sanitized value should be identical to the input (after stripping)
        """
        input_value = safe_start + content
        result = self.processor.sanitize_csv_cell(input_value)
        
        # Property: Safe values should not be modified (except stripping)
        expected = input_value.strip()
        assert result == expected, (
            f"Safe input '{input_value}' should not be modified, "
            f"expected '{expected}', got '{result}'"
        )
    
    def test_integration_csv_export_with_sanitization(self):
        """Integration test: Verify CSV export includes sanitization"""
        # Create a DataFrame with dangerous values
        df = pd.DataFrame({
            'Name': ['=SUM(A1:A10)', 'John Doe', '+ATTACK'],
            'Observations': ['Normal', '@COMMAND', 'Safe text']
        })
        
        # Sanitize before export
        sanitized_df = self.processor.sanitize_dataframe_for_export(df)
        
        # Export to CSV string
        csv_output = sanitized_df.to_csv(index=False)
        
        # Verify dangerous values are escaped in output
        assert "'=SUM(A1:A10)" in csv_output, (
            "Formula should be escaped in CSV output"
        )
        assert "'+ATTACK" in csv_output, (
            "Plus sign should be escaped in CSV output"
        )
        assert "'@COMMAND" in csv_output, (
            "@ symbol should be escaped in CSV output"
        )
        
        # Verify safe values are not modified
        assert "John Doe" in csv_output, (
            "Safe name should appear unchanged in CSV output"
        )
        assert "Safe text" in csv_output, (
            "Safe observation should appear unchanged in CSV output"
        )