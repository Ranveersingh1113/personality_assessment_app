# 🚦 Quota Management Guide

## Understanding the 429 Error

The error you encountered is a **rate limit exceeded** error from Google's Gemini API. This happens when you hit the free tier limits:

- **Requests per minute**: 15 requests
- **Requests per day**: 1000 requests  
- **Input tokens per minute**: Limited quota

## ✅ What We've Fixed

### 1. **Switched to Gemini 1.5 Flash**
- Faster and more efficient than Gemini 1.5 Pro
- Higher rate limits for free tier
- Lower token usage per request

### 2. **Added Rate Limiting**
- Automatic delays between API calls (2 seconds)
- Prevents hitting rate limits
- Real-time status monitoring in the sidebar

### 3. **Retry Logic**
- Automatically retries failed requests
- Waits 30 seconds between retries
- Clear error messages for quota issues

### 4. **Smart Batching**
- Processes multiple students efficiently
- Reduces overall API calls
- Better resource utilization

## 🎯 How to Use the System Now

### Individual Assessments
1. **Wait between assessments**: Give 1-2 minutes between each student
2. **Monitor the sidebar**: Check rate limiting status
3. **Use clear observations**: Better input = fewer API calls needed

### Batch Assessments
1. **Upload CSV files**: Process multiple students at once
2. **Let the system handle timing**: Automatic delays built-in
3. **Check results**: All assessments saved automatically

### Rate Limiting Status
The sidebar now shows:
- **Minute Requests**: Current/limit for this minute
- **Daily Requests**: Current/limit for today
- **Warnings**: When approaching limits

## 💡 Tips for Free Tier Users

### Immediate Actions
- ✅ **Wait 1-2 minutes** between assessments
- ✅ **Use batch processing** for multiple students
- ✅ **Monitor the sidebar** for rate limit status
- ✅ **Clear your browser cache** if issues persist

### Long-term Solutions
- 🔄 **Upgrade to paid plan**: Higher limits available
- 🔄 **Use during off-peak hours**: Lower API usage globally
- 🔄 **Optimize observations**: Clear, detailed notes reduce API calls

## 🚨 When You Still Hit Limits

### If you get a 429 error:
1. **Wait 30 seconds** - the system will retry automatically
2. **Check the sidebar** - see current usage
3. **Try again** - after the retry delay
4. **Consider batch mode** - for multiple students

### If retries fail:
1. **Wait 1-2 minutes** before trying again
2. **Check your API key** - ensure it's valid
3. **Upgrade your plan** - if you need higher limits

## 📊 Understanding Your Usage

### Free Tier Limits
- **Per Minute**: 15 requests
- **Per Day**: 1000 requests
- **Input Tokens**: Limited per minute

### Paid Tier Benefits
- **Per Minute**: 60+ requests
- **Per Day**: 10,000+ requests
- **Higher token limits**
- **Priority support**

## 🔧 Configuration Options

You can adjust rate limiting in `config.py`:

```python
# Rate Limiting Configuration
ENABLE_RATE_LIMITING = True
RATE_LIMIT_DELAY = 2.0  # Seconds between calls
MAX_REQUESTS_PER_MINUTE = 15  # Conservative limit
MAX_REQUESTS_PER_DAY = 1000  # Conservative limit
RETRY_ON_RATE_LIMIT = True
MAX_RETRIES = 3
RETRY_DELAY = 30  # Seconds to wait before retry
```

## 📞 Getting Help

### If issues persist:
1. **Check the console logs** for detailed error information
2. **Verify your API key** is valid and has quota
3. **Monitor usage** in Google AI Studio dashboard
4. **Consider upgrading** to a paid plan

### Support Resources:
- [Google AI Studio](https://aistudio.google.com/) - Check your usage
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Rate Limits Guide](https://ai.google.dev/gemini-api/docs/rate-limits)

---

**Remember**: The system now automatically manages rate limits, but it's still good practice to wait between assessments and monitor your usage!
