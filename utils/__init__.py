"""
Utility modules for performance optimization and data management.
"""
from .performance import (
    get_storage_manager_cached,
    load_assessments_cached,
    get_all_profiles_cached,
    get_school_hierarchy_cached,
    clear_all_caches,
    lazy_load_component,
    init_session_state
)

from .data_export_import import (
    export_all_data_as_zip,
    import_data_from_zip,
    render_export_import_ui,
    get_data_stats
)

__all__ = [
    'get_storage_manager_cached',
    'load_assessments_cached',
    'get_all_profiles_cached',
    'get_school_hierarchy_cached',
    'clear_all_caches',
    'lazy_load_component',
    'init_session_state',
    'export_all_data_as_zip',
    'import_data_from_zip',
    'render_export_import_ui',
    'get_data_stats',
]
