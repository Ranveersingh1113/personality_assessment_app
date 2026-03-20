import streamlit as st
import pandas as pd
import json
import os
import sys
import time  # Added for retry delays in batch processing
from datetime import datetime

# Ensure project root is on sys.path so sibling packages import correctly
_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_FRONTEND_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai_core.personality_assessment import PersonalityAssessmentSystem
from ai_core.csv_reference_processor import CSVReferenceProcessor
from ai_core.assessment_storage_manager import AssessmentStorageManager
from ai_core.enhanced_csv_processor import EnhancedCSVProcessor
import re
from config import PERSONALITY_QUALITIES

# Page configuration
st.set_page_config(
    page_title="🎓 Personality Assessment System for Students",
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
if 'csv_processor' not in st.session_state:
    st.session_state.csv_processor = EnhancedCSVProcessor()
else:
    # Ensure the processor has the new methods (for backward compatibility)
    if not hasattr(st.session_state.csv_processor, 'clear_upload_history'):
        st.session_state.csv_processor = EnhancedCSVProcessor()
if 'session_manager' not in st.session_state:
    from ai_core.session_manager import SessionManager
    st.session_state.session_manager = SessionManager()
    # Create or resume session
    session_id = st.session_state.session_manager.create_session()
if 'duplicate_detector' not in st.session_state:
    from ai_core.duplicate_detector import DuplicateDetector
    st.session_state.duplicate_detector = DuplicateDetector()
if 'workflow_protection' not in st.session_state:
    from ai_core.workflow_protection import WorkflowProtection
    st.session_state.workflow_protection = WorkflowProtection()
if 'finalization_complete' not in st.session_state:
    st.session_state.finalization_complete = False

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
            assessments = r['assessment']['assessments']
            
            # Handle both local model format and API model format
            for assessment_item in assessments:
                if isinstance(assessment_item, dict):
                    # Check if this is local model format (nested dictionary)
                    if not assessment_item.get('quality'):
                        # Local model format: {'quality_name': {'quality': '...', 'level': '...', 'reasoning': '...'}}
                        for quality_key, quality_data in assessment_item.items():
                            if isinstance(quality_data, dict) and 'quality' in quality_data:
                                row = base_row.copy()
                                row['quality'] = quality_data.get('quality', '')
                                row['level'] = quality_data.get('level', '')
                                row['reasoning'] = quality_data.get('reasoning', '')
                                row['summary'] = r['assessment'].get('summary', '')
                                rows.append(row)
                    else:
                        # API model format: {'quality': '...', 'level': '...', 'reasoning': '...'}
                        row = base_row.copy()
                        row['quality'] = assessment_item.get('quality', '')
                        row['level'] = assessment_item.get('level', '')
                        row['reasoning'] = assessment_item.get('reasoning', '')
                        row['summary'] = r['assessment'].get('summary', '')
                        rows.append(row)
            
            # If no assessments were processed, add base row with summary
            if not any('quality' in row for row in rows if row.get('student_id') == base_row['student_id']):
                base_row['summary'] = r['assessment'].get('summary', '')
                rows.append(base_row)
        else:
            rows.append(base_row)
    
    return pd.DataFrame(rows)

def get_saved_assessments_index():
    """Scan assessments folder and build index of school/class/date with error handling"""
    assessments_dir = "assessments"
    index = {}  # {school: {class: [dates]}}
    
    if not os.path.exists(assessments_dir):
        return index
    
    try:
        files = os.listdir(assessments_dir)
    except PermissionError:
        st.error(f"❌ Permission denied accessing assessments directory")
        return index
    except OSError as e:
        st.error(f"❌ Error accessing assessments directory: {str(e)}")
        return index
    
    for filename in files:
        if not filename.endswith('.csv') or filename.startswith('checkpoint'):
            continue
        
        filepath = os.path.join(assessments_dir, filename)
        
        try:
            # Try different encodings
            df = None
            for encoding in ['utf-8', 'cp1252', 'latin-1']:
                try:
                    df = pd.read_csv(filepath, nrows=1, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                continue
            
            if 'school' in df.columns and 'class' in df.columns and 'date' in df.columns:
                # Safely access DataFrame values with null checks
                school = 'Unknown'
                class_name = 'Unknown'
                date = filename
                
                if not df.empty:
                    school_val = df['school'].iloc[0]
                    school = str(school_val) if pd.notna(school_val) else 'Unknown'
                    
                    class_val = df['class'].iloc[0]
                    class_name = str(class_val) if pd.notna(class_val) else 'Unknown'
                    
                    date_val = df['date'].iloc[0]
                    date = str(date_val) if pd.notna(date_val) else filename
                
                if school not in index:
                    index[school] = {}
                if class_name not in index[school]:
                    index[school][class_name] = []
                if date not in index[school][class_name]:
                    index[school][class_name].append({'date': date, 'file': filename})
        except pd.errors.EmptyDataError:
            # Skip empty files
            continue
        except pd.errors.ParserError:
            # Skip malformed CSV files
            continue
        except PermissionError:
            # Skip files we can't access
            continue
        except (IOError, OSError):
            # Skip files with I/O errors
            continue
    
    return index

def load_assessment_file(filename):
    """Load a specific assessment CSV file with comprehensive error handling"""
    filepath = f"assessments/{filename}"
    
    if not os.path.exists(filepath):
        st.warning(f"⚠️ File not found: {filename}")
        return None
    
    # Try different encodings
    encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            return df
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError:
            st.error(f"❌ File is empty: {filename}")
            return None
        except pd.errors.ParserError as e:
            st.error(f"❌ Error parsing CSV file: {filename}")
            st.error(f"Details: {str(e)}")
            return None
        except PermissionError:
            st.error(f"❌ Permission denied accessing file: {filename}")
            return None
        except IOError as e:
            st.error(f"❌ Error reading file: {filename}")
            st.error(f"Details: {str(e)}")
            return None
    
    # If all encodings failed
    st.error(f"❌ Could not read file with any supported encoding: {filename}")
    st.info("💡 Please ensure the file is a valid CSV with UTF-8, CP1252, Latin-1, or ISO-8859-1 encoding")
    return None

# ============ END CSV HELPER FUNCTIONS ============

def main():
    st.title("🎓 Personality Assessment System for Students")
    st.markdown("---")
    
    # Session recovery functionality has been removed to focus on core batch assessment features
    
    # Sidebar for system setup
    with st.sidebar:
        st.header("⚙️ System Setup")
        
        # Developer Mode Toggle (always visible for easy testing)
        st.markdown("---")
        developer_mode_toggle = st.checkbox(
            "🔧 Developer Mode (Local Models)",
            value=os.getenv('DEVELOPER_MODE', 'false').lower() == 'true',
            help="Enable to use local Ollama models instead of Gemini API"
        )
        
        # Set developer mode based on toggle or environment variable
        developer_mode = developer_mode_toggle or os.getenv('DEVELOPER_MODE', 'false').lower() == 'true'
        
        if developer_mode:
            st.info("💻 Developer mode enabled - Local models available")
        
        st.markdown("---")
        
        # Model Selection (visible when developer mode is on)
        if developer_mode:
            st.subheader("🤖 Model Selection")
            
            model_choice = st.radio(
                "Choose AI Model:",
                ["🌐 Gemini API (Cloud)", "🖥️ Local Llama Model (Ollama)"],
                help="Cloud models require API key, local models are free but need Ollama installed"
            )
            
            if model_choice == "🖥️ Local Llama Model (Ollama)":
                # Check for local models
                try:
                    from ai_core.local_personality_assessment import get_available_local_models
                    with st.spinner("🔍 Scanning for local models..."):
                        local_models = get_available_local_models()
                    
                    if local_models:
                        model_names = [m['name'] for m in local_models]
                        selected_local = st.selectbox(
                            "Select Local Model:",
                            model_names,
                            help="These models run on your computer - no API costs!"
                        )
                        
                        # Show model info
                        selected_model_info = next((m for m in local_models if m['name'] == selected_local), None)
                        if selected_model_info:
                            size_gb = selected_model_info.get('size', 0) / (1024**3)
                            st.caption(f"📦 Size: {size_gb:.1f} GB")
                        
                        st.session_state.selected_model = f"local:{selected_local}"
                        st.session_state.is_local_model = True
                        st.session_state.local_model_name = selected_local
                        st.success(f"✅ Selected: {selected_local}")
                        st.info("💡 No API key needed for local models")
                    else:
                        st.error("❌ No local models found")
                        st.markdown("""
                        **To use local models:**
                        1. Install Ollama: https://ollama.ai
                        2. Pull a model: `ollama pull llama3.2:3b`
                        3. Restart this app
                        """)
                        # Fallback to API
                        st.session_state.selected_model = "gemini-2.5-flash"
                        st.session_state.is_local_model = False
                except Exception as e:
                    st.error(f"❌ Error loading local models: {str(e)}")
                    st.info("Falling back to Gemini API")
                    st.session_state.selected_model = "gemini-2.5-flash"
                    st.session_state.is_local_model = False
            else:
                # Use Gemini API
                st.session_state.selected_model = "gemini-2.5-flash"
                st.session_state.is_local_model = False
                st.info("☁️ Using Gemini 2.5 Flash API")
            
            st.markdown("---")
        else:
            # For regular users, always use Gemini API
            st.session_state.selected_model = "gemini-2.5-flash"
            st.session_state.is_local_model = False
        
        # API Configuration (only show if not using local model)
        if not st.session_state.get('is_local_model', False):
            st.subheader("🔑 API Configuration")
            
            # API Key input
            api_key_input = st.text_input(
                "Enter your Gemini API Key:",
                type="password",
                value=st.session_state.get('user_api_key', ''),
                help="Get your free API key from https://aistudio.google.com/apikey"
            )
            
            if api_key_input:
                st.session_state.user_api_key = api_key_input
                # Override the default API key
                os.environ['GEMINI_API_KEY'] = api_key_input
                os.environ['GOOGLE_API_KEY'] = api_key_input
                st.success("✅ API Key configured!")
            else:
                # Check if default key exists in .env
                default_key = os.getenv('GOOGLE_API_KEY', '')
                if default_key and default_key != "your-api-key-here":
                    st.info("ℹ️ Using default API key from configuration")
                else:
                    st.warning("⚠️ Please enter your API key to use the system")
        else:
            st.success("🖥️ Local model selected - No API key required!")
        
        st.markdown("---")
        with st.expander("ℹ️ About Gemini API", expanded=False):
            st.markdown("""
            **Gemini 2.5 Flash** is Google's fast and efficient AI model.
            
            **Free Tier Limits:**
            - 10 requests per minute
            - 250 requests per day
            - Perfect for small to medium NGO usage
            
            **How to get API Key:**
            1. Visit https://aistudio.google.com/apikey
            2. Sign in with Google account
            3. Click "Create API Key"
            4. Copy and paste it above
            
            **Upgrading to Paid Tier:**
            - Same API key works for both free and paid
            - Just add billing in Google Cloud Console
            - Higher limits: 1000 RPM, 10000 RPD
            - Cost: ~$0.08/month for 500 students
            """)
        
        st.markdown("---")
        
        # Initialize button
        api_key = st.session_state.get('user_api_key', '')
        if not api_key:
            # Check if default key exists in .env
            default_key = os.getenv('GOOGLE_API_KEY', '')
            if default_key and default_key != "your-api-key-here":
                api_key = default_key
        
        if api_key or developer_mode:
            if st.button("🚀 Initialize System", type="primary"):
                with st.spinner("Setting up the assessment system..."):
                    try:
                        # Check if using local model (developer mode only)
                        if st.session_state.get('is_local_model', False):
                            # Initialize local model system
                            from ai_core.local_personality_assessment import LocalPersonalityAssessment
                            local_model_name = st.session_state.get('local_model_name', 'llama3.2:3b')
                            
                            # Create a wrapper that mimics PersonalityAssessmentSystem
                            class LocalAssessmentWrapper:
                                def __init__(self, model_name):
                                    self.local_assessor = LocalPersonalityAssessment(model_name)
                                    self.model_name = model_name
                                
                                def assess_student_personality(self, observations):
                                    return self.local_assessor.assess_student_personality(observations)
                                
                                def generate_swot_analysis(self, observations):
                                    """Generate SWOT analysis in English using local model"""
                                    try:
                                        from ai_core.local_model_adapter import LocalModelAdapter
                                        adapter = LocalModelAdapter(self.model_name)
                                        
                                        prompt = f"""You are an educational counselor. Create a SWOT analysis for a student based on observations.

Student Observations:
{observations}

Create a SWOT analysis with:
- STRENGTHS: Internal positive traits/skills (3-5 points)
- WEAKNESSES: Internal areas for improvement (3-5 points)
- OPPORTUNITIES: External/future possibilities (3-5 points)
- THREATS: Potential risks (3-5 points)

Output in JSON format:
{{
    "summary": "Brief summary of the student",
    "swot_items": [
        {{"category": "STRENGTH", "point": "Leadership skills", "explanation": ""}},
        {{"category": "WEAKNESS", "point": "Time management", "explanation": ""}},
        {{"category": "OPPORTUNITY", "point": "Advanced courses", "explanation": ""}},
        {{"category": "THREAT", "point": "Peer pressure", "explanation": ""}}
    ]
}}

Respond ONLY with valid JSON."""
                                        
                                        response = adapter.generate_content(prompt, temperature=0.3)
                                        import json
                                        result = json.loads(response['text'])
                                        return result
                                    except Exception as e:
                                        return {"error": str(e)}
                                
                                def generate_marathi_swot(self, observations):
                                    """Generate SWOT analysis in Marathi using local model"""
                                    try:
                                        from ai_core.local_model_adapter import LocalModelAdapter
                                        adapter = LocalModelAdapter(self.model_name)
                                        
                                        prompt = f"""तुम्ही एक शैक्षणिक सल्लागार आहात. विद्यार्थ्याच्या निरीक्षणांवर आधारित SWOT विश्लेषण तयार करा.

विद्यार्थ्याचे निरीक्षण:
{observations}

SWOT विश्लेषण तयार करा:
- क्षमता (STRENGTHS): अंतर्गत सकारात्मक गुण/कौशल्ये (3-5 मुद्दे)
- कमतरता (WEAKNESSES): सुधारणेसाठी क्षेत्रे (3-5 मुद्दे)
- संधी (OPPORTUNITIES): बाह्य/भविष्यातील शक्यता (3-5 मुद्दे)
- भीती (THREATS): संभाव्य धोके (3-5 मुद्दे)

सोप्या मराठीत लिहा. JSON फॉरमॅटमध्ये उत्तर द्या:
{{
    "summary": "विद्यार्थ्याचा थोडक्यात सारांश",
    "swot_items": [
        {{"category": "STRENGTH", "point": "नेतृत्व गुण", "explanation": ""}},
        {{"category": "WEAKNESS", "point": "वेळेचे व्यवस्थापन", "explanation": ""}},
        {{"category": "OPPORTUNITY", "point": "प्रगत अभ्यासक्रम", "explanation": ""}},
        {{"category": "THREAT", "point": "मित्रांचा दबाव", "explanation": ""}}
    ]
}}

फक्त वैध JSON मध्ये उत्तर द्या."""
                                        
                                        response = adapter.generate_content(prompt, temperature=0.3)
                                        import json
                                        result = json.loads(response['text'])
                                        return result
                                    except Exception as e:
                                        return {"error": str(e)}
                                
                                def setup_vector_database(self):
                                    pass  # Not needed for local models
                            
                            system = LocalAssessmentWrapper(local_model_name)
                            system.setup_vector_database()
                            st.session_state.assessment_system = system
                            st.session_state.system_ready = True
                            st.success("✅ Local model system initialized successfully!")
                            st.success(f"🖥️ Using: {local_model_name} (Local)")
                            st.info("🎯 **Testing Mode**: No API quota will be used!")
                        else:
                            # Initialize Gemini system
                            if api_key:
                                os.environ["GOOGLE_API_KEY"] = api_key
                            
                            from ai_core.personality_assessment import PersonalityAssessmentSystem
                            system = PersonalityAssessmentSystem(model_name="gemini-2.5-flash")
                            system.setup_vector_database()
                            st.session_state.assessment_system = system
                            st.session_state.system_ready = True
                            st.success("✅ System initialized successfully!")
                            st.success("🤖 Using: Gemini 2.5 Flash")
                    except Exception as e:
                        st.error(f"❌ Setup failed: {str(e)}")
                        if developer_mode:
                            st.error("💡 **Tip**: If using local model, make sure Ollama is running and the model is pulled")
                        st.session_state.system_ready = False
        
        # System status
        st.markdown("---")
        if st.session_state.system_ready:
            st.success("✅ System Ready")
            if st.session_state.get('is_local_model', False):
                local_model_name = st.session_state.get('local_model_name', 'Unknown')
                st.info(f"🖥️ Using: {local_model_name} (Local)")
                st.info("✅ No API quota usage")
            else:
                st.info("🤖 Using: Gemini 2.5 Flash API")
        else:
            st.warning("⚠️ System Not Ready")
            st.info("Enter your API key and click Initialize")
    
    # Main content area
    if not st.session_state.system_ready:
        st.markdown("### 🚀 Welcome to the Personality Assessment System!")
        st.markdown("---")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 🎯 Getting Started")
            st.markdown("""
            **To begin using the system, please complete the setup in the sidebar:**
            
            1. **🤖 Choose Your AI Model**
               - Select from Gemini models (API-based) or Local models (Ollama)
               - Local models are perfect for testing - no API costs!
            
            2. **🔑 Configure Authentication** (API models only)
               - Enter your Google API key for Gemini models
               - Local models require no API key
            
            3. **🚀 Initialize the System**
               - Click the "Initialize System" button to get started
               - The system will set up the AI model and prepare for assessments
            """)
            
            st.info("💡 **New to the system?** Try a local model first - it's free and perfect for exploring features!")
        
        with col2:
            st.markdown("#### 🎓 What You Can Do")
            st.markdown("""
            **Individual Assessments**
            - Assess single students with detailed observations
            - Get personality insights and recommendations
            
            **Batch Processing**
            - Upload CSV files with multiple students
            - Process entire classes efficiently
            - Review and approve results before saving
            
            **Analytics & Reports**
            - View student growth over time
            - Generate comprehensive report cards
            - Track progress across multiple sessions
            """)
            
            st.success("✅ **Ready to start?** Complete the setup in the sidebar!")
        
        return
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Individual Assessment", "👥 Batch Assessment", "📊 Stored Assessments", "🧠 SWOT Analysis", "⚙️ System Info"])
    
    with tab1:
        individual_assessment_tab()
    
    with tab2:
        batch_assessment_tab()
    
    with tab3:
        stored_assessments_tab()
    
    with tab4:
        swot_analysis_tab()
    
    with tab5:
        system_info_tab()

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
    
    # Show workflow guidance
    workflow = st.session_state.workflow_protection
    guidance = workflow.get_workflow_guidance('batch_upload')
    
    workflow.show_contextual_help(
        'batch_upload',
        guidance['help'],
        guidance.get('tips', [])
    )
    
    # Check if finalization was just completed - if so, show success and hide upload
    if st.session_state.get('finalization_complete', False):
        st.success("🎉 Batch assessment completed successfully!")
        st.info("📊 Your assessments have been saved to Stored Assessments.")
        st.info("🔄 To process another batch, refresh the page or click the button below.")
        
        if st.button("🆕 Start New Assessment", type="primary"):
            # Clear finalization flag and reset for new assessment
            st.session_state.finalization_complete = False
            st.rerun()
        
        return  # Exit early to hide upload section
    
    # File upload option
    st.subheader("📁 Upload CSV File")
    
    # Update help text for new format
    st.info("📋 **Supported CSV Format:**")
    st.info("• **Required Columns**: `Name, School, Class, Session, Observations`")
    
    # Add upload controls
    col_upload, col_clear, col_history = st.columns([3, 1, 1])
    with col_upload:
        uploaded_file = st.file_uploader(
            "Choose a CSV file", 
            type=['csv'],
            help="CSV can use either the new 5-column format (Name, School, Class, Session, Observations) or legacy 2-column format (Name, Observations)"
        )
    with col_clear:
        if st.button("🗑️ Clear Upload", help="Clear the current upload and reset"):
            # Clear all related session state
            if 'force_process_duplicate' in st.session_state:
                del st.session_state.force_process_duplicate
            st.rerun()
    with col_history:
        if st.button("🔄 Reset History", help="Clear upload history to allow re-uploading files"):
            # Clear the upload history (with fallback for older instances)
            if hasattr(st.session_state.csv_processor, 'clear_upload_history'):
                st.session_state.csv_processor.clear_upload_history()
            else:
                # Fallback: recreate the processor to get the new methods
                st.session_state.csv_processor = EnhancedCSVProcessor()
            
            if 'force_process_duplicate' in st.session_state:
                del st.session_state.force_process_duplicate
            st.success("Upload history cleared!")
            st.rerun()
    
    if uploaded_file is not None:
        # Get file content for processing
        file_content = uploaded_file.getvalue().decode('utf-8')
        filename = uploaded_file.name
        
        # Store original filename for later use in finalization
        st.session_state.original_csv_filename = filename
        
        # Check for duplicate file upload
        csv_processor = st.session_state.csv_processor
        is_duplicate_file = csv_processor.check_file_duplicate(file_content, filename)
        
        # Determine CSV format first
        import pandas as pd
        try:
            df_preview = pd.read_csv(uploaded_file, nrows=1)
            has_new_format = all(col in df_preview.columns for col in ['Name', 'School', 'Class', 'Session', 'Observations'])
            
            if has_new_format:
                st.success("✅ **CSV format validated**: Name, School, Class, Session, Observations")
                # School and Class information will be extracted from the CSV file
                batch_school = "From_CSV"
                batch_class = "From_CSV"
            else:
                st.error("❌ **Invalid CSV format**")
                st.error("Required columns: Name, School, Class, Session, Observations")
                st.stop()
                
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.stop()
        
        # Reset file pointer for processing
        uploaded_file.seek(0)
        file_content = uploaded_file.getvalue().decode('utf-8')
        
        # Handle duplicate file detection
        if is_duplicate_file and not st.session_state.get('force_process_duplicate', False):
            st.warning("⚠️ **Duplicate File Detected!**")
            st.info(f"The file '{filename}' appears to have been uploaded before with identical content.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Process Anyway", key="process_duplicate"):
                    st.session_state.force_process_duplicate = True
                    st.rerun()
            with col2:
                if st.button("❌ Cancel Upload", key="cancel_duplicate"):
                    # Clear the duplicate processing flag and force a rerun to reset the UI
                    if 'force_process_duplicate' in st.session_state:
                        del st.session_state.force_process_duplicate
                    st.info("Upload cancelled. Please select a different file or refresh the page.")
                    st.stop()  # Use st.stop() instead of return to properly halt execution
        else:
            # Process the CSV with enhanced validation
            with st.spinner("🔍 Validating CSV file..."):
                validation_result = csv_processor.validate_and_process_csv(file_content, filename)
            
            # Display validation results
            summary = csv_processor.get_processing_summary(validation_result)
            
            # Show processing summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Rows", summary['total_rows'])
            with col2:
                st.metric("Valid Students", summary['valid_students'], 
                         delta=f"Skipped {summary['blank_rows_skipped']} blank rows")
            with col3:
                st.metric("Issues Found", summary['issues_count'])
            with col4:
                if summary['is_processable']:
                    st.success("✅ Ready to Process")
                else:
                    st.error("❌ Has Critical Issues")
            
            # Show detailed validation report if there are issues
            if validation_result.issues:
                with st.expander("📋 Detailed Validation Report", expanded=summary['critical_issues'] > 0):
                    st.text(csv_processor.generate_validation_report(validation_result))
            
            # Check for duplicates within the file
            if summary['is_processable']:
                duplicate_report = csv_processor.detect_duplicates(validation_result.processed_data)
                
                if duplicate_report.total_duplicates > 0:
                    st.warning(f"⚠️ Found {duplicate_report.total_duplicates} potential duplicate students in the file")
                    with st.expander("🔍 Duplicate Detection Report"):
                        for dup in duplicate_report.duplicates_found:
                            st.write(f"**{dup.student_name}** ({dup.duplicate_type})")
                            st.write(f"  - Rows: {', '.join(map(str, dup.row_numbers))}")
                            st.write(f"  - Similarity: {dup.similarity_score:.1%}")
            
            # Display preview of cleaned data
            if summary['is_processable']:
                st.subheader("📋 Cleaned Data Preview")
                st.info(f"Showing {len(validation_result.processed_data)} valid student records (blank rows removed)")
                
                # Add realistic warnings based on selected model's daily limit
                batch_size = len(validation_result.processed_data)
                
                # Check if using local model first - no quota limits for local models
                is_local_model = st.session_state.get('is_local_model', False)
                
                if not is_local_model:
                    # API model - check quota limits
                    try:
                        from config import AVAILABLE_MODELS, DEFAULT_MODEL
                        selected_model_key = st.session_state.get('selected_model', DEFAULT_MODEL)
                        is_paid_tier = st.session_state.get('is_paid_tier', False)
                        
                        # Get model-specific limits
                        model_info = AVAILABLE_MODELS.get(selected_model_key, AVAILABLE_MODELS[DEFAULT_MODEL])
                        tier = 'paid_tier' if is_paid_tier else 'free_tier'
                        daily_limit = model_info[tier]['requests_per_day']
                        
                        # Handle "Unlimited*" case
                        if isinstance(daily_limit, str) and "unlimited" in daily_limit.lower():
                            st.success(f"✅ **UNLIMITED QUOTA**: Processing {batch_size} students with paid tier unlimited requests")
                            st.info("🎯 No daily limits - you can process large batches without concern")
                        else:
                            # Use actual numeric limit
                            daily_limit = int(daily_limit)
                            
                            if batch_size > daily_limit:
                                st.error(f"🚨 **EXCEEDS DAILY QUOTA**: {model_info['name']} allows {daily_limit} requests per day!")
                                st.error(f"❌ Cannot process {batch_size} students - you'll hit quota limit after {daily_limit} students")
                                st.warning("⚠️ **Solutions:**")
                                st.warning(f"• Split this file into smaller files (≤{daily_limit} students each)")
                                st.warning("• Process across multiple days")
                                st.warning("• Upgrade to paid Google API plan for higher limits")
                                
                                # Offer to split the file
                                st.info("💡 **File Splitting Suggestion:**")
                                num_files = (batch_size + daily_limit - 1) // daily_limit  # Round up division
                                st.info(f"• Split into {num_files} files of ~{daily_limit} students each")
                                st.info(f"• Process 1 file per day = {num_files} days total")
                                st.stop()  # Prevent processing
                                
                            elif batch_size > daily_limit * 0.75:  # 75% of quota
                                st.warning(f"⚠️ **HIGH QUOTA USAGE**: This will use {batch_size} of your {daily_limit} daily requests!")
                                st.warning("⚠️ **Warning**: This will use most of your daily quota")
                                st.info("💡 **Consider**: Splitting into smaller batches or saving some quota for individual assessments")
                                
                                confirm_quota = st.checkbox(f"I understand this will use {batch_size}/{daily_limit} of my daily quota", key="confirm_csv_quota")
                                if not confirm_quota:
                                    st.stop()
                                    
                            elif batch_size > daily_limit * 0.25:  # 25% of quota
                                quota_percent = (batch_size / daily_limit) * 100
                                st.info(f"📊 **Quota Usage**: This will use {batch_size} of your {daily_limit} daily requests ({quota_percent:.0f}% of quota)")
                                st.info(f"💡 **{model_info['name']} Limit**: {daily_limit} requests per day total")
                                st.info(f"💡 **Remaining after this batch**: {daily_limit - batch_size} requests")
                    except (ImportError, KeyError, AttributeError) as e:
                        # Fallback to conservative warnings if config unavailable
                        st.warning(f"⚠️ Could not load quota information: {str(e)}")
                        if batch_size > 50:
                            st.warning(f"⚠️ **Large Batch**: Processing {batch_size} students - ensure you have sufficient quota")
                            confirm_quota = st.checkbox("I understand this is a large batch", key="confirm_csv_quota_fallback")
                            if not confirm_quota:
                                st.stop()
                
                st.dataframe(validation_result.processed_data.head(), width='stretch')
                
                # Show next steps guidance
                workflow = st.session_state.workflow_protection
                
                workflow.show_next_steps('batch_validated', [
                    {
                        'title': 'Review the data preview above',
                        'description': 'Check that student names and observations look correct',
                        'action': 'Scroll up to see the data table'
                    },
                    {
                        'title': 'Start processing',
                        'description': 'Click the button below to begin AI assessment',
                        'action': 'Ready to process when you are'
                    }
                ])
                
                # Start processing button
                if st.button("🚀 Start Batch Assessment", type="primary", key="start_batch_assessment"):
                    # Check if assessment system is ready
                    if not st.session_state.get('system_ready', False) or not st.session_state.get('assessment_system'):
                        st.error("❌ Assessment system is not initialized. Please initialize the system in the sidebar first.")
                        st.stop()
                    
                    # Mark file as processed and clear the duplicate flag
                    csv_processor.mark_file_processed(filename)
                    if 'force_process_duplicate' in st.session_state:
                        del st.session_state.force_process_duplicate
                    
                    # Start the batch assessment
                    try:
                        process_batch_assessment(validation_result.processed_data, batch_school, batch_class)
                    except Exception as e:
                        st.error(f"❌ Failed to start batch assessment: {str(e)}")
                        st.exception(e)  # Show full traceback for debugging
            else:
                st.error("❌ Cannot process file due to critical issues. Please fix the issues and upload again.")
                
            # Clear duplicate processing flag after successful processing display
            if st.session_state.get('force_process_duplicate', False):
                # Keep the flag until the user actually starts processing or cancels
                pass
    elif uploaded_file is not None:
        st.info("📋 CSV loaded. Please fill in School Name and Class above to proceed.")

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
            # Use state flag instead of st.rerun() to prevent workflow interruption
            st.session_state.review_reset = True

    # Check if we should show confirmation dialog (moved here to ensure it's always checked)
    if st.session_state.get('show_finalize_confirmation', False):
        st.warning("⚠️ **Confirm Finalization**")
        st.info("This will store assessments permanently and download the CSV file.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Finalize", key="confirm_finalize_top", type="primary"):
                st.session_state.show_finalize_confirmation = False
                st.session_state.confirm_finalize = True
                st.rerun()
        with col2:
            if st.button("❌ Cancel", key="cancel_finalize_top"):
                st.session_state.show_finalize_confirmation = False
                st.info("Finalization cancelled. Continue reviewing.")
                st.rerun()
        st.stop()  # Stop here to show only the confirmation dialog

    # Check if we should proceed with finalization (moved here to ensure it's always checked)
    if st.session_state.get('confirm_finalize', False):
        # Proceed with finalization immediately
        st.session_state.confirm_finalize = False  # Reset for next time
        
        # Get data from session state
        review_df = st.session_state.review_df
        results = st.session_state.batch_results or []
        
        if review_df is None or len(results) == 0:
            st.error("❌ No data available for finalization. Please process a batch first.")
        else:
            try:
                # Use the full review_df (not just the current page)
                export_df = review_df[["Name", "Observations", "Final Labels"]].copy()
                export_df["Predicted Labels"] = review_df["Predicted Labels"].apply(lambda x: json.dumps(x, ensure_ascii=False))
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
                
                # Generate filename based on original uploaded CSV name
                original_filename = st.session_state.get('original_csv_filename', 'batch_assessment.csv')
                
                # Remove .csv extension and add _assessment suffix
                if original_filename.endswith('.csv'):
                    base_name = original_filename[:-4]  # Remove .csv
                else:
                    base_name = original_filename
                
                csv_name = f"{base_name}_assessment.csv"

                os.makedirs("assessments", exist_ok=True)
                with open(f"assessments/{csv_name}", "wb") as cf:
                    cf.write(csv_bytes)

                # Store approved assessments in the storage manager
                approved_rows = review_df[review_df['Approved'] == True]
                batch_timestamp = st.session_state.get('batch_timestamp')
                store_approved_batch_assessments(review_df, results, batch_timestamp)
                
                # Simple success message
                st.success(f"✅ Assessment completed! {len(approved_rows)} student assessments saved to Stored Assessments.")
                
                st.download_button(
                    label="⬇️ Download Reviewed CSV",
                    data=csv_bytes,
                    file_name=csv_name,
                    mime="text/csv"
                )
                
                # Clear session state after successful finalization to prevent duplicate display
                st.session_state.review_df = None
                st.session_state.batch_results = None
                st.session_state.batch_timestamp = None
                st.session_state.saved_batch_csv = None
                if 'original_csv_filename' in st.session_state:
                    del st.session_state.original_csv_filename
                
                # Clear upload state to hide upload section
                if 'uploaded_file_content' in st.session_state:
                    del st.session_state.uploaded_file_content
                if 'uploaded_file_name' in st.session_state:
                    del st.session_state.uploaded_file_name
                if 'force_process_duplicate' in st.session_state:
                    del st.session_state.force_process_duplicate
                
                # Set finalization complete flag
                st.session_state.finalization_complete = True
                
                st.info("You can now start a new batch assessment.")
                return  # Exit the function to prevent duplicate render_review_interface call
                
            except Exception as e:
                st.error(f"❌ Error during finalization: {str(e)}")
                st.exception(e)
                return  # Exit on error to prevent duplicate display

    # Only render review interface if we haven't just completed finalization
    if st.session_state.review_df is not None:
        render_review_interface()

def stored_assessments_tab():
    """Enhanced stored assessments tab with hierarchical school organization"""
    # Import the enhanced interface
    try:
        from frontend.enhanced_stored_assessments import EnhancedStoredAssessmentsInterface
        
        # Create and render the enhanced interface
        enhanced_interface = EnhancedStoredAssessmentsInterface(st.session_state.storage_manager)
        enhanced_interface.render_main_interface()
        
    except ImportError as e:
        st.error(f"Could not load enhanced interface: {e}")
        # Fallback to original implementation
        _render_legacy_stored_assessments()
    except Exception as e:
        st.error(f"Error in enhanced interface: {e}")
        # Fallback to original implementation
        _render_legacy_stored_assessments()

def _render_legacy_stored_assessments():
    """Legacy stored assessments implementation as fallback"""
    st.header("📊 Stored Assessments")
    
    # Add metadata summary at the top
    try:
        storage_manager = st.session_state.storage_manager
        system_meta = storage_manager.get_system_metadata()
        
        # Quick stats in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📚 Total Students", system_meta.get('total_students', 0))
        
        with col2:
            st.metric("📝 Total Observations", system_meta.get('total_observations', 0))
        
        with col3:
            # Show last update time
            last_updated = system_meta.get('last_updated')
            if last_updated:
                try:
                    dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    time_str = dt.strftime("%m/%d %H:%M")
                except (ValueError, AttributeError, TypeError):
                    time_str = "Unknown"
            else:
                time_str = "Never"
            st.metric("🕒 Last Updated", time_str)
        
        st.markdown("---")
        
    except Exception as e:
        st.warning(f"Could not load system metadata: {e}")
    
    # Add view selection tabs
    view_tab1, view_tab2 = st.tabs(["📁 File-based View", "👤 Student-based View (Consolidated)"])
    
    with view_tab1:
        display_file_based_assessments()
    
    with view_tab2:
        display_consolidated_student_view()

def display_file_based_assessments():
    """Original file-based assessment view"""
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
    if st.button("🔄 Refresh List", key="refresh_file_view"):
        st.rerun()

def display_consolidated_student_view():
    """New consolidated student view with multiple observations"""
    st.subheader("👤 Student-based Consolidated View")
    st.info("📋 This view shows all observations for each student consolidated over time, addressing feedback about multiple observations being considered together.")
    
    try:
        from ai_core.assessment_storage_manager import AssessmentStorageManager
        storage_manager = AssessmentStorageManager()
        
        # Get all consolidated profiles
        with st.spinner("🔄 Loading and consolidating student data..."):
            profiles = storage_manager.get_all_consolidated_profiles()
        
        if not profiles:
            st.info("No student data found. Upload some assessments to see consolidated profiles here.")
            return
        
        # Display summary statistics
        st.subheader("📊 Consolidated Summary")
        total_students = len(profiles)
        total_observations = sum(p.observation_count for p in profiles)
        total_assessments = sum(p.assessment_count for p in profiles)
        
        # Group by school for school-wise display
        school_groups = {}
        for profile in profiles:
            school = profile.school if profile.school != 'Unknown' else 'Unspecified School'
            if school not in school_groups:
                school_groups[school] = []
            school_groups[school].append(profile)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Students", total_students)
        with col2:
            st.metric("Schools", len(school_groups))
        with col3:
            st.metric("Total Observations", total_observations)
        with col4:
            st.metric("Total Assessments", total_assessments)
        
        st.markdown("---")
        
        # School-wise organization (addresses feedback issue b)
        st.subheader("🏫 School-wise Student Organization")
        
        for school_name, school_profiles in school_groups.items():
            with st.expander(f"🏫 {school_name} ({len(school_profiles)} students)", expanded=False):
                
                # School summary
                school_obs = sum(p.observation_count for p in school_profiles)
                school_assessments = sum(p.assessment_count for p in school_profiles)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Students", len(school_profiles))
                with col2:
                    st.metric("Observations", school_obs)
                
                # Student selection within school
                student_names = [p.student_name for p in school_profiles]
                selected_student = st.selectbox(
                    f"Select student from {school_name}:",
                    ["-- Select Student --"] + student_names,
                    key=f"student_select_{school_name}"
                )
                
                if selected_student and selected_student != "-- Select Student --":
                    # Find the selected profile
                    profile = next(p for p in school_profiles if p.student_name == selected_student)
                    display_student_consolidated_profile(profile)
        
        # Search functionality
        st.markdown("---")
        st.subheader("🔍 Search Students")
        search_term = st.text_input("Search by student name:", placeholder="Enter student name to search", key="student_search")
        
        if search_term:
            matching_profiles = [
                p for p in profiles 
                if search_term.lower() in p.student_name.lower()
            ]
            
            if matching_profiles:
                st.success(f"Found {len(matching_profiles)} matching student(s)")
                for profile in matching_profiles:
                    with st.expander(f"👤 {profile.student_name} ({profile.school})", expanded=False):
                        display_student_consolidated_profile(profile)
            else:
                st.warning("No students found matching your search")
    
    except Exception as e:
        st.error(f"Error loading consolidated data: {e}")
        st.info("This feature requires the enhanced storage system. Please ensure all components are properly installed.")

def display_student_consolidated_profile(profile):
    """Display detailed consolidated profile for a student"""
    st.markdown(f"### 👤 {profile.student_name}")
    
    # Basic info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Observations", profile.observation_count)
    with col2:
        st.metric("Assessments", profile.assessment_count)
    with col3:
        date_range = (profile.last_observed - profile.first_observed).days
        st.metric(
            "📅 Observation Span", 
            f"{date_range} days",
            help="""Time period between first and last observation:
• 0 days: Single observation
• 1-30 days: Short to medium-term tracking  
• 31+ days: Long-term developmental tracking

Longer spans provide better insights into consistent behavioral patterns."""
        )
    
    # Timeline (addresses feedback issue c)
    st.markdown("#### 📅 Observation Timeline")
    timeline_data = []
    for obs in profile.observations:
        timeline_data.append({
            'Date': obs.timestamp.strftime('%Y-%m-%d'),
            'Type': 'Observation',
            'Content': obs.content[:100] + "..." if len(obs.content) > 100 else obs.content
        })
    
    for assessment in profile.assessments:
        # Count only qualities that were actually assessed (not "NOT OBSERVED" or "Unknown")
        assessed_qualities = [q for q in assessment.qualities.keys() 
                            if q != 'Unknown' and assessment.qualities[q].get('level') != 'NOT OBSERVED']
        timeline_data.append({
            'Date': assessment.timestamp.strftime('%Y-%m-%d'),
            'Type': 'Assessment',
            'Content': f"{len(assessed_qualities)} qualities assessed"
        })
    
    if timeline_data:
        import pandas as pd
        timeline_df = pd.DataFrame(timeline_data)
        timeline_df = timeline_df.sort_values('Date', ascending=False)
        st.dataframe(timeline_df, width='stretch')
    
    # Consolidated assessment
    if profile.consolidated_assessment:
        st.markdown("#### 🎯 Consolidated Assessment")
        st.success("✅ Multiple observations have been consolidated into a comprehensive assessment")
        
        # Display consolidated qualities
        for quality, details in profile.consolidated_assessment.qualities.items():
            with st.expander(f"{quality}: {details['level']}", expanded=False):
                st.write(f"**Level:** {details['level']}")
                st.write(f"**Confidence:** {details['confidence']:.2f}")
                if details['reasoning']:
                    st.write(f"**Reasoning:** {details['reasoning']}")
    else:
        st.info("No consolidated assessment available yet")
    
    # Individual observations
    with st.expander("📝 View All Individual Observations", expanded=False):
        for i, obs in enumerate(profile.observations, 1):
            st.markdown(f"**Observation {i}** ({obs.timestamp.strftime('%Y-%m-%d')})")
            st.text(obs.content)
            st.markdown("---")


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
                    # Invalidate cache so all tabs show updated data
                    if 'cached_profiles' in st.session_state:
                        del st.session_state['cached_profiles']
                    if 'cached_assessments' in st.session_state:
                        del st.session_state['cached_assessments']
                    st.session_state.force_refresh_profiles = True
                    
                    st.success("✅ Assessment replaced successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to replace assessment")
        
        with col2:
            if st.button("➕ Append to Existing", key=f"append_{student_name}_{assessment_date}"):
                if storage_manager.append_assessment(student_name, observations, result, assessment_date):
                    # Invalidate cache so all tabs show updated data
                    if 'cached_profiles' in st.session_state:
                        del st.session_state['cached_profiles']
                    if 'cached_assessments' in st.session_state:
                        del st.session_state['cached_assessments']
                    st.session_state.force_refresh_profiles = True
                    
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
            current_time = datetime.now().strftime("%H:%M:%S")
            st.success(f"✅ Assessment saved successfully with automatic timestamp ({current_time})!")
            
            # Invalidate cache so Stored Assessments tab shows updated data
            if 'cached_profiles' in st.session_state:
                del st.session_state['cached_profiles']
            if 'cached_assessments' in st.session_state:
                del st.session_state['cached_assessments']
            st.session_state.force_refresh_profiles = True
            
            # Show quick metadata update
            try:
                meta = storage_manager.get_observation_metadata(student_name)
                st.info(f"📊 {student_name} now has {meta['observation_count']} total observations")
            except (KeyError, AttributeError, TypeError):
                # Metadata not available, skip display
                pass
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
    """Process batch assessment from CSV with enhanced handling for large batches"""
    # Generate timestamp and safe filename components
    date_str = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize session tracking for this batch
    session_manager = st.session_state.session_manager
    session_manager.update_batch_progress(
        batch_id=timestamp,
        progress={
            'current': 0,
            'total': len(df),
            'status': 'starting',
            'started_at': datetime.now().isoformat(),
            'school': school_name,
            'class': class_name
        }
    )
    
    # Add pending task for batch processing
    session_manager.add_pending_task({
        'id': f'batch_process_{timestamp}',
        'type': 'batch_processing',
        'description': f'Processing {len(df)} students from {school_name} - {class_name}',
        'batch_id': timestamp
    })
    
    # Determine if we're using new format or legacy format
    has_new_format = all(col in df.columns for col in ['Name', 'School', 'Class', 'Session', 'Observations'])
    
    # Generate filename based on original uploaded CSV name
    original_filename = st.session_state.get('original_csv_filename', 'batch_assessment.csv')
    
    # Remove .csv extension and add _assessed suffix
    if original_filename.endswith('.csv'):
        base_name = original_filename[:-4]  # Remove .csv
    else:
        base_name = original_filename
    
    csv_filename = f"{base_name}_assessed.csv"
    
    checkpoint_file = f"assessments/checkpoint_{timestamp}.csv"
    
    try:
        results = []
        os.makedirs("assessments", exist_ok=True)
        
        # Create enhanced progress indicator optimized for 20-request limit
        progress_container = st.container()
        with progress_container:
            st.markdown("### 🔄 Processing Batch Assessment")
            
            # Show processing information based on model type
            total_students = len(df)
            
            # Check if using local model
            if st.session_state.get('is_local_model', False):
                local_model_name = st.session_state.get('local_model_name', 'Unknown')
                
                # More accurate time estimates for local models based on model size
                if 'llama3.2:1b' in local_model_name.lower():
                    seconds_per_student = 3  # Faster for 1B model
                elif 'llama3.2:3b' in local_model_name.lower():
                    seconds_per_student = 6  # Medium for 3B model
                elif '7b' in local_model_name.lower():
                    seconds_per_student = 10  # Slower for 7B model
                else:
                    seconds_per_student = 6  # Default estimate
                
                estimated_time_minutes = (total_students * seconds_per_student) / 60
                
                st.info(f"🖥️ **Processing {total_students} students with {local_model_name}**")
            else:
                # More accurate API model estimates based on rate limits
                try:
                    from config import AVAILABLE_MODELS, DEFAULT_MODEL
                    selected_model_key = st.session_state.get('selected_model', DEFAULT_MODEL)
                    is_paid_tier = st.session_state.get('is_paid_tier', False)
                    
                    # Get model-specific limits
                    model_info = AVAILABLE_MODELS.get(selected_model_key, AVAILABLE_MODELS[DEFAULT_MODEL])
                    tier = 'paid_tier' if is_paid_tier else 'free_tier'
                    requests_per_minute = model_info[tier].get('requests_per_minute', 10)
                    
                    if is_paid_tier and isinstance(requests_per_minute, str) and "unlimited" in requests_per_minute.lower():
                        # Paid tier with high limits - no delays needed
                        seconds_per_student = 8  # Just processing time
                        estimated_time_minutes = (total_students * seconds_per_student) / 60
                        st.info(f"📊 **Processing {total_students} students** (estimated time: {estimated_time_minutes:.1f} minutes)")
                        st.info("💳 **Paid Tier**: High rate limits - minimal delays between requests")
                    else:
                        # Free tier or limited paid tier - need delays
                        processing_time = 8  # Base processing time per student
                        delay_time = max(0, (60 / requests_per_minute) - processing_time)  # Delay to respect rate limits
                        total_time_per_student = processing_time + delay_time
                        estimated_time_minutes = (total_students * total_time_per_student) / 60
                        
                        st.info(f"📊 **Processing {total_students} students** (estimated time: {estimated_time_minutes:.1f} minutes)")
                        if delay_time > 0:
                            st.info(f"⏱️ **Rate Limit Delays**: ~{delay_time:.0f}s between requests ({requests_per_minute} requests/minute limit)")
                        else:
                            st.info(f"⚡ **Fast Processing**: {requests_per_minute} requests/minute limit allows continuous processing")
                
                except Exception:
                    # Fallback to conservative estimates
                    estimated_time_minutes = total_students * 0.6  # 36 seconds per student average
                    st.info(f"📊 **Processing {total_students} students** (estimated time: {estimated_time_minutes:.1f} minutes)")
                    st.info("💡 **Note**: Includes delays to respect API rate limits")
                
                # Show batch size warnings for free tier
                if total_students > 20 and not is_paid_tier:
                    st.warning(f"⚠️ **Large batch detected**: {total_students} students")
                    st.warning(f"Your current model supports 20 requests/day. Consider:")
                    st.warning("• Processing in batches of 20 students")
                    st.warning("• Switching to Gemini 2.0 Flash (1,500 RPD)")
                    st.warning("• Verifying your Google Cloud account for higher limits")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            time_estimate = st.empty()
            current_student = st.empty()
            quota_status = st.empty()
        
        # Ensure columns are properly normalized (should already be done by CSV processor)
        if 'Name' not in df.columns or 'Observations' not in df.columns:
            df.columns = df.columns.str.strip().str.title()
        
        start_time = datetime.now()
        
        # Import rate limiter for status updates - only for API models
        show_rate_status = False
        if not st.session_state.get('is_local_model', False):
            try:
                from backend.rate_limiter import get_rate_limiter
                rate_limiter = get_rate_limiter()
                show_rate_status = True
            except (ImportError, AttributeError, OSError):
                show_rate_status = False
        
        # Determine if we're using new format or legacy format
        has_new_format = all(col in df.columns for col in ['Name', 'School', 'Class', 'Session', 'Observations'])
        
        for idx, row in df.iterrows():
            student_name = str(row.get('Name', f'Student_{idx+1}')).strip()
            observations = str(row.get('Observations', '')).strip()
            
            # Extract school and class information based on format
            if has_new_format:
                # Use data from CSV
                row_school = str(row.get('School', 'Unknown')).strip()
                row_class = str(row.get('Class', 'Unknown')).strip()
                session = str(row.get('Session', 'Unknown')).strip()
            else:
                # Use provided parameters for legacy format
                row_school = school_name
                row_class = class_name
                session = 'Legacy_Upload'
            
            # Skip if somehow empty data got through (extra safety)
            if not student_name or not observations:
                continue
            
            # Update progress indicators
            progress = (idx + 1) / total_students
            progress_bar.progress(progress)
            
            # Calculate time estimates
            elapsed_time = (datetime.now() - start_time).total_seconds()
            if idx > 0:
                avg_time_per_student = elapsed_time / idx
                remaining_students = total_students - idx
                estimated_remaining = avg_time_per_student * remaining_students
                
                if estimated_remaining > 60:
                    time_estimate.text(f"⏱️ Estimated time remaining: {estimated_remaining/60:.1f} minutes")
                else:
                    time_estimate.text(f"⏱️ Estimated time remaining: {estimated_remaining:.0f} seconds")
            
            current_student.text(f"🎯 Currently assessing: **{student_name}** ({idx + 1}/{total_students})")
            status_text.text(f"Processing student {idx + 1} of {total_students} • {progress:.1%} complete")
            
            # Show quota usage during processing - only for API models
            if not st.session_state.get('is_local_model', False):
                try:
                    if show_rate_status:
                        status = rate_limiter.get_status()
                        daily_used = status['daily_requests']
                        daily_limit = status['max_per_day']
                        daily_remaining = daily_limit - daily_used
                        quota_status.text(f"📊 Quota: {daily_used}/{daily_limit} used | {daily_remaining} remaining today")
                except (KeyError, AttributeError, TypeError):
                    # Rate limiter not available or status incomplete
                    pass
            else:
                # Local model - show no quota usage
                quota_status.text("🖥️ Local Model: No quota usage - unlimited processing!")
            
            # Enhanced error handling with retry logic
            max_retries = 3
            retry_count = 0
            assessment_success = False
            last_error = None
            
            while retry_count < max_retries and not assessment_success:
                try:
                    result = st.session_state.assessment_system.assess_student_personality(observations)
                    results.append({
                        'student_id': f"student_{idx+1}",
                        'name': student_name,
                        'school': row_school,
                        'class': row_class,
                        'session': session,
                        'observations': observations,
                        'assessment': result
                    })
                    assessment_success = True
                    
                except Exception as e:
                    error_msg = str(e)
                    last_error = error_msg
                    retry_count += 1
                    
                    # Handle different error types
                    if "rate limit" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                        if retry_count < max_retries:
                            wait_time = 60 * retry_count  # Exponential backoff: 60s, 120s, 180s
                            st.warning(f"⚠️ Rate limit reached at student {idx + 1}. Waiting {wait_time}s before retry {retry_count}/{max_retries}...")
                            time.sleep(wait_time)
                        else:
                            st.error(f"❌ Rate limit exceeded after {max_retries} retries. Saving progress...")
                            # Save checkpoint and stop processing
                            checkpoint_df = pd.DataFrame(results)
                            checkpoint_df.to_csv(checkpoint_file, index=False, encoding='utf-8')
                            session_manager.update_batch_progress(
                                batch_id=timestamp,
                                progress={
                                    'current': idx,
                                    'total': total_students,
                                    'status': 'paused_rate_limit',
                                    'checkpoint_file': checkpoint_file,
                                    'resume_from': idx,
                                    'school': school_name if not has_new_format else 'Multiple',
                                    'class': class_name if not has_new_format else 'Multiple'
                                }
                            )
                            st.error(f"💾 Progress saved. Processed {idx}/{total_students} students.")
                            st.info("🔄 You can resume this batch later from the Session Recovery section.")
                            return  # Exit function to allow user to resume later
                    
                    elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                        if retry_count < max_retries:
                            wait_time = 10 * retry_count  # 10s, 20s, 30s
                            st.warning(f"⚠️ Connection error at student {idx + 1}. Retrying in {wait_time}s... ({retry_count}/{max_retries})")
                            time.sleep(wait_time)
                        else:
                            st.error(f"❌ Connection failed after {max_retries} retries.")
                    
                    elif "api" in error_msg.lower() and "key" in error_msg.lower():
                        st.error(f"❌ API key error: {error_msg}")
                        st.error("Please check your API key in the sidebar and try again.")
                        # Save checkpoint before stopping
                        checkpoint_df = pd.DataFrame(results)
                        checkpoint_df.to_csv(checkpoint_file, index=False, encoding='utf-8')
                        return  # Stop processing - API key issue needs user intervention
                    
                    else:
                        # Generic error - retry with shorter wait
                        if retry_count < max_retries:
                            st.warning(f"⚠️ Error at student {idx + 1}: {error_msg[:100]}... Retrying ({retry_count}/{max_retries})")
                            time.sleep(5)
            
            # If all retries failed, record the error
            if not assessment_success:
                results.append({
                    'student_id': f"student_{idx+1}",
                    'name': student_name,
                    'school': row_school,
                    'class': row_class,
                    'session': session,
                    'observations': observations,
                    'error': f"Failed after {max_retries} retries: {last_error}"
                })
                st.error(f"❌ Student {idx + 1} ({student_name}) failed after {max_retries} attempts. Continuing with next student...")
            
            # Save checkpoint every 5 students for small batches
            if (idx + 1) % 5 == 0 or idx == len(df) - 1:
                checkpoint_df = pd.DataFrame(results)
                checkpoint_df.to_csv(checkpoint_file, index=False, encoding='utf-8')
                
                # Auto-save session progress
                session_manager = st.session_state.session_manager
                session_manager.update_batch_progress(
                    batch_id=timestamp,
                    progress={
                        'current': idx + 1,
                        'total': total_students,
                        'status': 'in_progress',
                        'school': school_name if not has_new_format else 'Multiple',
                        'class': class_name if not has_new_format else 'Multiple'
                    }
                )
                
                # Show checkpoint save
                if total_students > 10:
                    progress_pct = ((idx + 1) / total_students) * 100
                    status_text.text(f"💾 Checkpoint saved • {progress_pct:.1f}% complete • {idx + 1}/{total_students} students")
        
        # Clear progress indicators and show completion
        progress_container.empty()
        
        # Show completion summary with enhanced metrics for large batches
        successful = len([r for r in results if not r.get('error')])
        failed = len([r for r in results if r.get('error')])
        processing_time = (datetime.now() - start_time).total_seconds()
        
        st.success(f"✅ Batch assessment completed!")
        
        # Enhanced completion metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("✅ Successful", successful)
        with col2:
            st.metric("❌ Failed", failed)
        with col3:
            st.metric("⏱️ Time Taken", f"{processing_time/60:.1f} min")
        with col4:
            success_rate = (successful / total_students) * 100 if total_students > 0 else 0
            st.metric("📊 Success Rate", f"{success_rate:.1f}%")
        
        # Show API usage summary for large batches
        if total_students > 50:
            try:
                if show_rate_status:
                    status = rate_limiter.get_status()
                    st.info(f"📊 **API Usage**: Used {total_students} of {status['max_per_day']} daily requests ({(total_students/status['max_per_day']*100):.1f}% of quota)")
            except (KeyError, AttributeError, TypeError, ZeroDivisionError):
                # Rate limiter not available or calculation error
                pass
        
        # Persist final results to session and render review UI
        st.session_state.batch_results = results
        st.session_state.batch_timestamp = timestamp
        st.session_state.saved_batch_csv = csv_filename  # Store the actual filename

        # Save final results as CSV with proper naming
        final_csv_path = f"assessments/{csv_filename}"
        results_df = build_csv_from_results(results)
        results_df.to_csv(final_csv_path, index=False, encoding='utf-8')
        
        # Clean up checkpoint file
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)

        # Build and persist review dataframe
        st.session_state.review_df = build_review_dataframe(results)
        st.session_state.batch_timestamp = timestamp  # Store timestamp for later use
        
        # Mark batch as completed in session
        session_manager = st.session_state.session_manager
        session_manager.update_batch_progress(
            batch_id=timestamp,
            progress={
                'current': total_students,
                'total': total_students,
                'status': 'completed',
                'completed_at': datetime.now().isoformat()
            }
        )
        
        # Complete the pending task
        session_manager.complete_task(f'batch_process_{timestamp}')
        
        # Add new pending task for review
        session_manager.add_pending_task({
            'id': f'batch_review_{timestamp}',
            'type': 'batch_review',
            'description': f'Review and finalize {total_students} assessments',
            'batch_id': timestamp
        })
        
        session_manager.save_session(force=True)
        
        # Show completion message with next steps
        st.info(f"📁 Results saved to: {csv_filename}")
        if failed > 0:
            st.warning(f"⚠️ {failed} students failed processing. Check the review section below for details.")
        st.info("👇 **Next Step:** Review and approve the assessments below")

        # Set flag to indicate batch processing is complete
        st.session_state.batch_processing_complete = True
        
    except Exception as e:
        st.error(f"❌ Batch assessment failed: {str(e)}")
        st.exception(e)  # Show full traceback for debugging
        
        # Update session to mark batch as failed
        session_manager = st.session_state.session_manager
        processed_count = len(results) if 'results' in locals() else 0
        
        session_manager.update_batch_progress(
            batch_id=timestamp,
            progress={
                'current': processed_count,
                'total': len(df),
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.now().isoformat(),
                'checkpoint_file': checkpoint_file if os.path.exists(checkpoint_file) else None,
                'school': school_name if not has_new_format else 'Multiple',
                'class': class_name if not has_new_format else 'Multiple'
            }
        )
        
        # Complete the processing task (even though it failed)
        session_manager.complete_task(f'batch_process_{timestamp}')
        session_manager.save_session(force=True)
        
        # Handle partial results
        if os.path.exists(checkpoint_file):
            st.success(f"💾 Partial results saved to: {checkpoint_file}")
            st.info(f"✅ Successfully processed {processed_count}/{len(df)} students before error.")
            st.info("🔄 **Recovery Options:**")
            st.info("1. Check the Session Recovery section to resume this batch")
            st.info("2. Review partial results below")
            st.info("3. Fix any issues and restart the batch")
            
            # If we have partial results, still create review dataframe
            if 'results' in locals() and results:
                st.session_state.review_df = build_review_dataframe(results)
                st.session_state.batch_results = results
                st.session_state.batch_timestamp = timestamp
                st.success("📊 Partial results are available for review below.")
                
                # Show what was completed
                successful = len([r for r in results if not r.get('error')])
                failed = len([r for r in results if r.get('error')])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✅ Completed", successful)
                with col2:
                    st.metric("❌ Failed", failed)
                with col3:
                    st.metric("⏸️ Remaining", len(df) - processed_count)
        else:
            st.warning("⚠️ No checkpoint file found. No partial results were saved.")
            st.info("💡 Tip: Checkpoints are saved every 5 students. The error may have occurred before the first checkpoint.")



def build_review_dataframe(results):
    """Construct review dataframe from batch results with validation and error handling."""
    review_rows = []
    validation_errors = []
    
    for i, r in enumerate(results):
        try:
            name_val = r.get('name', '')
            obs_val = r.get('observations', '')
            
            # Validate required fields
            if not name_val or not name_val.strip():
                validation_errors.append(f"Row {i+1}: Missing student name")
                name_val = f"Student_{i+1}"  # Fallback name
            
            if not obs_val or not obs_val.strip():
                validation_errors.append(f"Row {i+1}: Missing observations")
            
            # Handle assessment errors
            if r.get('error'):
                predicted = []
                validation_errors.append(f"Row {i+1} ({name_val}): Assessment failed - {r.get('error')}")
            else:
                # Extract and validate labels
                assessment_data = r.get('assessment', {})
                if not assessment_data:
                    validation_errors.append(f"Row {i+1} ({name_val}): No assessment data returned")
                    predicted = []
                else:
                    try:
                        predicted = extract_predicted_labels(assessment_data)
                        if not predicted:
                            validation_errors.append(f"Row {i+1} ({name_val}): No valid labels extracted from assessment")
                    except Exception as e:
                        validation_errors.append(f"Row {i+1} ({name_val}): Label extraction failed - {str(e)}")
                        predicted = []
            
            review_rows.append({
                'Name': name_val,
                'Observations': obs_val,
                'Predicted Labels': predicted,
                'Final Labels': list(predicted),
                'Approved': False
            })
            
        except Exception as e:
            validation_errors.append(f"Row {i+1}: Unexpected error processing row - {str(e)}")
            # Add a fallback row
            review_rows.append({
                'Name': f"Student_{i+1}",
                'Observations': "Error processing observations",
                'Predicted Labels': [],
                'Final Labels': [],
                'Approved': False
            })
    
    # Log validation errors for debugging
    if validation_errors:
        print(f"🔍 DEBUG: {len(validation_errors)} validation errors found:")
        for error in validation_errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        
        # Store errors in session state for display
        st.session_state.review_validation_errors = validation_errors
    else:
        # Clear any previous errors
        if 'review_validation_errors' in st.session_state:
            del st.session_state.review_validation_errors
    
    return pd.DataFrame(review_rows)

def render_review_interface():
    """Render the persistent reviewer interface using session state with pagination."""
    results = st.session_state.batch_results or []
    timestamp = st.session_state.batch_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    review_df = st.session_state.review_df
    if review_df is not None and 'Error' in review_df.columns:
        review_df = review_df.drop(columns=['Error'])
        st.session_state.review_df = review_df

    st.subheader("📊 Batch Assessment Results")
    
    # Display validation errors if any
    if 'review_validation_errors' in st.session_state:
        validation_errors = st.session_state.review_validation_errors
        if validation_errors:
            with st.expander(f"⚠️ Validation Issues ({len(validation_errors)} found)", expanded=False):
                st.warning("The following issues were found during batch processing:")
                for error in validation_errors[:20]:  # Show first 20 errors
                    st.write(f"• {error}")
                if len(validation_errors) > 20:
                    st.info(f"... and {len(validation_errors) - 20} more issues")
                st.info("💡 **Tip**: Review these issues and manually edit the Final Labels column as needed.")
    
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
    
    # Show workflow guidance for review
    workflow = st.session_state.workflow_protection
    guidance = workflow.get_workflow_guidance('batch_review')
    workflow.show_contextual_help(
        'batch_review',
        guidance['help'],
        guidance.get('tips', [])
    )
    
    # Pagination controls for large datasets
    total_rows = len(review_df) if review_df is not None else 0
    rows_per_page = 25  # Limit to 25 rows per page for better performance
    
    if total_rows > rows_per_page:
        # Initialize pagination state
        if 'review_page' not in st.session_state:
            st.session_state.review_page = 0
        
        total_pages = (total_rows - 1) // rows_per_page + 1
        current_page = st.session_state.review_page
        
        # Pagination controls
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=current_page == 0):
                st.session_state.review_page = max(0, current_page - 1)
        
        with col2:
            if st.button("➡️ Next", disabled=current_page >= total_pages - 1):
                st.session_state.review_page = min(total_pages - 1, current_page + 1)
        
        with col3:
            st.info(f"📄 Page {current_page + 1} of {total_pages} ({total_rows} total rows)")
        
        with col4:
            # Jump to page
            page_input = st.number_input("Go to page:", min_value=1, max_value=total_pages, value=current_page + 1, key="page_jump")
            if st.button("Go"):
                st.session_state.review_page = page_input - 1
        
        with col5:
            # Show all rows option (with warning)
            if st.button("📋 Show All", help="⚠️ May slow down UI for large datasets"):
                st.session_state.review_page = -1  # Special value for showing all
        
        # Calculate slice for current page
        if st.session_state.review_page == -1:
            # Show all rows
            start_idx = 0
            end_idx = total_rows
            display_df = review_df
            st.warning(f"⚠️ Showing all {total_rows} rows - UI may be slow")
        else:
            start_idx = current_page * rows_per_page
            end_idx = min(start_idx + rows_per_page, total_rows)
            display_df = review_df.iloc[start_idx:end_idx].copy()
    else:
        # Small dataset - show all rows
        display_df = review_df
        start_idx = 0
        end_idx = total_rows
    
    # Bulk approval controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        show_debug = st.toggle("Show raw assessments (debug)", value=False)
    with col2:
        if st.button("✅ Select All", use_container_width=True):
            if total_rows > rows_per_page and st.session_state.review_page != -1:
                # Only select current page
                review_df.iloc[start_idx:end_idx, review_df.columns.get_loc("Approved")] = True
                st.info(f"Selected rows {start_idx + 1}-{end_idx} on current page")
            else:
                # Select all rows
                review_df["Approved"] = True
            st.session_state.review_df = review_df
    with col3:
        if st.button("❌ Deselect All", use_container_width=True):
            if total_rows > rows_per_page and st.session_state.review_page != -1:
                # Only deselect current page
                review_df.iloc[start_idx:end_idx, review_df.columns.get_loc("Approved")] = False
                st.info(f"Deselected rows {start_idx + 1}-{end_idx} on current page")
            else:
                # Deselect all rows
                review_df["Approved"] = False
            st.session_state.review_df = review_df

    # Data editor with current page data
    # Initialize editor reset counter if not exists
    if 'editor_reset_counter' not in st.session_state:
        st.session_state.editor_reset_counter = 0
    
    # Use a key that includes reset counter to force reload when needed
    editor_key = f"review_editor_{timestamp}_{st.session_state.get('review_page', 0)}_{st.session_state.editor_reset_counter}"
    
    edited_df_page = st.data_editor(
        display_df,
        key=editor_key,
        width='stretch',
        num_rows="fixed",
        column_config={
            "Predicted Labels": st.column_config.ListColumn(
                help="Model-predicted labels (quality-level). ⚠️ Clearing this data cannot be undone!",
                width="medium"
            ),
            "Final Labels": st.column_config.ListColumn(
                help="Edit labels as needed before approval. ⚠️ Clearing this data cannot be undone!",
                width="medium"
            ),
            "Approved": st.column_config.CheckboxColumn(help="Tick after reviewing this row.")
        }
    )
    
    # Check for data loss and show confirmation dialog
    if total_rows > 0:
        # Compare original and edited data to detect clearing of labels
        original_page = review_df.iloc[start_idx:end_idx].copy()
        data_loss_detected = False
        cleared_rows = []
        
        for idx in range(len(edited_df_page)):
            orig_predicted = original_page.iloc[idx]['Predicted Labels']
            orig_final = original_page.iloc[idx]['Final Labels']
            new_predicted = edited_df_page.iloc[idx]['Predicted Labels']
            new_final = edited_df_page.iloc[idx]['Final Labels']
            
            # Check if labels were cleared (non-empty to empty)
            if (isinstance(orig_predicted, list) and len(orig_predicted) > 0 and 
                (not isinstance(new_predicted, list) or len(new_predicted) == 0)):
                data_loss_detected = True
                cleared_rows.append(f"Row {start_idx + idx + 1}: Predicted Labels cleared")
            
            if (isinstance(orig_final, list) and len(orig_final) > 0 and 
                (not isinstance(new_final, list) or len(new_final) == 0)):
                data_loss_detected = True
                cleared_rows.append(f"Row {start_idx + idx + 1}: Final Labels cleared")
        
        # Show confirmation dialog if data loss detected
        if data_loss_detected:
            if 'confirm_data_loss' not in st.session_state:
                st.session_state.confirm_data_loss = False
            
            if not st.session_state.confirm_data_loss:
                # Show compact popup dialog in main UI
                st.error("⚠️ **Data Loss Warning**")
                
                with st.container():
                    st.markdown("**The following label data will be permanently lost:**")
                    for row_info in cleared_rows:
                        st.write(f"• {row_info}")
                    
                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("✅ Confirm Changes", type="primary", key="confirm_data_loss_yes", use_container_width=True):
                            st.session_state.confirm_data_loss = True
                            # Apply the changes
                            review_df.iloc[start_idx:end_idx] = edited_df_page
                            st.session_state.review_df = review_df
                            st.success("Changes applied.")
                            st.rerun()
                    with col_confirm2:
                        if st.button("❌ Cancel Changes", key="confirm_data_loss_no", use_container_width=True):
                            # Reset the data editor by incrementing the reset counter
                            st.session_state.editor_reset_counter += 1
                            st.session_state.confirm_data_loss = False
                            st.info("Changes cancelled.")
                            st.rerun()
                
                # Don't update the dataframe until confirmed - use original data
                review_df.iloc[start_idx:end_idx] = original_page
                st.session_state.review_df = review_df
                return
            else:
                # Confirmation given, apply changes
                review_df.iloc[start_idx:end_idx] = edited_df_page
                st.session_state.review_df = review_df
                st.session_state.confirm_data_loss = False  # Reset for next time
        else:
            # No data loss, apply changes normally
            review_df.iloc[start_idx:end_idx] = edited_df_page
            st.session_state.review_df = review_df

    # Overall approval status
    all_approved = bool(len(review_df) > 0 and review_df["Approved"].all())
    approved_count = review_df["Approved"].sum() if len(review_df) > 0 else 0
    
    if not all_approved:
        st.info(f"📋 {approved_count}/{len(review_df)} rows approved. Review and approve all rows before finalizing.")
        if total_rows > rows_per_page:
            remaining_pages = []
            for page in range((total_rows - 1) // rows_per_page + 1):
                page_start = page * rows_per_page
                page_end = min(page_start + rows_per_page, total_rows)
                page_approved = review_df.iloc[page_start:page_end]["Approved"].sum()
                page_total = page_end - page_start
                if page_approved < page_total:
                    remaining_pages.append(f"Page {page + 1} ({page_approved}/{page_total})")
            
            if remaining_pages:
                st.warning(f"📄 Pages with unapproved rows: {', '.join(remaining_pages[:5])}")
    else:
        st.success(f"✅ All {len(review_df)} rows approved and ready to finalize!")

    # Debug section with pagination
    if show_debug:
        st.markdown("---")
        with st.expander("Raw assessment data by row"):
            if not results:
                st.warning("⚠️ No results data available. Make sure you have completed a batch assessment first.")
                return
            
            # Add download option for raw assessments
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info("📋 **Raw Assessment Data**: Complete AI reasoning and assessment details for research and analysis")
            with col2:
                # Create downloadable JSON of raw assessments
                import json
                raw_data = {
                    'timestamp': datetime.now().isoformat(),
                    'total_assessments': len(results),
                    'model_used': st.session_state.get('selected_model', 'Unknown'),
                    'is_local_model': st.session_state.get('is_local_model', False),
                    'assessments': results
                }
                
                raw_json = json.dumps(raw_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Download Raw Data",
                    data=raw_json.encode('utf-8'),
                    file_name=f"raw_assessments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    help="Download complete raw assessment data for analysis"
                )
            
            # Show all results without truncation
            for i, r in enumerate(results):
                st.write(f"**Row {i + 1}: {r.get('name','')}**")
                if r.get('error'):
                    st.error(r.get('error'))
                elif r.get('assessment'):
                    try:
                        # Show complete assessment data without truncation
                        assessment_str = json.dumps(r['assessment'], indent=2, ensure_ascii=False)
                        st.code(assessment_str, language='json')
                    except Exception as e:
                        st.error(f"Error displaying assessment data: {str(e)}")
                        st.write("Raw assessment object:")
                        st.write(r['assessment'])
                else:
                    st.warning("No assessment returned for this row.")
                
                # Add separator between rows for clarity
                if i < len(results) - 1:
                    st.markdown("---")

    # Add action buttons section
    st.markdown("---")
    st.subheader("🎯 Review Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("❌ Cancel Review", type="secondary", help="Cancel the current review and return to batch assessment"):
            # Clear review data and return to batch assessment
            if 'review_df' in st.session_state:
                del st.session_state.review_df
            if 'batch_results' in st.session_state:
                del st.session_state.batch_results
            if 'batch_timestamp' in st.session_state:
                del st.session_state.batch_timestamp
            if 'saved_batch_csv' in st.session_state:
                del st.session_state.saved_batch_csv
            if 'original_csv_filename' in st.session_state:
                del st.session_state.original_csv_filename
            
            st.success("✅ Review cancelled. You can start a new batch assessment.")
            st.info("👆 Upload a new CSV file above to begin a fresh assessment.")
            st.rerun()
    
        
        elif st.button("✅ Finalize & Download CSV", type="primary", disabled=not all_approved):
            # Show critical action warning
            workflow = st.session_state.workflow_protection
            workflow.show_critical_action_warning(
                "Finalize Assessments",
                f"This will store {approved_count} assessments permanently and download the CSV file."
            )
            
            # Set flag to show confirmation dialog at top level
            st.session_state.show_finalize_confirmation = True
            st.rerun()

def store_approved_batch_assessments(edited_df, results, batch_timestamp=None):
    """Store approved batch assessments in the main storage system"""
    storage_manager = st.session_state.storage_manager
    assessment_date = datetime.now().strftime("%Y-%m-%d")
    
    approved_rows = edited_df[edited_df['Approved'] == True] if 'Approved' in edited_df.columns else edited_df
    stored_count = 0
    
    # Extract school and class from first result
    school_name = "Unknown"
    class_name = "Unknown"
    if results and len(results) > 0:
        school_name = results[0].get('school', 'Unknown')
        class_name = results[0].get('class', 'Unknown')
    
    # Find and load batch assessment CSV file
    batch_df = None
    saved_csv_filename = st.session_state.get('saved_batch_csv')
    if saved_csv_filename:
        batch_csv_file = f"assessments/{saved_csv_filename}"
        if os.path.exists(batch_csv_file):
            try:
                batch_df = pd.read_csv(batch_csv_file, encoding='utf-8')
            except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
                # Try alternative encoding
                try:
                    batch_df = pd.read_csv(batch_csv_file, encoding='latin-1')
                except Exception:
                    pass
    
    def get_assessment_result_from_batch(student_name, batch_df):
        """Convert batch CSV data to proper assessment result format"""
        if batch_df is None:
            return None
        
        student_data = batch_df[batch_df['name'] == student_name]
        if len(student_data) == 0:
            return None
        
        assessment_result = {'assessments': []}
        for idx, row in student_data.iterrows():
            assessment_item = {
                'quality': row['quality'],
                'level': row['level'],
                'reasoning': row['reasoning'] if pd.notna(row['reasoning']) else ''
            }
            assessment_result['assessments'].append(assessment_item)
        
        return assessment_result
    
    # Store assessments
    for idx, row in approved_rows.iterrows():
        student_name = row['Name']
        observations = row['Observations']
        
        # Get assessment result from batch CSV data or fallback to results array
        assessment_result = None
        student_school = school_name
        student_class = class_name
        
        if batch_df is not None:
            assessment_result = get_assessment_result_from_batch(student_name, batch_df)
            student_batch_data = batch_df[batch_df['name'] == student_name]
            if len(student_batch_data) > 0:
                first_row = student_batch_data.iloc[0]
                # Safely access values with null checks
                school_val = first_row.get('school', school_name)
                student_school = school_val if pd.notna(school_val) else school_name
                
                class_val = first_row.get('class', class_name)
                student_class = class_val if pd.notna(class_val) else class_name
        
        if not assessment_result:
            for result in results:
                if result.get('name') == student_name:
                    assessment_result = result.get('assessment')
                    student_school = result.get('school', school_name)
                    student_class = result.get('class', class_name)
                    break
        
        if assessment_result:
            try:
                # Prepend school/class info to observations
                enhanced_observations = f"[School: {student_school}] [Class: {student_class}]\n{observations}"
                
                # Check for duplicates and add assessment
                is_duplicate, _ = storage_manager.check_duplicate_assessments(student_name, assessment_date)
                
                if not is_duplicate:
                    if storage_manager.add_assessment(student_name, enhanced_observations, assessment_result, assessment_date):
                        stored_count += 1
            except (KeyError, AttributeError, TypeError, ValueError) as e:
                # Log error but continue processing other students
                st.warning(f"⚠️ Could not store assessment for {student_name}: {str(e)}")
                continue
    
    # Invalidate cache after storing new assessments so other tabs show updated data
    if stored_count > 0:
        if 'cached_profiles' in st.session_state:
            del st.session_state['cached_profiles']
        if 'cached_assessments' in st.session_state:
            del st.session_state['cached_assessments']
        st.session_state.force_refresh_profiles = True
    
    return stored_count

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
    """Return normalized labels in 'quality-level' format, including all valid entries."""
    # Allowed levels mapping
    level_map = {
        'low': 'low',
        'middle': 'middle',
        'mid': 'middle',
        'medium': 'middle',
        'high': 'high',
        'not observed': 'not-observed',
        'not_observed': 'not-observed',
        'notobserved': 'not-observed',
        'na': 'not-observed',
        'n/a': 'not-observed'
    }
    
    # Extract assessments from result
    assessments = assessment_result.get('assessments', [])
    if not assessments:
        print("⚠️ DEBUG: No assessments found in assessment_result")
        return []
    
    # Allowed qualities set (normalized hyphen-case) from config
    allowed_qualities = {q.lower().replace(' ', '-') for q in PERSONALITY_QUALITIES}
    
    labels = []
    seen = set()
    extraction_errors = []
    
    # Handle different assessment formats
    for item in assessments:
        try:
            # Check if this is a local model format (nested dictionary)
            if isinstance(item, dict) and not item.get('quality'):
                # Local model format: {'quality_name': {'quality': '...', 'level': '...', 'reasoning': '...'}}
                for quality_key, quality_data in item.items():
                    if isinstance(quality_data, dict):
                        quality_raw = quality_data.get('quality', '')
                        level_raw = quality_data.get('level', '')
                        
                        if not quality_raw or not level_raw:
                            continue
                        
                        # Normalize quality name
                        quality_normalized = _normalize_quality(quality_raw, allowed_qualities)
                        if not quality_normalized:
                            extraction_errors.append(f"Failed to normalize quality: {quality_raw}")
                            continue
                        
                        # Normalize level
                        level_lower = level_raw.lower().strip()
                        level_normalized = level_map.get(level_lower, '')
                        
                        # Include ALL valid levels (including 'not-observed')
                        if not level_normalized:
                            extraction_errors.append(f"Failed to normalize level: {level_raw}")
                            continue
                        
                        # Create label and check for duplicates
                        label = f"{quality_normalized}:{level_normalized}"
                        if label not in seen:
                            seen.add(label)
                            labels.append(label)
            else:
                # Standard format: {'quality': '...', 'level': '...', 'reasoning': '...'}
                quality_raw = item.get('quality', '')
                level_raw = item.get('level', '')
                
                if not quality_raw or not level_raw:
                    continue
                
                # Normalize quality name
                quality_normalized = _normalize_quality(quality_raw, allowed_qualities)
                if not quality_normalized:
                    extraction_errors.append(f"Failed to normalize quality: {quality_raw}")
                    continue
                
                # Normalize level
                level_lower = level_raw.lower().strip()
                level_normalized = level_map.get(level_lower, '')
                
                # Include ALL valid levels (including 'not-observed')
                if not level_normalized:
                    extraction_errors.append(f"Failed to normalize level: {level_raw}")
                    continue
                
                # Create label and check for duplicates
                label = f"{quality_normalized}:{level_normalized}"
                if label not in seen:
                    seen.add(label)
                    labels.append(label)
        except Exception as e:
            extraction_errors.append(f"Error processing assessment item: {str(e)}")
            continue
    
    # Log extraction results for debugging
    print(f"🔍 DEBUG: Extracted {len(labels)} labels from {len(assessments)} assessments")
    if extraction_errors:
        print(f"⚠️ DEBUG: {len(extraction_errors)} extraction errors:")
        for error in extraction_errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
    
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

def system_info_tab():
    """Display system information and enhanced storage manager features"""
    st.header("⚙️ System Information & Metadata")
    
    storage_manager = st.session_state.storage_manager
    
    # Create tabs for different system info sections
    info_tab1, info_tab2 = st.tabs([
        "📊 System Stats", "👥 Student Metadata"
    ])
    
    with info_tab1:
        display_system_metadata(storage_manager)
    
    with info_tab2:
        display_student_metadata(storage_manager)

def display_system_metadata(storage_manager):
    """Display system-wide metadata and statistics"""
    # Header with refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 System Statistics")
    with col2:
        if st.button("🔄 Refresh Stats", help="Reload system statistics", key="refresh_system_stats"):
            # Clear any cached data
            if 'cached_profiles' in st.session_state:
                del st.session_state['cached_profiles']
            if 'cached_assessments' in st.session_state:
                del st.session_state['cached_assessments']
            st.rerun()
    
    try:
        # Get system metadata (now recalculates from actual data)
        system_meta = storage_manager.get_system_metadata()
        
        # Display key metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Students", system_meta.get('total_students', 0))
        
        with col2:
            st.metric("Total Observations", system_meta.get('total_observations', 0))
        
        with col3:
            # Calculate average observations per student
            total_students = system_meta.get('total_students', 0)
            total_obs = system_meta.get('total_observations', 0)
            avg_obs = round(total_obs / total_students, 1) if total_students > 0 else 0
            st.metric("Avg Observations/Student", avg_obs)
        
        # Display detailed metadata
        st.subheader("📋 Detailed System Information")
        
        # Format timestamps nicely
        created_at = system_meta.get('created_at')
        last_updated = system_meta.get('last_updated')
        last_operation = system_meta.get('last_operation_timestamp')
        
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError, TypeError):
                pass
        
        if last_updated:
            try:
                dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                last_updated = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError, TypeError):
                pass
        
        if last_operation:
            try:
                dt = datetime.fromisoformat(last_operation.replace('Z', '+00:00'))
                last_operation = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError, TypeError):
                pass
        
        info_data = {
            "Storage File": system_meta.get('storage_file', 'Unknown'),
            "System Created": created_at or 'Unknown',
            "Last Updated": last_updated or 'Unknown',
            "Last Operation": last_operation or 'Never',
            "System Version": system_meta.get('version', 'Unknown'),
            "Metadata File": system_meta.get('metadata_file', 'Unknown')
        }
        
        for key, value in info_data.items():
            st.write(f"**{key}:** {value}")
            
    except Exception as e:
        st.error(f"Error loading system metadata: {e}")

def display_student_metadata(storage_manager):
    """Display student-specific metadata"""
    st.subheader("👥 Student Metadata")
    
    try:
        # Get all assessments to extract schools
        all_assessments = storage_manager.get_all_assessments()
        
        if not all_assessments:
            st.info("No assessment data found in the system.")
            return
        
        # Extract unique schools
        schools = sorted(list(set(assessment.get('school', 'Unknown') for assessment in all_assessments)))
        
        # School selector
        selected_school = st.selectbox(
            "Select a school:",
            options=['All Schools'] + schools,
            key="school_metadata_selector"
        )
        
        # Filter students by school
        if selected_school == 'All Schools':
            students = storage_manager.get_all_students()
        else:
            # Get students from selected school
            school_assessments = [a for a in all_assessments if a.get('school') == selected_school]
            students = sorted(list(set(assessment.get('student_name') for assessment in school_assessments)))
        
        if not students:
            st.info(f"No students found{' in ' + selected_school if selected_school != 'All Schools' else ''}.")
            return
        
        # Student selector
        selected_student = st.selectbox(
            "Select a student to view metadata:",
            options=students,
            key="student_metadata_selector"
        )
        
        if selected_student:
            # Get metadata for selected student
            meta = storage_manager.get_observation_metadata(selected_student)
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Observations", meta.get('observation_count', 0))
            
            with col2:
                st.metric("Assessments", meta.get('assessment_count', 0))
            
            with col3:
                has_consolidated = meta.get('has_consolidated_assessment', False)
                st.metric("Consolidated Profile", "✅" if has_consolidated else "❌")
            
            # Display detailed information
            st.subheader(f"📋 Details for {selected_student}")
            
            # Format dates
            first_observed = meta.get('first_observed')
            last_observed = meta.get('last_observed')
            
            if first_observed:
                try:
                    dt = datetime.fromisoformat(first_observed.replace('Z', '+00:00'))
                    first_observed = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError, TypeError):
                    pass
            
            if last_observed:
                try:
                    dt = datetime.fromisoformat(last_observed.replace('Z', '+00:00'))
                    last_observed = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError, TypeError):
                    pass
            
            detail_data = {
                "Student Name": meta.get('student_name', 'Unknown'),
                "First Observed": first_observed or 'Never',
                "Last Observed": last_observed or 'Never',
                "Observation Dates": ', '.join(meta.get('observation_dates', [])),
                "Assessment Dates": ', '.join(meta.get('assessment_dates', [])),
                "Data Sources": ', '.join(meta.get('data_sources', [])),
                "School": meta.get('school', 'Unknown'),
                "Class": meta.get('class', 'Unknown')
            }
            
            for key, value in detail_data.items():
                st.write(f"**{key}:** {value}")
        
        # Show summary table of all students
        st.subheader("📊 All Students Summary")
        
        summary_data = []
        for student in students:
            meta = storage_manager.get_observation_metadata(student)
            summary_data.append({
                'Student': student,
                'Observations': meta.get('observation_count', 0),
                'Assessments': meta.get('assessment_count', 0),
                'Last Observed': meta.get('last_observed', 'Never')[:10] if meta.get('last_observed') else 'Never'
            })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, width='stretch')
            
    except Exception as e:
        st.error(f"Error loading student metadata: {e}")

def display_data_integrity(storage_manager):
    """Display data integrity validation"""
    st.subheader("🔍 Data Integrity Validation")
    
    try:
        # Validation controls
        if st.button("🔍 Run Data Validation", type="primary"):
            with st.spinner("Validating data integrity..."):
                validation = storage_manager.validate_data_integrity()
                
                # Display results
                if validation['is_valid']:
                    st.success("✅ Data integrity validation passed!")
                else:
                    st.error("❌ Data integrity issues found!")
                
                # Show issues
                if validation['issues']:
                    st.subheader("🚨 Issues Found")
                    for issue in validation['issues']:
                        st.error(f"• {issue}")
                
                # Show warnings
                if validation['warnings']:
                    st.subheader("⚠️ Warnings")
                    for warning in validation['warnings']:
                        st.warning(f"• {warning}")
                
                # Show statistics
                if validation['statistics']:
                    st.subheader("📊 Validation Statistics")
                    stats_col1, stats_col2 = st.columns(2)
                    
                    stats_items = list(validation['statistics'].items())
                    mid_point = len(stats_items) // 2
                    
                    with stats_col1:
                        for key, value in stats_items[:mid_point]:
                            st.metric(key.replace('_', ' ').title(), value)
                    
                    with stats_col2:
                        for key, value in stats_items[mid_point:]:
                            st.metric(key.replace('_', ' ').title(), value)
        
        # Show current data info
        st.subheader("📋 Current Data Information")
        
        # Load basic info
        try:
            df = storage_manager.load_existing_data()
            if not df.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Rows", len(df))
                
                with col2:
                    st.metric("Total Columns", len(df.columns))
                
                with col3:
                    date_columns = storage_manager.get_date_columns(df)
                    st.metric("Date Columns", len(date_columns))
                
                # Show column info
                st.write("**Columns:**")
                st.write(", ".join(df.columns.tolist()))
                
                # Show sample data
                if st.checkbox("Show sample data"):
                    st.dataframe(df.head(), width='stretch')
            else:
                st.info("No data found in storage.")
                
        except Exception as e:
            st.warning(f"Could not load data info: {e}")
        
    except Exception as e:
        st.error(f"Error running data validation: {e}")

if __name__ == "__main__":
    main()


