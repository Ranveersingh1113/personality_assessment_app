import os
import json
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
import PyPDF2
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from langchain_core.runnables import RunnablePassthrough
from ai_core.csv_reference_processor import CSVReferenceProcessor
from backend.rate_limiter import get_rate_limiter, rate_limited_call

# Load environment variables
load_dotenv()

class AssessmentItem(BaseModel):
    quality: str = Field(description="Name of the personality quality")
    level: str = Field(description="Assessment level: LOW, MIDDLE, HIGH, or NOT OBSERVED")
    reasoning: str = Field(description="Brief explanation for the assessment")

class AssessmentResult(BaseModel):
    assessments: List[AssessmentItem] = Field(description="List of personality assessments")
    summary: str = Field(description="Overall assessment summary")

class SWOTItem(BaseModel):
    category: str = Field(description="Category: STRENGTH, WEAKNESS, OPPORTUNITY, or THREAT")
    point: str = Field(description="The specific point for this category")
    explanation: str = Field(description="Brief explanation based on observations")

class SWOTAnalysisResult(BaseModel):
    swot_items: List[SWOTItem] = Field(description="List of SWOT analysis points")
    summary: str = Field(description="Overall strategic summary")

class PersonalityAssessmentSystem:
    def __init__(self):
        """Initialize the Personality Assessment System"""
        try:
            from config import PERSONALITY_QUALITIES
            self.qualities = PERSONALITY_QUALITIES
        except ImportError:
            # Fallback to hardcoded qualities if config not available
            self.qualities = [
                "Adaptability", "Academic achievement", "Boldness", "Competition", 
                "Creativity", "Enthusiasm", "Excitability", "General ability",
                "Guilt proneness", "Individualism", "Innovation", "Leadership",
                "Maturity", "Mental health", "Morality", "Self control",
                "Sensitivity", "Self sufficiency", "Social warmth", "Tension"
            ]
        
        try:
            from config import GEMINI_MODEL, GEMINI_TEMPERATURE
            model_name = GEMINI_MODEL
            temperature = GEMINI_TEMPERATURE
        except ImportError:
            model_name = "gemini-flash-latest"
            temperature = 0.1
        
        # Initialize Gemini LLM - using only Flash models (fast and efficient)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or not api_key.strip():
            raise ValueError(
                "GOOGLE_API_KEY is not set or empty. "
                "Please ensure your .env file contains a valid API key."
            )
        # Fixed to use only Flash model family as requested
        # Using gemini-flash-latest which auto-selects the best available Flash model
        # (Gemini 2.0/2.5 Flash on this API key - newer and better than 1.5 Flash)
        self.model_name = "gemini-flash-latest"
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=temperature,
            google_api_key=api_key
        )
        
        # Initialize Hugging Face embeddings
        try:
            from config import EMBEDDING_MODEL
            embedding_model = EMBEDDING_MODEL
        except ImportError:
            embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.vector_store = None
        self.reference_data = {}
        self.csv_reference_processor = CSVReferenceProcessor()
        
    def extract_pdf_content(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        import logging
        logger = logging.getLogger(__name__)
        
        if not os.path.exists(pdf_path):
            logger.warning(f"PDF file not found: {pdf_path}")
            return ""
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if pdf_reader.is_encrypted:
                    logger.warning(f"PDF is encrypted and cannot be read: {pdf_path}")
                    return ""
                text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as page_err:
                        logger.warning(f"Error reading page {page_num}: {page_err}")
                        continue
                return text
        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            return ""
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            return ""
    
    def create_reference_sheet_data(self) -> str:
        """Create reference sheet data from CSV reference processor"""
        return self.csv_reference_processor.format_reference_data_for_vector_db()
    
    def setup_vector_database(self):
        """Set up the vector database with PDF content and reference sheet"""
        print("Setting up vector database...")
        
        # Extract PDF content (path relative to project root)
        pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map-t.pdf")
        if not os.path.exists(pdf_path):
            pdf_path = "map-t.pdf"
        pdf_content = self.extract_pdf_content(pdf_path)
        if not pdf_content:
            print("Warning: Could not extract PDF content")
            pdf_content = "PDF content unavailable"
        
        # Get reference sheet data from CSV
        reference_content = self.create_reference_sheet_data()
        
        # Combine all content
        combined_content = f"PDF DEFINITIONS:\n{pdf_content}\n\nREFERENCE SHEET:\n{reference_content}"
        
        # Split text into chunks
        try:
            from config import CHUNK_SIZE, CHUNK_OVERLAP
            chunk_size = CHUNK_SIZE
            chunk_overlap = CHUNK_OVERLAP
        except ImportError:
            chunk_size = 1000
            chunk_overlap = 200
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        documents = text_splitter.split_text(combined_content)
        doc_objects = [Document(page_content=text, metadata={"source": "personality_assessment"}) for text in documents]
        
        # Clean up existing vector store to prevent memory leaks
        if self.vector_store is not None:
            try:
                self.vector_store.delete_collection()
            except Exception:
                pass  # Ignore cleanup errors, proceed with new collection
        
        # Create vector store
        self.vector_store = Chroma.from_documents(
            documents=doc_objects,
            embedding=self.embeddings,
            collection_name="personality_assessment"
        )
        
        print(f"Vector database created with {len(documents)} chunks")
    
    def create_assessment_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for personality assessment"""
        template = """You are an expert personality assessor for rural students. Your task is to evaluate a student's personality traits based on observer notes.

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
5. You MUST respond with ONLY valid JSON - no additional text before or after
6. Use this EXACT JSON structure:
{{
    "assessments": [
        {{
            "quality": "Quality Name",
            "level": "LOW",
            "reasoning": "Brief explanation based on observations"
        }},
        {{
            "quality": "Quality Name", 
            "level": "MIDDLE",
            "reasoning": "Brief explanation based on observations"
        }},
        {{
            "quality": "Quality Name",
            "level": "HIGH", 
            "reasoning": "Brief explanation based on observations"
        }},
        {{
            "quality": "Quality Name",
            "level": "NOT OBSERVED",
            "reasoning": "No clear evidence observed"
        }}
    ],
    "summary": "Overall assessment summary"
}}

CRITICAL: Respond with ONLY the JSON object. Do not include any text before or after the JSON. Ensure all quotes are properly escaped and the JSON is valid."""

        return ChatPromptTemplate.from_template(template)
    
    def create_assessment_prompt_with_parser(self, parser) -> ChatPromptTemplate:
        """Create the prompt template with parser instructions"""
        template = """You are an expert personality assessor for rural students. Your task is to evaluate a student's personality traits based on observer notes.

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
5. Follow the exact format instructions below

{format_instructions}

Remember: Only assess qualities that are clearly demonstrated in the observations. If a quality is not shown, mark it as "NOT OBSERVED" rather than guessing."""

        return ChatPromptTemplate.from_template(template)
    
    @rate_limited_call
    def assess_student_personality(self, observations: str) -> Dict[str, Any]:
        """Assess a student's personality based on observations"""
        if not self.vector_store:
            raise ValueError("Vector database not initialized. Call setup_vector_database() first.")
        
        # Get rate limiter and retry settings
        try:
            from config import MAX_RETRIES, RETRY_DELAY, RETRY_ON_RATE_LIMIT
        except ImportError:
            MAX_RETRIES = 3
            RETRY_DELAY = 30
            RETRY_ON_RATE_LIMIT = True
        
        # Create structured output parser
        parser = PydanticOutputParser(pydantic_object=AssessmentResult)
        
        # Create the assessment prompt with parser instructions
        prompt = self.create_assessment_prompt_with_parser(parser)
        
        # Retrieve relevant context
        try:
            from config import MAX_RETRIEVAL_RESULTS
            k_value = MAX_RETRIEVAL_RESULTS
        except ImportError:
            k_value = 10
        
        retriever = self.vector_store.as_retriever(search_kwargs={"k": k_value})
        
        # Create the assessment chain with structured output
        chain = (
            {"context": retriever, "observations": RunnablePassthrough(), "qualities": lambda x: ", ".join(self.qualities), "format_instructions": lambda x: parser.get_format_instructions()}
            | prompt
            | self.llm
            | parser
        )
        
        # Retry logic for rate limits
        for attempt in range(MAX_RETRIES + 1):
            try:
                # Get assessment
                result = chain.invoke(observations)
                
                # Convert Pydantic model to dict
                return result.model_dump()
                    
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_str and ("quota" in error_str.lower() or "rate" in error_str.lower()) and RETRY_ON_RATE_LIMIT:
                    if attempt < MAX_RETRIES:
                        print(f"Rate limit hit (attempt {attempt + 1}/{MAX_RETRIES + 1}). Waiting {RETRY_DELAY} seconds...")
                        print(f"Error details: {error_str}")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        return {
                            "error": f"Rate limit exceeded after {MAX_RETRIES + 1} attempts. Error: {error_str}",
                            "observations": observations
                        }
                
                # Note: Model fallback removed - using only gemini-1.5-flash as requested
                # For other errors, try fallback
                try:
                    fallback_result = self._fallback_assessment(observations, retriever)
                    # Only accept fallback if it returns multiple assessments
                    if fallback_result and len(fallback_result.get("assessments", [])) >= 2:
                        return fallback_result
                except Exception:
                    pass
                # As last resort, return a clear error instead of silent heuristic
                return {
                    "error": f"Assessment failed after retries: {error_str}",
                    "observations": observations
                }
    
    @rate_limited_call
    def _fallback_assessment(self, observations: str, retriever) -> Dict[str, Any]:
        """Fallback assessment method using string parsing"""
        try:
            # Use the original prompt method
            prompt = self.create_assessment_prompt()
            
            # Create simple chain
            chain = (
                {"context": retriever, "observations": RunnablePassthrough(), "qualities": lambda x: ", ".join(self.qualities)}
                | prompt
                | self.llm
                | StrOutputParser()
            )
            
            # Get assessment
            result = chain.invoke(observations)
            result = result.strip()
            
            # Try to parse JSON
            try:
                parsed_result = json.loads(result)
                return parsed_result
            except json.JSONDecodeError as e:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    try:
                        json_content = json_match.group(0)
                        parsed_result = json.loads(json_content)
                        return parsed_result
                    except json.JSONDecodeError:
                        pass
                
                # If all parsing attempts fail, return detailed error
                return {
                    "raw_response": result,
                    "error": f"Could not parse JSON response: {str(e)}",
                    "response_length": len(result),
                    "response_preview": result[:200] + "..." if len(result) > 200 else result
                }
                
        except Exception as e:
            return {
                "error": f"Fallback assessment failed: {str(e)}",
                "observations": observations
            }
    
    def batch_assess_students(self, students_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Assess multiple students in batch"""
        results = []
        
        for i, student in enumerate(students_data):
            print(f"Assessing student {i+1}/{len(students_data)}: {student.get('name', f'Student {i+1}')}")
            
            observations = student.get('observations', '')
            if not observations:
                results.append({
                    "student_id": student.get('id', f'student_{i+1}'),
                    "name": student.get('name', f'Student {i+1}'),
                    "error": "No observations provided"
                })
                continue
            
            try:
                assessment = self.assess_student_personality(observations)
                results.append({
                    "student_id": student.get('id', f'student_{i+1}'),
                    "name": student.get('name', f'Student {i+1}'),
                    "assessment": assessment
                })
            except Exception as e:
                results.append({
                    "student_id": student.get('id', f'student_{i+1}'),
                    "name": student.get('name', f'Student {i+1}'),
                    "error": f"Assessment failed: {str(e)}"
                })
        
        return results

    @rate_limited_call
    def generate_swot_analysis(self, observations: str) -> Dict[str, Any]:
        """Generate a SWOT analysis based on observations"""
        if not self.vector_store:
            raise ValueError("Vector database not initialized. Call setup_vector_database() first.")
        
        # Get rate limiter and retry settings
        try:
            from config import MAX_RETRIES, RETRY_DELAY, RETRY_ON_RATE_LIMIT
        except ImportError:
            MAX_RETRIES = 3
            RETRY_DELAY = 30
            RETRY_ON_RATE_LIMIT = True
            
        parser = PydanticOutputParser(pydantic_object=SWOTAnalysisResult)
        
        template = """You are an expert educational counselor and personality analyst. Your task is to perform a SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis for a student based on observer notes.

CONTEXT INFORMATION:
{context}

STUDENT OBSERVATIONS:
{observations}

TASK: creating a SWOT analysis matrix.
- STRENGTHS: Internal positive attributes (e.g., leadership, creativity, resilience).
- WEAKNESSES: Internal areas for improvement (e.g., lack of focus, shyness, impulsivity).
- OPPORTUNITIES: External or future possibilities for growth based on their traits (e.g., "Could excel in team sports due to high energy", "Leadership roles would boost confidence").
- THREATS: Potential challenges or risks if current behaviors continue (e.g., "May struggle academically due to lack of focus", "Social isolation risk").

INSTRUCTIONS:
1. Base your analysis STRICTLY on the provided observations.
2. Be constructive and specific.
3. For "category", use exactly one of: "STRENGTH", "WEAKNESS", "OPPORTUNITY", "THREAT".
4. Follow the format instructions below:

{format_instructions}
"""
        prompt = ChatPromptTemplate.from_template(template)
        
        try:
            from config import MAX_RETRIEVAL_RESULTS
            k_value = MAX_RETRIEVAL_RESULTS
        except ImportError:
            k_value = 10
            
        retriever = self.vector_store.as_retriever(search_kwargs={"k": k_value})
        
        chain = (
            {"context": retriever, "observations": RunnablePassthrough(), "format_instructions": lambda x: parser.get_format_instructions()}
            | prompt
            | self.llm
            | parser
        )
        
        # Retry logic
        for attempt in range(MAX_RETRIES + 1):
            try:
                result = chain.invoke(observations)
                return result.model_dump()
            except Exception as e:
                error_str = str(e)
                if "429" in error_str and ("quota" in error_str.lower() or "rate" in error_str.lower()) and RETRY_ON_RATE_LIMIT:
                    if attempt < MAX_RETRIES:
                        print(f"Rate limit hit (attempt {attempt + 1}/{MAX_RETRIES + 1}). Waiting {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        return {
                            "error": f"Rate limit exceeded after {MAX_RETRIES + 1} attempts. Error: {error_str}",
                            "observations": observations
                        }
                return {
                    "error": f"SWOT Analysis failed: {error_str}",
                    "observations": observations
                }

    @rate_limited_call
    def generate_marathi_swot(self, observations: str) -> Dict[str, Any]:
        """Generate a SWOT analysis in Marathi based on observations"""
        if not self.vector_store:
            raise ValueError("Vector database not initialized. Call setup_vector_database() first.")
        
        try:
            from config import MAX_RETRIES, RETRY_DELAY, RETRY_ON_RATE_LIMIT
        except ImportError:
            MAX_RETRIES = 3
            RETRY_DELAY = 10
            RETRY_ON_RATE_LIMIT = True

        parser = PydanticOutputParser(pydantic_object=SWOTAnalysisResult)
        
        template = """You are an expert educational counselor. Perform a SWOT analysis for a student based on year-long observations.
        
IMPORTANT: 
- The output must be in **MARATHI** language (Devanagari script) ONLY.
- **NO ENGLISH WORDS**.
- **ABSTRACT TRAITS ONLY**: Do NOT describe what the student *did*. Do NOT include "because..." or specific examples.
- BAD: "Drawing skills (drew a good picture)"
- GOOD: "Excellent Drawing Skills" (उत्कृष्ट चित्रकला कौशल्ये)
- BAD: "Helped friend (shared tiffin)"
- GOOD: "Social Helpfulness" (सामाजिक मदत करण्याची वृत्ती)

CONTEXT:
{context}

OBSERVATIONS:
{observations}

TASK: Create a SWOT matrix in Marathi.
- STRENGTHS (क्षमता): Internal positive traits/skills only.
- WEAKNESSES (कमतरता): Internal areas for improvement only.
- OPPORTUNITIES (संधी): External/future possibilities (Short phrases).
- THREATS (भीती): Potential risks (Short phrases).

INSTRUCTIONS:
1. Identify the core trait or quality.
2. Output ONLY that trait in Marathi.
3. NO explanations, NO evidence, NO "Observation 1 says..."
4. Output strictly in valid JSON as per:
{{
    "summary": "Short Marathi summary...",
    "swot_items": [
        {{ "category": "STRENGTH", "point": "Marathi Trait Only", "explanation": "" }},
        ...
    ]
}}
5. The 'category' field in JSON must be one of: "STRENGTH", "WEAKNESS", "OPPORTUNITY", "THREAT".

{format_instructions}
"""
        prompt = ChatPromptTemplate.from_template(template)
        
        # Simplified retrieval for faster processing
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        chain = (
            {"context": retriever, "observations": RunnablePassthrough(), "format_instructions": lambda x: parser.get_format_instructions()}
            | prompt
            | self.llm
            | parser
        )

        for attempt in range(MAX_RETRIES + 1):
            try:
                result = chain.invoke(observations)
                return result.model_dump()
            except Exception as e:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                return {"error": str(e)}

    def batch_generate_swot(self, students_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Generate SWOT analysis for multiple students in batch"""
        results = []
        
        for i, student in enumerate(students_data):
            print(f"Generating SWOT for student {i+1}/{len(students_data)}: {student.get('name', f'Student {i+1}')}")
            
            observations = student.get('observations', '')
            if not observations:
                results.append({
                    "student_id": student.get('id', f'student_{i+1}'),
                    "name": student.get('name', f'Student {i+1}'),
                    "error": "No observations provided"
                })
                continue
            
            try:
                swot = self.generate_swot_analysis(observations)
                results.append({
                    "student_id": student.get('id', f'student_{i+1}'),
                    "name": student.get('name', f'Student {i+1}'),
                    "swot_analysis": swot
                })
            except Exception as e:
                results.append({
                    "student_id": student.get('id', f'student_{i+1}'),
                    "name": student.get('name', f'Student {i+1}'),
                    "error": f"SWOT generation failed: {str(e)}"
                })
        
        return results

    def _heuristic_assessment(self, observations: str) -> Dict[str, Any]:
        """Produce a simple heuristic assessment when LLM is unavailable."""
        text = (observations or "").lower()
        keywords = {
            "leadership": ["lead", "led", "organize", "captain"],
            "creativity": ["creative", "idea", "innov", "design"],
            "enthusiasm": ["enthusiastic", "eager", "excited", "active"],
            "academic achievement": ["score", "grade", "rank", "marks"],
            "self control": ["calm", "control", "discipline", "patient"],
            "social warmth": ["friendly", "help", "support", "team"],
            "boldness": ["confident", "bold", "speak up", "present"],
            "sensitivity": ["sensitive", "empathy", "kind", "caring"],
        }
        assessments = []
        for quality in self.qualities:
            q_lower = quality.lower()
            cues = keywords.get(q_lower, [])
            score = sum(1 for k in cues if k in text)
            if score >= 2:
                level = "HIGH"
            elif score == 1:
                level = "MIDDLE"
            else:
                level = "NOT OBSERVED"
            assessments.append({
                "quality": quality,
                "level": level,
                "reasoning": "Heuristic fallback based on keyword presence"
            })
        summary = "Heuristic fallback assessment generated due to LLM unavailability."
        # Filter to only observed qualities for downstream labeling utility
        observed = [a for a in assessments if a["level"] != "NOT OBSERVED"]
        return {
            "assessments": observed,
            "summary": summary
        }
    
    def save_assessments(self, assessments: List[Dict[str, Any]], filename: str = "personality_assessments.json"):
        """Save assessment results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(assessments, f, indent=2, ensure_ascii=False)
            print(f"Assessments saved to {filename}")
        except Exception as e:
            print(f"Error saving assessments: {e}")

def main():
    """Main function to demonstrate the system"""
    print("Personality Assessment System for Rural Students")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY not found in environment variables")
        print("Please create a .env file with your Google API key:")
        print("GOOGLE_API_KEY=your_api_key_here")
        return
    
    # Initialize system
    system = PersonalityAssessmentSystem()
    
    # Setup vector database
    system.setup_vector_database()
    
    # Example usage
    print("\nExample Assessment:")
    print("-" * 30)
    
    sample_observations = """
    Student was very quiet during the session, rarely participated in group activities. 
    When asked questions, they gave short answers and seemed nervous. 
    They did complete the individual worksheet but took longer than others. 
    Student showed good manners and followed instructions carefully.
    """
    
    print("Sample Observations:")
    print(sample_observations)
    
    print("\nAssessing personality...")
    result = system.assess_student_personality(sample_observations)
    
    print("\nAssessment Result:")
    print(json.dumps(result, indent=2))
    
    # Example batch processing
    print("\n" + "=" * 50)
    print("Batch Processing Example:")
    
    sample_students = [
        {
            "id": "student_001",
            "name": "Rahul Kumar",
            "observations": "Student actively participated in all activities, helped other students, showed leadership qualities, and was very enthusiastic about learning new concepts."
        },
        {
            "id": "student_002", 
            "name": "Priya Singh",
            "observations": "Student was quiet but attentive, completed tasks independently, showed good academic focus, and was polite to teachers and peers."
        }
    ]
    
    batch_results = system.batch_assess_students(sample_students)
    system.save_assessments(batch_results)
    
    print("\nBatch assessment completed and saved!")

if __name__ == "__main__":
    main()
