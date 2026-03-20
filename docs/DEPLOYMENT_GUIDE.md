# Deployment Guide for NGO

Complete guide for deploying the Student Personality Assessment System on NGO laptops.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Windows 10 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Internet**: Required for initial setup and API calls

### Software Requirements
- **Python 3.8 or higher** - [Download from python.org](https://www.python.org/downloads/)
- **Google Gemini API Key** - [Get from Google AI Studio](https://makersuite.google.com/app/apikey)

---

## 🚀 Installation Steps

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
4. Click "Install Now"
5. Verify installation:
   - Open Command Prompt
   - Type: `python --version`
   - Should show: `Python 3.x.x`

### Step 2: Get the Application Files

1. Copy the entire `personality_assessment_app` folder to your laptop
2. Recommended location: `C:\Users\YourName\personality_assessment_app`

### Step 3: Set Up API Key

1. Get your Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Open the `.env` file in the application folder
3. Replace `your-api-key-here` with your actual API key:
   ```
   GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```
4. Save the file

### Step 4: Run the Application

1. Navigate to the application folder
2. **Double-click `run_app.bat`**
3. Wait for the setup to complete (first time takes 2-3 minutes)
4. The app will open automatically in your browser at `http://localhost:8501`

---

## 🎯 First Time Setup

### Initialize the System

1. In the sidebar, enter your API key (if not in .env file)
2. Click "🚀 Initialize System"
3. Wait for "✅ System initialized successfully!"

### Test the System

1. Go to "Individual Assessment" tab
2. Enter a test student name and observations
3. Click "Assess Personality"
4. Verify results appear correctly

---

## 📁 Understanding Data Storage

### Where Your Data is Stored

```
personality_assessment_app/
├── assessments/                    # All student data
│   ├── student_assessments.csv    # Main database
│   ├── metadata.json               # System info
│   ├── audit_log.json             # Activity log
│   └── backups/                    # Automatic backups
│       ├── backup_20260319_120000.csv
│       └── backup_20260319_130000.csv
│
├── sessions/                       # Temporary session data
│   └── batch_20260319_120000.json # Recovery files
│
└── report_cards_batch_*/          # Generated reports
    ├── Student1_ReportCard.xlsx
    └── Student2_ReportCard.xlsx
```

### Data Persistence

✅ **Data PERSISTS between sessions:**
- All student assessments
- Observation history
- System metadata
- Backups

✅ **Data is STORED LOCALLY:**
- On your laptop hard drive
- Not in the cloud
- Works offline (except API calls)

---

## 💾 Backup Strategy

### Automatic Backups (Built-in)

The system automatically:
- Creates backup before any data change
- Keeps last 10 backups
- Stores in `assessments/backups/`

### Manual Backups (Recommended)

**Weekly Backup:**
1. Copy entire `assessments/` folder
2. Paste to USB drive
3. Label with date: `assessments_backup_2026-03-19`

**Monthly Backup:**
1. Copy entire `personality_assessment_app` folder
2. Upload to Google Drive or OneDrive
3. Keep for at least 1 year

### Restore from Backup

If data is lost:
1. Stop the application
2. Copy backup files to `assessments/` folder
3. Restart application
4. Data will be restored

---

## 🔧 Daily Usage

### Starting the Application

**Method 1: Batch File (Easiest)**
- Double-click `run_app.bat`
- Wait for browser to open

**Method 2: Command Line**
```bash
cd personality_assessment_app
.venv\Scripts\activate
streamlit run frontend/streamlit_app.py
```

### Stopping the Application

**Method 1: Close Window**
- Close the Command Prompt window

**Method 2: Keyboard**
- Press `Ctrl+C` in the Command Prompt
- Type `Y` and press Enter

### Accessing the Application

- **URL**: http://localhost:8501
- **Browser**: Chrome, Firefox, or Edge
- **Network**: Only accessible from this laptop

---

## 📊 Common Workflows

### Batch Assessment

1. Prepare CSV file with columns: `Name`, `School`, `Class`, `Observations`
2. Go to "Batch Assessment" tab
3. Upload CSV file
4. Review validation results
5. Click "Start Processing"
6. Review and approve results
7. Click "Finalize and Store"

### Individual Assessment

1. Go to "Individual Assessment" tab
2. Enter student name and observations
3. Click "Assess Personality"
4. Review results
5. Click "Store Assessment"

### View Stored Data

1. Go to "Stored Assessments" tab
2. Browse by school/class
3. Search for specific students
4. View growth trends

### Generate Report Cards

1. Go to "Report Card & SWOT Analysis" tab
2. Upload Excel template
3. Upload student data CSV
4. Click "Generate Report Cards"
5. Download ZIP file with all reports

---

## ⚠️ Troubleshooting

### Application Won't Start

**Problem**: "Python is not installed"
- **Solution**: Install Python from python.org, ensure "Add to PATH" is checked

**Problem**: "Failed to install dependencies"
- **Solution**: Check internet connection, try again

**Problem**: Browser doesn't open
- **Solution**: Manually open browser and go to http://localhost:8501

### API Issues

**Problem**: "API key not found"
- **Solution**: Check .env file has correct API key

**Problem**: "Rate limit exceeded"
- **Solution**: Wait 1 minute, reduce batch size, or upgrade API tier

**Problem**: "API call failed"
- **Solution**: Check internet connection, verify API key is valid

### Data Issues

**Problem**: "Data not showing"
- **Solution**: Click "🔄 Refresh All Data" button

**Problem**: "Duplicate student warning"
- **Solution**: Choose Replace, Append, or Cancel based on your needs

**Problem**: "Cannot save data"
- **Solution**: Close Excel if file is open, check file permissions

---

## 🔒 Security Best Practices

### API Key Security

✅ **DO:**
- Keep API key in .env file only
- Never share API key with others
- Regenerate key if compromised

❌ **DON'T:**
- Share .env file
- Post API key online
- Email API key

### Data Privacy

✅ **DO:**
- Keep laptop password protected
- Lock screen when away
- Regular backups to secure location

❌ **DON'T:**
- Share student data publicly
- Store backups on public cloud without encryption
- Leave application open unattended

---

## 📞 Support

### Getting Help

1. Check this guide first
2. Review error messages carefully
3. Check the docs/ folder for specific guides
4. Contact system administrator

### Reporting Issues

When reporting problems, include:
- Error message (screenshot)
- What you were trying to do
- Steps to reproduce the issue
- Your Python version (`python --version`)

---

## 🔄 Updates

### Updating the Application

1. Backup your `assessments/` folder
2. Download new version
3. Copy your `assessments/` folder to new version
4. Copy your `.env` file to new version
5. Run `run_app.bat`

### Checking for Updates

- Check with system administrator monthly
- Review release notes before updating
- Test new version with sample data first

---

## 📈 Performance Tips

### For Faster Processing

- Process batches of 20-30 students at a time
- Use batch assessment instead of individual for multiple students
- Close other applications while processing
- Ensure good internet connection for API calls

### For Better Results

- Write detailed observations (100+ words)
- Include specific examples of behavior
- Observe students over multiple sessions
- Use consistent observation format

---

## ✅ Pre-Deployment Checklist

Before deploying to NGO:

- [ ] Python 3.8+ installed
- [ ] Application files copied to laptop
- [ ] .env file configured with API key
- [ ] run_app.bat tested and working
- [ ] Sample assessment completed successfully
- [ ] Backup strategy explained to NGO staff
- [ ] User training completed
- [ ] This guide provided to NGO
- [ ] Emergency contact information shared

---

## 📚 Additional Resources

- [Getting Started Guide](START_HERE_NGO_GUIDE.md)
- [Testing Checklist](TESTING_CHECKLIST.md)
- [Growth Trends Guide](GROWTH_TRENDS_USER_GUIDE.md)
- [Developer Mode Guide](DEVELOPER_MODE_GUIDE.md)

---

**Last Updated**: March 2026
**Version**: 1.3
