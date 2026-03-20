# Test Datasets for Data Consolidation System

This folder contains realistic test datasets to manually verify the data consolidation features. Each dataset uses the **5-column CSV format**: `Name, School, Class, Session, Observations`

## 📊 **CSV Format Specification**

**Required Columns (in order):**
1. **Name**: Student's full name
2. **School**: School name 
3. **Class**: Class/grade identifier
4. **Session**: Assessment session name
5. **Observations**: Detailed observation text

**Example:**
```csv
Name,School,Class,Session,Observations
John Smith,Sunrise Primary,5A,Mid_Year_Assessment_2024,"Shows excellent leadership skills..."
```

## 📁 Dataset Descriptions

### 1. **consolidation_test_january.csv** → **consolidation_test_january.csv**
- **Purpose**: Initial baseline assessments for 10 students
- **Session**: `Mid_Year_Assessment_2024`
- **Students**: 10 students from Sunrise Primary (5A and 5B)
- **Use Case**: Upload first to establish baseline data
- **Expected Result**: Should show 10 individual student profiles

### 2. **consolidation_test_march.csv** → **consolidation_test_march.csv**
- **Purpose**: Follow-up assessments showing student progress
- **Session**: `End_Year_Assessment_2024`
- **Students**: Same 10 students + 2 new students from Riverside School
- **Use Case**: Upload after January data to test consolidation
- **Expected Result**: 
  - Original 10 students should show 2 observations each (consolidated)
  - 2 new students should show 1 observation each
  - Timeline should show progression from Mid-Year to End-Year

### 3. **consolidation_test_may.csv** → **consolidation_test_may.csv**
- **Purpose**: Additional progress review assessments
- **Session**: `Annual_Progress_Review_2024`
- **Students**: Mix of original students + some new ones from Hillside Academy
- **Use Case**: Upload third to see long-term consolidation
- **Expected Result**:
  - Students with 3 observations should show clear progression
  - Quality scores should be higher for students with more observations
  - School-wise organization should show 3 different schools

### 4. **single_school_intensive.csv**
- **Purpose**: Intensive assessment of one school with detailed observations
- **Session**: `Intensive_Assessment_2024`
- **Students**: 15 students from Green Valley School (grades 3-4)
- **Use Case**: Test detailed observation processing and quality scoring
- **Expected Result**: High-quality consolidated profiles with detailed assessments

### 5. **multi_school_comparison.csv**
- **Purpose**: Compare students from different geographic/cultural contexts
- **Session**: `Multi_School_Assessment_2024`
- **Students**: 12 students from 5 different school types (urban, rural, mountain, coastal, tribal)
- **Use Case**: Test school-wise organization and cultural diversity handling
- **Expected Result**: Clear school-wise grouping with diverse backgrounds represented

### 6. **improvement_journey.csv**
- **Purpose**: Students at different stages of development
- **Session**: `Baseline_Assessment_2024`
- **Students**: 8 students from Hope Academy showing various improvement levels
- **Use Case**: Test system's ability to handle different performance levels
- **Expected Result**: Different quality scores reflecting student progress levels

### 7. **blank_rows_test.csv**
- **Purpose**: Test handling of blank rows and empty data
- **Session**: `Blank_Row_Test_2024`
- **Students**: 5 valid students with multiple blank rows interspersed
- **Use Case**: Verify that blank rows are properly ignored
- **Expected Result**: Should show exactly 5 students, ignoring all blank rows

### 8. **large_batch_mid_year.csv** ⭐ **NEW**
- **Purpose**: Simulate realistic NGO bi-annual upload (150-200 students)
- **Session**: `Mid_Year_Assessment_2024`
- **Students**: 20 students across 5 schools (scaled-down version)
- **Use Case**: Test large batch processing and school organization
- **Expected Result**: Efficient processing, clear school-wise organization

### 9. **large_batch_end_year.csv** ⭐ **NEW**
- **Purpose**: Follow-up to mid-year batch showing 6-month progression
- **Session**: `End_Year_Assessment_2024`
- **Students**: Same 20 students + 2 new students
- **Use Case**: Test bi-annual consolidation pattern
- **Expected Result**: 
  - 20 students show 6-month progression (2 observations each)
  - 2 new students show single observations
  - Clear before/after comparison across large cohort

## 🧪 **Manual Testing Instructions**

### **Step 1: Test Basic Consolidation**
1. Upload `consolidation_test_january.csv`
2. Go to "Stored Assessments" → "Student-based View (Consolidated)"
3. Verify: 10 students, organized by school (Sunrise Primary)
4. Check session organization: All under "Mid_Year_Assessment_2024"

### **Step 2: Test Multi-Observation Consolidation**
1. Upload `consolidation_test_march.csv`
2. Check consolidated view again
3. Verify: 
   - Original students now have 2 observations each
   - Timeline shows Mid_Year_Assessment_2024 and End_Year_Assessment_2024
   - New students (Alex, Sophie) appear with 1 observation
   - School organization shows both Sunrise Primary and Riverside School
   - Session-based filtering works

### **Step 3: Test Large Batch Processing (Bi-Annual Pattern)**
1. Upload `large_batch_mid_year.csv`
2. Check processing speed and organization
3. Verify:
   - 20 students processed efficiently
   - 5 schools properly organized
   - All students under "Mid_Year_Assessment_2024" session

### **Step 4: Test Bi-Annual Progression**
1. Upload `large_batch_end_year.csv`
2. Check consolidation results
3. Verify:
   - 20 original students now have 2 observations (6-month span)
   - 2 new students have 1 observation each
   - Quality scores higher for students with progression data
   - Timeline shows clear 6-month development
   - Session comparison works (Mid_Year vs End_Year)

### **Step 5: Test School-wise Organization**
1. Upload `multi_school_comparison.csv`
2. Check school-wise organization
3. Verify:
   - Students grouped by school type
   - Each school shows correct student count
   - Search functionality works across all schools
   - Session information preserved

### **Step 6: Test Blank Row Handling**
1. Upload `blank_rows_test.csv`
2. Check processing results
3. Verify:
   - Exactly 5 students processed
   - No blank entries in consolidated view
   - Student count accurate (addresses user feedback issue h)

## 🎯 **What to Look For**

### **Consolidation Features (Issue a)**
- [ ] Multiple observations for same student are combined
- [ ] Recent observations have higher influence in consolidated assessment
- [ ] Individual observations are preserved and viewable
- [ ] Consolidated assessment considers all historical data
- [ ] Session information is preserved in each observation

### **School-wise Organization (Issue b)**
- [ ] Students grouped by school in expandable sections
- [ ] School summaries show meaningful metrics (student count, observation count)
- [ ] Easy navigation between different schools
- [ ] Search works across all schools
- [ ] Session-based filtering available

### **Observation Tracking (Issue c)**
- [ ] Timeline shows all observation dates and sessions for each student
- [ ] Observation count displayed for each student
- [ ] Session names clearly visible
- [ ] Can see progression over time
- [ ] Session comparison functionality

### **Session Management**
- [ ] Session names preserved and displayed correctly
- [ ] Students can be filtered by session
- [ ] Session-based analytics available
- [ ] Clear session identification in timelines
- [ ] Proper handling of students across multiple sessions

### **Large Batch Processing**
- [ ] Efficient processing of 20+ students per upload
- [ ] Responsive UI during large batch processing
- [ ] Proper memory management
- [ ] Accurate consolidation across large datasets
- [ ] School organization scales well with more students

## 📊 **Expected Results Summary**

After uploading all test datasets, you should see:

- **Total Students**: ~60+ unique students
- **Schools Represented**: 10+ different schools
- **Sessions**: 8+ different assessment sessions
- **Students with Multiple Observations**: 30+ students
- **Maximum Observations per Student**: 3 observations
- **Time Span**: Mid-year to End-year (6+ months)
- **Quality Score Range**: 0.3 to 0.9+ depending on observation frequency and detail

## 🔧 **Session Naming Best Practices**

### **Recommended Format:**
`{Assessment_Type}_{Period}_{Year}`

### **Examples:**
- `Mid_Year_Assessment_2024`
- `End_Year_Assessment_2024`
- `Baseline_Assessment_Jan_2024`
- `Progress_Review_July_2024`
- `Annual_Evaluation_2024`

### **Benefits:**
- Chronological sorting
- Clear identification
- Consistent naming
- Easy filtering and comparison

## 🚀 **Testing the Bi-Annual Pattern**

The new large batch datasets specifically test the NGO's actual usage pattern:

1. **Upload 1** (`large_batch_mid_year.csv`): 20 students, mid-year assessment
2. **Upload 2** (`large_batch_end_year.csv`): Same 20 students + 2 new ones, end-year assessment
3. **Result**: Clear 6-month progression tracking for entire cohort

This simulates their real workflow of assessing 150-200 students twice per year.