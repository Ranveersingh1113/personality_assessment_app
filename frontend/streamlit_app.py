import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime

# Ensure project root is on sys.path so sibling packages import correctly
_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_FRONTEND_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai_core.personality_assessment import PersonalityAssessmentSystem
from ai_core.csv_reference_processor import CSVReferenceProcessor
from ai_core.assessment_storage_manager import AssessmentStorageManager
import re
from config import PERSONALITY_QUALITIES

# Page configuration
st.set_page_config(
    page_title="Personality Assessment System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'assessment_system' not in st.session_state:
    st.session_state.assessment_system = None
if 'system_ready' not in st.session_state:
    st.session_state.system_ready = False
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = None
if 'batch_timestamp' not in st.session_state:
    st.session_state.batch_timestamp = None
if 'review_df' not in st.session_state:
    st.session_state.review_df = None
if 'saved_batch_csv' not in st.session_state:
    st.session_state.saved_batch_csv = None
if 'storage_manager' not in st.session_state:
    st.session_state.storage_manager = AssessmentStorageManager()
if 'duplicate_handling' not in st.session_state:
    st.session_state.duplicate_handling = {}

# ============ CSV HELPER FUNCTIONS ============

def sanitize_filename(name):
    """Sanitize a string for use in filenames"""
    safe = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
    return safe.replace(' ', '_')

def save_individual_assessment_csv(student_name, school_name, class_name, observations, result):
    """Save individual assessment as CSV with naming: studentname_schoolname_date.csv"""
    os.makedirs("assessments", exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d")
    safe_student = sanitize_filename(student_name)
    safe_school = sanitize_filename(school_name)
    
    filename = f"{safe_student}_{safe_school}_{date_str}.csv"
    filepath = f"assessments/{filename}"
    
    # Build assessment data rows
    rows = []
    if result.get('assessments'):
        for assessment in result['assessments']:
            rows.append({
                'student_name': student_name,
                'school': school_name,
                'class': class_name,
                'date': datetime.now().strftime("%Y-%m-%d"),
                'quality': assessment.get('quality', ''),
                'level': assessment.get('level', ''),
                'reasoning': assessment.get('reasoning', ''),
                'observations': observations,
                'summary': result.get('summary', '')
            })
    
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False, encoding='utf-8')
        st.success(f"✅ Assessment saved to: {filename}")
    else:
        st.warning("No assessment data to save")

def build_csv_from_results(results):
    """Build a DataFrame from batch results for CSV export"""
    rows = []
    for r in results:
        base_row = {
            'student_id': r.get('student_id', ''),
            'name': r.get('name', ''),
            'school': r.get('school', ''),
            'class': r.get('class', ''),
            'observations': r.get('observations', ''),
            'date': datetime.now().strftime("%Y-%m-%d")
        }
        
        if 'error' in r:
            base_row['error'] = r['error']
            rows.append(base_row)
        elif 'assessment' in r and r['assessment'].get('assessments'):
            for assessment in r['assessment']['assessments']:
                row = base_row.copy()
                row['quality'] = assessment.get('quality', '')
                row['level'] = assessment.get('level', '')
                row['reasoning'] = assessment.get('reasoning', '')
                row['summary'] = r['assessment'].get('summary', '')
                rows.append(row)
        else:
            rows.append(base_row)
    
    return pd.DataFrame(rows)

def get_saved_assessments_index():
    """Scan assessments folder and build index of school/class/date"""
    assessments_dir = "assessments"
    index = {}  # {school: {class: [dates]}}
    
    if not os.path.exists(assessments_dir):
        return index
    
    for filename in os.listdir(assessments_dir):
        if not filename.endswith('.csv') or filename.startswith('checkpoint'):
            continue
        
        filepath = os.path.join(assessments_dir, filename)
        try:
            df = pd.read_csv(filepath, nrows=1)  # Just read header + 1 row
            if 'school' in df.columns and 'class' in df.columns and 'date' in df.columns:
                school = str(df['school'].iloc[0]) if not df.empty else 'Unknown'
                class_name = str(df['class'].iloc[0]) if not df.empty else 'Unknown'
                date = str(df['date'].iloc[0]) if not df.empty else filename
                
                if school not in index:
                    index[school] = {}
                if class_name not in index[school]:
                    index[school][class_name] = []
                if date not in index[school][class_name]:
                    index[school][class_name].append({'date': date, 'file': filename})
        except Exception:
            continue
    
    return index

def load_assessment_file(filename):
    """Load a specific assessment CSV file"""
    filepath = f"assessments/{filename}"
    if os.path.exists(filepath):
        return pd.read_csv(filepath, encoding='utf-8')
    return None

# ============ END CSV HELPER FUNCTIONS ============

def main():
    st.title("🎓 Personality Assessment System for Students")
    st.markdown("---")
    
    # Sidebar for system setup
    with st.sidebar:
        st.header("⚙️ System Setup")
        
        # Check API key
        api_key = st.text_input("Google API Key", type="password", help="Enter your Google API key for Gemini")
        
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            
            if st.button("🚀 Initialize System", type="primary"):
                with st.spinner("Setting up the assessment system..."):
                    try:
                        system = PersonalityAssessmentSystem()
                        system.setup_vector_database()
                        st.session_state.assessment_system = system
                        st.session_state.system_ready = True
                        st.success("✅ System initialized successfully!")
                    except Exception as e:
                        st.error(f"❌ Setup failed: {str(e)}")
                        st.session_state.system_ready = False
        
        # System status
        if st.session_state.system_ready:
            st.success("✅ System Ready")
        else:
            st.warning("⚠️ System Not Ready")
        
        # Rate limiting status
        try:
            from backend.rate_limiter import get_rate_limiter
            rate_limiter = get_rate_limiter()
            status = rate_limiter.get_status()
            
            st.markdown("---")
            st.markdown("### 🚦 Rate Limiting Status")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Minute Requests", f"{status['minute_requests']}/{status['max_per_minute']}")
            with col2:
                st.metric("Daily Requests", f"{status['daily_requests']}/{status['max_per_day']}")
            
            if status['minute_requests'] >= status['max_per_minute'] * 0.8:
                st.warning("⚠️ Approaching rate limit")
            elif status['daily_requests'] >= status['max_per_day'] * 0.8:
                st.warning("⚠️ Approaching daily limit")
        except Exception as e:
            st.info("Rate limiting status unavailable")
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        if st.session_state.system_ready:
            st.info("Vector database loaded with reference data")
            st.info("Using Gemini 2.x + Hugging Face All-MiniLM-L6-v2")
        else:
            st.info("System needs initialization")
    
    # Main content area
    if not st.session_state.system_ready:
        st.info("👈 Please set up the system in the sidebar first by providing your Google API key and initializing the system.")
        return
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Individual Assessment", "👥 Batch Assessment", "📊 Stored Assessments", "🧠 SWOT Analysis"])
    
    with tab1:
        individual_assessment_tab()
    
    with tab2:
        batch_assessment_tab()
    
    with tab3:
        stored_assessments_tab()
    
    with tab4:
        swot_analysis_tab()

def individual_assessment_tab():
    st.header("🔍 Individual Student Assessment")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Student Information")
        school_name = st.text_input("School Name", placeholder="Enter school name", key="ind_school")
        class_name = st.text_input("Class", placeholder="Enter class (e.g., 5th, 6A)", key="ind_class")
        student_name = st.text_input("Student Name", placeholder="Enter student's full name", key="ind_student")
        observations = st.text_area(
            "Observer Notes", 
            height=200,
            placeholder="Enter detailed observations about the student's behavior during the session...\n\nInclude observations about:\n• Participation and engagement\n• Social interactions\n• Academic behavior\n• Emotional responses\n• Any other relevant behaviors",
            key="ind_observations"
        )
        
        all_fields_filled = student_name and school_name and class_name and observations
        if st.button("🎯 Assess Personality", type="primary", disabled=not all_fields_filled):
            if all_fields_filled:
                perform_assessment_with_storage(student_name, school_name, class_name, observations)
    
    with col2:
        st.subheader("💡 Assessment Guidelines")
        st.info("""
        **What to observe:**
        - Student's participation level
        - Interaction with peers and teachers
        - Response to challenges
        - Emotional reactions
        - Problem-solving approach
        - Leadership qualities
        - Academic engagement
        """)
        
        st.info("""
        **Assessment Output:**
        - **HIGH**: Student clearly demonstrates this quality
        - **MIDDLE**: Student shows moderate evidence
        - **LOW**: Student shows limited evidence
        - **NOT OBSERVED**: Insufficient evidence
        """)

def batch_assessment_tab():
    st.header("👥 Batch Student Assessment")
    
    # School and Class info (required for batch)
    st.subheader("🏫 School Information")
    col1, col2 = st.columns(2)
    with col1:
        batch_school = st.text_input("School Name", placeholder="Enter school name", key="batch_school")
    with col2:
        batch_class = st.text_input("Class", placeholder="Enter class (e.g., 5th, 6A)", key="batch_class")
    
    if not batch_school or not batch_class:
        st.warning("⚠️ Please enter School Name and Class before uploading CSV")
    
    # File upload option
    st.subheader("📁 Upload CSV File")
    uploaded_file = st.file_uploader(
        "Choose a CSV file", 
        type=['csv'],
        help="CSV should have columns: Name, Observations"
    )
    
    if uploaded_file is not None and batch_school and batch_class:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Successfully loaded {len(df)} students")
            
            # Display preview
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(), width='stretch')
            
            if st.button("🚀 Start Batch Assessment", type="primary"):
                process_batch_assessment(df, batch_school, batch_class)
                
        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")
    elif uploaded_file is not None:
        st.info("📋 CSV loaded. Please fill in School Name and Class above to proceed.")
    
    # Manual entry option
    st.subheader("✏️ Manual Entry")
    num_students = st.number_input("Number of students", min_value=1, max_value=50, value=3)
    
    if st.button("📝 Create Entry Form"):
        manual_batch_form(num_students)

    st.markdown("---")
    st.subheader("🧐 Review Session")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.session_state.review_df is not None:
            st.success("A review session is in progress.")
        else:
            st.info("No active review session. Run a batch assessment to start.")
    with col_b:
        if st.session_state.review_df is not None and st.button("♻️ Reset Review Session"):
            st.session_state.review_df = None
            st.session_state.batch_results = None
            st.session_state.batch_timestamp = None
            st.session_state.saved_batch_csv = None
            st.rerun()

    if st.session_state.review_df is not None:
        render_review_interface()

def stored_assessments_tab():
    """Display and manage stored assessments with school/class/date filtering"""
    st.header("📊 Stored Assessments")
    
    # Build index of saved assessments
    index = get_saved_assessments_index()
    
    if not index:
        st.info("No assessments stored yet. Run some assessments to see them here.")
        return
    
    # Display summary
    st.subheader("📈 Summary")
    total_schools = len(index)
    total_classes = sum(len(classes) for classes in index.values())
    total_files = sum(len(dates) for school in index.values() for dates in school.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Schools", total_schools)
    with col2:
        st.metric("Classes", total_classes)
    with col3:
        st.metric("Assessment Files", total_files)
    
    st.markdown("---")
    
    # Cascading selection: School → Class → Date
    st.subheader("🔍 Browse Assessments")
    
    # School selection
    schools = sorted(index.keys())
    selected_school = st.selectbox("1️⃣ Select School", ["-- Select School --"] + schools, key="stored_school")
    
    if selected_school and selected_school != "-- Select School --":
        # Class selection (filtered by school)
        classes = sorted(index[selected_school].keys())
        selected_class = st.selectbox("2️⃣ Select Class", ["-- Select Class --"] + classes, key="stored_class")
        
        if selected_class and selected_class != "-- Select Class --":
            # Date selection (filtered by school + class)
            date_entries = index[selected_school][selected_class]
            dates = [entry['date'] for entry in date_entries]
            selected_date = st.selectbox("3️⃣ Select Date", ["-- Select Date --"] + dates, key="stored_date")
            
            if selected_date and selected_date != "-- Select Date --":
                # Find the matching file
                matching_files = [e['file'] for e in date_entries if e['date'] == selected_date]
                
                if matching_files:
                    filename = matching_files[0]
                    st.success(f"📁 Viewing: {filename}")
                    
                    # Load and display the file
                    df = load_assessment_file(filename)
                    
                    if df is not None and not df.empty:
                        # Show summary of students
                        if 'name' in df.columns or 'student_name' in df.columns:
                            name_col = 'name' if 'name' in df.columns else 'student_name'
                            unique_students = df[name_col].nunique()
                            st.info(f"👥 {unique_students} student(s) in this assessment")
                        
                        # Display data
                        st.dataframe(df, width='stretch')
                        
                        # Download option
                        csv_data = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download this Assessment",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv"
                        )
                    else:
                        st.warning("Could not load assessment data")
    
    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh List"):
        st.rerun()


def perform_assessment_with_storage(student_name, school_name, class_name, observations):
    """Perform individual student assessment with storage integration"""
    try:
        with st.spinner("🔍 Analyzing student behavior and assessing personality traits..."):
            result = st.session_state.assessment_system.assess_student_personality(observations)
        
        # Display results
        st.subheader(f"📊 Assessment Results for {student_name}")
        
        if result.get('error'):
            error_msg = result['error']
            if "429" in error_msg and "quota" in error_msg.lower():
                st.error("❌ Rate limit exceeded! Please wait a moment and try again.")
                st.info("💡 Tips to avoid rate limits:")
                st.info("• Wait 1-2 minutes between assessments")
                st.info("• Consider upgrading to a paid API plan")
                st.info("• Use batch processing for multiple students")
            else:
                st.error(f"❌ Assessment failed: {error_msg}")
            return
        
        if result.get('raw_response'):
            st.warning("⚠️ Raw response received (JSON parsing failed)")
            st.code(result['raw_response'])
            return
        
        if result.get('assessments'):
            # Group assessments by level
            levels = ['HIGH', 'MIDDLE', 'LOW', 'NOT OBSERVED']
            grouped = {level: [] for level in levels}
            
            for assessment in result['assessments']:
                grouped[assessment['level']].append(assessment)
            
            # Display in columns
            cols = st.columns(4)
            for i, level in enumerate(levels):
                with cols[i]:
                    st.metric(
                        label=level,
                        value=len(grouped[level]),
                        delta=f"{len(grouped[level])} qualities"
                    )
            
            # Detailed breakdown
            st.subheader("📋 Detailed Assessment")
            for level in levels:
                if grouped[level]:
                    with st.expander(f"{level} ({len(grouped[level])} qualities)"):
                        for assessment in grouped[level]:
                            st.write(f"**{assessment['quality']}**")
                            if assessment.get('reasoning'):
                                st.write(f"*{assessment['reasoning']}*")
                            st.divider()
            
            # Summary
            if result.get('summary'):
                st.subheader("📝 Overall Summary")
                st.info(result['summary'])
            
            # Save as CSV with new naming: studentname_schoolname_date.csv
            save_individual_assessment_csv(student_name, school_name, class_name, observations, result)
        else:
            st.warning("No assessment data available")
            
    except Exception as e:
        st.error(f"❌ Assessment failed: {str(e)}")

def handle_assessment_storage(student_name, observations, result):
    """Handle storage of assessment with duplicate checking"""
    storage_manager = st.session_state.storage_manager
    assessment_date = datetime.now().strftime("%Y-%m-%d")
    
    # Check for duplicates
    is_duplicate, existing_data = storage_manager.check_duplicate_assessments(student_name, assessment_date)
    
    if is_duplicate:
        # Show duplicate handling interface
        st.markdown("---")
        st.subheader("⚠️ Duplicate Assessment Detected")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Existing Assessment:**")
            st.text(str(existing_data['data']))
        
        with col2:
            st.write("**New Assessment:**")
            st.text(f"Observations: {observations}")
            formatted_assessment = storage_manager.format_assessment_data(result)
            st.text(f"Assessment:\n{formatted_assessment}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Replace Existing", key=f"replace_{student_name}_{assessment_date}"):
                if storage_manager.replace_assessment(student_name, observations, result, assessment_date):
                    st.success("✅ Assessment replaced successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to replace assessment")
        
        with col2:
            if st.button("➕ Append to Existing", key=f"append_{student_name}_{assessment_date}"):
                if storage_manager.append_assessment(student_name, observations, result, assessment_date):
                    st.success("✅ Assessment appended successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to append assessment")
        
        with col3:
            if st.button("❌ Cancel", key=f"cancel_{student_name}_{assessment_date}"):
                st.info("Assessment not saved")
    else:
        # No duplicate, save normally
        if storage_manager.add_assessment(student_name, observations, result, assessment_date):
            st.success("✅ Assessment saved successfully!")
        else:
            st.error("❌ Failed to save assessment")

def perform_assessment(student_name, observations):
    """Perform individual student assessment"""
    try:
        with st.spinner("🔍 Analyzing student behavior and assessing personality traits..."):
            result = st.session_state.assessment_system.assess_student_personality(observations)
        
        # Display results
        st.subheader(f"📊 Assessment Results for {student_name}")
        
        if result.get('error'):
            error_msg = result['error']
            if "429" in error_msg and "quota" in error_msg.lower():
                st.error("❌ Rate limit exceeded! Please wait a moment and try again.")
                st.info("💡 Tips to avoid rate limits:")
                st.info("• Wait 1-2 minutes between assessments")
                st.info("• Consider upgrading to a paid API plan")
                st.info("• Use batch processing for multiple students")
            else:
                st.error(f"❌ Assessment failed: {error_msg}")
            return
        
        if result.get('raw_response'):
            st.warning("⚠️ Raw response received (JSON parsing failed)")
            st.code(result['raw_response'])
            return
        
        if result.get('assessments'):
            # Group assessments by level
            levels = ['HIGH', 'MIDDLE', 'LOW', 'NOT OBSERVED']
            grouped = {level: [] for level in levels}
            
            for assessment in result['assessments']:
                grouped[assessment['level']].append(assessment)
            
            # Display in columns
            cols = st.columns(4)
            for i, level in enumerate(levels):
                with cols[i]:
                    st.metric(
                        label=level,
                        value=len(grouped[level]),
                        delta=f"{len(grouped[level])} qualities"
                    )
            
            # Detailed breakdown
            st.subheader("📋 Detailed Assessment")
            for level in levels:
                if grouped[level]:
                    with st.expander(f"{level} ({len(grouped[level])} qualities)"):
                        for assessment in grouped[level]:
                            st.write(f"**{assessment['quality']}**")
                            if assessment.get('reasoning'):
                                st.write(f"*{assessment['reasoning']}*")
                            st.divider()
            
            # Summary
            if result.get('summary'):
                st.subheader("📝 Overall Summary")
                st.info(result['summary'])
            
            # Save assessment
            save_assessment(student_name, observations, result)
        else:
            st.warning("No assessment data available")
            
    except Exception as e:
        st.error(f"❌ Assessment failed: {str(e)}")

def process_batch_assessment(df, school_name, class_name):
    """Process batch assessment from CSV with checkpoint recovery"""
    # Generate timestamp and safe filename components
    date_str = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sanitize names for filename
    safe_school = "".join([c for c in school_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
    safe_class = "".join([c for c in class_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
    
    # Filename format: schoolname_class_date.csv
    csv_filename = f"{safe_school}_{safe_class}_{date_str}.csv"
    checkpoint_file = f"assessments/checkpoint_{timestamp}.csv"
    
    try:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        os.makedirs("assessments", exist_ok=True)
        
        # Validate required columns
        if 'Name' not in df.columns:
            st.error("❌ CSV must have a 'Name' column")
            return
        if 'Observations' not in df.columns:
            st.error("❌ CSV must have an 'Observations' column")
            return
        
        for idx, row in df.iterrows():
            student_name = row.get('Name', f'Student_{idx+1}')
            observations = row.get('Observations', '')
            
            status_text.text(f"Assessing {student_name} ({idx + 1}/{len(df)})")
            
            try:
                result = st.session_state.assessment_system.assess_student_personality(observations)
                results.append({
                    'student_id': f"student_{idx+1}",
                    'name': student_name,
                    'school': school_name,
                    'class': class_name,
                    'observations': observations,
                    'assessment': result
                })
            except Exception as e:
                results.append({
                    'student_id': f"student_{idx+1}",
                    'name': student_name,
                    'school': school_name,
                    'class': class_name,
                    'observations': observations,
                    'error': str(e)
                })
            
            # Save checkpoint after each student as CSV
            checkpoint_df = pd.DataFrame(results)
            checkpoint_df.to_csv(checkpoint_file, index=False, encoding='utf-8')
            
            progress_bar.progress((idx + 1) / len(df))
        
        # Persist final results to session and render review UI
        st.session_state.batch_results = results
        st.session_state.batch_timestamp = timestamp

        # Save final results as CSV with proper naming
        final_csv_path = f"assessments/{csv_filename}"
        results_df = build_csv_from_results(results)
        results_df.to_csv(final_csv_path, index=False, encoding='utf-8')
        st.session_state.saved_batch_csv = csv_filename
        
        # Clean up checkpoint file on successful completion
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)

        # Build and persist review dataframe
        st.session_state.review_df = build_review_dataframe(results)
        
        st.success(f"✅ Batch assessment saved to: {csv_filename}")

        # Trigger rerun so the tab renders the review interface once
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Batch assessment failed: {str(e)}")
        if os.path.exists(checkpoint_file):
            st.info(f"💾 Partial results saved to: {checkpoint_file}")



def manual_batch_form(num_students):
    """Create manual batch entry form"""
    st.subheader(f"✏️ Manual Entry for {num_students} Students")
    
    students_data = []
    
    for i in range(num_students):
        with st.expander(f"Student {i+1}", expanded=True):
            name = st.text_input(f"Name {i+1}", key=f"name_{i}")
            observations = st.text_area(f"Observations {i+1}", height=100, key=f"obs_{i}")
            
            if name and observations:
                students_data.append({
                    'Name': name,
                    'Observations': observations
                })
    
    if students_data and st.button("🚀 Assess All Students", type="primary"):
        process_batch_assessment(pd.DataFrame(students_data))

def build_review_dataframe(results):
    """Construct review dataframe from batch results."""
    review_rows = []
    for r in results:
        name_val = r.get('name', '')
        obs_val = r.get('observations', '')
        if r.get('error'):
            predicted = []
        else:
            predicted = extract_predicted_labels(r.get('assessment', {}))
        review_rows.append({
            'Name': name_val,
            'Observations': obs_val,
            'Predicted Labels': predicted,
            'Final Labels': list(predicted),
            'Approved': False
        })
    return pd.DataFrame(review_rows)

def render_review_interface():
    """Render the persistent reviewer interface using session state."""
    results = st.session_state.batch_results or []
    timestamp = st.session_state.batch_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    review_df = st.session_state.review_df
    if review_df is not None and 'Error' in review_df.columns:
        review_df = review_df.drop(columns=['Error'])
        st.session_state.review_df = review_df

    st.subheader("📊 Batch Assessment Results")
    successful = len([r for r in results if not r.get('error')])
    failed = len([r for r in results if r.get('error')])
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Successful", successful)
    with col2:
        st.metric("❌ Failed", failed)
    with col3:
        if st.session_state.saved_batch_csv:
            st.info(f"Saved CSV: {st.session_state.saved_batch_csv}")

    st.markdown("---")
    st.subheader("🧐 Review and Approve Predicted Labels")
    show_debug = st.toggle("Show raw assessments (debug)", value=False)

    edited_df = st.data_editor(
        review_df,
        key=f"review_editor_{timestamp}",
        width='stretch',
        num_rows="fixed",
        column_config={
            "Predicted Labels": st.column_config.ListColumn(
                help="Model-predicted labels (quality-level).",
                width="medium"
            ),
            "Final Labels": st.column_config.ListColumn(
                help="Edit labels as needed before approval.",
                width="medium"
            ),
            "Approved": st.column_config.CheckboxColumn(help="Tick after reviewing this row.")
        }
    )

    all_approved = bool(len(edited_df) > 0 and edited_df["Approved"].all())
    if not all_approved:
        st.info("Review rows and tick 'Approved' for each before finalizing.")

    if show_debug and results:
        st.markdown("---")
        with st.expander("Raw assessment data by row"):
            for i, r in enumerate(results):
                st.write(f"Row {i+1}: {r.get('name','')}")
                if r.get('error'):
                    st.error(r.get('error'))
                elif r.get('assessment'):
                    st.code(json.dumps(r['assessment'], indent=2, ensure_ascii=False))
                else:
                    st.warning("No assessment returned for this row.")

    if st.button("✅ Finalize & Download CSV", type="primary", disabled=not all_approved):
        # Persist final edits once
        st.session_state.review_df = edited_df
        export_df = edited_df[["Name", "Observations", "Final Labels"]].copy()
        export_df["Predicted Labels"] = edited_df["Predicted Labels"].apply(lambda x: json.dumps(x, ensure_ascii=False))
        export_df["Final Labels"] = export_df["Final Labels"].apply(lambda x: json.dumps(x, ensure_ascii=False))
        
        # Add school, class, and date columns from batch results for stored assessments indexing
        if results:
            school_name = results[0].get('school', 'Unknown')
            class_name = results[0].get('class', 'Unknown')
            date_str = datetime.now().strftime("%Y-%m-%d")
            export_df['school'] = school_name
            export_df['class'] = class_name
            export_df['date'] = date_str
        
        export_df = export_df[["Name", "Observations", "Predicted Labels", "Final Labels", "school", "class", "date"]]

        csv_bytes = export_df.to_csv(index=False).encode('utf-8')
        
        # Use the same filename that was created during batch processing (schoolname_class_date.csv)
        csv_name = st.session_state.saved_batch_csv or f"batch_assessment_{timestamp}.csv"

        os.makedirs("assessments", exist_ok=True)
        with open(f"assessments/{csv_name}", "wb") as cf:
            cf.write(csv_bytes)

        st.success(f"💾 Reviewed CSV saved to: {csv_name}")
        st.download_button(
            label="⬇️ Download Reviewed CSV",
            data=csv_bytes,
            file_name=csv_name,
            mime="text/csv"
        )

def store_approved_batch_assessments(edited_df, results):
    """Store approved batch assessments in the main storage system"""
    storage_manager = st.session_state.storage_manager
    assessment_date = datetime.now().strftime("%Y-%m-%d")
    
    stored_count = 0
    duplicate_count = 0
    
    for idx, row in edited_df.iterrows():
        if not row.get('Approved', False):
            continue
            
        student_name = row['Name']
        observations = row['Observations']
        
        # Find the corresponding assessment result
        assessment_result = None
        for result in results:
            if result.get('name') == student_name:
                assessment_result = result.get('assessment')
                break
        
        if not assessment_result:
            continue
        
        # Check for duplicates
        is_duplicate, _ = storage_manager.check_duplicate_assessments(student_name, assessment_date)
        
        if is_duplicate:
            duplicate_count += 1
            st.warning(f"⚠️ Skipping {student_name} - duplicate assessment for {assessment_date}")
        else:
            if storage_manager.add_assessment(student_name, observations, assessment_result, assessment_date):
                stored_count += 1
            else:
                st.error(f"❌ Failed to store assessment for {student_name}")
    
    if stored_count > 0:
        st.success(f"✅ Stored {stored_count} assessments in main storage system")
    if duplicate_count > 0:
        st.info(f"ℹ️ Skipped {duplicate_count} duplicate assessments")

def _normalize_quality(text: str, allowed: set) -> str:
    t = text.lower().strip()
    # keep letters and spaces
    t = re.sub(r"[^a-z\s]", " ", t)
    # collapse spaces and hyphenate
    t = "-".join([p for p in t.split() if p])
    if t in allowed:
        return t
    # token overlap fallback
    tokens = set(t.split("-"))
    best = None
    best_score = 0
    for a in allowed:
        score = len(tokens.intersection(set(a.split("-"))))
        if score > best_score:
            best, best_score = a, score
    return best if best and best_score > 0 else ""

def extract_predicted_labels(assessment_result):
    """Return normalized labels in 'quality-level' format, filtering invalid/duplicate entries."""
    # Allowed levels mapping
    level_map = {
        'low': 'low',
        'middle': 'middle',
        'mid': 'middle',
        'medium': 'middle',
        'high': 'high',
        'not observed': 'not observed',
        'not_observed': 'not observed',
        'notobserved': 'not observed',
        'na': 'not observed',
        'n/a': 'not observed'
    }
    
    # Extract assessments from result
    assessments = assessment_result.get('assessments', [])
    if not assessments:
        return []
    
    # Allowed qualities set (normalized hyphen-case) from config
    allowed_qualities = {q.lower().replace(' ', '-') for q in PERSONALITY_QUALITIES}
    
    labels = []
    seen = set()
    
    for item in assessments:
        quality_raw = item.get('quality', '')
        level_raw = item.get('level', '')
        
        if not quality_raw or not level_raw:
            continue
        
        # Normalize quality name
        quality_normalized = _normalize_quality(quality_raw, allowed_qualities)
        if not quality_normalized:
            continue
        
        # Normalize level
        level_lower = level_raw.lower().strip()
        level_normalized = level_map.get(level_lower, '')
        
        # Skip 'not observed' entries and invalid levels
        if not level_normalized or level_normalized == 'not observed':
            continue
        
        # Create label and check for duplicates
        label = f"{quality_normalized}:{level_normalized}"
        if label not in seen:
            seen.add(label)
            labels.append(label)
    
    return labels

def swot_analysis_tab():
    st.header("📋 Report Card & SWOT Analysis")
    
    tab1, tab2, tab3 = st.tabs(["👤 Individual Analysis", "👥 Batch Analysis", "📄 Generate Report Cards"])
    
    with tab1:
        st.subheader("📝 Student Information")
        student_name = st.text_input("Student Name", placeholder="Enter student's full name", key="swot_student_name")
        observations = st.text_area(
            "Observer Notes", 
            height=200,
            placeholder="Enter detailed observations...",
            key="swot_observations"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Generate English SWOT", type="primary", disabled=not (student_name and observations)):
                if student_name and observations:
                    try:
                        with st.spinner("Generating SWOT Analysis..."):
                            if st.session_state.assessment_system:
                                result = st.session_state.assessment_system.generate_swot_analysis(observations)
                                if result.get('error'):
                                    st.error(f"Analysis failed: {result['error']}")
                                else:
                                    display_swot_grid(student_name, result)
                            else:
                                st.error("System not initialized.")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        with col2:
             if st.button("🇮🇳 Generate Marathi SWOT", disabled=not (student_name and observations)):
                if student_name and observations:
                    try:
                        with st.spinner("Generating Marathi SWOT Analysis..."):
                            if st.session_state.assessment_system:
                                result = st.session_state.assessment_system.generate_marathi_swot(observations)
                                if result.get('error'):
                                    st.error(f"Analysis failed: {result['error']}")
                                else:
                                    display_swot_grid(student_name, result, is_marathi=True)
                            else:
                                st.error("System not initialized.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab2:
        st.subheader("📁 Upload CSV for Batch SWOT")
        uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'], key="swot_batch_upload")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.info(f"Loaded {len(df)} students.")
                if st.button("🚀 Start Batch SWOT Analysis"):
                    process_batch_swot(df)
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
                
    with tab3:
        report_card_generation_tab()

def report_card_generation_tab():
    st.markdown("### 🎓 Report Card Generation (Marathi)")
    st.info("Upload your Excel template and Student Data CSV to generate bulk report cards.")
    
    # 1. Template Upload
    st.subheader("1. Upload Template (Excel)")
    template_file = st.file_uploader("Upload Report Card Template (.xlsx)", type=['xlsx'], key="rc_template")
    
    if template_file:
        from ai_core.report_card_generator import ReportCardGenerator
        generator = ReportCardGenerator()
        generator.set_template(template_file)
        st.success("✅ Template loaded successfully!")
        
    # 2. Data Upload
    st.subheader("2. Upload Student Data (CSV)")
    st.markdown("CSV Columns required: `Name`, `School` (optional), `Observations`")
    data_file = st.file_uploader("Upload Student Data (.csv)", type=['csv'], key="rc_data")
    
    if data_file and template_file:
        df = pd.read_csv(data_file)
        st.write("Preview:", df.head(3))
        
        if st.button("🚀 Generate Report Cards"):
            progress_bar = st.progress(0)
            status_txt = st.empty()
            
            batch_data = []
            errors = []
            
            for idx, row in df.iterrows():
                status_txt.text(f"Processing {row.get('Name', 'Student')}... ({idx+1}/{len(df)})")
                
                try:
                    # Generate Marathi SWOT
                    swot_res = st.session_state.assessment_system.generate_marathi_swot(row['Observations'])
                    
                    if swot_res.get('error'):
                        errors.append(f"{row.get('Name')}: {swot_res['error']}")
                        continue
                        
                    batch_data.append({
                        'name': row.get('Name', 'Unknown'),
                        'school': row.get('School', ''),
                        'swot_data': swot_res
                    })
                    
                except Exception as e:
                    errors.append(f"{row.get('Name')}: {str(e)}")
                
                progress_bar.progress((idx + 1) / len(df))
            
            # Generate Files
            status_txt.text("Creating Excel files...")
            try:
                from ai_core.report_card_generator import ReportCardGenerator
                gen = ReportCardGenerator()
                zip_path, gen_errors = gen.batch_generate(batch_data)
                
                errors.extend(gen_errors)
                
                st.success("🎉 Generation Completed!")
                
                if errors:
                    with st.expander("⚠️ Errors occurred"):
                        for e in errors:
                            st.write(e)
                
                # Download Button
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="📥 Download All Report Cards (ZIP)",
                        data=f,
                        file_name="report_cards.zip",
                        mime="application/zip"
                    )
                    
            except Exception as e:
                st.error(f"Generation failed: {e}")

def display_swot_grid(name, result, is_marathi=False):
    st.markdown(f"### SWOT Analysis for **{name}**")
    
    if result.get('summary'):
        st.info(f"**Strategic Summary:** {result['summary']}")
    
    items = result.get('swot_items', [])
    strengths = [i for i in items if i['category'] == 'STRENGTH']
    weaknesses = [i for i in items if i['category'] == 'WEAKNESS']
    opportunities = [i for i in items if i['category'] == 'OPPORTUNITY']
    threats = [i for i in items if i['category'] == 'THREAT']
    
    # 2x2 Grid Layout
    col1, col2 = st.columns(2)
    
    # Headers based on language
    h_s = "💪 Strengths (क्षमता)" if is_marathi else "💪 Strengths"
    h_w = "⚠️ Weaknesses (कमतरता)" if is_marathi else "⚠️ Weaknesses"
    h_o = "🌟 Opportunities (संधी)" if is_marathi else "🌟 Opportunities"
    h_t = "🛡️ Threats (भीती)" if is_marathi else "🛡️ Threats"

    with col1:
        st.markdown(f"#### {h_s}")
        for s in strengths:
            st.success(f"**{s['point']}**: {s['explanation']}")
            
        st.markdown(f"#### {h_o}")
        for o in opportunities:
            st.info(f"**{o['point']}**: {o['explanation']}")
            
    with col2:
        st.markdown(f"#### {h_w}")
        for w in weaknesses:
            st.warning(f"**{w['point']}**: {w['explanation']}")
            
        st.markdown(f"#### {h_t}")
        for t in threats:
            st.error(f"**{t['point']}**: {t['explanation']}")

def process_batch_swot(df):
    results = []
    progress_bar = st.progress(0)
    
    for idx, row in df.iterrows():
        try:
            res = st.session_state.assessment_system.generate_swot_analysis(row['Observations'])
            results.append({
                "Name": row['Name'],
                "Observations": row['Observations'],
                "SWOT Analysis": json.dumps(res, ensure_ascii=False)
            })
        except Exception as e:
            results.append({
                "Name": row['Name'],
                "Observations": row['Observations'],
                "Error": str(e)
            })
        progress_bar.progress((idx + 1) / len(df))
        
    st.success("Batch Analysis Completed!")
    
    # Create downloadable CSV
    result_df = pd.DataFrame(results)
    csv = result_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="⬇️ Download Batch SWOT Results",
        data=csv,
        file_name="batch_swot_analysis.csv",
        mime="text/csv"
    )

def save_assessment(student_name, observations, result):
    """Save individual assessment to file"""
    try:
        assessment_data = {
            'student_name': student_name,
            'observations': observations,
            'assessment': result,
            'timestamp': datetime.now().isoformat()
        }
        
        os.makedirs("assessments", exist_ok=True)
        filename = f"assessments/{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(assessment_data, f, indent=2, ensure_ascii=False)
        
        st.success(f"💾 Assessment saved to: {filename}")
        
    except Exception as e:
        st.warning(f"⚠️ Could not save assessment: {str(e)}")

if __name__ == "__main__":
    main()


