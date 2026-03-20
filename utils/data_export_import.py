"""
Data export and import utilities for local storage management.
Allows NGO to download/upload their assessment data.
"""
import streamlit as st
import zipfile
import io
import os
import shutil
from datetime import datetime
from pathlib import Path


def export_all_data_as_zip() -> bytes:
    """
    Export all assessment data and backups as a zip file.
    
    Returns:
        Bytes of the zip file
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add main assessment file
        if os.path.exists('assessments/student_assessments.csv'):
            zip_file.write('assessments/student_assessments.csv', 
                          'student_assessments.csv')
        
        # Add metadata
        if os.path.exists('assessments/metadata.json'):
            zip_file.write('assessments/metadata.json', 
                          'metadata.json')
        
        # Add audit log
        if os.path.exists('assessments/audit_log.json'):
            zip_file.write('assessments/audit_log.json', 
                          'audit_log.json')
        
        # Add all backups
        backup_dir = 'assessments/backups'
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, file)
                if os.path.isfile(file_path):
                    zip_file.write(file_path, f'backups/{file}')
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def import_data_from_zip(uploaded_file) -> tuple[bool, str]:
    """
    Import assessment data from uploaded zip file.
    
    Args:
        uploaded_file: Streamlit uploaded file object
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Create backup of current data before importing
        from utils.performance import get_storage_manager_cached
        storage_manager = get_storage_manager_cached()
        backup_path = storage_manager._create_backup()
        
        # Extract uploaded zip
        with zipfile.ZipFile(uploaded_file, 'r') as zip_file:
            # Ensure assessments directory exists
            os.makedirs('assessments', exist_ok=True)
            os.makedirs('assessments/backups', exist_ok=True)
            
            # Extract main files
            for file_name in ['student_assessments.csv', 'metadata.json', 'audit_log.json']:
                if file_name in zip_file.namelist():
                    zip_file.extract(file_name, 'assessments/')
            
            # Extract backups
            for file_name in zip_file.namelist():
                if file_name.startswith('backups/'):
                    zip_file.extract(file_name, 'assessments/')
        
        # Clear caches to reload new data
        from utils.performance import clear_all_caches
        clear_all_caches()
        
        return True, f"Data imported successfully! Previous data backed up to: {backup_path}"
    
    except Exception as e:
        return False, f"Failed to import data: {str(e)}"


def export_assessments_only() -> bytes:
    """
    Export only the main assessment CSV file.
    Useful for quick downloads or sharing with others.
    
    Returns:
        Bytes of the CSV file
    """
    try:
        with open('assessments/student_assessments.csv', 'rb') as f:
            return f.read()
    except FileNotFoundError:
        return b""


def get_export_filename() -> str:
    """
    Generate filename for export with timestamp.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"personality_assessments_{timestamp}.zip"


def render_export_import_ui():
    """
    Render the export/import UI component.
    Call this in the sidebar or a dedicated section.
    """
    st.markdown("### 💾 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export Data")
        
        # Export all data
        if st.button("📦 Download All Data", use_container_width=True):
            with st.spinner("Preparing export..."):
                zip_data = export_all_data_as_zip()
                filename = get_export_filename()
                
                st.download_button(
                    label="⬇️ Download ZIP",
                    data=zip_data,
                    file_name=filename,
                    mime="application/zip",
                    use_container_width=True
                )
                st.success("Export ready! Click Download ZIP button above.")
        
        # Export CSV only
        if st.button("📄 Download CSV Only", use_container_width=True):
            csv_data = export_assessments_only()
            if csv_data:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name="student_assessments.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("No assessment data found")
    
    with col2:
        st.markdown("#### Import Data")
        
        uploaded_file = st.file_uploader(
            "Upload previous data",
            type=['zip'],
            help="Upload a ZIP file exported from this system",
            key="data_import_uploader"
        )
        
        if uploaded_file is not None:
            if st.button("📥 Import Data", type="primary", use_container_width=True):
                with st.spinner("Importing data..."):
                    success, message = import_data_from_zip(uploaded_file)
                    
                    if success:
                        st.success(message)
                        st.info("Page will reload to show imported data...")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
    
    st.markdown("---")
    st.caption("💡 Tip: Export your data weekly and save it to Google Drive or USB drive for backup")


def get_data_stats() -> dict:
    """
    Get statistics about current data for display.
    """
    stats = {
        'total_students': 0,
        'total_assessments': 0,
        'total_backups': 0,
        'data_size_mb': 0,
        'last_updated': 'Never'
    }
    
    try:
        from utils.performance import load_assessments_cached
        df = load_assessments_cached()
        stats['total_students'] = len(df)
        
        # Count total assessments (date columns)
        date_cols = [col for col in df.columns if col.startswith('Session_')]
        stats['total_assessments'] = sum(df[col].notna().sum() for col in date_cols)
        
        # Count backups
        backup_dir = 'assessments/backups'
        if os.path.exists(backup_dir):
            stats['total_backups'] = len([f for f in os.listdir(backup_dir) 
                                         if f.startswith('backup_')])
        
        # Calculate data size
        if os.path.exists('assessments/student_assessments.csv'):
            size_bytes = os.path.getsize('assessments/student_assessments.csv')
            stats['data_size_mb'] = round(size_bytes / (1024 * 1024), 2)
            
            # Get last modified time
            mtime = os.path.getmtime('assessments/student_assessments.csv')
            stats['last_updated'] = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    
    except Exception as e:
        print(f"Error getting data stats: {e}")
    
    return stats
