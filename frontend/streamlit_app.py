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
if 'saved_batch_json' not in st.session_state:
    st.session_state.saved_batch_json = None

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
        st.info("👈 Please set up the system in the sidebar first by providing your OpenAI API key and initializing the system.")
        return
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Individual Assessment", "👥 Batch Assessment", "📁 Export Template", "📋 System Info"])
    
    with tab1:
        individual_assessment_tab()
    
    with tab2:
        batch_assessment_tab()
    
    with tab3:
        export_template_tab()
    
    with tab4:
        system_info_tab()

def individual_assessment_tab():
    st.header("🔍 Individual Student Assessment")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Student Information")
        student_name = st.text_input("Student Name", placeholder="Enter student's full name")
        observations = st.text_area(
            "Observer Notes", 
            height=200,
            placeholder="Enter detailed observations about the student's behavior during the session...\n\nInclude observations about:\n• Participation and engagement\n• Social interactions\n• Academic behavior\n• Emotional responses\n• Any other relevant behaviors"
        )
        
        if st.button("🎯 Assess Personality", type="primary", disabled=not (student_name and observations)):
            if student_name and observations:
                perform_assessment(student_name, observations)
    
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
    
    # File upload option
    st.subheader("📁 Upload CSV File")
    uploaded_file = st.file_uploader(
        "Choose a CSV file", 
        type=['csv'],
        help="CSV should have columns: Name, Observations"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Successfully loaded {len(df)} students")
            
            # Display preview
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(), width='stretch')
            
            if st.button("🚀 Start Batch Assessment", type="primary"):
                process_batch_assessment(df)
                
        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")
    
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
            st.session_state.saved_batch_json = None
            st.rerun()

    if st.session_state.review_df is not None:
        render_review_interface()

def export_template_tab():
    st.header("📁 Export Reference Sheet Template")
    
    st.info("Download a CSV template that you can fill with your reference observations and import into Google Sheets.")
    
    if st.button("📥 Download CSV Template"):
        try:
            processor = CSVReferenceProcessor()
            processor.export_reference_data_to_csv("reference_sheet_template.csv")
            
            # Read the generated file and provide download
            if os.path.exists("reference_sheet_template.csv"):
                with open("reference_sheet_template.csv", "r") as f:
                    csv_data = f.read()
                
                st.download_button(
                    label="💾 Download Template",
                    data=csv_data,
                    file_name="personality_assessment_template.csv",
                    mime="text/csv"
                )
            else:
                st.error("Template file not found")
        except Exception as e:
            st.error(f"Error creating template: {str(e)}")

def system_info_tab():
    st.header("📋 System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 System Status")
        if st.session_state.assessment_system:
            st.success("✅ Assessment System: Active")
            st.success("✅ Vector Database: Loaded")
            st.success("✅ LLM Model: Ready")
        else:
            st.error("❌ Assessment System: Not Initialized")
        
        st.subheader("📚 Available Qualities")
        qualities = [
            "Adaptability", "Academic achievement", "Boldness", "Competition", 
            "Creativity", "Enthusiasm", "Excitability", "General ability",
            "Guilt proneness", "Individualism", "Innovation", "Leadership",
            "Maturity", "Mental health", "Morality", "Self control",
            "Sensitivity", "Self sufficiency", "Social warmth", "Tension"
        ]
        
        for i, quality in enumerate(qualities, 1):
            st.write(f"{i:2d}. {quality}")
    
    with col2:
        st.subheader("📖 Reference Data")
        if os.path.exists("map-t.pdf"):
            st.success("✅ PDF Definitions: Available")
            st.info("Contains detailed definitions of all 20 personality qualities")
        else:
            st.warning("⚠️ PDF Definitions: Not Found")
        
        st.subheader("💾 Data Storage")
        if os.path.exists("assessments"):
            assessment_files = len([f for f in os.listdir("assessments") if f.endswith('.json')])
            st.info(f"📁 Assessment files: {assessment_files}")
        else:
            st.info("📁 Assessment files: 0")

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

def process_batch_assessment(df):
    """Process batch assessment from CSV"""
    try:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, row in df.iterrows():
            status_text.text(f"Assessing {row['Name']} ({idx + 1}/{len(df)})")
            
            try:
                result = st.session_state.assessment_system.assess_student_personality(row['Observations'])
                results.append({
                    'student_id': f"student_{idx+1}",
                    'name': row['Name'],
                    'observations': row['Observations'],
                    'assessment': result
                })
            except Exception as e:
                results.append({
                    'student_id': f"student_{idx+1}",
                    'name': row['Name'],
                    'observations': row.get('Observations', ''),
                    'error': str(e)
                })
            
            progress_bar.progress((idx + 1) / len(df))
        
        # Persist results to session and render review UI
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.batch_results = results
        st.session_state.batch_timestamp = timestamp

        os.makedirs("assessments", exist_ok=True)
        filename = f"batch_assessment_{timestamp}.json"
        with open(f"assessments/{filename}", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        st.session_state.saved_batch_json = filename

        # Build and persist review dataframe
        st.session_state.review_df = build_review_dataframe(results)

        # Trigger rerun so the tab renders the review interface once
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Batch assessment failed: {str(e)}")

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
        if st.session_state.saved_batch_json:
            st.info(f"Saved JSON: {st.session_state.saved_batch_json}")

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
        export_df = export_df[["Name", "Observations", "Predicted Labels", "Final Labels"]]

        csv_bytes = export_df.to_csv(index=False).encode('utf-8')
        csv_name = f"batch_assessment_{timestamp}.csv"

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
    # Allowed qualities set (normalized hyphen-case) from config
    allowed_qualities = set([q.lower().replace(' ', '-') for q in PERSONALITY_QUALITIES])
    try:
        items = assessment_result.get('assessments', [])
    except AttributeError:
        return []
    labels = []
    for item in items:
        try:
            q_raw = str(item.get('quality', ''))
            q_norm = _normalize_quality(q_raw, allowed_qualities)
            l_raw = str(item.get('level', '')).strip().lower()
            # extract clean level even if noisy text like "Level: HIGH" or "high." etc.
            m = re.search(r"low|middle|mid|medium|high|not\s*observed|n/?a", l_raw)
            key = m.group(0) if m else l_raw
            key = key.replace('  ', ' ').replace('_', ' ')
            l_norm = level_map.get(key, level_map.get(key.strip(), key.strip()))
            if q_norm in allowed_qualities and l_norm in ('low', 'middle', 'high'):
                labels.append(f"{q_norm}-{l_norm}")
        except Exception:
            continue
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for lab in labels:
        if lab not in seen:
            seen.add(lab)
            deduped.append(lab)
    return deduped

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


