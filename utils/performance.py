"""
Performance optimization utilities for the personality assessment system.
Provides caching, lazy loading, and performance monitoring.
"""
import streamlit as st
import time
from functools import wraps
from typing import Any, Callable
import hashlib
import json


def get_storage_manager_cached():
    """
    Get cached storage manager instance.
    Creates once per session and reuses.
    """
    if 'storage_manager' not in st.session_state:
        from ai_core.assessment_storage_manager import AssessmentStorageManager
        st.session_state.storage_manager = AssessmentStorageManager()
    return st.session_state.storage_manager


@st.cache_data(ttl=300, show_spinner=False)
def load_assessments_cached():
    """
    Load assessment data with caching.
    Cache expires after 5 minutes or can be manually cleared.
    """
    storage_manager = get_storage_manager_cached()
    return storage_manager.load_existing_data()


@st.cache_data(ttl=300, show_spinner=False)
def get_all_profiles_cached():
    """
    Get all consolidated profiles with caching.
    """
    storage_manager = get_storage_manager_cached()
    return storage_manager.get_all_consolidated_profiles()


@st.cache_data(ttl=300, show_spinner=False)
def get_school_hierarchy_cached():
    """
    Get school hierarchy with caching.
    """
    from frontend.enhanced_stored_assessments import EnhancedStoredAssessmentsInterface
    storage_manager = get_storage_manager_cached()
    interface = EnhancedStoredAssessmentsInterface(storage_manager)
    return interface._build_school_hierarchy()


def clear_all_caches():
    """
    Clear all cached data.
    Call this after data updates (new assessments, imports, etc.)
    """
    st.cache_data.clear()
    
    # Also clear session state caches
    keys_to_clear = ['cached_profiles', 'cached_assessments', 'cached_hierarchy']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def lazy_load_component(component_name: str, load_func: Callable, *args, **kwargs) -> Any:
    """
    Lazy load a component only when needed.
    Stores result in session state to avoid reloading.
    
    Args:
        component_name: Unique name for this component
        load_func: Function to call to load the component
        *args, **kwargs: Arguments to pass to load_func
    
    Returns:
        The loaded component
    """
    cache_key = f"lazy_{component_name}"
    
    if cache_key not in st.session_state:
        with st.spinner(f"Loading {component_name}..."):
            st.session_state[cache_key] = load_func(*args, **kwargs)
    
    return st.session_state[cache_key]


def performance_monitor(func: Callable) -> Callable:
    """
    Decorator to monitor function performance.
    Logs execution time for debugging.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        if execution_time > 1.0:  # Log if takes more than 1 second
            print(f"⚠️ {func.__name__} took {execution_time:.2f}s")
        
        return result
    return wrapper


def get_data_hash(data: Any) -> str:
    """
    Generate hash of data for cache invalidation.
    """
    try:
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()
    except (TypeError, ValueError, AttributeError):
        # Fallback to Python's built-in hash for non-JSON-serializable data
        return str(hash(str(data)))


def init_session_state():
    """
    Initialize session state variables for performance optimization.
    Call this at the start of the app.
    """
    defaults = {
        'data_loaded': False,
        'current_tab': 'Batch Assessment',
        'last_data_hash': None,
        'analytics_loaded': False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def should_reload_data() -> bool:
    """
    Check if data should be reloaded based on hash comparison.
    """
    try:
        current_data = load_assessments_cached()
        current_hash = get_data_hash(current_data.to_dict())
        
        if st.session_state.get('last_data_hash') != current_hash:
            st.session_state.last_data_hash = current_hash
            return True
        return False
    except (AttributeError, KeyError, TypeError, ValueError):
        # If comparison fails, reload to be safe
        return True
