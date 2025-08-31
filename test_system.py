#!/usr/bin/env python3
"""
Test script for the Personality Assessment System
This script tests individual components without requiring API calls
"""

import os
import sys

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        import streamlit
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import pandas
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        import langchain
        print("✅ LangChain imported successfully")
    except ImportError as e:
        print(f"❌ LangChain import failed: {e}")
        return False
    
    try:
        import chromadb
        print("✅ ChromaDB imported successfully")
    except ImportError as e:
        print(f"❌ ChromaDB import failed: {e}")
        return False
    
    try:
        import PyPDF2
        print("✅ PyPDF2 imported successfully")
    except ImportError as e:
        print(f"❌ PyPDF2 import failed: {e}")
        return False
    
    try:
        import google.generativeai
        print("✅ Google Generative AI imported successfully")
    except ImportError as e:
        print(f"❌ Google Generative AI import failed: {e}")
        return False
    
    try:
        import sentence_transformers
        print("✅ Sentence Transformers imported successfully")
    except ImportError as e:
        print(f"❌ Sentence Transformers import failed: {e}")
        return False
    
    return True

def test_local_modules():
    """Test if local modules can be imported"""
    print("\n🧪 Testing local module imports...")
    
    try:
        from personality_assessment import PersonalityAssessmentSystem
        print("✅ PersonalityAssessmentSystem imported successfully")
    except ImportError as e:
        print(f"❌ PersonalityAssessmentSystem import failed: {e}")
        return False
    
    try:
        from csv_reference_processor import CSVReferenceProcessor
        print("✅ CSVReferenceProcessor imported successfully")
    except ImportError as e:
        print(f"❌ CSVReferenceProcessor import failed: {e}")
        return False
    
    try:
        from config import PERSONALITY_QUALITIES
        print("✅ Config imported successfully")
        print(f"   Found {len(PERSONALITY_QUALITIES)} personality qualities")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    return True

def test_files():
    """Test if required files exist"""
    print("\n🧪 Testing required files...")
    
    required_files = [
        "streamlit_app.py",
        "personality_assessment.py", 
        "csv_reference_processor.py",
        "config.py",
        "map-t.pdf",
        "requirements.txt"
    ]
    
    all_files_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} not found")
            all_files_exist = False
    
    return all_files_exist

def test_config():
    """Test configuration values"""
    print("\n🧪 Testing configuration...")
    
    try:
        from config import PERSONALITY_QUALITIES, ASSESSMENT_LEVELS
        
        print(f"✅ Personality qualities: {len(PERSONALITY_QUALITIES)}")
        print(f"✅ Assessment levels: {ASSESSMENT_LEVELS}")
        
        # Check if all 20 qualities are present
        expected_qualities = [
            "Adaptability", "Academic achievement", "Boldness", "Competition",
            "Creativity", "Enthusiasm", "Excitability", "General ability",
            "Guilt proneness", "Individualism", "Innovation", "Leadership",
            "Maturity", "Mental health", "Morality", "Self control",
            "Sensitivity", "Self sufficiency", "Social warmth", "Tension"
        ]
        
        missing_qualities = [q for q in expected_qualities if q not in PERSONALITY_QUALITIES]
        if missing_qualities:
            print(f"❌ Missing qualities: {missing_qualities}")
            return False
        else:
            print("✅ All expected qualities present")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_streamlit_app():
    """Test if Streamlit app can be parsed"""
    print("\n🧪 Testing Streamlit app...")
    
    try:
        with open("streamlit_app.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for basic Streamlit components
        if "import streamlit" in content:
            print("✅ Streamlit import found")
        else:
            print("❌ Streamlit import not found")
            return False
        
        if "st.title" in content:
            print("✅ Streamlit UI components found")
        else:
            print("❌ Streamlit UI components not found")
            return False
        
        if "def main()" in content:
            print("✅ Main function found")
        else:
            print("❌ Main function not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Streamlit app test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎓 Personality Assessment System - System Test")
    print("=" * 50)
    print()
    
    tests = [
        ("Module Imports", test_imports),
        ("Local Modules", test_local_modules),
        ("Required Files", test_files),
        ("Configuration", test_config),
        ("Streamlit App", test_streamlit_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\nTo run the system:")
        print("   streamlit run streamlit_app.py")
        print("   or")
        print("   python run_app.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues before running the system.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
