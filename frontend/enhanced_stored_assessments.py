"""
Enhanced Stored Assessments Interface with School-wise Organization

This module implements Task 4 requirements:
- 2.1: Hierarchical organization by school/class
- 2.2: Detailed breakdowns and statistics  
- 2.3: Search and filter functionality
- 2.4: Summary metrics per school
- 2.5: User-friendly navigation
- 2.6: Power BI-like visualization dashboard
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import re
from collections import defaultdict

# Import visualization dashboard
try:
    from .analytics_visualizations import AnalyticsVisualizationDashboard
    VISUALIZATIONS_AVAILABLE = True
except ImportError:
    VISUALIZATIONS_AVAILABLE = False
    st.warning("⚠️ Visualization libraries not available. Install plotly for enhanced charts.")


class EnhancedStoredAssessmentsInterface:
    """Enhanced interface for stored assessments with hierarchical organization"""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        
        # Initialize visualization dashboard if available
        if VISUALIZATIONS_AVAILABLE:
            self.viz_dashboard = AnalyticsVisualizationDashboard(storage_manager)
        else:
            self.viz_dashboard = None
        
    def render_main_interface(self):
        """Render the main enhanced stored assessments interface"""
        # Header with refresh button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("📊 Enhanced Stored Assessments")
        with col2:
            if st.button("🔄 Refresh All Data", help="Reload all assessment data to show latest updates"):
                # Clear cached data and force reload
                if 'cached_profiles' in st.session_state:
                    del st.session_state.cached_profiles
                if 'cached_assessments' in st.session_state:
                    del st.session_state.cached_assessments
                st.session_state.force_refresh_profiles = True
                st.rerun()
        
        # System overview metrics
        self._render_system_overview()
        
        st.markdown("---")
        
        # Main interface tabs
        tab1, tab2, tab3 = st.tabs([
            "🏫 School Hierarchy", 
            "🔍 Search & Filter", 
            "📊 Growth Trends"
        ])
        
        with tab1:
            self._render_school_hierarchy_view()
            
        with tab2:
            self._render_search_filter_view()
            
        with tab3:
            self._render_growth_trends_dashboard()
    
    def _render_system_overview(self):
        """Render system overview with key metrics"""
        try:
            # Get comprehensive system statistics
            stats = self._get_comprehensive_stats()
            
            # Top-level metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("🏫 Schools", stats['total_schools'])
            with col2:
                st.metric("🎓 Classes", stats['total_classes'])
            with col3:
                st.metric("👥 Students", stats['total_students'])
            with col4:
                st.metric("📝 Observations", stats['total_observations'])
            with col5:
                st.metric("📊 Assessments", stats['total_assessments'])
                
        except Exception as e:
            st.error(f"Error loading system overview: {e}")
    
    def _render_school_hierarchy_view(self):
        """Render hierarchical school organization view (Requirement 2.1)"""
        st.subheader("🏫 School-wise Organization")
        st.info("📋 Navigate through schools and classes to view detailed assessment data")
        
        try:
            # Get school hierarchy data
            hierarchy = self._build_school_hierarchy()
            
            if not hierarchy:
                st.info("No assessment data found. Upload some assessments to see the hierarchy.")
                return
            
            # School selection and overview
            schools = sorted(hierarchy.keys())
            
            # School overview cards
            st.markdown("### 📊 School Overview")
            
            # Display schools in expandable cards
            for school_name in schools:
                school_data = hierarchy[school_name]
                
                with st.expander(
                    f"🏫 {school_name} ({school_data['student_count']} students, {school_data['class_count']} classes)",
                    expanded=False
                ):
                    self._render_school_details(school_name, school_data)
            
            # Detailed school selection
            st.markdown("---")
            st.markdown("### 🔍 Detailed School View")
            
            selected_school = st.selectbox(
                "Select school for detailed view:",
                ["-- Select School --"] + schools,
                key="hierarchy_school_select"
            )
            
            if selected_school and selected_school != "-- Select School --":
                self._render_detailed_school_view(selected_school, hierarchy[selected_school])
                
        except Exception as e:
            st.error(f"Error rendering school hierarchy: {e}")
    
    def _render_school_details(self, school_name: str, school_data: Dict):
        """Render detailed information for a specific school"""
        # School metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Students", school_data['student_count'])
        with col2:
            st.metric("🎓 Classes", school_data['class_count'])
        with col3:
            st.metric("📝 Observations", school_data['observation_count'])
        with col4:
            st.metric("📊 Assessments", school_data['assessment_count'])
        
        # Class breakdown
        st.markdown("**📚 Classes:**")
        for class_name, class_data in school_data['classes'].items():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"• **{class_name}**")
            with col2:
                st.write(f"{class_data['student_count']} students")
            with col3:
                st.write(f"{class_data['observation_count']} observations")
        
        # Recent activity
        if school_data.get('recent_assessments'):
            st.markdown("**🕒 Recent Activity:**")
            for assessment in school_data['recent_assessments'][:3]:
                st.write(f"• {assessment['student_name']} - {assessment['date']}")
    
    def _render_detailed_school_view(self, school_name: str, school_data: Dict):
        """Render detailed view for a selected school"""
        st.markdown(f"## 🏫 {school_name} - Detailed View")
        
        # School summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 School Statistics")
            st.write(f"**Total Students:** {school_data['student_count']}")
            st.write(f"**Total Classes:** {school_data['class_count']}")
            st.write(f"**Total Observations:** {school_data['observation_count']}")
            st.write(f"**Total Assessments:** {school_data['assessment_count']}")
            
            # Calculate averages
            avg_obs_per_student = school_data['observation_count'] / max(school_data['student_count'], 1)
            st.write(f"**Avg Observations per Student:** {avg_obs_per_student:.1f}")
        
        with col2:
            st.markdown("### 📅 Activity Timeline")
            if school_data.get('date_range'):
                st.write(f"**First Assessment:** {school_data['date_range']['first']}")
                st.write(f"**Latest Assessment:** {school_data['date_range']['last']}")
                
                # Calculate activity span
                try:
                    first_date = datetime.strptime(school_data['date_range']['first'], '%Y-%m-%d')
                    last_date = datetime.strptime(school_data['date_range']['last'], '%Y-%m-%d')
                    span_days = (last_date - first_date).days
                    st.write(f"**Activity Span:** {span_days} days")
                    
                    # Add interpretation
                    if span_days == 0:
                        st.caption("📅 All assessments on same day")
                    elif span_days <= 7:
                        st.caption("📅 Short-term data collection (1 week)")
                    elif span_days <= 30:
                        st.caption("📅 Medium-term tracking (1 month)")
                    else:
                        st.caption("📅 Long-term developmental tracking (30+ days)")
                        
                except (ValueError, TypeError, AttributeError):
                    # Date parsing failed, skip date range display
                    pass
        
        # Class-wise breakdown
        st.markdown("### 🎓 Class-wise Breakdown")
        
        classes = sorted(school_data['classes'].keys())
        selected_class = st.selectbox(
            "Select class for detailed view:",
            ["-- All Classes --"] + classes,
            key=f"class_select_{school_name}"
        )
        
        if selected_class == "-- All Classes --":
            # Show all classes summary
            class_df = pd.DataFrame([
                {
                    'Class': class_name,
                    'Students': class_data['student_count'],
                    'Observations': class_data['observation_count']
                }
                for class_name, class_data in school_data['classes'].items()
            ])
            st.dataframe(class_df, use_container_width=True)
        else:
            # Show specific class details
            class_data = school_data['classes'][selected_class]
            self._render_class_details(school_name, selected_class, class_data)
    
    def _render_class_details(self, school_name: str, class_name: str, class_data: Dict):
        """Render detailed information for a specific class"""
        st.markdown(f"#### 🎓 {class_name} Details")
        
        # Class metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Students", class_data['student_count'])
        with col2:
            st.metric("📝 Observations", class_data['observation_count'])
        # Removed Avg Obs/Student metric
        
        # Student list
        if class_data.get('students'):
            st.markdown("**👥 Students in this class:**")
            
            # Create student dataframe
            student_data = []
            for student in class_data['students']:
                student_data.append({
                    'Student Name': student['name'],
                    'Observations': student['observation_count'],
                    'Last Assessment': student.get('last_assessment_date', 'N/A')
                })
            
            if student_data:
                student_df = pd.DataFrame(student_data)
                st.dataframe(student_df, use_container_width=True)
                
                # Student selection for detailed view
                student_names = [s['name'] for s in class_data['students']]
                selected_student = st.selectbox(
                    "Select student for detailed view:",
                    ["-- Select Student --"] + student_names,
                    key=f"student_select_{school_name}_{class_name}"
                )
                
                if selected_student and selected_student != "-- Select Student --":
                    self._render_student_consolidated_view(selected_student)
    
    def _render_search_filter_view(self):
        """Render search and filter interface (Requirement 2.3)"""
        st.subheader("🔍 Search & Filter Assessments")
        st.info("📋 Search across all assessment data with advanced filtering options")
        
        # Search controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_term = st.text_input(
                "🔍 Search students, schools, or observations:",
                placeholder="Enter student name, school, or keywords from observations...",
                key="global_search"
            )
        
        with col2:
            search_type = st.selectbox(
                "Search in:",
                ["All Fields", "Student Names", "Schools", "Observations", "Assessment Results"],
                key="search_type"
            )
        
        # Advanced filters
        with st.expander("🎛️ Advanced Filters", expanded=False):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                # School filter
                hierarchy = self._build_school_hierarchy()
                schools = ["All Schools"] + sorted(hierarchy.keys()) if hierarchy else ["All Schools"]
                selected_schools = st.multiselect("🏫 Schools:", schools, default=["All Schools"])
                
                # Class filter
                if "All Schools" not in selected_schools and selected_schools:
                    available_classes = set()
                    for school in selected_schools:
                        if school in hierarchy:
                            available_classes.update(hierarchy[school]['classes'].keys())
                    classes = ["All Classes"] + sorted(available_classes)
                else:
                    classes = ["All Classes"]
                
                selected_classes = st.multiselect("🎓 Classes:", classes, default=["All Classes"])
            
            with filter_col2:
                # Date range filter
                st.markdown("📅 **Date Range:**")
                date_from = st.date_input("From:", key="filter_date_from")
                date_to = st.date_input("To:", key="filter_date_to")
                
                # Observation count filter
                st.markdown("📝 **Observation Count:**")
                min_observations = st.number_input("Minimum observations:", min_value=0, value=0, key="min_obs")
                max_observations = st.number_input("Maximum observations:", min_value=0, value=100, key="max_obs")
            
            with filter_col3:
                # Assessment status filter
                st.markdown("📊 **Assessment Status:**")
                status_options = ["All", "Has Assessments", "No Assessments", "Multiple Assessments"]
                assessment_status = st.selectbox("Status:", status_options, key="assessment_status")
        
        # Perform search - trigger on search term OR filters applied
        has_search_term = search_term and search_term.strip()
        has_filters_applied = any([
            "All Schools" not in selected_schools,
            "All Classes" not in selected_classes,
            min_observations > 0,
            max_observations < 100,
            assessment_status != "All"
        ])
        
        if has_search_term or has_filters_applied:
            # Debug information
            if st.checkbox("🐛 Show search debug info", key="search_debug"):
                st.write(f"**Search Parameters:**")
                st.write(f"- Search term: '{search_term}'")
                st.write(f"- Search type: {search_type}")
                st.write(f"- Schools: {selected_schools}")
                st.write(f"- Classes: {selected_classes}")
                st.write(f"- Has search term: {has_search_term}")
                st.write(f"- Has filters: {has_filters_applied}")
            
            results = self._perform_search(
                search_term=search_term,
                search_type=search_type,
                schools=selected_schools,
                classes=selected_classes,
                date_from=date_from,
                date_to=date_to,
                min_observations=min_observations,
                max_observations=max_observations,
                assessment_status=assessment_status
            )
            
            self._display_search_results(results)
        else:
            st.info("👆 Enter search terms or apply filters to see results")
    
    def _render_analytics_dashboard(self):
        """Render student growth analytics dashboard (Requirement 2.4)"""
        st.subheader("📈 Student Growth Analytics Dashboard")
        st.info("📊 Track individual student personality development and growth over time")
        
        try:
            # School and student selection
            hierarchy = self._build_school_hierarchy()
            
            if not hierarchy:
                st.warning("No assessment data available for analytics")
                return
            
            # School selection
            schools = sorted(hierarchy.keys())
            selected_school = st.selectbox(
                "🏫 Select School for Growth Analysis:",
                schools,
                key="analytics_school_select"
            )
            
            if selected_school:
                school_data = hierarchy[selected_school]
                
                # Class filter (optional)
                classes = ["All Classes"] + sorted(school_data['classes'].keys())
                selected_class = st.selectbox(
                    "🎓 Filter by Class (optional):",
                    classes,
                    key="analytics_class_filter"
                )
                
                # Get students for selected school/class
                students_data = self._get_students_for_analytics(selected_school, selected_class, hierarchy)
                
                if not students_data:
                    st.warning(f"No students with multiple assessments found in {selected_school}")
                    return
                
                # Display school overview
                self._render_school_analytics_overview(selected_school, students_data)
                
                # Student selection for detailed growth analysis
                st.markdown("---")
                st.markdown("### 👤 Individual Student Growth Analysis")
                
                # Filter students with multiple observations for growth tracking
                growth_students = [s for s in students_data if s['observation_count'] > 1]
                
                if growth_students:
                    student_names = [s['name'] for s in growth_students]
                    selected_student = st.selectbox(
                        "Select student for detailed growth analysis:",
                        ["-- Select Student --"] + student_names,
                        key="analytics_student_select"
                    )
                    
                    if selected_student and selected_student != "-- Select Student --":
                        self._render_student_growth_analysis(selected_student)
                else:
                    st.info("No students with multiple observations available for growth analysis")
                    st.info("💡 Students need at least 2 observations over time to track growth")
                
                # Class comparison (if multiple classes)
                if len(school_data['classes']) > 1 and selected_class == "All Classes":
                    st.markdown("---")
                    self._render_class_comparison_analytics(selected_school, school_data)
                
        except Exception as e:
            st.error(f"Error generating analytics dashboard: {e}")
            import traceback
            st.error(traceback.format_exc())
    
    def _get_students_for_analytics(self, selected_school: str, selected_class: str, hierarchy: Dict) -> List[Dict]:
        """Get students data for analytics based on school and class selection"""
        students_data = []
        
        try:
            school_data = hierarchy[selected_school]
            
            if selected_class == "All Classes":
                # Get students from all classes in the school
                for class_name, class_data in school_data['classes'].items():
                    for student in class_data['students']:
                        students_data.append({
                            'name': student['name'],
                            'class': class_name,
                            'observation_count': student['observation_count'],
                            'assessment_count': student['assessment_count'],
                            'last_assessment_date': student['last_assessment_date'],
                            'data_quality_score': student['data_quality_score']
                        })
            else:
                # Get students from specific class
                if selected_class in school_data['classes']:
                    class_data = school_data['classes'][selected_class]
                    for student in class_data['students']:
                        students_data.append({
                            'name': student['name'],
                            'class': selected_class,
                            'observation_count': student['observation_count'],
                            'assessment_count': student['assessment_count'],
                            'last_assessment_date': student['last_assessment_date'],
                            'data_quality_score': student['data_quality_score']
                        })
            
            return students_data
            
        except Exception as e:
            st.error(f"Error getting students for analytics: {e}")
            return []
    
    def _render_school_analytics_overview(self, school_name: str, students_data: List[Dict]):
        """Render analytics overview for the selected school"""
        st.markdown(f"### 🏫 {school_name} - Growth Analytics Overview")
        
        # Calculate school-level metrics
        total_students = len(students_data)
        total_observations = sum(s['observation_count'] for s in students_data)
        total_assessments = sum(s['assessment_count'] for s in students_data)
        
        # Students with growth potential (multiple observations)
        growth_ready_students = [s for s in students_data if s['observation_count'] > 1]
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Students", total_students)
        with col2:
            st.metric("📝 Total Observations", total_observations)
        with col3:
            st.metric("📊 Total Assessments", total_assessments)
        with col4:
            st.metric("📈 Growth Ready", len(growth_ready_students))
        with col3:
            st.metric("📊 Total Assessments", total_assessments)
        with col4:
            st.metric("✅ Avg Quality", f"{avg_quality:.1%}")
        with col5:
            st.metric("📈 Growth Ready", len(growth_ready_students))
        
        # Growth insights
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Student Distribution by Observation Count")
            obs_distribution = defaultdict(int)
            for student in students_data:
                obs_count = student['observation_count']
                if obs_count == 1:
                    obs_distribution['1 observation'] += 1
                elif obs_count <= 3:
                    obs_distribution['2-3 observations'] += 1
                elif obs_count <= 5:
                    obs_distribution['4-5 observations'] += 1
                else:
                    obs_distribution['6+ observations'] += 1
            
            for category, count in obs_distribution.items():
                percentage = (count / total_students) * 100
                st.write(f"• **{category}**: {count} students ({percentage:.1f}%)")
        
        # Growth recommendations
        st.markdown("#### 💡 Growth Analysis Recommendations")
        
        if len(growth_ready_students) == 0:
            st.warning("⚠️ No students have multiple observations for growth tracking")
            st.info("💡 Collect additional observations over time to enable growth analysis")
        elif len(growth_ready_students) < total_students * 0.5:
            st.info(f"📈 {len(growth_ready_students)} of {total_students} students ready for growth analysis")
            st.info("💡 Consider collecting more observations for remaining students")
        else:
            st.success(f"✅ {len(growth_ready_students)} of {total_students} students ready for comprehensive growth analysis")
    
    def _render_student_growth_analysis(self, student_name: str):
        """Render detailed growth analysis for a specific student"""
        st.markdown(f"#### 📈 Growth Analysis: {student_name}")
        
        try:
            # Get student's consolidated profile
            profile = self.storage_manager.get_consolidated_student_profile(student_name)
            
            if not profile:
                st.error(f"Could not find profile for {student_name}")
                return
            
            # Student overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📝 Observations", profile.observation_count)
            with col2:
                st.metric("📊 Assessments", profile.assessment_count)
            with col3:
                span_days = (profile.last_observed - profile.first_observed).days
                st.metric("📅 Tracking Period", f"{span_days} days")
            
            # Timeline of observations
            st.markdown("##### 📅 Observation Timeline")
            
            timeline_data = []
            for obs in profile.observations:
                timeline_data.append({
                    'Date': obs.timestamp.strftime('%Y-%m-%d'),
                    'Content Length': len(obs.content),
                    'Preview': obs.content[:100] + "..." if len(obs.content) > 100 else obs.content
                })
            
            if timeline_data:
                timeline_df = pd.DataFrame(timeline_data)
                st.dataframe(timeline_df, use_container_width=True)
            
            # Growth analysis - compare assessments over time
            if len(profile.assessments) > 1:
                st.markdown("##### 📊 Personality Trait Development Over Time")
                
                # Extract trait progression
                trait_progression = self._analyze_trait_progression(profile.assessments)
                
                if trait_progression:
                    # Display trait changes
                    st.markdown("**🔄 Observed Changes:**")
                    
                    for trait, changes in trait_progression.items():
                        if len(changes) > 1:
                            first_level = changes[0]['level']
                            last_level = changes[-1]['level']
                            
                            if first_level != last_level:
                                # Show progression
                                col1, col2, col3 = st.columns([2, 1, 2])
                                with col1:
                                    st.write(f"**{trait}:**")
                                with col2:
                                    if self._is_improvement(first_level, last_level):
                                        st.write("📈 ↗️")
                                    elif self._is_decline(first_level, last_level):
                                        st.write("📉 ↘️")
                                    else:
                                        st.write("↔️")
                                with col3:
                                    st.write(f"{first_level} → {last_level}")
                
                # Show detailed progression for key traits
                key_traits = ['Leadership', 'Social warmth', 'Self control', 'Creativity', 'Academic achievement']
                available_traits = [trait for trait in key_traits if trait in trait_progression]
                
                if available_traits:
                    st.markdown("##### 🎯 Key Trait Analysis")
                    
                    selected_trait = st.selectbox(
                        "Select trait for detailed analysis:",
                        available_traits,
                        key=f"trait_analysis_{student_name}"
                    )
                    
                    if selected_trait in trait_progression:
                        trait_data = trait_progression[selected_trait]
                        
                        # Show progression chart
                        st.markdown(f"**{selected_trait} Progression:**")
                        
                        for i, assessment in enumerate(trait_data):
                            date = assessment['date']
                            level = assessment['level']
                            reasoning = assessment.get('reasoning', 'No reasoning provided')
                            
                            with st.expander(f"Assessment {i+1} - {date} ({level})", expanded=i == len(trait_data)-1):
                                st.write(f"**Level:** {level}")
                                st.write(f"**Reasoning:** {reasoning}")
            
            else:
                st.info("💡 Multiple assessments needed to track growth over time")
            
            # Growth insights and recommendations
            st.markdown("##### 💡 Growth Insights & Recommendations")
            
            insights = self._generate_student_growth_insights(profile)
            
            for insight in insights:
                if insight['type'] == 'success':
                    st.success(f"✅ {insight['message']}")
                elif insight['type'] == 'warning':
                    st.warning(f"⚠️ {insight['message']}")
                elif insight['type'] == 'info':
                    st.info(f"💡 {insight['message']}")
                    
        except Exception as e:
            st.error(f"Error analyzing student growth: {e}")
            import traceback
            st.error(traceback.format_exc())
    
    def _render_class_comparison_analytics(self, school_name: str, school_data: Dict):
        """Render class comparison analytics for the school"""
        st.markdown("### 🎓 Class Comparison Analytics")
        
        # Prepare class comparison data
        class_comparison = []
        
        for class_name, class_data in school_data['classes'].items():
            students = class_data['students']
            
            if students:
                avg_quality = sum(s['data_quality_score'] for s in students) / len(students)
                avg_observations = sum(s['observation_count'] for s in students) / len(students)
                growth_ready = len([s for s in students if s['observation_count'] > 1])
                
                class_comparison.append({
                    'Class': class_name,
                    'Students': len(students),
                    'Avg Quality': f"{avg_quality:.1%}",
                    'Avg Observations': f"{avg_observations:.1f}",
                    'Growth Ready': growth_ready,
                    'Growth %': f"{(growth_ready/len(students)*100):.1f}%"
                })
        
        if class_comparison:
            # Display comparison table
            comparison_df = pd.DataFrame(class_comparison)
            st.dataframe(comparison_df, use_container_width=True)
            
            # Class insights
            st.markdown("#### 📊 Class Performance Insights")
            
            # Best performing class by quality
            best_quality_class = max(class_comparison, key=lambda x: float(x['Avg Quality'].rstrip('%')))
            st.success(f"🏆 **Highest Data Quality**: {best_quality_class['Class']} ({best_quality_class['Avg Quality']})")
            
            # Most growth-ready class
            best_growth_class = max(class_comparison, key=lambda x: float(x['Growth %'].rstrip('%')))
            st.info(f"📈 **Most Growth-Ready**: {best_growth_class['Class']} ({best_growth_class['Growth %']} of students)")
            
            # Recommendations
            low_quality_classes = [c for c in class_comparison if float(c['Avg Quality'].rstrip('%')) < 60]
            if low_quality_classes:
                st.warning(f"⚠️ **Classes needing attention**: {', '.join([c['Class'] for c in low_quality_classes])}")
                st.info("💡 Consider collecting more detailed observations for these classes")
        else:
            st.info("No class data available for comparison")
    
    def _analyze_trait_progression(self, assessments: List) -> Dict[str, List[Dict]]:
        """Analyze how personality traits have changed over time"""
        trait_progression = defaultdict(list)
        
        # Sort assessments by timestamp
        sorted_assessments = sorted(assessments, key=lambda x: x.timestamp)
        
        for assessment in sorted_assessments:
            date = assessment.timestamp.strftime('%Y-%m-%d')
            
            for trait, details in assessment.qualities.items():
                if trait != 'Unknown' and details.get('level') != 'NOT OBSERVED':
                    trait_progression[trait].append({
                        'date': date,
                        'level': details.get('level', 'Unknown'),
                        'reasoning': details.get('reasoning', ''),
                        'confidence': details.get('confidence', 0.0)
                    })
        
        return dict(trait_progression)
    
    def _is_improvement(self, first_level: str, last_level: str) -> bool:
        """Determine if trait level change represents improvement"""
        level_order = {'LOW': 0, 'MIDDLE': 1, 'HIGH': 2}
        
        # For most traits, HIGH is better than MIDDLE is better than LOW
        # This is a simplified approach - in reality, some traits might have different interpretations
        first_score = level_order.get(first_level, 1)
        last_score = level_order.get(last_level, 1)
        
        return last_score > first_score
    
    def _is_decline(self, first_level: str, last_level: str) -> bool:
        """Determine if trait level change represents decline"""
        level_order = {'LOW': 0, 'MIDDLE': 1, 'HIGH': 2}
        
        first_score = level_order.get(first_level, 1)
        last_score = level_order.get(last_level, 1)
        
        return last_score < first_score
    
    def _generate_student_growth_insights(self, profile) -> List[Dict[str, str]]:
        """Generate insights and recommendations for student growth"""
        insights = []
        
        # Observation frequency insight
        span_days = (profile.last_observed - profile.first_observed).days
        if span_days > 0:
            obs_frequency = profile.observation_count / span_days
            if obs_frequency > 0.2:  # More than 1 observation per 5 days
                insights.append({
                    'type': 'success',
                    'message': f"Excellent observation frequency - {profile.observation_count} observations over {span_days} days"
                })
            elif obs_frequency < 0.1:  # Less than 1 observation per 10 days
                insights.append({
                    'type': 'info',
                    'message': f"Consider more frequent observations - currently {profile.observation_count} over {span_days} days"
                })
        
        # Assessment availability
        if profile.assessment_count > 1:
            insights.append({
                'type': 'success',
                'message': f"Multiple assessments available ({profile.assessment_count}) - enables growth tracking"
            })
        elif profile.assessment_count == 0:
            insights.append({
                'type': 'info',
                'message': "No personality assessments yet - run assessment to establish baseline"
            })
        
        # Growth potential
        if profile.observation_count >= 3 and span_days >= 7:
            insights.append({
                'type': 'success',
                'message': "Excellent foundation for growth analysis - multiple observations over time"
            })
        elif profile.observation_count < 2:
            insights.append({
                'type': 'info',
                'message': "Collect additional observations to enable meaningful growth tracking"
            })
        
        return insights
    
    def _render_growth_trends_dashboard(self):
        """Render simplified growth trends dashboard as main tab"""
        st.subheader("📈 Student Growth Trends Analysis")
        st.info("📊 Track individual student personality development and growth over time")
        
        # Add refresh button to ensure latest data is loaded
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Refresh Data", help="Reload latest assessment data"):
                # Clear any cached data and force reload
                if hasattr(st.session_state, 'cached_profiles'):
                    del st.session_state.cached_profiles
                if hasattr(st.session_state, 'cached_assessments'):
                    del st.session_state.cached_assessments
                st.rerun()
        
        if not VISUALIZATIONS_AVAILABLE:
            st.warning("⚠️ Enhanced visualizations require additional libraries")
            st.info("Install with: `pip install plotly altair matplotlib seaborn` for interactive charts")
            
            # Fallback to basic growth analysis
            try:
                # Use cached profiles
                if 'cached_profiles' not in st.session_state:
                    st.session_state.cached_profiles = self.storage_manager.get_all_consolidated_profiles()
                profiles = st.session_state.cached_profiles
                
                if profiles:
                    self._render_basic_growth_analysis(profiles)
                else:
                    st.info("No data available for growth analysis")
                    st.info("💡 **Tip**: Complete some batch assessments first to see growth trends")
            except Exception as e:
                st.error(f"Error loading growth analysis: {e}")
            return
        
        # Full interactive growth trends dashboard
        try:
            # Use cached profiles
            if 'cached_profiles' not in st.session_state:
                st.session_state.cached_profiles = self.storage_manager.get_all_consolidated_profiles()
            profiles = st.session_state.cached_profiles
            
            if not profiles:
                st.warning("No data available for growth analysis")
                st.info("💡 **Tip**: Complete some batch assessments first to see growth trends")
                return
            
            # School selection for focused analysis
            schools = sorted(list(set(p.school for p in profiles if p.school != 'Unknown')))
            if not schools:
                st.warning("No school data found in assessments")
                return
                
            selected_school = st.selectbox("🏫 Select School for Growth Analysis:", schools, key="growth_school")
            
            school_profiles = [p for p in profiles if p.school == selected_school]
            
            if not school_profiles:
                st.warning(f"No data found for {selected_school}")
                return
            
            # Check if there are students with multiple assessments
            growth_ready_students = [p for p in school_profiles if len(p.assessments) > 1]
            
            if not growth_ready_students:
                st.warning(f"No growth data available for {selected_school}")
                st.info(f"""
                Why? Growth trends require students to have multiple assessments over time.
                
                Current Status for {selected_school}:
                - Total students: {len(school_profiles)}
                - Students with multiple assessments: 0
                
                To see growth trends:
                1. Assess the same students multiple times over different dates
                2. Each student needs at least 2 assessments to track growth
                3. Return to this tab after completing additional assessments
                
                Tip: Try selecting a different school that has historical assessment data.
                """)
                return
            
            # Show growth data availability
            st.success(f"Growth data available for {len(growth_ready_students)} out of {len(school_profiles)} students")
            
            # Add overview description
            with st.expander("Understanding Growth Trends Charts", expanded=False):
                st.markdown("""
                Chart Descriptions
                
                1. Student Growth Timeline
                - What it shows: Tracks the number of HIGH-level personality traits for each student over time
                - How to read: Each line represents one student's journey. Higher points mean more HIGH traits
                - What to look for: Upward trends indicate positive personality development
                - Use case: Identify students showing consistent growth or those needing additional support
                
                2. Student Growth Radar
                - What it shows: Compares a student's first assessment with their latest assessment across all traits
                - How to read: Blue area = first assessment, Red area = latest assessment. Larger red area means growth
                - What to look for: Traits where the red line extends beyond blue show improvement
                - Use case: Understand which specific personality traits have developed for individual students
                
                3. Trait Development Trends
                - What it shows: Average trait levels across all students over time (top 5 most-assessed traits)
                - How to read: Each line represents one personality trait. Y-axis shows Low/Middle/High levels
                - What to look for: Overall trends in trait development across the entire school
                - Use case: Identify which traits are improving school-wide and which need more focus
                """)
            
            # Render interactive growth visualizations
            self.viz_dashboard._render_growth_timeline_chart(school_profiles)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Individual student growth radar
                self.viz_dashboard._render_student_growth_radar(school_profiles)
            
            with col2:
                # Trait development trends
                self.viz_dashboard._render_trait_development_trends(school_profiles)
            
        except Exception as e:
            st.error(f"Error rendering growth trends dashboard: {e}")
            # Fallback to basic analysis
            try:
                # Use cached profiles
                if 'cached_profiles' not in st.session_state:
                    st.session_state.cached_profiles = self.storage_manager.get_all_consolidated_profiles()
                profiles = st.session_state.cached_profiles
                
                if profiles:
                    self._render_basic_growth_analysis(profiles)
            except Exception as fallback_error:
                st.error(f"Fallback growth analysis also failed: {fallback_error}")
    
    def _render_basic_growth_analysis(self, profiles: List):
        """Render basic growth analysis using Streamlit native features"""
        st.markdown("#### 📊 Basic Growth Analysis")
        
        # School selection
        schools = sorted(list(set(p.school for p in profiles if p.school != 'Unknown')))
        selected_school = st.selectbox("🏫 Select School:", schools, key="basic_growth_school")
        
        school_profiles = [p for p in profiles if p.school == selected_school]
        
        if not school_profiles:
            st.warning(f"No students found for {selected_school}")
            return
        
        # Growth-ready students
        growth_students = [p for p in school_profiles if len(p.assessments) > 1]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Total Students", len(school_profiles))
        with col2:
            st.metric("📈 Growth Ready", len(growth_students))
        with col3:
            if len(school_profiles) > 0:
                growth_percentage = (len(growth_students) / len(school_profiles)) * 100
                st.metric("📊 Growth Coverage", f"{growth_percentage:.1f}%")
        
        if not growth_students:
            st.warning(f"No growth data available for {selected_school}")
            st.info(f"""
            Why? Growth trends require students to have multiple assessments over time.
            
            Current Status:
            - All {len(school_profiles)} students have only 1 assessment each
            - Growth tracking needs at least 2 assessments per student
            
            To enable growth tracking:
            1. Assess the same students again on different dates
            2. Upload historical assessment data if available
            3. Return to this tab after completing additional assessments
            
            Tip: Try selecting "Sunrise Primary" to see an example of growth trends.
            """)
            return
        
        # Add chart descriptions
        with st.expander("Understanding Growth Analysis", expanded=False):
            st.markdown("""
            Chart Descriptions
            
            Growth Data Table
            - Shows students with multiple assessments and their improvement metrics
            - Traits Improved: Number of traits that moved from LOW to MIDDLE, MIDDLE to HIGH, or LOW to HIGH
            - Improvement Rate: Percentage of comparable traits that showed improvement
            - Time Span: Days between first and latest assessment
            
            Student Improvement Rates Chart
            - Bar chart showing number of improved traits per student
            - Higher bars indicate more traits have improved
            - Use to identify top performers and students needing support
            """)
        
        if growth_students:
            st.markdown("#### 🎯 Students with Growth Data")
            
            growth_data = []
            for profile in growth_students:
                if len(profile.assessments) >= 2:
                    assessments = sorted(profile.assessments, key=lambda x: x.timestamp)
                    first = assessments[0]
                    last = assessments[-1]
                    
                    # Calculate improvements
                    improvements = 0
                    total_comparable = 0
                    
                    for trait in first.qualities:
                        if (trait in last.qualities and 
                            trait != 'Unknown' and
                            first.qualities[trait].get('level') != 'NOT OBSERVED' and
                            last.qualities[trait].get('level') != 'NOT OBSERVED'):
                            
                            level_scores = {'LOW': 1, 'MIDDLE': 2, 'HIGH': 3}
                            first_score = level_scores.get(first.qualities[trait].get('level'), 0)
                            last_score = level_scores.get(last.qualities[trait].get('level'), 0)
                            
                            if last_score > first_score:
                                improvements += 1
                            total_comparable += 1
                    
                    if total_comparable > 0:
                        improvement_rate = (improvements / total_comparable) * 100
                        time_span = (last.timestamp - first.timestamp).days
                        
                        growth_data.append({
                            'Student': profile.student_name,
                            'Assessments': len(profile.assessments),
                            'Time Span (Days)': time_span,
                            'Traits Improved': improvements,
                            'Total Traits': total_comparable,
                            'Improvement Rate': f"{improvement_rate:.1f}%"
                        })
            
            if growth_data:
                growth_df = pd.DataFrame(growth_data)
                
                # Generate natural language summary
                total_students = len(growth_df)
                avg_improvement_rate = growth_df['Traits Improved'].mean()
                avg_time_span = growth_df['Time Span (Days)'].mean()
                
                top_performer = growth_df.loc[growth_df['Traits Improved'].idxmax()]
                
                st.write("Growth Summary:")
                st.write(f"We have tracked {total_students} students over an average period of {avg_time_span:.0f} days. During this time, students improved in an average of {avg_improvement_rate:.1f} personality traits. The student showing the most growth is {top_performer['Student']}, who improved in {top_performer['Traits Improved']} different personality traits.")
                st.write("")
                
                st.dataframe(growth_df, use_container_width=True)
                
                # Simple bar chart of improvement rates
                st.markdown("#### 📈 Student Improvement Rates")
                st.write("This bar chart shows the number of personality traits that improved for each student. Taller bars indicate students who have shown positive development in more traits.")
                st.write("")
                chart_data = growth_df.set_index('Student')['Traits Improved']
                st.bar_chart(chart_data)
            else:
                st.info("No comparable growth data available")
        else:
            st.info("No students with multiple assessments for growth tracking")
            st.info("💡 Students need at least 2 assessments over time to track growth")
    
    def _get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics with caching and performance optimization"""
        try:
            # Use cached profiles if available
            if 'cached_profiles' not in st.session_state or st.session_state.get('force_refresh_profiles', False):
                with st.spinner("Loading assessment data..."):
                    # Load all profiles (optimized with caching)
                    st.session_state.cached_profiles = self.storage_manager.get_all_consolidated_profiles()
                    st.session_state.force_refresh_profiles = False
            
            profiles = st.session_state.cached_profiles
            
            # Get basic system metadata
            system_meta = self.storage_manager.get_system_metadata()
            
            # Calculate comprehensive statistics
            stats = {
                'total_students': len(profiles),
                'total_observations': sum(p.observation_count for p in profiles),
                'total_assessments': sum(p.assessment_count for p in profiles),
                'total_schools': len(set(p.school for p in profiles if p.school != 'Unknown')),
                'total_classes': len(set(f"{p.school}_{p.class_name}" for p in profiles if p.class_name != 'Unknown')),
                'last_updated_display': self._format_last_updated(system_meta.get('last_updated')),
                'date_range_days': 0
            }
            
            # Calculate date range
            if profiles:
                all_dates = []
                for profile in profiles:
                    all_dates.append(profile.first_observed)
                    all_dates.append(profile.last_observed)
                
                if all_dates:
                    min_date = min(all_dates)
                    max_date = max(all_dates)
                    stats['date_range_days'] = (max_date - min_date).days
            
            return stats
            
        except Exception as e:
            st.error(f"Error calculating comprehensive stats: {e}")
            return {
                'total_students': 0,
                'total_observations': 0,
                'total_assessments': 0,
                'total_schools': 0,
                'total_classes': 0,
                'last_updated_display': 'Unknown',
                'date_range_days': 0
            }
    
    def _build_school_hierarchy(self) -> Dict[str, Any]:
        """Build hierarchical school data structure with caching"""
        try:
            # Use cached profiles
            if 'cached_profiles' not in st.session_state:
                st.session_state.cached_profiles = self.storage_manager.get_all_consolidated_profiles()
            
            profiles = st.session_state.cached_profiles
            
            hierarchy = defaultdict(lambda: {
                'student_count': 0,
                'class_count': 0,
                'observation_count': 0,
                'assessment_count': 0,
                'classes': defaultdict(lambda: {
                    'student_count': 0,
                    'observation_count': 0,
                    'students': []
                }),
                'recent_assessments': [],
                'date_range': {'first': None, 'last': None}
            })
            
            for profile in profiles:
                school = profile.school if profile.school != 'Unknown' else 'Unspecified School'
                class_name = profile.class_name if profile.class_name != 'Unknown' else 'Unspecified Class'
                
                # Update school-level stats
                hierarchy[school]['student_count'] += 1
                hierarchy[school]['observation_count'] += profile.observation_count
                hierarchy[school]['assessment_count'] += profile.assessment_count
                
                # Update class-level stats
                hierarchy[school]['classes'][class_name]['student_count'] += 1
                hierarchy[school]['classes'][class_name]['observation_count'] += profile.observation_count
                
                # Add student to class
                hierarchy[school]['classes'][class_name]['students'].append({
                    'name': profile.student_name,
                    'observation_count': profile.observation_count,
                    'assessment_count': profile.assessment_count,
                    'last_assessment_date': profile.last_observed.strftime('%Y-%m-%d'),
                    'data_quality_score': profile.data_quality_score
                })
                
                # Update date range
                first_date = profile.first_observed.strftime('%Y-%m-%d')
                last_date = profile.last_observed.strftime('%Y-%m-%d')
                
                if not hierarchy[school]['date_range']['first'] or first_date < hierarchy[school]['date_range']['first']:
                    hierarchy[school]['date_range']['first'] = first_date
                
                if not hierarchy[school]['date_range']['last'] or last_date > hierarchy[school]['date_range']['last']:
                    hierarchy[school]['date_range']['last'] = last_date
                
                # Add to recent assessments
                hierarchy[school]['recent_assessments'].append({
                    'student_name': profile.student_name,
                    'date': last_date,
                    'observation_count': profile.observation_count
                })
            
            # Calculate class counts and sort recent assessments
            for school_data in hierarchy.values():
                school_data['class_count'] = len(school_data['classes'])
                school_data['recent_assessments'].sort(key=lambda x: x['date'], reverse=True)
            
            return dict(hierarchy)
            
        except Exception as e:
            st.error(f"Error building school hierarchy: {e}")
            return {}
    
    def _perform_search(self, **filters) -> List[Dict]:
        """Perform search with given filters"""
        try:
            # Use cached profiles
            if 'cached_profiles' not in st.session_state:
                st.session_state.cached_profiles = self.storage_manager.get_all_consolidated_profiles()
            profiles = st.session_state.cached_profiles
            
            results = []
            
            search_term = filters.get('search_term', '').lower()
            search_type = filters.get('search_type', 'All Fields')
            
            for profile in profiles:
                # Apply filters
                if not self._matches_filters(profile, filters):
                    continue
                
                # Apply search term
                if search_term and not self._matches_search(profile, search_term, search_type):
                    continue
                
                # Add to results
                results.append({
                    'student_name': profile.student_name,
                    'school': profile.school,
                    'class': profile.class_name,
                    'observation_count': profile.observation_count,
                    'assessment_count': profile.assessment_count,
                    'last_observed': profile.last_observed.strftime('%Y-%m-%d'),
                    'data_quality_score': profile.data_quality_score,
                    'profile': profile
                })
            
            return results
            
        except Exception as e:
            st.error(f"Error performing search: {e}")
            return []
    
    def _matches_filters(self, profile, filters) -> bool:
        """Check if profile matches the given filters"""
        # School filter
        selected_schools = filters.get('schools', ['All Schools'])
        if 'All Schools' not in selected_schools:
            if profile.school not in selected_schools:
                return False
        
        # Class filter
        selected_classes = filters.get('classes', ['All Classes'])
        if 'All Classes' not in selected_classes:
            if profile.class_name not in selected_classes:
                return False
        
        # Date range filter
        date_from = filters.get('date_from')
        date_to = filters.get('date_to')
        
        if date_from:
            if profile.last_observed.date() < date_from:
                return False
        
        if date_to:
            if profile.first_observed.date() > date_to:
                return False
        
        # Observation count filter
        min_obs = filters.get('min_observations', 0)
        max_obs = filters.get('max_observations', 100)
        
        if not (min_obs <= profile.observation_count <= max_obs):
            return False
        
        # Assessment status filter
        assessment_status = filters.get('assessment_status', 'All')
        if assessment_status == 'Has Assessments' and profile.assessment_count == 0:
            return False
        elif assessment_status == 'No Assessments' and profile.assessment_count > 0:
            return False
        elif assessment_status == 'Multiple Assessments' and profile.assessment_count <= 1:
            return False
        
        return True
    
    def _matches_search(self, profile, search_term: str, search_type: str) -> bool:
        """Check if profile matches the search term"""
        search_term = search_term.lower()
        
        if search_type == 'All Fields':
            # Search in all fields
            searchable_text = f"{profile.student_name} {profile.school} {profile.class_name}".lower()
            
            # Also search in observations
            for obs in profile.observations:
                searchable_text += f" {obs.content}".lower()
            
            return search_term in searchable_text
        
        elif search_type == 'Student Names':
            return search_term in profile.student_name.lower()
        
        elif search_type == 'Schools':
            return search_term in profile.school.lower()
        
        elif search_type == 'Observations':
            for obs in profile.observations:
                if search_term in obs.content.lower():
                    return True
            return False
        
        elif search_type == 'Assessment Results':
            if profile.consolidated_assessment:
                for quality, details in profile.consolidated_assessment.qualities.items():
                    if search_term in quality.lower() or search_term in details.get('reasoning', '').lower():
                        return True
            return False
        
        return False
    
    def _display_search_results(self, results: List[Dict]):
        """Display search results"""
        if not results:
            st.info("No results found matching your search criteria.")
            return
        
        st.success(f"Found {len(results)} matching student(s)")
        
        # Results summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            unique_schools = len(set(r['school'] for r in results))
            st.metric("🏫 Schools", unique_schools)
        
        with col2:
            unique_classes = len(set(f"{r['school']}_{r['class']}" for r in results))
            st.metric("🎓 Classes", unique_classes)
        
        with col3:
            total_observations = sum(r['observation_count'] for r in results)
            st.metric("📝 Total Observations", total_observations)
        
        # Results table
        results_df = pd.DataFrame([
            {
                'Student': r['student_name'],
                'School': r['school'],
                'Class': r['class'],
                'Observations': r['observation_count'],
                'Assessments': r['assessment_count'],
                'Last Observed': r['last_observed'],
                'Quality Score': f"{r['data_quality_score']:.1%}"
            }
            for r in results
        ])
        
        st.dataframe(
            results_df, 
            use_container_width=True,
            column_config={
                "Quality Score": st.column_config.TextColumn(
                    "Quality Score",
                    help="""Data Quality Score indicates how comprehensive the student's assessment data is:
• 80-100%: Excellent - Rich observations over time with detailed content
• 60-80%: Good - Adequate observations and assessments
• 40-60%: Fair - Basic data, could use more observations  
• 0-40%: Poor - Limited data, needs attention"""
                )
            }
        )
        
        # Detailed view selection
        student_names = [r['student_name'] for r in results]
        selected_student = st.selectbox(
            "Select student for detailed view:",
            ["-- Select Student --"] + student_names,
            key="search_results_student_select"
        )
        
        if selected_student and selected_student != "-- Select Student --":
            self._render_student_consolidated_view(selected_student)
    
    def _render_student_consolidated_view(self, student_name: str):
        """Render consolidated view for a specific student"""
        try:
            profile = self.storage_manager.get_consolidated_student_profile(student_name)
            
            if not profile:
                st.error(f"Could not find profile for {student_name}")
                return
            
            st.markdown(f"### 👤 {profile.student_name} - Consolidated Profile")
            
            # Student metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📝 Observations", profile.observation_count)
            with col2:
                st.metric("📊 Assessments", profile.assessment_count)
            with col3:
                span_days = (profile.last_observed - profile.first_observed).days
                st.metric("📅 Observation Span", f"{span_days} days")
            
            # School and class info
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**🏫 School:** {profile.school}")
            with col2:
                st.write(f"**🎓 Class:** {profile.class_name}")
            
            # Observation timeline
            st.markdown("#### 📅 Observation Timeline")
            
            timeline_data = []
            for obs in profile.observations:
                timeline_data.append({
                    'Date': obs.timestamp.strftime('%Y-%m-%d'),
                    'Type': 'Observation',
                    'Content Preview': obs.content[:100] + "..." if len(obs.content) > 100 else obs.content
                })
            
            for assessment in profile.assessments:
                # Count only qualities that were actually assessed (not "NOT OBSERVED" or "Unknown")
                assessed_qualities = [q for q in assessment.qualities.keys() 
                                    if q != 'Unknown' and assessment.qualities[q].get('level') != 'NOT OBSERVED']
                timeline_data.append({
                    'Date': assessment.timestamp.strftime('%Y-%m-%d'),
                    'Type': 'Assessment',
                    'Content Preview': f"{len(assessed_qualities)} qualities assessed"
                })
            
            if timeline_data:
                timeline_df = pd.DataFrame(timeline_data)
                timeline_df = timeline_df.sort_values('Date', ascending=False)
                st.dataframe(timeline_df, use_container_width=True)
            
            # Consolidated assessment
            if profile.consolidated_assessment:
                st.markdown("#### 🎯 Consolidated Assessment Results")
                st.success("✅ Multiple observations consolidated into comprehensive assessment")
                
                # Display qualities in organized format
                quality_levels = defaultdict(list)
                for quality, details in profile.consolidated_assessment.qualities.items():
                    quality_levels[details['level']].append({
                        'quality': quality,
                        'confidence': details['confidence'],
                        'reasoning': details.get('reasoning', '')
                    })
                
                # Display by level
                for level in ['HIGH', 'MIDDLE', 'LOW']:
                    if quality_levels[level]:
                        with st.expander(f"{level} Level ({len(quality_levels[level])} qualities)", expanded=True):
                            for item in quality_levels[level]:
                                st.write(f"**{item['quality']}**")
                                if item['reasoning']:
                                    st.write(f"*{item['reasoning']}*")
                                st.divider()
            else:
                st.info("No consolidated assessment available yet")
            
            # Individual observations
            with st.expander("📝 View All Individual Observations", expanded=False):
                for i, obs in enumerate(profile.observations, 1):
                    st.markdown(f"**Observation {i}** ({obs.timestamp.strftime('%Y-%m-%d %H:%M')})")
                    st.text(obs.content)
                    if i < len(profile.observations):
                        st.markdown("---")
                        
        except Exception as e:
            st.error(f"Error rendering student profile: {e}")
    
    def _generate_analytics_data(self) -> Dict[str, Any]:
        """Generate comprehensive analytics data"""
        try:
            # Use cached profiles
            if 'cached_profiles' not in st.session_state:
                st.session_state.cached_profiles = self.storage_manager.get_all_consolidated_profiles()
            profiles = st.session_state.cached_profiles
            
            # School comparison data
            school_stats = defaultdict(lambda: {
                'students': 0,
                'observations': 0,
                'assessments': 0,
                'avg_quality': 0.0
            })
            
            for profile in profiles:
                school = profile.school if profile.school != 'Unknown' else 'Unspecified'
                school_stats[school]['students'] += 1
                school_stats[school]['observations'] += profile.observation_count
                school_stats[school]['assessments'] += profile.assessment_count
                school_stats[school]['avg_quality'] += profile.data_quality_score
            
            # Calculate averages
            school_comparison = []
            for school, stats in school_stats.items():
                if stats['students'] > 0:
                    stats['avg_quality'] /= stats['students']
                
                school_comparison.append({
                    'School': school,
                    'Students': stats['students'],
                    'Observations': stats['observations'],
                    'Assessments': stats['assessments'],
                    'Avg Quality': f"{stats['avg_quality']:.1%}",
                    'Obs per Student': f"{stats['observations'] / max(stats['students'], 1):.1f}"
                })
            
            # Timeline data
            timeline_data = self._generate_timeline_data(profiles)
            
            # Quality metrics
            quality_metrics = self._calculate_quality_metrics(profiles)
            
            # Generate insights
            insights = self._generate_insights(profiles, school_stats)
            
            return {
                'school_comparison': school_comparison,
                'timeline_data': timeline_data,
                'quality_metrics': quality_metrics,
                'insights': insights
            }
            
        except Exception as e:
            st.error(f"Error generating analytics: {e}")
            return {}
    
    def _generate_timeline_data(self, profiles) -> List[Dict]:
        """Generate timeline data for analytics"""
        # Group observations by date
        date_counts = defaultdict(int)
        
        for profile in profiles:
            for obs in profile.observations:
                date_str = obs.timestamp.strftime('%Y-%m-%d')
                date_counts[date_str] += 1
        
        # Convert to list format for charting
        timeline_data = []
        for date_str, count in sorted(date_counts.items()):
            timeline_data.append({
                'Date': date_str,
                'Observations': count
            })
        
        return timeline_data
    
    def _calculate_quality_metrics(self, profiles) -> Dict[str, int]:
        """Calculate data quality metrics"""
        complete_profiles = 0
        rich_observations = 0
        multi_assessment = 0
        needs_attention = 0
        
        for profile in profiles:
            # Complete profiles (high quality score)
            if profile.data_quality_score >= 0.8:
                complete_profiles += 1
            
            # Rich observations (multiple detailed observations)
            if profile.observation_count >= 3:
                avg_length = sum(len(obs.content) for obs in profile.observations) / profile.observation_count
                if avg_length >= 200:  # Detailed observations
                    rich_observations += 1
            
            # Multiple assessments
            if profile.assessment_count > 1:
                multi_assessment += 1
            
            # Needs attention (low quality or few observations)
            if profile.data_quality_score < 0.5 or profile.observation_count < 2:
                needs_attention += 1
        
        return {
            'complete_profiles': complete_profiles,
            'rich_observations': rich_observations,
            'multi_assessment': multi_assessment,
            'needs_attention': needs_attention
        }
    
    def _generate_insights(self, profiles, school_stats) -> List[Dict]:
        """Generate key insights from the data"""
        insights = []
        
        if not profiles:
            return insights
        
        # Most active school
        if school_stats:
            most_active_school = max(school_stats.items(), key=lambda x: x[1]['observations'])
            insights.append({
                'type': 'success',
                'message': f"Most active school: {most_active_school[0]} with {most_active_school[1]['observations']} observations"
            })
        
        # Data quality insight
        if len(profiles) > 0:
            avg_quality = sum(p.data_quality_score for p in profiles) / len(profiles)
            if avg_quality >= 0.8:
                insights.append({
                    'type': 'success',
                    'message': f"Excellent data quality with average score of {avg_quality:.1%}"
                })
            elif avg_quality < 0.6:
                insights.append({
                    'type': 'warning',
                    'message': f"Data quality needs improvement - average score is {avg_quality:.1%}"
                })
        
        # Observation distribution
        total_observations = sum(p.observation_count for p in profiles)
        if len(profiles) > 0:
            avg_obs_per_student = total_observations / len(profiles)
            
            if avg_obs_per_student >= 3:
                insights.append({
                    'type': 'success',
                    'message': f"Good observation coverage with {avg_obs_per_student:.1f} observations per student on average"
                })
            else:
                insights.append({
                    'type': 'info',
                    'message': f"Consider collecting more observations - currently {avg_obs_per_student:.1f} per student on average"
                })
        
        # Recent activity
        recent_profiles = [p for p in profiles if (datetime.now() - p.last_observed).days <= 7]
        if recent_profiles:
            insights.append({
                'type': 'info',
                'message': f"{len(recent_profiles)} students have been assessed in the last 7 days"
            })
        
        return insights
    
    def _calculate_data_quality_score(self, stats) -> float:
        """Calculate overall data quality score"""
        if stats['total_students'] == 0:
            return 0.0
        
        # Factors for quality score
        obs_per_student = stats['total_observations'] / stats['total_students']
        assessment_coverage = stats['total_assessments'] / stats['total_students']
        
        # Normalize scores
        obs_score = min(obs_per_student / 3.0, 1.0)  # 3+ observations is ideal
        assessment_score = min(assessment_coverage, 1.0)  # 1+ assessment per student
        
        # Weighted average
        quality_score = (obs_score * 0.6) + (assessment_score * 0.4)
        
        return quality_score
    
    def _format_last_updated(self, last_updated: str) -> str:
        """Format last updated timestamp for display"""
        if not last_updated:
            return "Never"
        
        try:
            dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            return dt.strftime("%m/%d %H:%M")
        except (ValueError, AttributeError, TypeError):
            return "Unknown"
    
    def _export_summary_report(self):
        """Export summary report"""
        try:
            # Generate summary data
            stats = self._get_comprehensive_stats()
            analytics = self._generate_analytics_data()
            
            # Create summary report
            report_data = {
                'Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'System Statistics': stats,
                'School Comparison': analytics.get('school_comparison', []),
                'Quality Metrics': analytics.get('quality_metrics', {}),
                'Key Insights': [insight['message'] for insight in analytics.get('insights', [])]
            }
            
            # Convert to JSON for download
            report_json = json.dumps(report_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="📊 Download Summary Report (JSON)",
                data=report_json,
                file_name=f"assessment_summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            st.success("✅ Summary report generated!")
            
        except Exception as e:
            st.error(f"Error generating summary report: {e}")
    
    def _export_detailed_data(self):
        """Export detailed assessment data"""
        try:
            # Use cached profiles
            if 'cached_profiles' not in st.session_state:
                st.session_state.cached_profiles = self.storage_manager.get_all_consolidated_profiles()
            profiles = st.session_state.cached_profiles
            
            # Create detailed export data
            detailed_data = []
            
            for profile in profiles:
                # Basic profile info
                profile_data = {
                    'student_name': profile.student_name,
                    'school': profile.school,
                    'class': profile.class_name,
                    'observation_count': profile.observation_count,
                    'assessment_count': profile.assessment_count,
                    'first_observed': profile.first_observed.isoformat(),
                    'last_observed': profile.last_observed.isoformat(),
                    'data_quality_score': profile.data_quality_score,
                    'observations': [],
                    'assessments': [],
                    'consolidated_assessment': None
                }
                
                # Add observations
                for obs in profile.observations:
                    profile_data['observations'].append({
                        'timestamp': obs.timestamp.isoformat(),
                        'content': obs.content,
                        'source': obs.source
                    })
                
                # Add assessments
                for assessment in profile.assessments:
                    profile_data['assessments'].append({
                        'timestamp': assessment.timestamp.isoformat(),
                        'qualities': assessment.qualities
                    })
                
                # Add consolidated assessment
                if profile.consolidated_assessment:
                    profile_data['consolidated_assessment'] = {
                        'qualities': profile.consolidated_assessment.qualities,
                        'confidence_score': profile.consolidated_assessment.confidence_score,
                        'consolidation_method': profile.consolidated_assessment.consolidation_method
                    }
                
                detailed_data.append(profile_data)
            
            # Convert to JSON for download
            detailed_json = json.dumps(detailed_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="📋 Download Detailed Data (JSON)",
                data=detailed_json,
                file_name=f"assessment_detailed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            st.success("✅ Detailed data export generated!")
            
        except Exception as e:
            st.error(f"Error generating detailed export: {e}")
    
    def _render_visual_analytics_dashboard(self):
        """Render Power BI-like visual analytics dashboard"""
        if not VISUALIZATIONS_AVAILABLE:
            st.error("📊 Visual Analytics Dashboard Unavailable")
            st.markdown("""
            **Missing Dependencies**: The visual analytics dashboard requires additional libraries.
            
            **To enable visualizations:**
            1. Install required packages: `pip install plotly altair matplotlib seaborn`
            2. Restart the application
            
            **What you'll get:**
            - 📊 Interactive charts and graphs
            - 📈 Growth trend visualizations  
            - 🎯 Trait analysis heatmaps
            - 👥 Student comparison dashboards
            - 📋 Executive summary with KPIs
            """)
            
            # Show a preview of what would be available
            st.markdown("### 🎯 Preview: Available Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **📊 School Overview Dashboard**
                - Interactive school comparison charts
                - Data quality distribution graphs
                - Student distribution pie charts
                - Observation activity heatmaps
                """)
                
                st.markdown("""
                **📈 Growth Trends Analysis**
                - Student growth timeline charts
                - Individual growth radar charts
                - Trait development trend lines
                """)
            
            with col2:
                st.markdown("""
                **🎯 Trait Analysis Dashboard**
                - Personality trait distribution matrix
                - Trait correlation heatmaps
                - Trait level distribution charts
                - School-wise trait comparisons
                """)
                
                st.markdown("""
                **👥 Student Comparison Dashboard**
                - Student performance rankings
                - Performance scatter plots
                - Progress comparison charts
                - Peer analysis visualizations
                """)
            
            # Fallback to basic charts using Streamlit native charts
            st.markdown("---")
            st.markdown("### 📊 Basic Analytics (Available Now)")
            
            try:
                # Use cached profiles
                if 'cached_profiles' not in st.session_state:
                    st.session_state.cached_profiles = self.storage_manager.get_all_consolidated_profiles()
                profiles = st.session_state.cached_profiles
                
                if profiles:
                    self._render_basic_charts(profiles)
                else:
                    st.info("No data available for basic analytics")
            except Exception as e:
                st.error(f"Error loading basic analytics: {e}")
            
            return
        
        # Render full visualization dashboard
        st.markdown("### 📊 Power BI-Style Visual Analytics")
        st.markdown("*Interactive charts and comprehensive data visualizations*")
        
        try:
            self.viz_dashboard.render_visualization_dashboard()
        except Exception as e:
            st.error(f"Error rendering visual analytics dashboard: {e}")
            st.markdown("**Fallback**: Using basic analytics instead")
            
            # Fallback to basic analytics
            try:
                # Use cached profiles
                if 'cached_profiles' not in st.session_state:
                    st.session_state.cached_profiles = self.storage_manager.get_all_consolidated_profiles()
                profiles = st.session_state.cached_profiles
                
                if profiles:
                    self._render_basic_charts(profiles)
            except Exception as fallback_error:
                st.error(f"Fallback analytics also failed: {fallback_error}")
    
    def _render_basic_charts(self, profiles: List):
        """Render basic charts using Streamlit native charting"""
        st.markdown("#### 📊 Basic School Analytics")
        
        # Prepare basic school data
        school_stats = defaultdict(lambda: {'students': 0, 'observations': 0, 'quality_sum': 0})
        
        for profile in profiles:
            school = profile.school if profile.school != 'Unknown' else 'Other'
            school_stats[school]['students'] += 1
            school_stats[school]['observations'] += profile.observation_count
            school_stats[school]['quality_sum'] += profile.data_quality_score
        
        # Convert to DataFrame for charting
        chart_data = []
        for school, stats in school_stats.items():
            avg_quality = stats['quality_sum'] / stats['students'] if stats['students'] > 0 else 0
            chart_data.append({
                'School': school,
                'Students': stats['students'],
                'Total Observations': stats['observations'],
                'Average Quality': avg_quality * 100  # Convert to percentage
            })
        
        chart_df = pd.DataFrame(chart_data)
        
        if not chart_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Students per School**")
                st.bar_chart(chart_df.set_index('School')['Students'])
            
            with col2:
                st.markdown("**Average Quality Score (%)**")
                st.bar_chart(chart_df.set_index('School')['Average Quality'])
            
            # Data quality distribution
            st.markdown("#### 📈 Data Quality Distribution")
            
            quality_categories = []
            for _, row in chart_df.iterrows():
                quality = row['Average Quality']
                if quality >= 80:
                    category = 'Excellent (80%+)'
                elif quality >= 60:
                    category = 'Good (60-80%)'
                elif quality >= 40:
                    category = 'Fair (40-60%)'
                else:
                    category = 'Needs Attention (<40%)'
                quality_categories.append(category)
            
            quality_dist = pd.Series(quality_categories).value_counts()
            st.bar_chart(quality_dist)
            
            # Summary metrics
            st.markdown("#### 📋 Summary Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Schools", len(chart_df))
            with col2:
                st.metric("Total Students", chart_df['Students'].sum())
            with col3:
                st.metric("Total Observations", chart_df['Total Observations'].sum())
            with col4:
                avg_system_quality = chart_df['Average Quality'].mean()
                st.metric("System Avg Quality", f"{avg_system_quality:.1f}%")
        else:
            st.info("No data available for basic charts")