"""
Configuration file for the Personality Assessment System
Modify these settings to customize the system behavior
"""

# Gemini Configuration
# Use a supported Gemini model identifier (seen in your key's list)
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TEMPERATURE = 0.1  # Lower = more consistent, Higher = more creative

# Rate Limiting Configuration
ENABLE_RATE_LIMITING = True
RATE_LIMIT_DELAY = 1.0  # Reduced delay for paid tier
MAX_REQUESTS_PER_MINUTE = 60  # Higher limit for paid tier
MAX_REQUESTS_PER_DAY = 10000  # Updated for paid tier
RETRY_ON_RATE_LIMIT = True
MAX_RETRIES = 3
RETRY_DELAY = 15  # Reduced retry delay for paid tier

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
STREAMLIT_TITLE = "🎓 Personality Assessment System for Rural Students"

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

# Batch Processing Configuration
BATCH_SIZE = 10  # Process students in batches of this size
BATCH_DELAY = 1  # Delay between batches in seconds (to avoid rate limits)

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
