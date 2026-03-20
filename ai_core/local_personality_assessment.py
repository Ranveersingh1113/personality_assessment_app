"""
Local Model Personality Assessment System

Uses local models (Ollama) for testing without consuming API quota.
"""

import requests
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LocalPersonalityAssessment:
    """
    Personality assessment using local models via Ollama.
    
    Compatible interface with the main PersonalityAssessment class.
    """
    
    def __init__(self, model_name: str = "llama3.2:3b", base_url: str = "http://localhost:11434"):
        """
        Initialize local personality assessment.
        
        Args:
            model_name: Ollama model name (e.g., "llama3.2:3b")
            base_url: Ollama API base URL
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/generate"
        
        # Load reference sheet
        self.reference_sheet = self._load_reference_sheet()
        
    def _load_reference_sheet(self) -> str:
        """Load the personality assessment reference sheet"""
        return """
PERSONALITY ASSESSMENT REFERENCE SHEET

Rate each quality as HIGH, MIDDLE, LOW, or NOT OBSERVED based on observations.

1. ADAPTABILITY
   - HIGH: Easily adjusts to new situations, accepts changes well
   - MIDDLE: Shows some flexibility, needs time to adjust
   - LOW: Struggles with changes, prefers routine
   - NOT OBSERVED: No evidence of adaptability situations

2. ACADEMIC ACHIEVEMENT
   - HIGH: Excellent grades, strong learning skills, inclination to climb
   - MIDDLE: Average performance, steady progress
   - LOW: Below average, struggles with learning
   - NOT OBSERVED: No academic performance information

3. BOLDNESS
   - HIGH: Socially bold, adventurous, presents with confidence
   - MIDDLE: Hesitates at first but explains well when encouraged
   - LOW: Shy, withdrawn, avoids speaking up
   - NOT OBSERVED: No evidence of boldness/shyness

4. COMPETITION
   - HIGH: Compares progress with others, asks about others' work
   - MIDDLE: Shows some competitive spirit occasionally
   - LOW: Avoids competition, doesn't compare with others
   - NOT OBSERVED: No competitive behavior observed

5. CREATIVITY
   - HIGH: Asks unique questions, comes up with new ideas
   - MIDDLE: Shows occasional creative thinking
   - LOW: Follows conventional approaches, rarely innovative
   - NOT OBSERVED: No creative activities observed

6. ENTHUSIASM
   - HIGH: Very enthusiastic, taking leadership, answering confidently
   - MIDDLE: Answers in class but needs encouragement
   - LOW: Attentive but not participating, casual approach
   - NOT OBSERVED: No evidence of enthusiasm level

7. EXCITABILITY
   - HIGH: Responds quickly without thinking, impatient, hyperactive
   - MIDDLE: Shows controlled excitement, thinks before acting
   - LOW: Calm, measured responses, rarely excited
   - NOT OBSERVED: No situations showing excitability

8. GENERAL ABILITY
   - HIGH: High intelligence, ability to retain and apply knowledge
   - MIDDLE: Average cognitive abilities, learns at normal pace
   - LOW: Struggles to understand instructions, needs extra help
   - NOT OBSERVED: No evidence of general cognitive ability

9. GUILT PRONENESS
   - HIGH: Shows shame when reprimanded, puts head down
   - MIDDLE: Shows some concern when corrected
   - LOW: Doesn't seem affected by criticism
   - NOT OBSERVED: No situations involving correction/criticism

10. INDIVIDUALISM
    - HIGH: Prefers to work alone, seclusive behavior
    - MIDDLE: Works well both alone and in groups
    - LOW: Prefers group work, seeks collaboration
    - NOT OBSERVED: No evidence of work preferences

11. INNOVATION
    - HIGH: Introduces new methods, creative problem-solving
    - MIDDLE: Shows some innovative thinking
    - LOW: Sticks to traditional methods
    - NOT OBSERVED: No innovative situations observed

12. LEADERSHIP
    - HIGH: Takes leadership, controls and directs group actions
    - MIDDLE: Shows leadership in some situations
    - LOW: Follows others, rarely takes initiative
    - NOT OBSERVED: No leadership opportunities observed

13. MATURITY
    - HIGH: Shows seriousness, responsible behavior
    - MIDDLE: Age-appropriate maturity level
    - LOW: Immature behavior, lacks seriousness
    - NOT OBSERVED: No evidence of maturity level

14. MENTAL HEALTH
    - HIGH: Resilient, focused, good emotional state
    - MIDDLE: Generally stable with occasional concerns
    - LOW: Shows signs of distress, difficulty focusing
    - NOT OBSERVED: No mental health indicators observed

15. MORALITY
    - HIGH: Strong ethical behavior, honest, accepts mistakes
    - MIDDLE: Generally moral with occasional lapses
    - LOW: Shows concerning ethical behavior
    - NOT OBSERVED: No moral situations observed

16. SELF CONTROL
    - HIGH: Excellent impulse control, follows rules consistently
    - MIDDLE: Generally controlled with occasional lapses
    - LOW: Poor impulse control, difficulty following rules
    - NOT OBSERVED: No self-control situations observed

17. SENSITIVITY
    - HIGH: Easily hurt, attention-seeking behavior
    - MIDDLE: Normal emotional sensitivity
    - LOW: Insensitive to others, thick-skinned
    - NOT OBSERVED: No sensitivity situations observed

18. SELF SUFFICIENCY
    - HIGH: Independent, doesn't need group support
    - MIDDLE: Balanced independence and collaboration
    - LOW: Dependent on others, needs constant support
    - NOT OBSERVED: No independence situations observed

19. SOCIAL WARMTH
    - HIGH: Friendly, cooperative, helps others understand
    - MIDDLE: Generally sociable and warm
    - LOW: Cold, unfriendly, doesn't help others
    - NOT OBSERVED: No social interaction observed

20. TENSION
    - HIGH: Shows signs of stress, anxiety, distress
    - MIDDLE: Normal stress levels, manages well
    - LOW: Relaxed, calm, no signs of tension
    - NOT OBSERVED: No tension indicators observed
"""
    
    def check_availability(self) -> bool:
        """Check if local model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(m['name'] == self.model_name for m in models)
            return False
        except:
            return False
    
    def assess_student_personality(self, observations: str) -> Dict[str, Any]:
        """
        Assess student personality using local model.
        
        Args:
            observations: Student observations text
            
        Returns:
            Assessment result dictionary
        """
        if not self.check_availability():
            raise Exception(f"Local model {self.model_name} not available. Run: ollama pull {self.model_name}")
        
        prompt = f"""You are an educational psychologist assessing student personality traits.

REFERENCE SHEET:
{self.reference_sheet}

STUDENT OBSERVATIONS:
{observations}

TASK: Based on the observations above, assess the student for each of the 20 personality qualities.

INSTRUCTIONS:
1. For each quality, determine: HIGH, MIDDLE, LOW, or NOT OBSERVED
2. Provide clear reasoning based on the observations
3. Only rate what you can observe - use NOT OBSERVED when there's insufficient evidence

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

Adaptability: [LEVEL]
  ([Your reasoning based on observations])
Academic achievement: [LEVEL]
  ([Your reasoning based on observations])
Boldness: [LEVEL]
  ([Your reasoning based on observations])
Competition: [LEVEL]
  ([Your reasoning based on observations])
Creativity: [LEVEL]
  ([Your reasoning based on observations])
Enthusiasm: [LEVEL]
  ([Your reasoning based on observations])
Excitability: [LEVEL]
  ([Your reasoning based on observations])
General ability: [LEVEL]
  ([Your reasoning based on observations])
Guilt proneness: [LEVEL]
  ([Your reasoning based on observations])
Individualism: [LEVEL]
  ([Your reasoning based on observations])
Innovation: [LEVEL]
  ([Your reasoning based on observations])
Leadership: [LEVEL]
  ([Your reasoning based on observations])
Maturity: [LEVEL]
  ([Your reasoning based on observations])
Mental health: [LEVEL]
  ([Your reasoning based on observations])
Morality: [LEVEL]
  ([Your reasoning based on observations])
Self control: [LEVEL]
  ([Your reasoning based on observations])
Sensitivity: [LEVEL]
  ([Your reasoning based on observations])
Self sufficiency: [LEVEL]
  ([Your reasoning based on observations])
Social warmth: [LEVEL]
  ([Your reasoning based on observations])
Tension: [LEVEL]
  ([Your reasoning based on observations])

Be thorough but concise. Base all assessments strictly on the provided observations."""

        try:
            # Call local model
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 3000
                }
            }
            
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=120  # Local models can be slow
            )
            
            if response.status_code != 200:
                raise Exception(f"Local model error: {response.status_code} - {response.text}")
            
            result = response.json()
            assessment_text = result.get('response', '')
            
            # Parse the assessment
            parsed_assessment = self._parse_assessment(assessment_text)
            
            return {
                'assessments': [parsed_assessment],
                'summary': f"Assessment completed using {self.model_name}",
                'model_used': self.model_name,
                'local_model': True,
                'raw_response': assessment_text
            }
            
        except Exception as e:
            logger.error(f"Local assessment failed: {e}")
            raise Exception(f"Local model assessment failed: {str(e)}")
    
    def _parse_assessment(self, assessment_text: str) -> Dict[str, Any]:
        """Parse assessment text into structured format"""
        qualities = {}
        
        # Define all 20 qualities
        quality_names = [
            'Adaptability', 'Academic achievement', 'Boldness', 'Competition', 'Creativity',
            'Enthusiasm', 'Excitability', 'General ability', 'Guilt proneness', 'Individualism',
            'Innovation', 'Leadership', 'Maturity', 'Mental health', 'Morality',
            'Self control', 'Sensitivity', 'Self sufficiency', 'Social warmth', 'Tension'
        ]
        
        # Parse each quality
        for quality in quality_names:
            pattern = rf"{re.escape(quality)}:\s*(HIGH|MIDDLE|LOW|NOT OBSERVED)\s*\n\s*\(([^)]+)\)"
            match = re.search(pattern, assessment_text, re.IGNORECASE | re.MULTILINE)
            
            if match:
                level = match.group(1).upper()
                reasoning = match.group(2).strip()
                
                qualities[quality.lower().replace(' ', '_')] = {
                    'quality': quality,
                    'level': level,
                    'reasoning': reasoning
                }
            else:
                # Fallback - mark as not observed if not found
                qualities[quality.lower().replace(' ', '_')] = {
                    'quality': quality,
                    'level': 'NOT OBSERVED',
                    'reasoning': 'Assessment not found in response'
                }
        
        return qualities


def get_available_local_models():
    """Get list of available local models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=1)  # Reduced timeout
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [
                {
                    'name': m['name'],
                    'size': m.get('size', 0),
                    'size_gb': round(m.get('size', 0) / (1024**3), 1),
                    'modified': m.get('modified_at', ''),
                    'recommended': m['name'] in ['llama3.2:1b', 'llama3.2:3b', 'llama3.1:8b']
                }
                for m in models
            ]
        return []
    except requests.exceptions.RequestException:
        # Network/connection error - Ollama not running or not accessible
        return []
    except Exception:
        # Any other error - return empty list
        return []


if __name__ == "__main__":
    # Test local model
    print("Testing local model availability...")
    
    models = get_available_local_models()
    if models:
        print(f"\n✓ Found {len(models)} local models:")
        for model in models:
            status = "⭐ RECOMMENDED" if model['recommended'] else ""
            print(f"  • {model['name']} ({model['size_gb']} GB) {status}")
        
        # Test assessment
        print(f"\nTesting assessment with {models[0]['name']}...")
        assessor = LocalPersonalityAssessment(models[0]['name'])
        
        test_observations = "Student shows excellent leadership during group work. Takes initiative and helps other students understand difficult concepts. Always participates actively in class discussions."
        
        try:
            result = assessor.assess_student_personality(test_observations)
            print("✓ Assessment successful!")
            print(f"Model: {result['model_used']}")
            print(f"Summary: {result['summary']}")
        except Exception as e:
            print(f"✗ Assessment failed: {e}")
    else:
        print("✗ No local models found. Install Ollama and pull a model:")
        print("  ollama pull llama3.2:3b")