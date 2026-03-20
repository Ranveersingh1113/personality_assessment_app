"""
Property Tests for School-wise Data Organization (Task 4)

Tests:
- Property 3: Count Accuracy (Task 4.1)
- Property 4: Search Result Consistency (Task 4.2)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_core.assessment_storage_manager import AssessmentStorageManager
from ai_core.data_consolidator import DataConsolidator


# Strategy for generating student data
@st.composite
def student_data(draw):
    """Generate realistic student data"""
    # Generate name with letters and spaces
    first_name = draw(st.text(min_size=2, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    last_name = draw(st.text(min_size=2, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    name = f"{first_name} {last_name}".strip()
    
    school = draw(st.sampled_from(['School A', 'School B', 'School C']))
    class_name = draw(st.sampled_from(['5A', '5B', '6A', '6B']))
    observations = draw(st.text(min_size=10, max_size=200))
    date = draw(st.dates(min_value=datetime(2024, 1, 1).date(), max_value=datetime(2026, 12, 31).date()))
    
    return {
        'name': name,
        'school': school,
        'class': class_name,
        'observations': observations,
        'date': date.strftime('%Y-%m-%d')
    }


class TestCountAccuracy:
    """
    Property 3: Count Accuracy
    
    Validates Requirements 2.2, 3.2, 8.3:
    - Student counts match actual data
    - Observation counts are accurate
    - School/class counts are correct
    """
    
    @given(st.lists(student_data(), min_size=1, max_size=50))
    @settings(max_examples=20, deadline=None)
    def test_student_count_accuracy(self, students):
        """Property: Total student count equals unique student names"""
        assume(len(students) > 0)
        
        # Get unique student names
        unique_names = set(s['name'] for s in students if s['name'])
        expected_count = len(unique_names)
        
        # Simulate storage
        storage = AssessmentStorageManager()
        
        # Add students
        for student in students:
            if student['name']:
                try:
                    storage.add_assessment(
                        student['name'],
                        f"[School: {student['school']}] [Class: {student['class']}]\n{student['observations']}",
                        {'test': 'data'},
                        student['date']
                    )
                except:
                    pass  # Skip duplicates
        
        # Get all students
        all_students = storage.get_all_students()
        actual_count = len(all_students)
        
        # Property: Count should match
        assert actual_count == expected_count, \
            f"Student count mismatch: expected {expected_count}, got {actual_count}"
    
    @given(st.lists(student_data(), min_size=1, max_size=30))
    @settings(max_examples=15, deadline=None)
    def test_school_count_accuracy(self, students):
        """Property: School count equals unique schools in data"""
        assume(len(students) > 0)
        
        # Get unique schools
        unique_schools = set(s['school'] for s in students)
        expected_school_count = len(unique_schools)
        
        # Simulate storage and get profiles
        storage = AssessmentStorageManager()
        
        for student in students:
            if student['name']:
                try:
                    storage.add_assessment(
                        student['name'],
                        f"[School: {student['school']}] [Class: {student['class']}]\n{student['observations']}",
                        {'test': 'data'},
                        student['date']
                    )
                except:
                    pass
        
        # Get profiles and extract schools
        profiles = storage.get_all_consolidated_profiles()
        actual_schools = set(p.school for p in profiles if p.school != 'Unknown')
        actual_school_count = len(actual_schools)
        
        # Property: School count should match
        assert actual_school_count == expected_school_count, \
            f"School count mismatch: expected {expected_school_count}, got {actual_school_count}"
    
    @given(st.lists(student_data(), min_size=1, max_size=30))
    @settings(max_examples=15, deadline=None)
    def test_observation_count_per_student(self, students):
        """Property: Each student's observation count equals number of assessments"""
        assume(len(students) > 0)
        
        # Group by student name
        student_obs_count = {}
        for student in students:
            name = student['name']
            if name:
                student_obs_count[name] = student_obs_count.get(name, 0) + 1
        
        # Simulate storage
        storage = AssessmentStorageManager()
        
        for student in students:
            if student['name']:
                try:
                    storage.add_assessment(
                        student['name'],
                        f"[School: {student['school']}] [Class: {student['class']}]\n{student['observations']}",
                        {'test': 'data'},
                        student['date']
                    )
                except:
                    pass
        
        # Check each student's observation count
        for name, expected_count in student_obs_count.items():
            profile = storage.get_consolidated_student_profile(name)
            if profile:
                actual_count = profile.observation_count
                
                # Property: Observation count should match
                assert actual_count == expected_count, \
                    f"Observation count for {name}: expected {expected_count}, got {actual_count}"


class TestSearchResultConsistency:
    """
    Property 4: Search Result Consistency
    
    Validates Requirement 2.3:
    - Search results are consistent
    - Filters work correctly
    - No data loss in search
    """
    
    @given(
        st.lists(student_data(), min_size=5, max_size=20),
        st.sampled_from(['School A', 'School B', 'School C'])
    )
    @settings(max_examples=15, deadline=None)
    def test_school_filter_consistency(self, students, target_school):
        """Property: Filtering by school returns only students from that school"""
        assume(len(students) > 0)
        
        # Simulate storage
        storage = AssessmentStorageManager()
        
        for student in students:
            if student['name']:
                try:
                    storage.add_assessment(
                        student['name'],
                        f"[School: {student['school']}] [Class: {student['class']}]\n{student['observations']}",
                        {'test': 'data'},
                        student['date']
                    )
                except:
                    pass
        
        # Get all profiles
        all_profiles = storage.get_all_consolidated_profiles()
        
        # Filter by school
        filtered_profiles = [p for p in all_profiles if p.school == target_school]
        
        # Property: All filtered profiles should be from target school
        for profile in filtered_profiles:
            assert profile.school == target_school, \
                f"Profile {profile.student_name} has school {profile.school}, expected {target_school}"
        
        # Property: Count should match expected
        expected_count = len([s for s in students if s['school'] == target_school and s['name']])
        # Account for duplicates (same student, same date)
        unique_students = set()
        for s in students:
            if s['school'] == target_school and s['name']:
                unique_students.add(s['name'])
        expected_unique = len(unique_students)
        
        actual_count = len(filtered_profiles)
        
        assert actual_count == expected_unique, \
            f"Filtered count mismatch for {target_school}: expected {expected_unique}, got {actual_count}"
    
    @given(st.lists(student_data(), min_size=5, max_size=20))
    @settings(max_examples=15, deadline=None)
    def test_search_completeness(self, students):
        """Property: Searching for a student name returns that student"""
        assume(len(students) > 0)
        
        # Pick a student to search for
        target_student = students[0]
        assume(target_student['name'])
        
        # Simulate storage
        storage = AssessmentStorageManager()
        
        for student in students:
            if student['name']:
                try:
                    storage.add_assessment(
                        student['name'],
                        f"[School: {student['school']}] [Class: {student['class']}]\n{student['observations']}",
                        {'test': 'data'},
                        student['date']
                    )
                except:
                    pass
        
        # Search for target student
        profile = storage.get_consolidated_student_profile(target_student['name'])
        
        # Property: Should find the student
        assert profile is not None, \
            f"Could not find student {target_student['name']} after adding to storage"
        
        # Property: Name should match
        assert profile.student_name == target_student['name'], \
            f"Found student name {profile.student_name}, expected {target_student['name']}"
    
    @given(st.lists(student_data(), min_size=3, max_size=15))
    @settings(max_examples=10, deadline=None)
    def test_no_data_loss_in_filtering(self, students):
        """Property: Sum of filtered results equals total when filtering by all schools"""
        assume(len(students) > 0)
        
        # Simulate storage
        storage = AssessmentStorageManager()
        
        unique_students = set()
        for student in students:
            if student['name']:
                unique_students.add(student['name'])
                try:
                    storage.add_assessment(
                        student['name'],
                        f"[School: {student['school']}] [Class: {student['class']}]\n{student['observations']}",
                        {'test': 'data'},
                        student['date']
                    )
                except:
                    pass
        
        # Get all profiles
        all_profiles = storage.get_all_consolidated_profiles()
        total_count = len(all_profiles)
        
        # Get unique schools
        schools = set(p.school for p in all_profiles if p.school != 'Unknown')
        
        # Filter by each school and sum
        filtered_sum = 0
        for school in schools:
            school_profiles = [p for p in all_profiles if p.school == school]
            filtered_sum += len(school_profiles)
        
        # Property: Sum of filtered should equal total
        assert filtered_sum == total_count, \
            f"Data loss in filtering: total {total_count}, filtered sum {filtered_sum}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
