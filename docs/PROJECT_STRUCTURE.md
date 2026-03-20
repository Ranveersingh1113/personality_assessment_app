# Project Structure

## 🎓 Personality Assessment System for Students

Clean and organized codebase structure for the personality assessment application.

## Directory Structure

```
personality_assessment_app/
│
├── ai_core/                          # Core AI and assessment logic
│   ├── assessment_storage_manager.py # Storage and retrieval of assessments
│   ├── data_consolidator.py          # Data consolidation logic
│   ├── duplicate_detector.py         # Duplicate detection
│   ├── enhanced_csv_processor.py     # CSV processing
│   ├── local_model_adapter.py        # Local model integration
│   ├── local_personality_assessment.py # Local model assessments
│   ├── personality_assessment.py     # Main assessment logic
│   ├── session_manager.py            # Session management
│   └── workflow_protection.py        # Workflow protection
│
├── backend/                          # Backend utilities
│   └── rate_limiter.py               # API rate limiting
│
├── frontend/                         # User interface
│   ├── analytics_visualizations.py   # Charts and visualizations
│   ├── enhanced_stored_assessments.py # Assessment viewing interface
│   └── streamlit_app.py              # Main application
│
├── utils/                            # Utility functions
│   ├── data_export_import.py         # Data export/import
│   ├── performance.py                # Performance utilities
│   └── __init__.py
│
├── tests/                            # Unit tests
│   ├── test_data_consolidation_properties.py
│   ├── test_enhanced_csv_processor.py
│   ├── test_school_organization_properties.py
│   ├── test_system_performance.py
│   └── test_timestamp_monotonicity.py
│
├── test_datasets/                    # Test data for development
│   ├── blank_rows_test.csv
│   ├── consolidation_test_january.csv
│   ├── consolidation_test_march.csv
│   ├── consolidation_test_may.csv
│   ├── improvement_journey.csv
│   ├── large_batch_end_year.csv
│   ├── large_batch_mid_year.csv
│   ├── multi_school_comparison.csv
│   ├── single_school_intensive.csv
│   └── README.md
│
├── assessments/                      # Stored assessment data
│   └── student_assessments.csv
│
├── sessions/                         # Session checkpoints
│
├── test_batches/                     # Batch processing data
│
├── .kiro/                            # Kiro IDE configuration
│   └── specs/                        # Project specifications
│
├── .streamlit/                       # Streamlit configuration
│
├── .env                              # Environment variables (API keys)
├── .gitignore                        # Git ignore rules
├── config.py                         # Application configuration
├── dev_server.py                     # Development server
├── requirements.txt                  # Python dependencies
├── requirements_visualization.txt    # Visualization dependencies
├── run_app.bat                       # Windows batch file to run app
│
├── map-t.pdf                         # Reference document
├── reference_sheet_template.csv      # Assessment template
├── report_card_template.xlsx         # Report card template
├── Obseervations check list for feeding.1.xlsx - observation check list 1.csv
│
└── Documentation/                    # User guides
    ├── README.md                     # Main documentation
    ├── DEVELOPER_MODE_GUIDE.md       # Developer mode instructions
    ├── START_HERE_NGO_GUIDE.md       # NGO user guide
    ├── HOW_TO_UPLOAD_CONSOLIDATION_DATA.md
    ├── GROWTH_TRENDS_USER_GUIDE.md
    ├── LOCAL_MODEL_TESTING_GUIDE.md
    ├── TESTING_CHECKLIST.md
    ├── TESTING_WITH_LOCAL_MODELS.md
    ├── QUICK_REFERENCE_TABS.md
    ├── REMOVE_DUMMY_DATA_GUIDE.md
    └── SYSTEM_TABS_DOCUMENTATION.md
```

## Core Components

### AI Core (`ai_core/`)
- Assessment logic and AI integration
- Data storage and consolidation
- Session management
- Local and API-based models

### Frontend (`frontend/`)
- Streamlit-based user interface
- Analytics and visualizations
- Assessment viewing and management

### Backend (`backend/`)
- Rate limiting for API calls
- Utility functions

### Utils (`utils/`)
- Data export/import functionality
- Performance optimization utilities

## Configuration Files

- `.env` - API keys and environment variables
- `config.py` - Application settings and model configurations
- `requirements.txt` - Python package dependencies

## Data Files

- `assessments/` - Stored student assessments
- `sessions/` - Session checkpoints for batch processing
- `test_batches/` - Batch processing data
- `test_datasets/` - Sample data for testing

## Documentation

All user-facing documentation is kept in the root directory:
- User guides for NGO users
- Developer documentation
- Testing guides
- System reference documentation

## Running the Application

### For NGO Users
```bash
streamlit run frontend/streamlit_app.py
```

### For Developers (with local models)
```bash
# Windows PowerShell
$env:DEVELOPER_MODE="true"
streamlit run frontend/streamlit_app.py

# Linux/Mac
export DEVELOPER_MODE=true
streamlit run frontend/streamlit_app.py
```

## Key Features

1. **Single Student Assessment** - Assess individual students
2. **Batch Assessment** - Process multiple students at once
3. **Stored Assessments** - View and manage saved assessments
4. **Growth Trends** - Track student progress over time
5. **System Info** - View system statistics and metadata
6. **Data Consolidation** - Merge multiple assessments per student

## Technology Stack

- **Frontend**: Streamlit
- **AI Models**: Google Gemini API, Local Llama models (optional)
- **Data Storage**: CSV files
- **Visualization**: Plotly, Matplotlib
- **Language**: Python 3.8+

## Clean Codebase

This codebase has been cleaned of:
- ✅ 168 test files removed
- ✅ Debug scripts removed
- ✅ Temporary documentation removed
- ✅ Only essential files kept
- ✅ Organized structure maintained

## Next Steps

1. Review the `START_HERE_NGO_GUIDE.md` for getting started
2. Check `DEVELOPER_MODE_GUIDE.md` for development setup
3. See `SYSTEM_TABS_DOCUMENTATION.md` for feature details
