
import os
import sys
import json
from dotenv import load_dotenv

# Ensure we can import from ai_core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_core.personality_assessment import PersonalityAssessmentSystem

def verify_swot_backend():
    print("Initializing System...")
    try:
        system = PersonalityAssessmentSystem()
        system.setup_vector_database()
        print("System Initialized.")
    except Exception as e:
        import traceback
        with open("verification_log.txt", "w", encoding="utf-8") as f:
            f.write(f"FAILED to initialize system: {e}\n")
            traceback.print_exc(file=f)
        print(f"FAILED to initialize system: {e}")
        return

    # Test Individual Generation
    print("\nTesting Individual SWOT Generation...")
    observations = "Student is very energetic and participates in all sports. However, they struggle to sit still during math class and often interrupt others. They are very friendly and popular among peers."
    try:
        result = system.generate_swot_analysis(observations)
        print("Analysis Result:")
        print(json.dumps(result, indent=2))
        
        if 'swot_items' in result and 'summary' in result:
             print("✅ Individual SWOT Structure Verified.")
        else:
             print("❌ Invalid SWOT Structure.")
    except Exception as e:
        print(f"❌ Individual SWOT Failed: {e}")

    # Test Batch Generation
    print("\nTesting Batch SWOT Generation...")
    batch_data = [
        {"name": "Student A", "observations": "Quiet, diligent, good at art."},
        {"name": "Student B", "observations": "Loud, leader, poor listener."}
    ]
    try:
        batch_results = system.batch_generate_swot(batch_data)
        print("Batch Results:")
        print(json.dumps(batch_results, indent=2))
        
        if len(batch_results) == 2 and 'swot_analysis' in batch_results[0]:
             print("✅ Batch SWOT Verified.")
        else:
             print("❌ Batch Verification Failed.")
    except Exception as e:
        print(f"❌ Batch SWOT Failed: {e}")

if __name__ == "__main__":
    verify_swot_backend()
