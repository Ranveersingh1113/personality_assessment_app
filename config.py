"""
Configuration file for the Personality Assessment System
Modify these settings to customize the system behavior
"""

# Gemini Model Configuration
# Available models with their rate limits and capabilities
AVAILABLE_MODELS = {
    "gemini-2.5-flash": {
        "name": "Gemini 2.5 Flash",
        "description": "FREE for both input and output in free tier - best price-performance model",
        "free_tier": {
            "requests_per_minute": 2,
            "requests_per_day": 20,
            "tokens_per_minute": 250000,
            "pricing": "Free of charge",
            "note": "Actual limit may vary by account - some accounts show 20 RPD instead of 250 RPD"
        },
        "paid_tier": {
            "requests_per_minute": 1000,
            "requests_per_day": 10000,
            "tokens_per_minute": 4000000,
            "pricing": "$0.30 input, $2.50 output per 1M tokens"
        },
        "recommended_for": "Production use, batch processing, agentic applications (officially recommended)"
    },
    "gemini-2.5-pro": {
        "name": "Gemini 2.5 Pro",
        "description": "FREE advanced thinking model for complex reasoning tasks",
        "free_tier": {
            "requests_per_minute": 5,
            "requests_per_day": 25,
            "tokens_per_minute": 250000,
            "pricing": "Free of charge"
        },
        "paid_tier": {
            "requests_per_minute": 150,
            "requests_per_day": 1000,
            "tokens_per_minute": 1000000,
            "pricing": "$1.25-$2.50 input, $10.00-$15.00 output per 1M tokens"
        },
        "recommended_for": "Complex analysis, advanced reasoning tasks, thinking capabilities"
    },
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "description": "FREE second generation model with 1M context window",
        "free_tier": {
            "requests_per_minute": 15,
            "requests_per_day": 1500,
            "tokens_per_minute": 250000,
            "pricing": "Free of charge"
        },
        "paid_tier": {
            "requests_per_minute": 2000,
            "requests_per_day": "Unlimited*",
            "tokens_per_minute": 10000000,
            "pricing": "$0.10 input, $0.40 output per 1M tokens"
        },
        "recommended_for": "General use, stable performance, 1M context window"
    },
    "gemini-flash-latest": {
        "name": "Gemini Flash (Latest)",
        "description": "Auto-selects best available Flash model (Gemini 3 Flash)",
        "free_tier": {
            "requests_per_minute": 10,
            "requests_per_day": 100,
            "tokens_per_minute": 250000,
            "pricing": "Free of charge"
        },
        "paid_tier": {
            "requests_per_minute": 300,
            "requests_per_day": 1500,
            "tokens_per_minute": 1000000,
            "pricing": "Variable based on latest model"
        },
        "recommended_for": "Automatic optimization, always latest features"
    }
}

# Default model selection
DEFAULT_MODEL = "gemini-2.5-flash"  # Officially recommended for production use
GEMINI_TEMPERATURE = 0.1  # Lower = more consistent, Higher = more creative

# Rate Limiting Configuration - Dynamic based on selected model
def get_rate_limits(model_key, is_paid_tier=False):
    """Get rate limiting configuration for a specific model and tier"""
    model_info = AVAILABLE_MODELS.get(model_key, AVAILABLE_MODELS[DEFAULT_MODEL])
    tier = "paid_tier" if is_paid_tier else "free_tier"
    
    return {
        "requests_per_minute": model_info[tier]["requests_per_minute"],
        "requests_per_day": model_info[tier]["requests_per_day"],
        "tokens_per_minute": model_info[tier]["tokens_per_minute"]
    }

# Default rate limiting (can be overridden by UI selection)
ENABLE_RATE_LIMITING = True
RATE_LIMIT_DELAY = 30.0  # 30 seconds delay for 2 RPM (20 RPD / 2 RPM = safe spacing)
MAX_REQUESTS_PER_MINUTE = 2  # Conservative for Gemini 2.5 Flash actual limit
MAX_REQUESTS_PER_DAY = 20  # Actual observed limit for Gemini 2.5 Flash free tier
RETRY_ON_RATE_LIMIT = True
MAX_RETRIES = 3
RETRY_DELAY = 10

# Hugging Face Embeddings Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Fast and effective embeddings
EMBEDDING_DIMENSION = 384  # Dimension of the embeddings

# Vector Database Configuration
CHUNK_SIZE = 1000  # Size of text chunks for vector database
CHUNK_OVERLAP = 200  # Overlap between chunks for better context

# Assessment Configuration
MAX_RETRIEVAL_RESULTS = 10  # Number of context chunks to retrieve
ASSESSMENT_TIMEOUT = 120  # Maximum time for assessment in seconds

# Personality Qualities (20 qualities as specified)
PERSONALITY_QUALITIES = [
    "Adaptability",
    "Academic achievement", 
    "Boldness",
    "Competition",
    "Creativity",
    "Enthusiasm",
    "Excitability",
    "General ability",
    "Guilt proneness",
    "Individualism",
    "Innovation",
    "Leadership",
    "Maturity",
    "Mental health",
    "Morality",
    "Self control",
    "Sensitivity",
    "Self sufficiency",
    "Social warmth",
    "Tension"
]

# Assessment Levels
ASSESSMENT_LEVELS = ["LOW", "MIDDLE", "HIGH", "NOT OBSERVED"]

# File Paths
PDF_PATH = "map-t.pdf"
ASSESSMENTS_DIR = "assessments"
REFERENCE_TEMPLATE_PATH = "reference_sheet_template.csv"

# Google Sheets Configuration
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1B6A11n2tpFBioUZ57h-0NQ3hdSNF0eHu/edit?usp=sharing&ouid=114696827167797531442&rtpof=true&sd=true"
GOOGLE_SHEETS_ID = "1B6A11n2tpFBioUZ57h-0NQ3hdSNF0eHu"
GOOGLE_SHEETS_RANGE = "Sheet1!A:D"  # Adjust based on actual sheet structure

# Streamlit Configuration
STREAMLIT_PORT = 8501
STREAMLIT_HOST = "localhost"
STREAMLIT_TITLE = "🎓 Personality Assessment System for Students"

# Assessment Prompt Templates
ASSESSMENT_PROMPT_TEMPLATE = """You are an expert personality assessor for rural students. Your task is to evaluate a student's personality traits based on observer notes.

CONTEXT INFORMATION:
{context}

STUDENT OBSERVATIONS:
{observations}

TASK: Analyze the student's behavior and assess their personality traits. For each of the 20 qualities, determine if the student shows evidence of that trait and rate them as LOW, MIDDLE, or HIGH. If there's insufficient evidence for a quality, mark it as "NOT OBSERVED".

QUALITIES TO ASSESS:
{qualities}

INSTRUCTIONS:
1. Only assess qualities where you have clear evidence from the observations
2. Use the reference sheet and PDF definitions to understand each quality
3. Be conservative - don't hallucinate traits without evidence
4. Provide brief reasoning for each assessment
5. Format output as JSON with structure:
{{
    "assessments": [
        {{
            "quality": "Quality Name",
            "level": "LOW/MIDDLE/HIGH/NOT OBSERVED",
            "reasoning": "Brief explanation based on observations"
        }}
    ],
    "summary": "Overall assessment summary"
}}

Remember: Only assess qualities that are clearly demonstrated in the observations. If a quality is not shown, mark it as "NOT OBSERVED" rather than guessing."""

# Batch Processing Configuration - Updated for actual Gemini 2.5 Flash limits
BATCH_SIZE = 3  # Smaller batches to respect 10 RPM limit
BATCH_DELAY = 20  # 20 seconds between batches to stay well within limits

# Export Configuration
EXPORT_FORMATS = ["json", "csv", "excel"]
DEFAULT_EXPORT_FORMAT = "json"

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "personality_assessment.log"

# Performance Configuration
ENABLE_CACHING = True
CACHE_TTL = 3600  # Cache results for 1 hour
MAX_CONCURRENT_ASSESSMENTS = 3  # Limit concurrent API calls
