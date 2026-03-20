# Student Personality Assessment System

A comprehensive AI-powered system for assessing student personality traits and generating detailed reports for educational institutions.

## � Features

- **Batch Assessment**: Process multiple students simultaneously with CSV upload
- **Individual Assessment**: Detailed one-on-one personality evaluation
- **SWOT Analysis**: Generate strengths, weaknesses, opportunities, and threats analysis
- **Report Cards**: Automated Marathi report card generation
- **Growth Tracking**: Monitor student development over time
- **Data Management**: Store, search, and analyze assessment data
- **Multi-language Support**: English and Marathi interfaces

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key (for production use)
- Ollama (optional, for local testing)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd personality_assessment_app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API key:
   - Copy `.env.example` to `.env`
   - Add your Gemini API key: `GOOGLE_API_KEY=your-key-here`

4. Run the application:
```bash
streamlit run frontend/streamlit_app.py
```

Or use the batch file (Windows):
```bash
run_app.bat
```

## 📚 Documentation

- [Getting Started Guide](docs/START_HERE_NGO_GUIDE.md) - Complete setup and usage guide
- [Developer Mode Guide](docs/DEVELOPER_MODE_GUIDE.md) - Testing with local models
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Codebase organization
- [Testing Guide](docs/TESTING_CHECKLIST.md) - Quality assurance procedures

## 🏗️ Project Structure

```
personality_assessment_app/
├── ai_core/              # Core AI and assessment logic
├── frontend/             # Streamlit UI components
├── backend/              # Backend utilities
├── utils/                # Helper functions
├── assessments/          # Stored assessment data
├── test_datasets/        # Sample data for testing
├── tests/                # Unit and integration tests
├── docs/                 # Documentation
├── config.py             # Configuration settings
└── requirements.txt      # Python dependencies
```

## 🔧 Configuration

Key settings in `config.py`:
- `BATCH_SIZE`: Number of students processed per batch (default: 3)
- `BATCH_DELAY`: Delay between batches in seconds (default: 20)
- API rate limits and retry settings

## 📊 Usage

### Batch Assessment
1. Navigate to "Batch Assessment" tab
2. Upload CSV file with columns: `Name`, `School`, `Class`, `Observations`
3. Review and approve assessments
4. Store results for future reference

### Report Card Generation
1. Go to "Report Card & SWOT Analysis" tab
2. Upload Excel template and student data CSV
3. Generate Marathi report cards in bulk
4. Download ZIP file with all reports

### Stored Assessments
1. View all stored student data
2. Search and filter by school, class, or student
3. Track growth trends over time
4. Export data for analysis

## 🧪 Testing

Run tests with:
```bash
pytest tests/
```

For local model testing (no API quota usage):
1. Install Ollama
2. Pull a model: `ollama pull llama3.2:3b`
3. Enable Developer Mode in the app
4. Select local model from dropdown

## 🤝 Contributing

This system is designed for NGO use. For modifications or improvements, please ensure:
- All tests pass
- Documentation is updated
- Code follows existing patterns
- Security best practices are maintained

## � License

[Add your license information here]

## 🆘 Support

For issues or questions:
1. Check the documentation in the `docs/` folder
2. Review test datasets for examples
3. Consult the testing checklist for troubleshooting

## � Security Notes

- Never commit `.env` file with real API keys
- Keep assessment data confidential
- Use secure connections for deployment
- Regularly backup assessment data

## 📈 Version History

- v1.0 - Initial release with core assessment features
- v1.1 - Added Marathi support and report card generation
- v1.2 - Performance optimizations and caching
- v1.3 - Developer mode and local model support
