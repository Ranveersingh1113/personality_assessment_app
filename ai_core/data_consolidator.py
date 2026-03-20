"""
Data Consolidation System for Personality Assessment

This module provides functionality to consolidate multiple observations for the same student
over time, implementing temporal weighting and conflict resolution while preserving
individual observation data.

Addresses user feedback issue (a): "If a child's data is fed 2 to 3 times, will all their 
observations be considered together?"
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
import numpy as np
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Observation:
    """Individual observation record"""
    observation_id: str
    student_id: str
    student_name: str
    content: str
    timestamp: datetime
    source: str
    assessor: str = "system"
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Assessment:
    """Assessment result from AI processing"""
    assessment_id: str
    student_id: str
    qualities: Dict[str, Dict[str, Any]]  # quality -> {level, reasoning, confidence}
    timestamp: datetime
    source_observations: List[str]  # observation_ids used
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConsolidatedProfile:
    """Consolidated student profile with all observations and assessments"""
    student_id: str
    student_name: str
    school: str
    class_name: str
    observations: List[Observation]
    assessments: List[Assessment]
    consolidated_assessment: Optional[Assessment]
    first_observed: datetime
    last_observed: datetime
    observation_count: int
    assessment_count: int
    data_quality_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Timeline:
    """Timeline of observations and assessments for a student"""
    student_id: str
    events: List[Tuple[datetime, str, str]]  # (timestamp, event_type, event_id)
    date_range: Tuple[datetime, datetime]
    observation_frequency: float  # observations per day
    assessment_frequency: float  # assessments per day

class DataConsolidator:
    """
    Manages consolidation of multiple student observations and assessments over time.
    
    Key features:
    - Temporal weighting (recent observations have higher influence)
    - Conflict resolution when observations contradict
    - Metadata preservation from all source observations
    - Configurable consolidation strategies
    """
    
    def __init__(self, temporal_decay_days: int = 30, min_confidence_threshold: float = 0.3):
        """
        Initialize the data consolidator.
        
        Args:
            temporal_decay_days: Number of days for temporal weight to decay to 50%
            min_confidence_threshold: Minimum confidence score to include in consolidation
        """
        self.temporal_decay_days = temporal_decay_days
        self.min_confidence_threshold = min_confidence_threshold
        self.consolidation_cache = {}  # Cache for performance
        
    def consolidate_student_observations(self, student_id: str, 
                                       observations: List[Observation],
                                       assessments: List[Assessment]) -> ConsolidatedProfile:
        """
        Consolidate all observations and assessments for a single student.
        
        Args:
            student_id: Unique identifier for the student
            observations: List of all observations for this student
            assessments: List of all assessments for this student
            
        Returns:
            ConsolidatedProfile with merged data and consolidated assessment
            
        Raises:
            ValueError: If no observations provided or invalid data
            TypeError: If observations or assessments are not proper types
        """
        if not observations:
            raise ValueError(f"No observations provided for student {student_id}")
        
        if not isinstance(observations, list):
            raise TypeError(f"observations must be a list, got {type(observations)}")
        
        if not isinstance(assessments, list):
            raise TypeError(f"assessments must be a list, got {type(assessments)}")
            
        try:
            # Sort observations and assessments by timestamp
            sorted_observations = sorted(observations, key=lambda x: x.timestamp)
            sorted_assessments = sorted(assessments, key=lambda x: x.timestamp)
        except AttributeError as e:
            raise ValueError(f"Invalid observation or assessment object missing timestamp: {e}")
        
        try:
            # Extract basic student info from first observation
            first_obs = sorted_observations[0]
            student_name = first_obs.student_name
            school = first_obs.metadata.get('school', 'Unknown')
            class_name = first_obs.metadata.get('class', 'Unknown')
        except (AttributeError, KeyError, IndexError) as e:
            raise ValueError(f"Invalid observation data structure: {e}")
        
        # Calculate timeline metrics
        first_observed = sorted_observations[0].timestamp
        last_observed = sorted_observations[-1].timestamp
        observation_count = len(observations)
        assessment_count = len(assessments)
        
        # Calculate data quality score
        try:
            data_quality_score = self._calculate_data_quality_score(
                observations, assessments
            )
        except Exception as e:
            logger.warning(f"Error calculating data quality score: {e}")
            data_quality_score = 0.5  # Default to medium quality
        
        # Generate consolidated assessment if we have assessments
        consolidated_assessment = None
        if assessments:
            try:
                consolidated_assessment = self._generate_consolidated_assessment(
                    student_id, observations, assessments
                )
            except Exception as e:
                logger.error(f"Error generating consolidated assessment: {e}")
                # Continue without consolidated assessment
        
        return ConsolidatedProfile(
            student_id=student_id,
            student_name=student_name,
            school=school,
            class_name=class_name,
            observations=sorted_observations,
            assessments=sorted_assessments,
            consolidated_assessment=consolidated_assessment,
            first_observed=first_observed,
            last_observed=last_observed,
            observation_count=observation_count,
            assessment_count=assessment_count,
            data_quality_score=data_quality_score
        )
    
    def merge_observations(self, observations: List[Observation]) -> str:
        """
        Merge multiple observations into a single consolidated text.
        
        Args:
            observations: List of observations to merge
            
        Returns:
            Consolidated observation text with temporal weighting
            
        Raises:
            ValueError: If observations list is invalid
        """
        if not observations:
            return ""
        
        if not isinstance(observations, list):
            raise ValueError(f"observations must be a list, got {type(observations)}")
            
        if len(observations) == 1:
            return observations[0].content if hasattr(observations[0], 'content') else ""
        
        try:
            # Sort by timestamp (most recent first for weighting)
            sorted_obs = sorted(observations, key=lambda x: x.timestamp, reverse=True)
        except AttributeError as e:
            logger.error(f"Invalid observation missing timestamp: {e}")
            # Fallback: use observations as-is
            sorted_obs = observations
        
        try:
            # Calculate weights based on recency
            weights = self._calculate_temporal_weights(sorted_obs)
        except Exception as e:
            logger.warning(f"Error calculating temporal weights: {e}")
            # Fallback to equal weights
            weights = [1.0 / len(sorted_obs)] * len(sorted_obs)
        
        # Merge observations with weights
        merged_content = []
        for obs, weight in zip(sorted_obs, weights):
            try:
                # Add timestamp and weight info for transparency
                timestamp_str = obs.timestamp.strftime("%Y-%m-%d")
                content = obs.content if hasattr(obs, 'content') else str(obs)
                merged_content.append(
                    f"[{timestamp_str}, weight: {weight:.2f}] {content}"
                )
            except (AttributeError, ValueError) as e:
                logger.warning(f"Error formatting observation: {e}")
                # Skip malformed observations
                continue
        
        return "\n\n".join(merged_content)
    
    def get_observation_timeline(self, student_id: str, 
                               observations: List[Observation],
                               assessments: List[Assessment]) -> Timeline:
        """
        Generate a timeline of all events for a student.
        
        Args:
            student_id: Student identifier
            observations: List of observations
            assessments: List of assessments
            
        Returns:
            Timeline object with chronological events
            
        Raises:
            ValueError: If no events found or invalid data
        """
        if not isinstance(observations, list) or not isinstance(assessments, list):
            raise ValueError("observations and assessments must be lists")
        
        events = []
        
        # Add observation events
        for obs in observations:
            try:
                events.append((obs.timestamp, "observation", obs.observation_id))
            except AttributeError as e:
                logger.warning(f"Skipping invalid observation: {e}")
                continue
            
        # Add assessment events
        for assessment in assessments:
            try:
                events.append((assessment.timestamp, "assessment", assessment.assessment_id))
            except AttributeError as e:
                logger.warning(f"Skipping invalid assessment: {e}")
                continue
        
        # Sort events chronologically
        try:
            events.sort(key=lambda x: x[0])
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid timestamp in events: {e}")
        
        if not events:
            raise ValueError(f"No valid events found for student {student_id}")
        
        # Calculate date range
        date_range = (events[0][0], events[-1][0])
        
        # Calculate frequencies
        try:
            total_days = max(1, (date_range[1] - date_range[0]).days + 1)
            observation_frequency = len(observations) / total_days
            assessment_frequency = len(assessments) / total_days
        except (AttributeError, TypeError) as e:
            logger.warning(f"Error calculating frequencies: {e}")
            observation_frequency = 0.0
            assessment_frequency = 0.0
        
        return Timeline(
            student_id=student_id,
            events=events,
            date_range=date_range,
            observation_frequency=observation_frequency,
            assessment_frequency=assessment_frequency
        )
    
    def calculate_assessment_weights(self, observations: List[Observation]) -> Dict[str, float]:
        """
        Calculate weights for observations based on recency and quality.
        
        Args:
            observations: List of observations to weight
            
        Returns:
            Dictionary mapping observation_id to weight
        """
        if not observations:
            return {}
            
        weights = {}
        temporal_weights = self._calculate_temporal_weights(observations)
        
        for obs, temp_weight in zip(observations, temporal_weights):
            # Start with temporal weight
            final_weight = temp_weight
            
            # Adjust based on content quality (length, detail)
            content_quality = self._assess_content_quality(obs.content)
            final_weight *= content_quality
            
            # Ensure minimum weight
            final_weight = max(0.1, final_weight)
            
            weights[obs.observation_id] = final_weight
            
        return weights
    
    def generate_consolidated_assessment(self, student_id: str,
                                       observations: List[Observation],
                                       assessments: List[Assessment]) -> Assessment:
        """
        Generate a consolidated assessment from multiple individual assessments.
        
        Args:
            student_id: Student identifier
            observations: All observations for the student
            assessments: All assessments for the student
            
        Returns:
            Consolidated Assessment object
        """
        return self._generate_consolidated_assessment(student_id, observations, assessments)
    
    def _generate_consolidated_assessment(self, student_id: str,
                                        observations: List[Observation],
                                        assessments: List[Assessment]) -> Assessment:
        """Internal method to generate consolidated assessment"""
        if not assessments:
            return None
            
        # Calculate temporal weights for assessments
        assessment_weights = self._calculate_temporal_weights(assessments)
        
        # Consolidate qualities across all assessments
        consolidated_qualities = defaultdict(lambda: {
            'levels': [],
            'reasonings': [],
            'confidences': [],
            'weights': []
        })
        
        for assessment, weight in zip(assessments, assessment_weights):
            for quality, details in assessment.qualities.items():
                consolidated_qualities[quality]['levels'].append(details.get('level', 'Unknown'))
                consolidated_qualities[quality]['reasonings'].append(details.get('reasoning', ''))
                consolidated_qualities[quality]['confidences'].append(details.get('confidence', 0.5))
                consolidated_qualities[quality]['weights'].append(weight)
        
        # Generate final consolidated qualities
        final_qualities = {}
        for quality, data in consolidated_qualities.items():
            final_qualities[quality] = self._consolidate_quality_assessments(
                data['levels'], data['reasonings'], data['confidences'], data['weights']
            )
        
        # Create consolidated assessment
        consolidated_assessment = Assessment(
            assessment_id=f"consolidated_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            student_id=student_id,
            qualities=final_qualities,
            timestamp=datetime.now(),
            source_observations=[obs.observation_id for obs in observations],
            metadata={
                'consolidation_method': 'temporal_weighted',
                'source_assessments': [a.assessment_id for a in assessments],
                'total_observations': len(observations),
                'total_assessments': len(assessments),
                'temporal_decay_days': self.temporal_decay_days
            }
        )
        
        return consolidated_assessment
    
    def _calculate_temporal_weights(self, items: List[Any]) -> List[float]:
        """Calculate temporal weights for a list of timestamped items"""
        if not items:
            return []
            
        if len(items) == 1:
            return [1.0]
        
        # Get current time for reference
        now = datetime.now()
        
        # Calculate weights based on recency
        weights = []
        for item in items:
            days_ago = (now - item.timestamp).days
            # Exponential decay: weight = exp(-days_ago / decay_constant)
            decay_constant = self.temporal_decay_days / np.log(2)  # Half-life
            weight = np.exp(-days_ago / decay_constant)
            weights.append(weight)
        
        # Normalize weights to sum to 1
        total_weight = sum(weights)
        
        # Check for division by zero or invalid total weight
        if total_weight <= 0 or pd.isna(total_weight) or np.isnan(total_weight):
            logger.warning(f"Total weight is zero or invalid ({total_weight}), using equal weights as fallback")
            # Fallback to equal weights
            weights = [1.0 / len(items)] * len(items)
        else:
            weights = [w / total_weight for w in weights]
            
        return weights
    
    def _calculate_data_quality_score(self, observations: List[Observation], 
                                    assessments: List[Assessment]) -> float:
        """Calculate overall data quality score for a student"""
        if not observations:
            return 0.0
            
        quality_factors = []
        
        # Factor 1: Observation count (more is better, up to a point)
        obs_count_score = min(1.0, len(observations) / 5.0)  # Optimal around 5 observations
        quality_factors.append(obs_count_score)
        
        # Factor 2: Temporal distribution (spread over time is better)
        if len(observations) > 1:
            time_span = (max(obs.timestamp for obs in observations) - 
                        min(obs.timestamp for obs in observations)).days
            temporal_score = min(1.0, time_span / 30.0)  # Optimal around 30 days
        else:
            temporal_score = 0.5  # Single observation gets medium score
        quality_factors.append(temporal_score)
        
        # Factor 3: Content quality (average length and detail)
        content_scores = [self._assess_content_quality(obs.content) for obs in observations]
        avg_content_score = sum(content_scores) / len(content_scores)
        quality_factors.append(avg_content_score)
        
        # Factor 4: Assessment availability
        assessment_score = 1.0 if assessments else 0.5
        quality_factors.append(assessment_score)
        
        # Calculate weighted average
        return sum(quality_factors) / len(quality_factors)
    
    def _assess_content_quality(self, content: str) -> float:
        """Assess the quality of observation content"""
        if not content or not content.strip():
            return 0.0
            
        # Factor 1: Length (reasonable length is better)
        length_score = min(1.0, len(content.strip()) / 100.0)  # Optimal around 100 chars
        
        # Factor 2: Word count (more descriptive is better)
        word_count = len(content.split())
        word_score = min(1.0, word_count / 20.0)  # Optimal around 20 words
        
        # Factor 3: Sentence structure (multiple sentences suggest detail)
        sentence_count = content.count('.') + content.count('!') + content.count('?')
        sentence_score = min(1.0, sentence_count / 3.0)  # Optimal around 3 sentences
        
        # Weighted average
        return (length_score * 0.4 + word_score * 0.4 + sentence_score * 0.2)
    
    def _consolidate_quality_assessments(self, levels: List[str], reasonings: List[str],
                                       confidences: List[float], weights: List[float]) -> Dict[str, Any]:
        """Consolidate multiple assessments for a single quality"""
        if not levels:
            return {'level': 'Unknown', 'reasoning': '', 'confidence': 0.0}
        
        # Weight the confidence scores
        weighted_confidence = sum(c * w for c, w in zip(confidences, weights))
        
        # For levels, use the most recent high-confidence assessment
        # or the weighted majority if confidence is similar
        level_weights = defaultdict(float)
        for level, weight, confidence in zip(levels, weights, confidences):
            # Weight by both temporal weight and confidence
            combined_weight = weight * confidence
            level_weights[level] += combined_weight
        
        # Select the level with highest combined weight
        best_level = max(level_weights.items(), key=lambda x: x[1])[0]
        
        # Combine reasonings, prioritizing recent and high-confidence ones
        reasoning_parts = []
        for reasoning, weight, confidence in zip(reasonings, weights, confidences):
            if reasoning and reasoning.strip():
                combined_weight = weight * confidence
                if combined_weight > 0.3:  # Only include reasonably weighted reasonings
                    reasoning_parts.append(reasoning.strip())
        
        # Join unique reasonings
        unique_reasonings = []
        for reasoning in reasoning_parts:
            if reasoning not in unique_reasonings:
                unique_reasonings.append(reasoning)
        
        consolidated_reasoning = '; '.join(unique_reasonings[:3])  # Limit to top 3
        
        return {
            'level': best_level,
            'reasoning': consolidated_reasoning,
            'confidence': weighted_confidence
        }