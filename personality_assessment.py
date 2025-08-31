import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
import PyPDF2
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from langchain.schema.runnable import RunnablePassthrough
from csv_reference_processor import CSVReferenceProcessor

# Load environment variables
load_dotenv()

class AssessmentItem(BaseModel):
    quality: str = Field(description="Name of the personality quality")
    level: str = Field(description="Assessment level: LOW, MIDDLE, HIGH, or NOT OBSERVED")
    reasoning: str = Field(description="Brief explanation for the assessment")

class AssessmentResult(BaseModel):
    assessments: List[AssessmentItem] = Field(description="List of personality assessments")
    summary: str = Field(description="Overall assessment summary")

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
            model_name = "gemini-1.5-pro"
            temperature = 0.1
        
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY")
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
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def create_reference_sheet_data(self) -> str:
        """Create reference sheet data from CSV reference processor"""
        return self.csv_reference_processor.format_reference_data_for_vector_db()
    
    def setup_vector_database(self):
        """Set up the vector database with PDF content and reference sheet"""
        print("Setting up vector database...")
        
        # Extract PDF content
        pdf_content = self.extract_pdf_content("map-t.pdf")
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
    
    def assess_student_personality(self, observations: str) -> Dict[str, Any]:
        """Assess a student's personality based on observations"""
        if not self.vector_store:
            raise ValueError("Vector database not initialized. Call setup_vector_database() first.")
        
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
        
        try:
            # Get assessment
            result = chain.invoke(observations)
            
            # Convert Pydantic model to dict
            return result.model_dump()
                
        except Exception as e:
            # Fallback to string parsing if structured output fails
            try:
                fallback_result = self._fallback_assessment(observations, retriever)
                return fallback_result
            except Exception as fallback_error:
                return {
                    "error": f"Assessment failed: {str(e)}. Fallback also failed: {str(fallback_error)}",
                    "observations": observations
                }
    
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
