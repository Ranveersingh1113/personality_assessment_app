#!/usr/bin/env python3
"""
Test script for CSV reference data processing
This script tests the processing of the NGO's actual reference data
"""

import os
from csv_reference_processor import CSVReferenceProcessor

def main():
    print("🧪 Testing CSV Reference Data Processing")
    print("=" * 50)
    print()
    
    # Initialize processor
    processor = CSVReferenceProcessor()
    
    print("📊 Attempting to load reference data from CSV...")
    print(f"CSV file: {processor.csv_file_path}")
    print()
    
    # Check if CSV file exists
    if not os.path.exists(processor.csv_file_path):
        print(f"❌ CSV file not found: {processor.csv_file_path}")
        print("Please ensure the CSV file is in the current directory.")
        return
    
    print("✅ CSV file found")
    print()
    
    # Load reference data
    try:
        reference_data = processor.load_reference_data()
        
        if reference_data:
            print(f"✅ Successfully loaded {len(reference_data)} qualities")
            print()
            
            # Show sample data
            print("📋 Sample Reference Data:")
            print("-" * 30)
            
            for i, (quality, levels) in enumerate(reference_data.items()):
                if i < 3:  # Show first 3 qualities
                    print(f"\n🔹 {quality}:")
                    for level, observations in levels.items():
                        if observations:
                            print(f"  {level}: {len(observations)} observations")
                            for obs in observations[:2]:  # Show first 2 observations
                                print(f"    - {obs[:80]}...")
                else:
                    break
            
            if len(reference_data) > 3:
                print(f"\n... and {len(reference_data) - 3} more qualities")
            
            # Get summary statistics
            summary = processor.get_quality_summary()
            print(f"\n📊 Summary Statistics:")
            print("-" * 30)
            
            total_observations = 0
            for quality, level_counts in summary.items():
                quality_total = sum(level_counts.values())
                total_observations += quality_total
                print(f"{quality}: {quality_total} observations")
            
            print(f"\nTotal observations: {total_observations}")
            
            # Test search functionality
            print(f"\n🔍 Testing search functionality:")
            search_results = processor.search_observations("confident")
            print(f"Found {len(search_results)} observations containing 'confident'")
            
            if search_results:
                print("Sample search results:")
                for result in search_results[:3]:
                    print(f"  - {result['quality']} ({result['level']}): {result['observation'][:60]}...")
            
            # Export data
            print(f"\n💾 Exporting reference data...")
            processor.export_reference_data_to_json("test_reference_data.json")
            processor.export_reference_data_to_csv("test_reference_data.csv")
            print("✅ Reference data exported successfully")
            
            # Test vector database formatting
            print(f"\n📝 Testing vector database formatting...")
            formatted_text = processor.format_reference_data_for_vector_db()
            print(f"Formatted text length: {len(formatted_text)} characters")
            print("Sample formatted text:")
            print(formatted_text[:500] + "...")
            
        else:
            print("❌ No reference data found")
            
    except Exception as e:
        print(f"❌ Error processing reference data: {e}")
        print("\nThis might be due to:")
        print("- Incorrect CSV format")
        print("- Missing or corrupted file")
        print("- Permission issues")
    
    print("\n" + "=" * 50)
    print("🎉 CSV reference data processing test completed!")

if __name__ == "__main__":
    main()
