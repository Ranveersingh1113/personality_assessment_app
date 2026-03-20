# Documentation Index

Welcome to the Student Personality Assessment System documentation.

## 📖 Getting Started

- **[START_HERE_NGO_GUIDE.md](START_HERE_NGO_GUIDE.md)** - Complete guide for NGO users
  - System setup and initialization
  - Basic workflows
  - Common tasks and troubleshooting

## 👨‍💻 Developer Documentation

- **[DEVELOPER_MODE_GUIDE.md](DEVELOPER_MODE_GUIDE.md)** - Testing without API quota
  - Local model setup
  - Developer mode features
  - Testing workflows

- **[LOCAL_MODEL_TESTING_GUIDE.md](LOCAL_MODEL_TESTING_GUIDE.md)** - Detailed local model guide
  - Ollama installation
  - Model selection
  - Performance comparison

- **[TESTING_WITH_LOCAL_MODELS.md](TESTING_WITH_LOCAL_MODELS.md)** - Testing procedures
  - Test scenarios
  - Expected results
  - Troubleshooting

## 🏗️ Architecture

- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Codebase organization
  - Directory structure
  - Module descriptions
  - Key components

## ✅ Quality Assurance

- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - Pre-deployment testing
  - Feature testing
  - Integration testing
  - Performance testing

## 📊 User Guides

- **[GROWTH_TRENDS_USER_GUIDE.md](GROWTH_TRENDS_USER_GUIDE.md)** - Growth tracking features
  - Viewing student progress
  - Analytics dashboard
  - Interpreting trends

## 🔍 Quick Reference

### Common Tasks

1. **Running the Application**
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

2. **Batch Assessment**
   - Upload CSV with: Name, School, Class, Observations
   - Review and approve results
   - Store for future reference

3. **Report Card Generation**
   - Upload Excel template
   - Upload student data CSV
   - Generate Marathi reports

4. **Testing Locally**
   - Enable Developer Mode
   - Select local model
   - Process without API quota

### File Locations

- **Configuration**: `config.py`
- **Assessment Data**: `assessments/`
- **Test Data**: `test_datasets/`
- **Templates**: `report_card_template.xlsx`, `reference_sheet_template.csv`

### Support

For issues or questions:
1. Check relevant documentation above
2. Review test datasets for examples
3. Consult testing checklist for troubleshooting
