# 🎓 Personality Assessment System for Rural Students

A multi-agent RAG + LLM pipeline designed to assess personality traits of rural students based on observer notes. This system helps NGO workers efficiently classify students into 20 personality qualities with LOW, MIDDLE, or HIGH ratings.

## 🌟 Features

- **Multi-Agent RAG Pipeline**: Combines vector database search with LLM analysis
- **20 Personality Qualities**: Comprehensive assessment framework
- **Individual & Batch Assessment**: Process single students or multiple students at once
- **Streamlit Interface**: Clean, simple web interface
- **PDF Integration**: Uses map-t.pdf for quality definitions
- **Reference Sheet Support**: Uses actual NGO observation data from CSV
- **Export Capabilities**: Download results in JSON format

## 🎯 The 20 Personality Qualities

1. **Adaptability** - Ability to adjust to new situations
2. **Academic achievement** - Performance in academic tasks
3. **Boldness** - Confidence and courage in new situations
4. **Competition** - Drive to compete and win
5. **Creativity** - Imagination and innovative thinking
6. **Enthusiasm** - Energy and interest in activities
7. **Excitability** - Emotional responsiveness
8. **General ability** - Overall cognitive skills
9. **Guilt proneness** - Sense of responsibility and remorse
10. **Individualism** - Independent thinking and action
11. **Innovation** - Openness to new methods and approaches
12. **Leadership** - Ability to guide and influence others
13. **Maturity** - Emotional and behavioral maturity
14. **Mental health** - Emotional stability and stress management
15. **Morality** - Ethical judgment and integrity
16. **Self control** - Discipline and impulse control
17. **Sensitivity** - Emotional awareness and empathy
18. **Self sufficiency** - Independence and self-reliance
19. **Social warmth** - Friendliness and social interaction
20. **Tension** - Stress levels and anxiety

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google API key (for Gemini)
- map-t.pdf file (quality definitions)

### Installation

1. **Clone or download the project files**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Google API key:**
   - Create a `.env` file in the project directory
   - Add: `GOOGLE_API_KEY=your_api_key_here`
   - Or enter it directly in the Streamlit app

### Running the Application

#### Option 1: Using the startup script
```bash
python run_app.py
```

#### Option 2: Using the batch file (Windows)
Double-click `run_app.bat`

#### Option 3: Manual command
```bash
streamlit run streamlit_app.py
```

The application will open at `http://localhost:8501`

## 📱 Using the Application

### 1. System Setup
- Enter your OpenAI API key in the sidebar
- Click "Initialize System" to set up the vector database
- Wait for the system to load reference data

### 2. Individual Assessment
- Go to the "Individual Assessment" tab
- Enter student name and observer notes
- Click "Assess Personality" to get results
- View detailed breakdown by quality level

### 3. Batch Assessment
- Go to the "Batch Assessment" tab
- Upload a CSV file with columns: Name, Observations
- Or use manual entry for multiple students
- Process all students at once

### 4. Export Template
- Download the CSV template for reference sheet
- Fill in your observations for each quality level
- Import to Google Sheets for team collaboration

## 📊 Assessment Output

The system provides assessments in four categories:

- **HIGH** 🟢 - Student clearly demonstrates this quality
- **MIDDLE** 🟡 - Student shows moderate evidence
- **LOW** 🔴 - Student shows limited evidence  
- **NOT OBSERVED** ⚪ - Insufficient evidence (no hallucination)

## 📁 File Structure

```
service learning/
├── streamlit_app.py          # Main Streamlit application
├── personality_assessment.py # Core assessment engine
├── csv_reference_processor.py # CSV reference data processor
├── map-t.pdf                # Quality definitions (you provide)
├── Obseervations check list for feeding.1.xlsx - observation check list 1.csv # NGO reference data
├── requirements.txt          # Python dependencies
├── run_app.py               # Startup script
├── run_app.bat              # Windows startup script
├── README.md                # This file
└── assessments/             # Generated assessment files
```

## 🔧 Technical Details

### Architecture
- **Vector Database**: ChromaDB with Hugging Face embeddings (All-MiniLM-L6-v2)
- **LLM**: Google Gemini 1.5 Flash for personality analysis (optimized for rate limits)
- **RAG Pipeline**: Retrieves relevant context from PDF and CSV reference data
- **Rate Limiting**: Built-in rate limiting to prevent quota exceeded errors
- **Multi-Agent**: Specialized prompts for different assessment aspects

### Data Flow
1. Observer notes are input to the system
2. Vector database searches for relevant quality definitions
3. LLM analyzes observations against reference data
4. System outputs structured assessment with reasoning
5. Results are saved and can be exported

## 📈 Performance

- **Individual Assessment**: ~30-60 seconds per student
- **Batch Processing**: Processes multiple students sequentially
- **Vector Database**: Fast semantic search across reference materials
- **Memory Usage**: Efficient chunking and retrieval

## 🚦 Rate Limiting & Quota Management

The system includes built-in rate limiting to prevent quota exceeded errors:

### Rate Limits
- **Per Minute**: 15 requests (configurable)
- **Per Day**: 1000 requests (configurable)
- **Delay Between Calls**: 2 seconds (configurable)

### Features
- **Automatic Retry**: Retries failed requests with exponential backoff
- **Status Monitoring**: Real-time rate limit status in the sidebar
- **Smart Delays**: Automatically waits when approaching limits
- **Error Handling**: Clear error messages for quota issues

### Tips for Free Tier Users
- Wait 1-2 minutes between assessments
- Use batch processing for multiple students
- Monitor the rate limiting status in the sidebar
- Consider upgrading to a paid plan for higher limits

## 🛠️ Customization

### Adding New Qualities
Edit the `qualities` list in `personality_assessment.py`

### Modifying Assessment Criteria
Update the prompt templates in the assessment functions

### Changing LLM Model
Modify the model configuration in `PersonalityAssessmentSystem.__init__()`

## 🚨 Troubleshooting

### Common Issues

1. **"System not initialized"**
   - Check your Google API key
   - Ensure map-t.pdf is in the project directory
   - Try reinitializing the system

2. **"Assessment failed"**
   - Check API key validity
   - Verify internet connection
   - Review observer notes for clarity

3. **"Rate limit exceeded (429 error)"**
   - Wait 1-2 minutes between assessments
   - Check the rate limiting status in the sidebar
   - Consider upgrading to a paid API plan
   - Use batch processing for multiple students

4. **"Vector database error"**
   - Ensure all required files are present
   - Check file permissions
   - Try deleting and recreating the database

### Getting Help

- Check the console output for error messages
- Verify all dependencies are installed
- Ensure sufficient disk space for vector database

## 📞 Support

For technical support or questions about the system:
- Check the console logs for detailed error information
- Verify your Google API key and quota
- Ensure all required files are present and accessible

## 🔮 Future Enhancements

- **Real-time Collaboration**: Multiple observers working simultaneously
- **Advanced Analytics**: Trend analysis across student populations
- **Mobile App**: Native mobile interface for field observations
- **Integration**: Direct Google Sheets API integration
- **Custom Models**: Fine-tuned models for specific rural contexts

## 📄 License

This project is designed for educational and NGO use. Please ensure compliance with local data protection regulations when handling student information.

---

**Built with ❤️ for rural education development**
