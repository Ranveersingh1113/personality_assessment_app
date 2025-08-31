#!/usr/bin/env python3
"""
Test script to verify JSON parsing improvements
"""

import os
import json
from personality_assessment import PersonalityAssessmentSystem

def test_json_parsing():
    """Test the improved JSON parsing functionality"""
    print("🧪 Testing JSON Parsing Improvements")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("Please set your Google API key and try again")
        return False
    
    try:
        # Initialize system
        print("🔧 Initializing system...")
        system = PersonalityAssessmentSystem()
        system.setup_vector_database()
        
        # Test with sample observations
        test_observations = """
        Student was very quiet during the session, rarely participated in group activities. 
        When asked questions, they gave short answers and seemed nervous. 
        They did complete the individual worksheet but took longer than others. 
        Student showed good manners and followed instructions carefully.
        """
        
        print("📝 Testing assessment with sample observations...")
        result = system.assess_student_personality(test_observations)
        
        # Check if result is properly formatted
        if isinstance(result, dict):
            if 'assessments' in result:
                print("✅ Assessment completed successfully!")
                print(f"📊 Found {len(result['assessments'])} assessments")
                
                # Show a few examples
                for i, assessment in enumerate(result['assessments'][:3]):
                    print(f"  {i+1}. {assessment['quality']}: {assessment['level']}")
                
                if result.get('summary'):
                    print(f"📝 Summary: {result['summary'][:100]}...")
                
                return True
            elif 'error' in result:
                print(f"❌ Assessment failed: {result['error']}")
                if 'raw_response' in result:
                    print(f"📄 Raw response preview: {result['raw_response'][:200]}...")
                return False
            else:
                print("⚠️ Unexpected result format")
                print(f"Result keys: {list(result.keys())}")
                return False
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_json_parsing()
    if success:
        print("\n🎉 JSON parsing test passed!")
    else:
        print("\n❌ JSON parsing test failed!")
