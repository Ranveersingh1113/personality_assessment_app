import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from personality_assessment import PersonalityAssessmentSystem
from csv_reference_processor import CSVReferenceProcessor
from fpdf import FPDF

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
    # Add this CSS right after st.title() 
    st.markdown("""
    <style>
        /* Global dark theme */
        .stApp {
            background-color: #1E1E1E;
        }
        
        /* Make all text visible on dark background */
        .stMarkdown, .stText, h1, h2, h3, p {
            color: #E0E0E0 !important;
        }
        
        /* Style cards consistently across tabs */
        .profile-card, .report-card, .info-card {
            background-color: #2D2D2D;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        
        /* Style Streamlit inputs */
        .stTextInput, .stTextArea, .stSelectbox {
            background-color: #363636 !important;
            color: #E0E0E0 !important;
            border-color: #4D4D4D !important;
        }
        
        /* Style metric cards */
        .stMetric {
            background-color: #2D2D2D !important;
            border-radius: 10px !important;
            padding: 10px !important;
        }
        
        /* Style info/success/error boxes */
        .stAlert {
            background-color: #2D2D2D !important;
            color: #E0E0E0 !important;
            border: 1px solid #4D4D4D !important;
        }
        
        /* Style data tables/frames */
        .stDataFrame {
            background-color: #2D2D2D !important;
            color: #E0E0E0 !important;
        }
        
        /* Style tabs */
        .stTab {
            background-color: #2D2D2D !important;
            color: #E0E0E0 !important;
        }
        
        /* Style buttons */
        .stButton button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
        }
        
        /* Style sidebar */
        .css-1d391kg {  /* Sidebar class */
            background-color: #2D2D2D !important;
        }
    </style>
    """, unsafe_allow_html=True)

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
            from rate_limiter import get_rate_limiter
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
            st.info("Using Gemini 1.5 Flash + Hugging Face All-MiniLM-L6-v2")
        else:
            st.info("System needs initialization")
    
    # Main content area
    if not st.session_state.system_ready:
        st.info("👈 Please set up the system in the sidebar first by providing your OpenAI API key and initializing the system.")
        return
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Individual Assessment", 
        "👥 Batch Assessment", 
        "📊 Student Dashboard",
        "📁 Export Template", 
        "📋 System Info"
    ])
    
    with tab1:
        individual_assessment_tab()
    
    with tab2:
        batch_assessment_tab()
    
    with tab3:
        student_dashboard_tab()
    
    with tab4:
        export_template_tab()
    
    with tab5:
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

def student_dashboard_tab():
    """Display the student personality dashboard (shows all 20 qualities)."""
    st.markdown("""
    <style>
        /* Trait bars */
        .trait-bar {
            margin-bottom: 12px;
        }
        .trait-bar .label {
            font-size: 14px;
            margin-bottom: 6px;
        }
        .bar {
            height: 18px;
            border-radius: 9px;
        }
        .bar-high { background-color: rgba(92, 184, 92, 0.9); }
        .bar-middle { background-color: rgba(240, 173, 78, 0.9); }
        .bar-low { background-color: rgba(217, 83, 79, 0.9); }
        .bar-na { background-color: rgba(224, 224, 224, 0.3); }
    </style>
    """, unsafe_allow_html=True)
    
    # Helper: build SWOT and summary text from 20 traits
    def build_swot_and_summary(student_name, traits_list):
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        
        # PDF Styling
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'SWOT Analysis Report - {student_name}', ln=True)
        pdf.line(10, 30, 200, 30)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.ln(10)
        
        # Categorize traits
        strengths = [t for t in traits_list if t['level'] == 'HIGH']
        weaknesses = [t for t in traits_list if t['level'] == 'LOW']
        middles = [t for t in traits_list if t['level'] == 'MIDDLE']
        
        # Add SWOT sections
        sections = [
            ("Strengths", strengths, "These are areas where the student excels:"),
            ("Weaknesses", weaknesses, "These areas need improvement:"),
            ("Opportunities", middles, "These areas show potential for growth:"),
        ]
        
        for title, traits, intro in sections:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, title, ln=True)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, intro)
            for t in traits:
                pdf.cell(0, 8, f"• {t['quality']}", ln=True)
            pdf.ln(5)
        
        # Summary section
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Overall Summary', ln=True)
        pdf.set_font('Arial', '', 10)
        summary = (f"Assessment shows {len(strengths)} strengths, "
                  f"{len(middles)} areas with potential, and "
                  f"{len(weaknesses)} areas needing attention.")
        pdf.multi_cell(0, 5, summary)
        
        # Return both PDF bytes and text preview
        return pdf.output(dest='S').encode('latin-1'), summary

    def generate_and_offer_report(student_name, traits, selected_file):
        try:
            pdf_bytes, preview_text = build_swot_and_summary(student_name, traits)
            
            # Show preview
            with st.expander("📄 Report Preview", expanded=True):
                st.text(preview_text)
            
            # Offer download
            st.download_button(
                label="⬇️ Download SWOT Report (PDF)",
                data=pdf_bytes,
                file_name=f"{student_name.replace(' ', '_')}_SWOT.pdf",
                mime="application/pdf",
                key=f"download_report_{selected_file}"
            )
            
            # Store in session state
            st.session_state[f"report_{selected_file}"] = {
                'pdf': pdf_bytes,
                'preview': preview_text
            }
            
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")

    # Student selector
    st.subheader("👤 Select Student")
    selected_file = st.selectbox(
        "Choose a student assessment",
        options=assessment_files,
        format_func=lambda x: x.split('_')[0].replace('_', ' ').title()
    )

    if not selected_file:
        return

    try:
        with open(f"assessments/{selected_file}", "r", encoding="utf-8") as f:
            assessment_data = json.load(f)
    except Exception as e:
        st.error(f"Error reading assessment file: {str(e)}")
        return

    # Normalize assessments into a lookup by quality (case-insensitive)
    raw_assessments = assessment_data.get('assessment', {}).get('assessments', []) or []
    lookup = {}
    for a in raw_assessments:
        q = str(a.get('quality', '')).strip().lower()
        if q:
            lookup[q] = a

    # Full ordered list of 20 qualities (matches README / design)
    qualities_order = [
        "Adaptability", "Academic achievement", "Boldness", "Competition",
        "Creativity", "Enthusiasm", "Excitability", "General ability",
        "Guilt proneness", "Individualism", "Innovation", "Leadership",
        "Maturity", "Mental health", "Morality", "Self control",
        "Sensitivity", "Self sufficiency", "Social warmth", "Tension"
    ]

    # Build traits list (ensures all 20 are present)
    traits = []
    for q in qualities_order:
        key = q.strip().lower()
        item = lookup.get(key)
        if item:
            level = item.get('level', 'NOT OBSERVED')
        else:
            level = 'NOT OBSERVED'
        # Map levels to width & class
        if level == 'HIGH':
            width = 80
            cls = 'high'
        elif level == 'MIDDLE':
            width = 55
            cls = 'middle'
        elif level == 'LOW':
            width = 30
            cls = 'low'
        else:
            width = 6
            cls = 'na'
        traits.append({'quality': q, 'level': level, 'width': width, 'cls': cls})

    # Layout: profile (1) and report (3)
    profile_col, report_col = st.columns([1, 3])

    # Profile Card
    with profile_col:
        student_name = assessment_data.get('student_name', selected_file.split('_')[0].replace('_', ' ').title())
        timestamp = assessment_data.get('timestamp', '')
        date_str = ""
        try:
            if timestamp:
                # support ISO and simple formats
                try:
                    date_str = datetime.fromisoformat(timestamp).strftime('%d / %m / %Y')
                except Exception:
                    date_str = timestamp.split('T')[0]
        except Exception:
            date_str = ""

        st.markdown(f"""
            <div class="profile-card">
                <div style="font-size:20px;font-weight:600;margin-bottom:20px;color:#E0E0E0;">{student_name}</div>
                <div style="text-align:left;color:#E0E0E0;">
                    <div><strong>Class:</strong> 7th</div>
                    <div><strong>Section:</strong> B</div>
                    <div><strong>School:</strong> Vikram School</div>
                    <div><strong>Location:</strong> Saswad</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Report Card
    with report_col:
        # Header - last observation date and Generate button
        last_obs_display = date_str or "15 / 10 / 2025"
        hcol1, hcol2 = st.columns([3, 1])
        with hcol1:
            st.markdown(f"<div style='padding:6px 0;color:#fff;' class='date'>Last Observation Date: {last_obs_display}</div>", unsafe_allow_html=True)
        with hcol2:
            if st.button("Generate Report ➡️", key=f"gen_report_{selected_file}"):
                report_text = build_swot_and_summary(student_name, traits)
                # store in session for persistence per selected file
                st.session_state[f"report_{selected_file}"] = report_text
                generate_and_offer_report(student_name, report_text, selected_file)

        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("Latest Observation Record")

        # Two columns for 20 traits (10 each)
        col1, col2 = st.columns(2)

        def render_trait_bar_html(quality, cls, width):
            return f"""
                <div class="trait-bar">
                    <div class="label">{quality}</div>
                    <div class="bar bar-{cls}" style="width: {width}%;"></div>
                </div>
            """

        # Render first 10 in left column
        with col1:
            for t in traits[:10]:
                st.markdown(render_trait_bar_html(t['quality'], t['cls'], t['width']), unsafe_allow_html=True)

        # Render last 10 in right column
        with col2:
            for t in traits[10:]:
                st.markdown(render_trait_bar_html(t['quality'], t['cls'], t['width']), unsafe_allow_html=True)

        # Optional summary
        summary = assessment_data.get('assessment', {}).get('summary') or ""
        if summary:
            st.markdown("---")
            st.subheader("📝 Summary")
            st.info(summary)

        # When Generate Report button is clicked:
    if st.button("Generate Report ➡️", key=f"gen_report_{selected_file}"):
        generate_and_offer_report(student_name, traits, selected_file)

    # Show previously generated report if it exists
    saved_key = f"report_{selected_file}"
    if saved_key in st.session_state:
        st.markdown("---")
        st.subheader("📄 Previously Generated Report")
        with st.expander("Show Preview", expanded=False):
            st.text(st.session_state[saved_key]['preview'])
        st.download_button(
            label="⬇️ Download Previous Report (PDF)",
            data=st.session_state[saved_key]['pdf'],
            file_name=f"{student_name.replace(' ', '_')}_SWOT.pdf",
            mime="application/pdf",
            key=f"dl_prev_{selected_file}"
        )

        st.markdown('</div>', unsafe_allow_html=True)
# ...existing code...

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
    # Ensure legacy 'Error' column is removed if present
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

    # Do not persist on every tick to avoid per-change processing; persist on finalize only

    if show_debug and results:
        st.markdown("---")
        with st.expander("Raw assessment data by row"):
            for i, r in enumerate(results):
                st.write(f"Row {i+1}: {r.get('name','')}")
                if r.get('error'):
                    st.error(r.get('error'))
                elif r.get('assessment'):
                    st.code(json.dumps(r['assessment'], indent=2, ensure_ascii=False))

    all_approved = bool(len(edited_df) > 0 and edited_df["Approved"].all())
    if not all_approved:
        st.info("Review rows and tick 'Approved' for each before finalizing.")

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

def extract_predicted_labels(assessment_result):
    """Return list of predicted labels in 'quality-level' format excluding NOT OBSERVED."""
    try:
        items = assessment_result.get('assessments', [])
    except AttributeError:
        return []
    labels = []
    for item in items:
        try:
            quality = str(item.get('quality', '')).strip().lower().replace(' ', '-')
            level = str(item.get('level', '')).strip().lower()
            if level and level != 'not observed' and quality:
                labels.append(f"{quality}-{level}")
        except Exception:
            continue
    return labels

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
