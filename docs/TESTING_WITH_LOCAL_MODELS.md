# Testing with Local Models (Llama 3.2)

## Why Use Local Models for Testing?

- ✅ **No API quota usage** - Test unlimited without consuming Gemini quota
- ✅ **Faster iteration** - No network latency
- ✅ **Privacy** - Data stays on your machine
- ✅ **Free** - No costs
- ✅ **Perfect for UI testing** - Test workflows, confirmations, guidance features

## Quick Setup (5 minutes)

### Step 1: Install Ollama

**Windows**:
1. Download: https://ollama.com/download/windows
2. Run installer
3. Ollama starts automatically

**Mac**:
```bash
brew install ollama
```

**Linux**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Pull Llama 3.2 Model

Choose one based on your needs:

```bash
# Option A: Smallest/Fastest (1B) - Recommended for testing
ollama pull llama3.2:1b

# Option B: Balanced (3B) - Good quality + speed
ollama pull llama3.2:3b

# Option C: Best Quality (8B) - Slower but better
ollama pull llama3.1:8b
```

### Step 3: Verify Installation

```bash
# List installed models
ollama list

# Test the model
ollama run llama3.2:3b "Hello!"
```

You should see a response. Press Ctrl+D to exit.

### Step 4: Check Availability in App

```bash
python ai_core/local_model_adapter.py
```

Expected output:
```
✓ Ollama is running!

Available models:
  • llama3.2:3b

Recommended for testing:
  • llama3.2:1b
  • llama3.2:3b
  • llama3.1:8b
```

## Testing the New Features

### Test 1: Workflow Guidance

1. Start Streamlit app
2. Go to "Batch Assessment" tab
3. **Look for**: 💡 Help & Tips expander
4. **Verify**: Shows contextual help and tips
5. Upload a CSV file
6. **Look for**: "👉 What to do next" section
7. **Verify**: Shows numbered steps

### Test 2: Confirmation Dialogs

1. In Session Recovery UI (if available)
2. Click "🗑️ Start Fresh"
3. **Verify**: Shows "⚠️ Are you sure?" confirmation
4. **Verify**: Has "✅ Yes, Clear All" and "❌ Cancel" buttons
5. Click Cancel
6. **Verify**: Action cancelled

### Test 3: Critical Action Warning

1. Upload and process a small CSV (3-5 students)
2. Approve all assessments
3. Click "✅ Finalize & Download CSV"
4. **Verify**: Shows "🚨 Critical Action" warning
5. **Verify**: Shows impact description
6. **Verify**: Has confirmation buttons

### Test 4: Contextual Help in Review

1. After processing batch
2. In Review section
3. **Look for**: 💡 Help & Tips expander
4. **Verify**: Shows review guidance
5. **Verify**: Lists tips about Select All, editing, etc.

### Test 5: Next Steps Guidance

1. After CSV validation
2. Before "Start Batch Assessment" button
3. **Look for**: "👉 What to do next" section
4. **Verify**: Shows 3 numbered steps
5. **Verify**: Each step has description and action

## Using Local Model for Actual Testing

If you want to test with actual assessments (not just UI):

### Option 1: Quick Test Script

```python
from ai_core.local_model_adapter import LocalModelAdapter

# Initialize
model = LocalModelAdapter("llama3.2:3b")

# Check availability
if model.check_availability():
    print("✓ Model ready!")
    
    # Test generation
    response = model.generate_content("Describe a good student")
    print(response['text'])
else:
    print("✗ Model not available")
```

### Option 2: Integration (Future)

We can integrate local models into the main app by:
1. Adding model selection in sidebar
2. Detecting Ollama availability
3. Routing to local model when selected
4. Falling back to Gemini for production

**Note**: For now, focus on testing the UI features (guidance, confirmations, help) which don't require actual model calls.

## Performance Comparison

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| llama3.2:1b | ~2-3s | Good | UI testing, rapid iteration |
| llama3.2:3b | ~5-7s | Better | Balanced testing |
| llama3.1:8b | ~10-15s | Best | Quality validation |
| Gemini 2.5 Flash | ~1-2s | Excellent | Production use |

## What to Test

### Priority: UI Features (No Model Needed)

1. ✅ **Workflow Guidance**
   - Help expanders appear
   - Tips are relevant
   - Next steps are clear

2. ✅ **Confirmation Dialogs**
   - Start Fresh confirmation
   - Finalize confirmation
   - Cancel works correctly

3. ✅ **Critical Warnings**
   - Warnings appear for important actions
   - Impact is clearly described
   - Confirmation required

4. ✅ **Contextual Help**
   - Help available in each section
   - Content is relevant
   - Tips are helpful

5. ✅ **Visual Indicators**
   - Progress counters work
   - Status messages clear
   - Icons appropriate

### Secondary: With Local Model (Optional)

6. ⭕ **End-to-End Flow**
   - Upload CSV
   - Process with local model
   - Review results
   - Finalize and store

7. ⭕ **Session Recovery**
   - Start processing
   - Close browser
   - Reopen and verify recovery

## Troubleshooting

### Ollama Not Found

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve
```

### Model Not Downloaded

```bash
# List models
ollama list

# If empty, pull a model
ollama pull llama3.2:3b
```

### Slow Performance

- Use smaller model (llama3.2:1b)
- Close other applications
- Check CPU/RAM usage
- Consider using GPU if available

### Connection Refused

- Verify Ollama is running: `ollama list`
- Check port 11434 is not blocked
- Try restarting Ollama

## Summary

For testing the new Priority 1 features:
1. ✅ **Install Ollama** (5 minutes)
2. ✅ **Pull llama3.2:3b** (2 minutes)
3. ✅ **Test UI features** (no model calls needed)
4. ⭕ **Optional**: Test with local model for full flow

**Focus on UI testing first** - the workflow guidance, confirmations, and help features work without any model calls!

## Next Steps

After testing UI features:
1. Verify all guidance appears correctly
2. Test all confirmation dialogs
3. Check contextual help is useful
4. Provide feedback on improvements
5. Then move to Priority 2 tasks or integrate local model fully
