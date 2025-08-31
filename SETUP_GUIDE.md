# 🚀 Setup Guide for Personality Assessment System

## 🔧 Technology Stack

- **LLM**: Google Gemini 1.5 Pro
- **Embeddings**: Hugging Face All-MiniLM-L6-v2
- **Vector Database**: ChromaDB
- **Reference Data**: CSV-based observation data
- **Frontend**: Streamlit

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Google API Key** for Gemini
3. **CSV Reference Data** (included: "Obseervations check list for feeding.1.xlsx - observation check list 1.csv")
4. **map-t.pdf** file with quality definitions

## 🎯 Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

### 3. Configure Environment

Create a `.env` file in the project directory:

```env
# Required: Google API Key for Gemini
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Google Sheets Service Account (for live data)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

### 4. Test the System

Run the test scripts to verify everything works:

```bash
# Test basic system components
python test_system.py

# Test CSV reference data processing
python test_csv_reference.py

# Test core functionality
python demo.py
```

### 5. Run the Application

```bash
# Option 1: Use startup script
python run_app.py

# Option 2: Direct Streamlit command
streamlit run streamlit_app.py

# Option 3: Windows batch file
run_app.bat
```

## 📊 CSV Reference Data

The system uses the actual observation data provided by the NGO in CSV format:

### Reference Data Structure

The CSV file contains:
- **20 Personality Qualities**: All the qualities to be assessed
- **3 Levels**: Low, Middle, High for each quality
- **Multiple Observations**: Real examples for each level
- **Rich Context**: Actual behavioral observations from field work

### Data Processing

The system automatically:
- Loads the CSV reference data
- Processes observations for each quality and level
- Formats data for vector database ingestion
- Provides fallback data if CSV is unavailable

### Updating Reference Data

To update the reference data:
1. Modify the CSV file with new observations
2. Restart the system to reload the data
3. The system will automatically use the updated observations

## 🧪 Testing Your Setup

### 1. Basic System Test

```bash
python test_system.py
```

Expected output:
```
✅ All tests passed! System is ready to use.
```

### 2. CSV Reference Data Test

```bash
python test_csv_reference.py
```

Expected output:
```
✅ Successfully loaded 20 qualities
✅ Reference data exported successfully
```

### 3. Demo Assessment

```bash
python demo.py
```

Expected output:
```
✅ Assessment completed!
📊 Assessment results displayed
```

## 🚨 Troubleshooting

### Common Issues

1. **"Google API Key not found"**
   - Check your `.env` file
   - Verify the key is correct
   - Ensure no extra spaces or quotes

2. **"Authentication failed"**
   - Check your Google API key validity
   - Verify you have sufficient quota
   - Check internet connection

3. **"CSV file not found"**
   - Ensure the CSV file is in the project directory
   - Check file permissions
   - Verify CSV format is correct

4. **"Module import errors"**
   - Reinstall dependencies: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)
   - Verify all packages installed correctly

### Performance Issues

1. **Slow embeddings**
   - First run downloads the model (~80MB)
   - Subsequent runs will be faster
   - Consider using GPU if available

2. **Slow assessments**
   - Check API quota limits
   - Reduce batch size in config.py
   - Monitor API usage in Google Cloud Console

## 📊 System Verification

After setup, verify these components work:

- ✅ **Gemini API**: Can generate responses
- ✅ **Hugging Face Embeddings**: Can create vector embeddings
- ✅ **ChromaDB**: Can store and retrieve vectors
- ✅ **CSV Reference Data**: Can load and process observation data
- ✅ **Streamlit**: Can run web interface
- ✅ **PDF Processing**: Can extract text from map-t.pdf

## 🔄 Updating Reference Data

The NGO can update the CSV reference data anytime:

1. **Manual Updates**: Edit the CSV file with new observations
2. **Automatic Loading**: System loads updated data on startup
3. **Fallback Mode**: If CSV is unavailable, uses built-in data

## 📞 Support

If you encounter issues:

1. **Check logs**: Look for error messages in console output
2. **Verify API keys**: Ensure Google API key is valid and has quota
3. **Test components**: Run individual test scripts
4. **Check CSV file**: Verify the reference data file is present and readable

## 🎉 Success!

Once all tests pass, your system is ready to assess student personalities!

- **Individual Assessment**: Process one student at a time
- **Batch Assessment**: Process multiple students from CSV
- **Real Reference Data**: Uses actual NGO observation examples
- **Export Results**: Download assessments in JSON format

---

**Built with ❤️ for rural education development**
