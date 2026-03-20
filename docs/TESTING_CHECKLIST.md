# Testing Checklist - Priority 1 Features

## Quick Start

1. Open Streamlit app: http://localhost:8501
2. Follow checklist below
3. Mark items as you test them

## ✅ Task 8: Workflow Protection

### Contextual Help

- [ ] **Batch Upload Tab**
  - [ ] See "💡 Help & Tips" expander at top
  - [ ] Click to expand - shows help text
  - [ ] Shows 3 tips about CSV format
  - [ ] Help is relevant and clear

- [ ] **After CSV Validation**
  - [ ] See "👉 What to do next" section
  - [ ] Shows 3 numbered steps
  - [ ] Each step has title, description, action
  - [ ] Steps are in logical order

- [ ] **Review Section**
  - [ ] See "💡 Help & Tips" expander
  - [ ] Shows review guidance
  - [ ] Lists tips about Select All, editing
  - [ ] Help is actionable

### Confirmation Dialogs

- [ ] **Start Fresh Button**
  - [ ] Click "🗑️ Start Fresh" in recovery UI
  - [ ] See "⚠️ Are you sure?" warning
  - [ ] Shows what will be cleared
  - [ ] Has "✅ Yes, Clear All" button
  - [ ] Has "❌ Cancel" button
  - [ ] Cancel works - nothing cleared
  - [ ] Confirm works - session cleared

- [ ] **Finalize Button**
  - [ ] Process a small batch (or use existing data)
  - [ ] Approve all rows
  - [ ] Click "✅ Finalize & Download CSV"
  - [ ] See "🚨 Critical Action" warning
  - [ ] Shows impact (X assessments will be stored)
  - [ ] Has "✅ Yes, Finalize" button
  - [ ] Has "❌ Review More" button
  - [ ] Cancel works - returns to review
  - [ ] Confirm works - finalizes and downloads

### Visual Cues

- [ ] **Icons Used Appropriately**
  - [ ] 💡 for help/tips
  - [ ] 👉 for next steps
  - [ ] ⚠️ for warnings
  - [ ] 🚨 for critical actions
  - [ ] ✅ for confirmations
  - [ ] ❌ for cancellations

- [ ] **Color Coding**
  - [ ] Info messages are blue
  - [ ] Warnings are yellow/orange
  - [ ] Errors are red
  - [ ] Success messages are green

## ✅ Task 9: Approval Reminders

### Session Recovery

- [ ] **Recovery UI Appears**
  - [ ] Start batch processing (if possible)
  - [ ] Close browser mid-process
  - [ ] Reopen app
  - [ ] See "🔄 Session Recovery Available" banner
  - [ ] Shows pending tasks count
  - [ ] Shows incomplete batches count
  - [ ] Lists specific pending items

- [ ] **Recovery Actions**
  - [ ] "✅ Resume Work" button present
  - [ ] "🗑️ Start Fresh" button present
  - [ ] Resume works (if data available)
  - [ ] Start Fresh shows confirmation

### Approval Progress

- [ ] **Progress Counter**
  - [ ] In review section
  - [ ] Shows "📋 X/Y rows approved"
  - [ ] Updates when checking boxes
  - [ ] Updates when using Select All

- [ ] **Status Messages**
  - [ ] Before all approved: "Review and approve all rows..."
  - [ ] After all approved: "✅ All X rows approved..."
  - [ ] Finalize button disabled until all approved
  - [ ] Finalize button enabled when all approved

### Visual Indicators

- [ ] **Approval Status**
  - [ ] Checkboxes for each row
  - [ ] Select All button works
  - [ ] Deselect All button works
  - [ ] Counter updates correctly

## ✅ Task 4: Property Tests

### Run Tests

```bash
# Run all property tests
python -m pytest tests/test_school_organization_properties.py -v

# Run specific test
python -m pytest tests/test_school_organization_properties.py::TestCountAccuracy -v
```

- [ ] **Count Accuracy Tests**
  - [ ] test_student_count_accuracy passes
  - [ ] test_school_count_accuracy passes
  - [ ] test_observation_count_per_student passes

- [ ] **Search Consistency Tests**
  - [ ] test_school_filter_consistency passes
  - [ ] test_search_completeness passes
  - [ ] test_no_data_loss_in_filtering passes

## 🎯 Overall Experience

### Usability

- [ ] **Guidance is Clear**
  - [ ] Help text is easy to understand
  - [ ] Next steps are actionable
  - [ ] Tips are relevant

- [ ] **Confirmations Prevent Accidents**
  - [ ] Can't accidentally clear data
  - [ ] Can't accidentally finalize without review
  - [ ] Cancel options always available

- [ ] **Visual Design**
  - [ ] Icons make sense
  - [ ] Colors are appropriate
  - [ ] Layout is clean
  - [ ] Text is readable

### Workflow

- [ ] **Logical Flow**
  - [ ] Steps follow natural order
  - [ ] Guidance appears at right time
  - [ ] Confirmations don't interrupt unnecessarily
  - [ ] Can complete tasks efficiently

- [ ] **Error Prevention**
  - [ ] Warnings appear before problems
  - [ ] Confirmations for destructive actions
  - [ ] Clear feedback on actions
  - [ ] Easy to undo/cancel

## 📝 Notes & Feedback

### What Works Well:
```
(Add notes here)
```

### What Could Be Improved:
```
(Add notes here)
```

### Bugs Found:
```
(Add notes here)
```

### Suggestions:
```
(Add notes here)
```

## ✅ Sign-Off

- [ ] All critical features tested
- [ ] No blocking bugs found
- [ ] Ready for Priority 2 tasks
- [ ] OR: Issues documented for fixing

**Tested By**: _______________
**Date**: _______________
**Status**: ⭕ Pass / ⭕ Fail / ⭕ Needs Work
