# Quick Start Guide

Get the Student Personality Assessment System running in 5 minutes!

## 🎯 For NGO Users

### Step 1: Install Python (One-time)
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ Check "Add Python to PATH"
4. Click "Install Now"

### Step 2: Get Your API Key (One-time)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key

### Step 3: Configure API Key (One-time)
1. Open `.env` file in the application folder
2. Replace `your-api-key-here` with your API key
3. Save the file

### Step 4: Run the Application
1. **Double-click `run_app.bat`**
2. Wait 2-3 minutes (first time only)
3. Browser opens automatically at http://localhost:8501

### Step 5: Initialize System
1. Click "🚀 Initialize System" in sidebar
2. Wait for "✅ System initialized successfully!"
3. Start using the system!

---

## 📊 Basic Usage

### Assess One Student
1. Go to "Individual Assessment" tab
2. Enter student name and observations
3. Click "Assess Personality"
4. Review and store results

### Assess Multiple Students
1. Prepare CSV: `Name`, `School`, `Class`, `Observations`
2. Go to "Batch Assessment" tab
3. Upload CSV file
4. Process and store results

### View Results
1. Go to "Stored Assessments" tab
2. Browse by school/class
3. Search for students
4. View growth trends

---

## 💾 Important Notes

✅ **Your data is stored locally** on your laptop
- Location: `assessments/student_assessments.csv`
- Automatic backups in `assessments/backups/`

✅ **Backup weekly** to USB drive
- Copy entire `assessments/` folder
- Label with date

✅ **Works offline** except for:
- Initial setup (needs internet)
- Processing assessments (needs API)

---

## ⚠️ Quick Troubleshooting

**App won't start?**
- Check Python is installed: `python --version`
- Run `run_app.bat` again

**API errors?**
- Check internet connection
- Verify API key in `.env` file

**Data not showing?**
- Click "🔄 Refresh All Data" button

---

## 📚 Need More Help?

- Full guide: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- User guide: [docs/START_HERE_NGO_GUIDE.md](docs/START_HERE_NGO_GUIDE.md)
- All docs: [docs/README.md](docs/README.md)

---

**Ready to start? Double-click `run_app.bat`!**
