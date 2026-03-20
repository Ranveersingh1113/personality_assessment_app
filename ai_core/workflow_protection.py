"""
Workflow Protection and User Guidance System

This module implements Task 8 requirements:
- Confirmation dialogs for potentially destructive actions
- Step-by-step workflow navigation with contextual help
- "What to do next" guidance system
- Visual cues for critical actions
"""

import streamlit as st
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime


class WorkflowProtection:
    """
    Manages workflow protection and user guidance throughout the application.
    
    Features:
    - Confirmation dialogs for destructive actions
    - Contextual help and guidance
    - Step-by-step workflow navigation
    - Visual cues for critical steps
    """
    
    def __init__(self):
        """Initialize workflow protection system"""
        self.current_step = None
        self.workflow_history = []
        
    def confirm_action(
        self, 
        action_name: str, 
        message: str, 
        warning_level: str = "warning",
        details: Optional[List[str]] = None
    ) -> bool:
        """
        Show confirmation dialog for potentially destructive action.
        
        Args:
            action_name: Name of the action (e.g., "Delete Data")
            message: Warning message to display
            warning_level: "info", "warning", or "error"
            details: Optional list of details about what will be affected
            
        Returns:
            True if user confirms, False otherwise
        """
        # Create unique key for this confirmation
        confirm_key = f"confirm_{action_name.lower().replace(' ', '_')}_{datetime.now().timestamp()}"
        
        # Show warning with appropriate icon
        icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🚨"
        }
        icon = icons.get(warning_level, "⚠️")
        
        st.warning(f"{icon} **{action_name}**")
        st.write(message)
        
        if details:
            with st.expander("📋 What will be affected:"):
                for detail in details:
                    st.write(f"• {detail}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Yes, {action_name}", key=f"{confirm_key}_yes", type="primary"):
                return True
        with col2:
            if st.button("❌ Cancel", key=f"{confirm_key}_no"):
                st.info("Action cancelled.")
                return False
        
        return False
    
    def show_next_steps(self, current_context: str, steps: List[Dict[str, str]]):
        """
        Show "what to do next" guidance.
        
        Args:
            current_context: Current workflow context (e.g., "batch_uploaded")
            steps: List of next step dictionaries with 'title', 'description', 'action'
        """
        st.info("👉 **What to do next:**")
        
        for i, step in enumerate(steps, 1):
            with st.container():
                col1, col2 = st.columns([1, 20])
                with col1:
                    st.write(f"**{i}.**")
                with col2:
                    st.write(f"**{step['title']}**")
                    if 'description' in step:
                        st.caption(step['description'])
                    if 'action' in step and step['action']:
                        st.caption(f"→ {step['action']}")
    
    def show_workflow_progress(self, steps: List[str], current_step: int):
        """
        Show workflow progress indicator.
        
        Args:
            steps: List of workflow step names
            current_step: Current step index (0-based)
        """
        st.markdown("### 📍 Workflow Progress")
        
        cols = st.columns(len(steps))
        for i, (col, step) in enumerate(zip(cols, steps)):
            with col:
                if i < current_step:
                    st.success(f"✅ {step}")
                elif i == current_step:
                    st.info(f"▶️ {step}")
                else:
                    st.write(f"⭕ {step}")
    
    def show_contextual_help(self, context: str, help_text: str, tips: Optional[List[str]] = None):
        """
        Show contextual help for current workflow step.
        
        Args:
            context: Context identifier
            help_text: Main help text
            tips: Optional list of tips
        """
        with st.expander("💡 Help & Tips", expanded=False):
            st.write(help_text)
            
            if tips:
                st.markdown("**💡 Tips:**")
                for tip in tips:
                    st.write(f"• {tip}")
    
    def validate_workflow_state(
        self, 
        required_state: Dict[str, Any], 
        error_guidance: str
    ) -> bool:
        """
        Validate that required workflow state exists.
        
        Args:
            required_state: Dictionary of required session state keys and expected types
            error_guidance: Guidance message if validation fails
            
        Returns:
            True if valid, False otherwise
        """
        missing = []
        for key, expected_type in required_state.items():
            if key not in st.session_state:
                missing.append(key)
            elif expected_type and not isinstance(st.session_state[key], expected_type):
                missing.append(f"{key} (wrong type)")
        
        if missing:
            st.error("⚠️ **Workflow State Error**")
            st.write("Required data is missing or invalid:")
            for item in missing:
                st.write(f"• {item}")
            st.info(f"💡 {error_guidance}")
            return False
        
        return True
    
    def show_critical_action_warning(self, action: str, impact: str):
        """
        Show prominent warning for critical actions.
        
        Args:
            action: Action being performed
            impact: Description of impact
        """
        st.warning(f"🚨 **Critical Action: {action}**")
        st.write(f"**Impact:** {impact}")
        st.write("Please review carefully before proceeding.")
    
    def track_workflow_step(self, step_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Track workflow step for history and analytics.
        
        Args:
            step_name: Name of the workflow step
            metadata: Optional metadata about the step
        """
        self.current_step = step_name
        self.workflow_history.append({
            'step': step_name,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        })
    
    def get_workflow_guidance(self, context: str) -> Dict[str, Any]:
        """
        Get workflow guidance for specific context.
        
        Args:
            context: Workflow context identifier
            
        Returns:
            Dictionary with guidance information
        """
        guidance_map = {
            'batch_upload': {
                'title': 'Batch Assessment Upload',
                'help': 'Upload a CSV file with student observations for batch processing.',
                'next_steps': [
                    {
                        'title': 'Review CSV format',
                        'description': 'Ensure your CSV has Name, School, Class, Session, and Observations columns',
                        'action': 'Check the format guide above'
                    },
                    {
                        'title': 'Upload file',
                        'description': 'Click "Choose a CSV file" to upload',
                        'action': 'Select your prepared CSV file'
                    },
                    {
                        'title': 'Review validation',
                        'description': 'Check for any errors or warnings',
                        'action': 'Fix any issues before processing'
                    }
                ],
                'tips': [
                    'Use the new 5-column format for best results',
                    'Check for blank rows before uploading',
                    'Ensure student names are consistent'
                ]
            },
            'batch_processing': {
                'title': 'Batch Processing',
                'help': 'The system is processing assessments for all students in your batch.',
                'next_steps': [
                    {
                        'title': 'Wait for completion',
                        'description': 'Processing takes ~30 seconds per student',
                        'action': 'Do not close the browser'
                    },
                    {
                        'title': 'Review results',
                        'description': 'Check the assessment results below',
                        'action': 'Scroll down after processing completes'
                    }
                ],
                'tips': [
                    'Progress is auto-saved every 5 students',
                    'You can resume if interrupted',
                    'Check the quota status during processing'
                ]
            },
            'batch_review': {
                'title': 'Review and Approve',
                'help': 'Review the AI-generated assessments and approve them before finalizing.',
                'next_steps': [
                    {
                        'title': 'Review assessments',
                        'description': 'Check each student\'s assessment for accuracy',
                        'action': 'Read through the predicted labels'
                    },
                    {
                        'title': 'Edit if needed',
                        'description': 'You can modify the Final Labels column',
                        'action': 'Click on cells to edit'
                    },
                    {
                        'title': 'Approve all',
                        'description': 'Use Select All button or check individually',
                        'action': 'Click ✅ Select All or check boxes'
                    },
                    {
                        'title': 'Finalize',
                        'description': 'Download CSV and store in system',
                        'action': 'Click ✅ Finalize & Download CSV'
                    }
                ],
                'tips': [
                    'Use Select All to approve all at once',
                    'You can edit labels before approving',
                    'Finalize button is disabled until all approved'
                ]
            },
            'stored_assessments': {
                'title': 'Stored Assessments',
                'help': 'View and manage all stored student assessments.',
                'next_steps': [
                    {
                        'title': 'Browse by school',
                        'description': 'Use School Hierarchy tab',
                        'action': 'Click 🏫 School Hierarchy'
                    },
                    {
                        'title': 'Search students',
                        'description': 'Use Search & Filter tab',
                        'action': 'Click 🔍 Search & Filter'
                    },
                    {
                        'title': 'View analytics',
                        'description': 'See statistics and trends',
                        'action': 'Click 📈 Analytics Dashboard'
                    }
                ],
                'tips': [
                    'School hierarchy shows all schools and classes',
                    'Search supports multiple criteria',
                    'Analytics show trends over time'
                ]
            }
        }
        
        return guidance_map.get(context, {
            'title': 'Workflow Guidance',
            'help': 'Follow the on-screen instructions to complete your task.',
            'next_steps': [],
            'tips': []
        })


# Global instance
_workflow_protection = None

def get_workflow_protection() -> WorkflowProtection:
    """Get or create global workflow protection instance"""
    global _workflow_protection
    if _workflow_protection is None:
        _workflow_protection = WorkflowProtection()
    return _workflow_protection
