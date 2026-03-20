"""
Property-based tests for Data Consolidation System

These tests verify the correctness properties of the data consolidation system
using property-based testing with Hypothesis.

Feature: personality-assessment-improvements
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
import uuid
from typing import List

from ai_core.data_consolidator import (
    DataConsolidator, Observation, Assessment, ConsolidatedProfile
)

# Test data generation strategies
@st.composite
def observation_strategy(draw, student_id=None, student_name=None):
    """Generate valid Observation objects"""
    if student_id is None:
        student_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    if student_name is None:
        student_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    
    return Observation(
        observation_id=str(uuid.uuid4()),
        student_id=student_id,
        student_name=student_name,
        content=draw(st.text(min_size=10, max_size=500)),
        timestamp=draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 12, 31)
        )),
        source=draw(st.sampled_from(["csv_upload", "manual_entry", "batch_import"])),
        assessor=draw(st.text(min_size=1, max_size=30)),
        session_id=str(uuid.uuid4()),
        metadata=draw(st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.text(), st.integers(), st.floats(allow_nan=False)),
            min_size=0, max_size=5
        ))
    )

@st.composite
def assessment_strategy(draw, student_id=None):
    """Generate valid Assessment objects"""
    if student_id is None:
        student_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    # Generate qualities dictionary
    quality_names = draw(st.lists(
        st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))),
        min_size=1, max_size=8, unique=True
    ))
    
    qualities = {}
    for quality in quality_names:
        qualities[quality] = {
            'level': draw(st.sampled_from(['Low', 'Medium', 'High', 'Very High'])),
            'reasoning': draw(st.text(min_size=0, max_size=200)),
            'confidence': draw(st.floats(min_value=0.0, max_value=1.0))
        }
    
    return Assessment(
        assessment_id=str(uuid.uuid4()),
        student_id=student_id,
        qualities=qualities,
        timestamp=draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 12, 31)
        )),
        source_observations=draw(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10)),
        metadata=draw(st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.text(), st.integers(), st.floats(allow_nan=False)),
            min_size=0, max_size=5
        ))
    )

@st.composite
def student_data_strategy(draw):
    """Generate observations and assessments for a single student"""
    student_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    student_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    
    observations = draw(st.lists(
        observation_strategy(student_id=student_id, student_name=student_name),
        min_size=1, max_size=10
    ))
    
    assessments = draw(st.lists(
        assessment_strategy(student_id=student_id),
        min_size=0, max_size=5
    ))
    
    return student_id, student_name, observations, assessments

class TestDataConsolidationProperties:
    """Property-based tests for data consolidation system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.consolidator = DataConsolidator()
    
    @given(student_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_1_data_consolidation_consistency(self, student_data):
        """
        Property 1: Data Consolidation Consistency
        For any student with multiple observations, consolidating and then 
        re-consolidating should produce the same result.
        
        Feature: personality-assessment-improvements, Property 1: Data Consolidation Consistency
        Validates: Requirements 1.1, 1.3
        """
        student_id, student_name, observations, assessments = student_data
        assume(len(observations) >= 1)  # Need at least one observation
        
        # First consolidation
        profile1 = self.consolidator.consolidate_student_observations(
            student_id, observations, assessments
        )
        
        # Second consolidation with same data
        profile2 = self.consolidator.consolidate_student_observations(
            student_id, observations, assessments
        )
        
        # Results should be consistent
        assert profile1.student_id == profile2.student_id
        assert profile1.student_name == profile2.student_name
        assert profile1.observation_count == profile2.observation_count
        assert profile1.assessment_count == profile2.assessment_count
        assert profile1.first_observed == profile2.first_observed
        assert profile1.last_observed == profile2.last_observed
        
        # Data quality scores should be identical
        assert abs(profile1.data_quality_score - profile2.data_quality_score) < 0.001
        
        # Consolidated assessments should be consistent if they exist
        if profile1.consolidated_assessment and profile2.consolidated_assessment:
            assert len(profile1.consolidated_assessment.qualities) == len(profile2.consolidated_assessment.qualities)
            
            # Check that quality keys are the same
            assert set(profile1.consolidated_assessment.qualities.keys()) == set(profile2.consolidated_assessment.qualities.keys())
    
    @given(student_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_2_observation_preservation(self, student_data):
        """
        Property 2: Observation Preservation
        For any set of individual observations, the consolidated view should 
        preserve all original observation metadata and content.
        
        Feature: personality-assessment-improvements, Property 2: Observation Preservation
        Validates: Requirements 1.4
        """
        student_id, student_name, observations, assessments = student_data
        assume(len(observations) >= 1)  # Need at least one observation
        
        # Consolidate observations
        profile = self.consolidator.consolidate_student_observations(
            student_id, observations, assessments
        )
        
        # All original observations should be preserved
        assert len(profile.observations) == len(observations)
        
        # Check that all observation IDs are preserved
        original_ids = {obs.observation_id for obs in observations}
        consolidated_ids = {obs.observation_id for obs in profile.observations}
        assert original_ids == consolidated_ids
        
        # Check that all observation content is preserved
        original_content = {obs.observation_id: obs.content for obs in observations}
        consolidated_content = {obs.observation_id: obs.content for obs in profile.observations}
        assert original_content == consolidated_content
        
        # Check that all observation timestamps are preserved
        original_timestamps = {obs.observation_id: obs.timestamp for obs in observations}
        consolidated_timestamps = {obs.observation_id: obs.timestamp for obs in profile.observations}
        assert original_timestamps == consolidated_timestamps
        
        # Check that metadata is preserved
        for original_obs in observations:
            consolidated_obs = next(
                obs for obs in profile.observations 
                if obs.observation_id == original_obs.observation_id
            )
            assert consolidated_obs.metadata == original_obs.metadata
    
    @given(st.lists(observation_strategy(), min_size=1, max_size=10))
    @settings(max_examples=100, deadline=None)
    def test_merge_observations_idempotency(self, observations):
        """
        Test that merging observations is idempotent when given the same input.
        """
        # Ensure all observations have the same student_id for valid merging
        student_id = "test_student_123"
        for obs in observations:
            obs.student_id = student_id
            obs.student_name = "Test Student"
        
        # Merge observations twice
        merged1 = self.consolidator.merge_observations(observations)
        merged2 = self.consolidator.merge_observations(observations)
        
        # Results should be identical
        assert merged1 == merged2
    
    @given(student_data_strategy())
    @settings(max_examples=50, deadline=None)
    def test_timeline_generation_completeness(self, student_data):
        """
        Test that timeline generation includes all observations and assessments.
        """
        student_id, student_name, observations, assessments = student_data
        assume(len(observations) >= 1)  # Need at least one observation
        
        # Generate timeline
        timeline = self.consolidator.get_observation_timeline(
            student_id, observations, assessments
        )
        
        # Timeline should include all events
        expected_event_count = len(observations) + len(assessments)
        assert len(timeline.events) == expected_event_count
        
        # Check that all observation IDs are in timeline
        observation_ids_in_timeline = {
            event[2] for event in timeline.events if event[1] == "observation"
        }
        original_observation_ids = {obs.observation_id for obs in observations}
        assert observation_ids_in_timeline == original_observation_ids
        
        # Check that all assessment IDs are in timeline
        assessment_ids_in_timeline = {
            event[2] for event in timeline.events if event[1] == "assessment"
        }
        original_assessment_ids = {assess.assessment_id for assess in assessments}
        assert assessment_ids_in_timeline == original_assessment_ids
    
    @given(st.lists(observation_strategy(), min_size=1, max_size=10))
    @settings(max_examples=50, deadline=None)
    def test_weight_calculation_properties(self, observations):
        """
        Test properties of weight calculation for observations.
        """
        # Ensure all observations have the same student_id
        student_id = "test_student_123"
        for obs in observations:
            obs.student_id = student_id
            obs.student_name = "Test Student"
        
        # Calculate weights
        weights = self.consolidator.calculate_assessment_weights(observations)
        
        # All observations should have weights
        assert len(weights) == len(observations)
        
        # All weights should be positive
        for weight in weights.values():
            assert weight > 0
        
        # Weights should be reasonable (not too extreme)
        for weight in weights.values():
            assert 0.01 <= weight <= 10.0  # Reasonable bounds
    
    @given(student_data_strategy())
    @settings(max_examples=50, deadline=None)
    def test_data_quality_score_bounds(self, student_data):
        """
        Test that data quality scores are within expected bounds.
        """
        student_id, student_name, observations, assessments = student_data
        assume(len(observations) >= 1)  # Need at least one observation
        
        # Consolidate observations
        profile = self.consolidator.consolidate_student_observations(
            student_id, observations, assessments
        )
        
        # Data quality score should be between 0 and 1
        assert 0.0 <= profile.data_quality_score <= 1.0
    
    @given(student_data_strategy())
    @settings(max_examples=50, deadline=None)
    def test_consolidated_assessment_generation(self, student_data):
        """
        Test properties of consolidated assessment generation.
        """
        student_id, student_name, observations, assessments = student_data
        assume(len(observations) >= 1)  # Need at least one observation
        assume(len(assessments) >= 1)  # Need at least one assessment
        
        # Consolidate observations
        profile = self.consolidator.consolidate_student_observations(
            student_id, observations, assessments
        )
        
        # Should have a consolidated assessment if assessments were provided
        assert profile.consolidated_assessment is not None
        
        # Consolidated assessment should reference all source observations
        expected_obs_ids = {obs.observation_id for obs in observations}
        actual_obs_ids = set(profile.consolidated_assessment.source_observations)
        assert expected_obs_ids == actual_obs_ids
        
        # Consolidated assessment should have metadata about the consolidation
        metadata = profile.consolidated_assessment.metadata
        assert 'consolidation_method' in metadata
        assert 'source_assessments' in metadata
        assert 'total_observations' in metadata
        assert 'total_assessments' in metadata
        
        # Metadata counts should match actual counts
        assert metadata['total_observations'] == len(observations)
        assert metadata['total_assessments'] == len(assessments)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])