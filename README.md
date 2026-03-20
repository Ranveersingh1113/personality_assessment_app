# Student Personality Assessment System

A comprehensive AI-powered system for assessing student personality traits and generating detailed reports for educational institutions. Built specifically for NGOs working with rural students, this system provides robust data management, growth tracking, and multi-language support.

## ✨ Key Features

### 🎯 Core Assessment Capabilities
- **Individual Assessment**: Detailed one-on-one personality evaluation with 20 personality traits
- **Batch Assessment**: Process multiple students simultaneously with CSV upload (up to 50 students)
- **Smart Validation**: Automatic detection of blank rows, duplicates, and data quality issues
- **Multi-Session Support**: Track student development across multiple observation sessions
- **SWOT Analysis**: Generate comprehensive strengths, weaknesses, opportunities, and threats analysis
- **Report Cards**: Automated Marathi report card generation with Excel template support

### � Data Management & Organization
- **School Hierarchy View**: Organized display by School → Class → Student
- **Data Consolidation**: Intelligent merging of multiple observations per student with temporal weighting
- **Duplicate Detection**: Comprehensive detection across files, students, and assessments
- **Search & Filter**: Advanced search with filters by school, class, date range, and observation count
- **Automatic Backups**: Versioned backups with automatic cleanup of old data
- **Audit Logging**: Complete activity tracking for all data operations

### 📈 Growth Tracking & Analytics
- **Timeline Views**: Visualize student development over time
- **Growth Trends Dashboard**: Track personality trait changes across multiple assessments
- **School Comparisons**: Compare performance across different schools and classes
- **Power BI-style Visualizations**: Interactive charts with Plotly and Altair
- **Student Progress Reports**: Individual growth analysis with radar charts and trend lines
- **Quality Metrics**: Data quality scoring and recommendations

### 🔧 Developer & Testing Features
- **Developer Mode**: Test without consuming API quota using local models
- **Local Model Support**: Integration with Ollama (Llama, Mistral, Gemma models)
- **Session Recovery**: Auto-save and recovery of incomplete work
- **Workflow Protection**: Guided workflows with validation and error prevention
- **Property-Based Testing**: Comprehensive test suite with Hypothesis
- **Performance Monitoring**: Built-in performance tracking and optimization

### 🌐 Multi-Language & Accessibility
- **English & Marathi**: Full support for both languages in UI and reports
- **Bilingual Report Cards**: Generate reports in Marathi with English fallback
- **Clean UI**: Simplified interface with essential metrics only
- **Responsive Design**: Works on desktop and tablet devices

## � Quick Start

### For NGO Users (Windows)

1. **Install Python** (one-time)
   - Download from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation

2. **Get API Key** (one-time)
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create and copy your API key

3. **Configure & Run**
   - Open `.env` file and add your API key
   - Double-click `run_app.bat`
   - Browser opens automatically at http://localhost:8501

📖 **Detailed Guide**: See [QUICK_START.md](QUICK_START.md) for step-by-step instructions

### For Developers

```bash
# Clone repository
git clone https://github.com/Ranveersingh1113/personality_assessment_app.git
cd personality_assessment_app

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_visualization.txt  # For analytics dashboard

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run application
streamlit run frontend/streamlit_app.py
```

## � Documentation

### Getting Started
- **[QUICK_START.md](QUICK_START.md)** - 5-minute setup guide
- **[docs/START_HERE_NGO_GUIDE.md](docs/START_HERE_NGO_GUIDE.md)** - Complete NGO user guide
- **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Deployment and maintenance
- **[docs/API_KEY_SETUP_GUIDE.md](docs/API_KEY_SETUP_GUIDE.md)** - API key configuration

### Developer Documentation
- **[docs/DEVELOPER_MODE_GUIDE.md](docs/DEVELOPER_MODE_GUIDE.md)** - Testing without API quota
- **[docs/LOCAL_MODEL_TESTING_GUIDE.md](docs/LOCAL_MODEL_TESTING_GUIDE.md)** - Local model setup
- **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Codebase architecture
- **[docs/TESTING_CHECKLIST.md](docs/TESTING_CHECKLIST.md)** - QA procedures

### User Guides
- **[docs/GROWTH_TRENDS_USER_GUIDE.md](docs/GROWTH_TRENDS_USER_GUIDE.md)** - Growth tracking features
- **[test_datasets/README.md](test_datasets/README.md)** - Sample data and testing

## 🏗️ Project Structure

```
personality_assessment_app/
├── ai_core/                          # Core AI and assessment logic
│   ├── personality_assessment.py    # Main assessment system (Gemini API)
│   ├── local_personality_assessment.py  # Local model assessment
│   ├── local_model_adapter.py       # Ollama integration
│   ├── assessment_storage_manager.py # Data storage with metadata
│   ├── data_consolidator.py         # Multi-observation consolidation
│   ├── duplicate_detector.py        # Comprehensive duplicate detection
│   ├── enhanced_csv_processor.py    # Robust CSV validation
│   ├── session_manager.py           # Auto-save and recovery
│   └── workflow_protection.py       # User guidance system
│
├── frontend/                         # Streamlit UI components
│   ├── streamlit_app.py             # Main application interface
│   ├── enhanced_stored_assessments.py  # School hierarchy view
│   └── analytics_visualizations.py  # Power BI-style dashboard
│
├── backend/                          # Backend utilities
│   └── rate_limiter.py              # API rate limiting
│
├── utils/                            # Helper functions
│   ├── safe_dataframe_access.py     # Safe data operations
│   ├── data_export_import.py        # Import/export utilities
│   └── performance.py               # Performance monitoring
│
├── assessments/                      # Stored assessment data (gitignored)
│   ├── student_assessments.csv      # Main data file
│   ├── backups/                     # Automatic versioned backups
│   └── audit_log.json               # Activity tracking
│
├── sessions/                         # Session recovery data (gitignored)
│
├── test_datasets/                    # Sample data for testing
│   ├── consolidation_test_*.csv     # Multi-session test data
│   ├── report_card_test_*.csv       # Report generation tests
│   └── README.md                    # Test data documentation
│
├── tests/                            # Unit and property-based tests
│   ├── test_enhanced_csv_processor.py
│   ├── test_data_consolidation_properties.py
│   ├── test_school_organization_properties.py
│   ├── test_timestamp_monotonicity.py
│   └── test_system_performance.py
│
├── docs/                             # Comprehensive documentation
│
├── config.py                         # System configuration
├── requirements.txt                  # Core dependencies
├── requirements_visualization.txt    # Visualization libraries
├── run_app.bat                       # Windows launcher script
├── dev_server.py                     # Development server
└── README.md                         # This file
```

## 🔧 Configuration

### Model Selection (`config.py`)

The system supports multiple Gemini models with different capabilities:

- **gemini-2.5-flash** (Default) - Best for production, officially recommended
  - Free tier: 2 RPM, 20 RPD, 250K TPM
  - Paid tier: 1000 RPM, 10K RPD, 4M TPM

- **gemini-2.5-pro** - Advanced reasoning and complex analysis
  - Free tier: 5 RPM, 25 RPD, 250K TPM
  - Thinking capabilities for complex tasks

- **gemini-2.0-flash** - 1M context window, stable performance
  - Free tier: 15 RPM, 1500 RPD, 250K TPM

### Key Settings

```python
# Batch processing
BATCH_SIZE = 3              # Students per batch
BATCH_DELAY = 20            # Seconds between batches

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 2
MAX_REQUESTS_PER_DAY = 20
RETRY_ON_RATE_LIMIT = True

# Assessment configuration
MAX_RETRIEVAL_RESULTS = 10
ASSESSMENT_TIMEOUT = 120
```

## 📊 Usage Workflows

### 1. Batch Assessment (Recommended for Multiple Students)

```
1. Prepare CSV with columns: Name, School, Class, Session, Observations
2. Navigate to "Batch Assessment" tab
3. Upload CSV file
4. Review validation report (duplicates, blank rows, data quality)
5. Process assessments in batches
6. Review and approve results
7. Store to database
```

**CSV Format:**
```csv
Name,School,Class,Session,Observations
Aarav Kumar,Sunrise School,Class 8,2024-01-15,Shows leadership in group activities...
Diya Sharma,Sunrise School,Class 8,2024-01-15,Very creative in art class...
```

### 2. Individual Assessment

```
1. Go to "Individual Assessment" tab
2. Enter student details (name, school, class)
3. Add observation notes
4. Click "Assess Personality"
5. Review 20 personality traits with levels (LOW/MIDDLE/HIGH)
6. Store results
```

### 3. Report Card Generation

```
1. Navigate to "Report Card & SWOT Analysis" tab
2. Upload Excel template (report_card_template.xlsx)
3. Upload student data CSV
4. Select language (Marathi/English)
5. Generate reports
6. Download ZIP file with all report cards
```

### 4. View Stored Assessments

```
1. Go to "Enhanced Stored Assessments" tab
2. View system overview (schools, classes, students, observations)
3. Browse school hierarchy (School → Class → Student)
4. Search and filter by various criteria
5. View growth trends and analytics
6. Export data for external analysis
```

### 5. Growth Tracking

```
1. Navigate to "Growth Trends" tab
2. Select school and student
3. View timeline of observations
4. Compare assessments over time
5. Analyze trait development with radar charts
6. Generate growth reports
```

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Property-Based Tests
```bash
pytest tests/test_data_consolidation_properties.py -v
pytest tests/test_school_organization_properties.py -v
```

### Local Model Testing (No API Quota)

1. **Install Ollama**
   ```bash
   # Download from https://ollama.ai
   ollama pull llama3.2:3b
   ```

2. **Enable Developer Mode**
   - Open application
   - Toggle "Developer Mode" in sidebar
   - Select local model from dropdown

3. **Test Features**
   - All assessment features work with local models
   - No API quota consumption
   - Slower but free for testing

📖 **Full Guide**: [docs/DEVELOPER_MODE_GUIDE.md](docs/DEVELOPER_MODE_GUIDE.md)

## 💾 Data Management

### Storage Location
- **Main Data**: `assessments/student_assessments.csv`
- **Backups**: `assessments/backups/` (automatic versioning)
- **Audit Log**: `assessments/audit_log.json`
- **Sessions**: `sessions/` (auto-save recovery)

### Backup Strategy
- Automatic backups before major operations
- Versioned with timestamps
- Old backups cleaned up automatically (keeps last 10)
- Manual backup: Copy entire `assessments/` folder

### Data Privacy
- All data stored locally on your laptop
- No cloud storage or external transmission
- `.gitignore` prevents accidental commits
- API key stored in `.env` (never committed)

## 🔒 Security Best Practices

✅ **Do:**
- Keep `.env` file secure with API key
- Regularly backup `assessments/` folder to USB drive
- Use strong passwords for any shared access
- Review audit logs periodically

❌ **Don't:**
- Commit `.env` file to git
- Share API keys publicly
- Store sensitive data in test files
- Disable workflow protection without reason

## 🐛 Troubleshooting

### Common Issues

**App won't start**
```bash
# Check Python installation
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**API Rate Limit Errors**
- Reduce `BATCH_SIZE` in config.py
- Increase `BATCH_DELAY` between batches
- Switch to local models for testing

**Data not showing**
- Click "🔄 Refresh All Data" button
- Check `assessments/student_assessments.csv` exists
- Verify CSV format is correct

**Visualization errors**
```bash
# Install visualization dependencies
pip install -r requirements_visualization.txt
```

📖 **Full Troubleshooting**: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)

## 🤝 Contributing

This system is designed for NGO use. For modifications:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature-name`
3. **Make changes** with tests
4. **Run test suite**: `pytest tests/`
5. **Update documentation**
6. **Submit pull request**

### Code Standards
- Follow existing code patterns
- Add docstrings to all functions
- Include type hints where possible
- Write property-based tests for data operations
- Update README for new features

## 📈 Version History

### v2.0 (Current) - Major Enhancement Release
- ✅ Enhanced CSV processing with validation and duplicate detection
- ✅ Data consolidation system for multi-session observations
- ✅ School hierarchy organization and navigation
- ✅ Growth tracking and analytics dashboard
- ✅ Power BI-style visualizations
- ✅ Developer mode with local model support
- ✅ Session recovery and auto-save
- ✅ Workflow protection and user guidance
- ✅ Comprehensive test suite with property-based testing
- ✅ Audit logging and automatic backups
- ✅ Cleaned UI (removed unnecessary metrics)
- ✅ Fixed system metadata accuracy

### v1.3 - Developer Features
- Added local model support (Ollama integration)
- Developer mode for testing without API quota
- Enhanced error handling and retry logic

### v1.2 - Performance & Caching
- Performance optimizations
- Caching system for faster responses
- Rate limiting improvements

### v1.1 - Marathi Support
- Marathi report card generation
- Bilingual UI support
- Excel template integration

### v1.0 - Initial Release
- Core assessment features
- Batch processing
- Individual assessments
- Basic data storage

## 📞 Support

### For NGO Users
1. Check [QUICK_START.md](QUICK_START.md)
2. Review [docs/START_HERE_NGO_GUIDE.md](docs/START_HERE_NGO_GUIDE.md)
3. Try test datasets in `test_datasets/`

### For Developers
1. Read [docs/DEVELOPER_MODE_GUIDE.md](docs/DEVELOPER_MODE_GUIDE.md)
2. Check [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
3. Review test files in `tests/`

### Issues & Questions
- GitHub Issues: [Report bugs or request features](https://github.com/Ranveersingh1113/personality_assessment_app/issues)
- Documentation: Check `docs/` folder for detailed guides

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

Built for educational NGOs working with rural students in India. Special thanks to all contributors and testers who helped improve this system.

---

**Ready to start?** See [QUICK_START.md](QUICK_START.md) for 5-minute setup guide!
