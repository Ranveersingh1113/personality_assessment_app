# Developer Mode Guide

## Overview

The system has two modes:

1. **User Mode** (Default) - Simple API key input for NGO users
2. **Developer Mode** - Access to local Llama models for testing

## For NGO Users (Default Mode)

The sidebar shows only:
- API Key input field
- Information about Gemini API
- Initialize button

Simple and clean interface!

## For Developers (Testing Mode)

### How to Enable Developer Mode

Set the `DEVELOPER_MODE` environment variable before running Streamlit:

**Windows (PowerShell):**
```powershell
$env:DEVELOPER_MODE="true"
streamlit run frontend/streamlit_app.py
```

**Windows (CMD):**
```cmd
set DEVELOPER_MODE=true
streamlit run frontend/streamlit_app.py
```

**Linux/Mac:**
```bash
export DEVELOPER_MODE=true
streamlit run frontend/streamlit_app.py
```

### What Developer Mode Enables

When enabled, you'll see an additional section in the sidebar:

```
🔧 Developer Mode
├── Model Selection
│   ├── Gemini API (for production testing)
│   └── Local Llama Model (for development)
└── Local Model Selector (if Ollama is running)
```

### Using Local Models for Testing

1. **Install Ollama** (if not already installed):
   ```bash
   # Visit https://ollama.ai to download
   ```

2. **Pull a model**:
   ```bash
   ollama pull llama3.2:3b
   ```

3. **Enable Developer Mode** and run Streamlit

4. **Select "Local Llama Model"** in the sidebar

5. **Choose your model** from the dropdown

6. **Click Initialize System**

### Benefits of Local Models for Testing

- ✅ **No API quota usage** - Test unlimited times
- ✅ **No cost** - Completely free
- ✅ **Fast iteration** - Test UI changes quickly
- ✅ **Privacy** - All data stays local
- ✅ **Offline** - No internet required

### Recommended Workflow

1. **Development/Testing**: Use local models with `DEVELOPER_MODE=true`
   - Test new features
   - Debug issues
   - Verify UI changes
   - Test with large batches

2. **Production Testing**: Use Gemini API
   - Final validation before deployment
   - Test with real API limits
   - Verify rate limiting behavior

3. **NGO Deployment**: Regular mode (no developer mode)
   - Clean, simple interface
   - Only API key input
   - No confusing options

## Example: Testing a New Feature

```powershell
# 1. Enable developer mode
$env:DEVELOPER_MODE="true"

# 2. Start Streamlit
streamlit run frontend/streamlit_app.py

# 3. In the sidebar:
#    - Select "Local Llama Model"
#    - Choose "llama3.2:3b"
#    - Click Initialize

# 4. Test your feature with unlimited quota!

# 5. When done, disable developer mode for clean UI:
$env:DEVELOPER_MODE="false"
streamlit run frontend/streamlit_app.py
```

## Switching Between Modes

You can switch modes anytime by:

1. Stop Streamlit (Ctrl+C)
2. Change the environment variable
3. Restart Streamlit

The system will automatically show/hide developer options based on the environment variable.

## Notes

- Developer mode is **completely hidden** from regular users
- No configuration files to change
- No code modifications needed
- Just set an environment variable!
- Perfect for maintaining a clean user experience while having powerful testing tools
