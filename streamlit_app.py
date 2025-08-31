import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from personality_assessment import PersonalityAssessmentSystem
from csv_reference_processor import CSVReferenceProcessor

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
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        if st.session_state.system_ready:
            st.info("Vector database loaded with reference data")
            st.info("Using Gemini 1.5 Pro + Hugging Face All-MiniLM-L6-v2")
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
            st.dataframe(df.head(), use_container_width=True)
            
            if st.button("🚀 Start Batch Assessment", type="primary"):
                process_batch_assessment(df)
                
        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")
    
    # Manual entry option
    st.subheader("✏️ Manual Entry")
    num_students = st.number_input("Number of students", min_value=1, max_value=50, value=3)
    
    if st.button("📝 Create Entry Form"):
        manual_batch_form(num_students)

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
            st.error(f"❌ Assessment failed: {result['error']}")
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
            colors = ['success', 'warning', 'danger', 'secondary']
            
            for i, (level, color) in enumerate(zip(levels, colors)):
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
                    'assessment': result
                })
            except Exception as e:
                results.append({
                    'student_id': f"student_{idx+1}",
                    'name': row['Name'],
                    'error': str(e)
                })
            
            progress_bar.progress((idx + 1) / len(df))
        
        # Display results
        st.subheader("📊 Batch Assessment Results")
        
        # Summary statistics
        successful = len([r for r in results if not r.get('error')])
        failed = len([r for r in results if r.get('error')])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ Successful", successful)
        with col2:
            st.metric("❌ Failed", failed)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_assessment_{timestamp}.json"
        
        os.makedirs("assessments", exist_ok=True)
        with open(f"assessments/{filename}", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        st.success(f"💾 Results saved to: {filename}")
        
        # Download results
        st.download_button(
            label="📥 Download Results",
            data=json.dumps(results, indent=2),
            file_name=filename,
            mime="application/json"
        )
        
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
                    'name': name,
                    'observations': observations
                })
    
    if students_data and st.button("🚀 Assess All Students", type="primary"):
        process_batch_assessment(pd.DataFrame(students_data))

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
