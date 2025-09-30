import pandas as pd
import os
from typing import Dict, List, Any
import json

class CSVReferenceProcessor:
    """Process the actual CSV reference data from the NGO"""
    
    def __init__(self, csv_file_path: str = "Obseervations check list for feeding.1.xlsx - observation check list 1.csv"):
        # Resolve CSV path relative to project root so it works from any CWD
        project_root = os.path.dirname(os.path.abspath(__file__))
        tentative = csv_file_path
        abs_path = tentative if os.path.isabs(tentative) else os.path.join(project_root, tentative)
        self.csv_file_path = abs_path
        self.reference_data = {}
        
    def load_reference_data(self) -> Dict[str, Dict[str, List[str]]]:
        """Load and process the CSV reference data"""
        try:
            if not os.path.exists(self.csv_file_path):
                print(f"CSV file not found: {self.csv_file_path}")
                return self.get_fallback_reference_data()
            
            # Read the CSV file
            df = pd.read_csv(self.csv_file_path)
            
            # Process the data
            current_quality = None
            reference_data = {}
            
            for index, row in df.iterrows():
                # Check if this row has a quality name in the first column
                if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip():
                    current_quality = str(row.iloc[0]).strip()
                    reference_data[current_quality] = {
                        'LOW': [],
                        'MIDDLE': [],
                        'HIGH': []
                    }
                
                # If we have a current quality, process the observations
                if current_quality:
                    # Process Low observations (column 1)
                    if pd.notna(row.iloc[1]) and str(row.iloc[1]).strip():
                        reference_data[current_quality]['LOW'].append(str(row.iloc[1]).strip())
                    
                    # Process Middle observations (column 2)
                    if pd.notna(row.iloc[2]) and str(row.iloc[2]).strip():
                        reference_data[current_quality]['MIDDLE'].append(str(row.iloc[2]).strip())
                    
                    # Process High observations (column 3)
                    if pd.notna(row.iloc[3]) and str(row.iloc[3]).strip():
                        reference_data[current_quality]['HIGH'].append(str(row.iloc[3]).strip())
            
            # Clean up empty qualities
            reference_data = {k: v for k, v in reference_data.items() if any(v.values())}
            
            print(f"Successfully loaded {len(reference_data)} qualities from CSV")
            self.reference_data = reference_data
            return reference_data
            
        except Exception as e:
            print(f"Error loading CSV reference data: {e}")
            return self.get_fallback_reference_data()
    
    def get_fallback_reference_data(self) -> Dict[str, Dict[str, List[str]]]:
        """Fallback reference data if CSV is not available"""
        return {
            "Adaptability": {
                "LOW": ["Student shows resistance to change, struggles with new situations, prefers routine"],
                "MIDDLE": ["Student adapts to some changes, shows moderate flexibility, occasional resistance"],
                "HIGH": ["Student easily adapts to new situations, shows flexibility, embraces change"]
            },
            "Academic achievement": {
                "LOW": ["Student shows poor academic performance, lacks motivation, struggles with studies"],
                "MIDDLE": ["Student shows average academic performance, moderate motivation, some engagement"],
                "HIGH": ["Student shows excellent academic performance, high motivation, strong engagement"]
            },
            "Boldness": {
                "LOW": ["Student is shy, avoids taking risks, lacks confidence in new situations"],
                "MIDDLE": ["Student shows moderate confidence, takes calculated risks, some assertiveness"],
                "HIGH": ["Student is confident, takes initiative, shows courage in challenging situations"]
            },
            "Competition": {
                "LOW": ["Student avoids competitive situations, lacks drive to win, passive in group activities"],
                "MIDDLE": ["Student participates in competitions, shows moderate drive, balanced approach"],
                "HIGH": ["Student actively seeks competitive situations, strong drive to win, highly motivated"]
            },
            "Creativity": {
                "LOW": ["Student shows limited imagination, prefers conventional approaches, struggles with new ideas"],
                "MIDDLE": ["Student shows some creativity, occasional innovative thinking, moderate imagination"],
                "HIGH": ["Student shows high creativity, innovative thinking, rich imagination, original ideas"]
            },
            "Enthusiasm": {
                "LOW": ["Student shows low energy, lack of interest, passive participation"],
                "MIDDLE": ["Student shows moderate energy, some interest, balanced participation"],
                "HIGH": ["Student shows high energy, great interest, active participation, excitement"]
            },
            "Excitability": {
                "LOW": ["Student shows calm demeanor, low emotional response, steady behavior"],
                "MIDDLE": ["Student shows moderate emotional response, balanced reactions, some excitement"],
                "HIGH": ["Student shows high emotional response, easily excited, reactive behavior"]
            },
            "General ability": {
                "LOW": ["Student shows limited cognitive skills, struggles with complex tasks, basic understanding"],
                "MIDDLE": ["Student shows average cognitive skills, handles moderate complexity, good understanding"],
                "HIGH": ["Student shows high cognitive skills, excels at complex tasks, deep understanding"]
            },
            "Guilt proneness": {
                "LOW": ["Student shows little remorse, doesn't acknowledge mistakes, lacks accountability"],
                "MIDDLE": ["Student shows some remorse, occasionally acknowledges mistakes, moderate accountability"],
                "HIGH": ["Student shows strong remorse, readily acknowledges mistakes, high accountability"]
            },
            "Individualism": {
                "LOW": ["Student heavily relies on others, follows group decisions, lacks independent thinking"],
                "MIDDLE": ["Student shows some independence, balanced individual/group thinking, moderate autonomy"],
                "HIGH": ["Student shows strong independence, makes own decisions, high autonomy, self-reliant"]
            },
            "Innovation": {
                "LOW": ["Student prefers traditional methods, resistant to new approaches, conventional thinking"],
                "MIDDLE": ["Student shows some openness to new methods, moderate innovation, balanced approach"],
                "HIGH": ["Student actively seeks new methods, highly innovative, embraces change, creative solutions"]
            },
            "Leadership": {
                "LOW": ["Student avoids leading roles, follows others, lacks initiative in group settings"],
                "MIDDLE": ["Student shows some leadership qualities, occasional initiative, moderate influence"],
                "HIGH": ["Student naturally takes leadership roles, strong initiative, high influence, guides others"]
            },
            "Maturity": {
                "LOW": ["Student shows immature behavior, poor decision-making, lacks responsibility"],
                "MIDDLE": ["Student shows moderate maturity, reasonable decisions, some responsibility"],
                "HIGH": ["Student shows high maturity, wise decisions, strong responsibility, thoughtful behavior"]
            },
            "Mental health": {
                "LOW": ["Student shows signs of stress, anxiety, poor emotional regulation, behavioral issues"],
                "MIDDLE": ["Student shows moderate emotional stability, some stress management, balanced behavior"],
                "HIGH": ["Student shows excellent emotional stability, good stress management, positive behavior"]
            },
            "Morality": {
                "LOW": ["Student shows poor ethical judgment, dishonest behavior, lacks integrity"],
                "MIDDLE": ["Student shows moderate ethical judgment, generally honest, some integrity"],
                "HIGH": ["Student shows strong ethical judgment, highly honest, strong integrity, principled"]
            },
            "Self control": {
                "LOW": ["Student shows poor impulse control, easily distracted, lacks discipline"],
                "MIDDLE": ["Student shows moderate self-control, some focus, balanced discipline"],
                "HIGH": ["Student shows excellent self-control, high focus, strong discipline, self-regulated"]
            },
            "Sensitivity": {
                "LOW": ["Student shows low emotional awareness, insensitive to others' feelings, lacks empathy"],
                "MIDDLE": ["Student shows moderate emotional awareness, some empathy, balanced sensitivity"],
                "HIGH": ["Student shows high emotional awareness, strong empathy, highly sensitive to others"]
            },
            "Self sufficiency": {
                "LOW": ["Student heavily depends on others, lacks confidence in abilities, needs constant support"],
                "MIDDLE": ["Student shows some independence, moderate confidence, balanced self-reliance"],
                "HIGH": ["Student shows high independence, strong confidence, highly self-reliant, capable"]
            },
            "Social warmth": {
                "LOW": ["Student shows cold behavior, avoids social interaction, lacks friendliness"],
                "MIDDLE": ["Student shows moderate social behavior, some interaction, balanced friendliness"],
                "HIGH": ["Student shows warm behavior, actively social, highly friendly, approachable"]
            },
            "Tension": {
                "LOW": ["Student shows relaxed demeanor, low stress, calm behavior, comfortable"],
                "MIDDLE": ["Student shows moderate tension, some stress, balanced behavior, occasional anxiety"],
                "HIGH": ["Student shows high tension, visible stress, anxious behavior, nervous, worried"]
            }
        }
    
    def format_reference_data_for_vector_db(self) -> str:
        """Format reference data for vector database ingestion"""
        reference_data = self.load_reference_data()
        
        formatted_text = "PERSONALITY QUALITY REFERENCE SHEET\n\n"
        
        for quality, levels in reference_data.items():
            formatted_text += f"QUALITY: {quality}\n"
            
            for level, observations in levels.items():
                if observations:
                    formatted_text += f"{level}:\n"
                    for obs in observations:
                        formatted_text += f"  - {obs}\n"
                    formatted_text += "\n"
        
        return formatted_text
    
    def get_quality_observations(self, quality: str, level: str) -> List[str]:
        """Get specific observations for a quality and level"""
        reference_data = self.load_reference_data()
        
        if quality in reference_data and level in reference_data[quality]:
            return reference_data[quality][level]
        return []
    
    def export_reference_data_to_json(self, filename: str = "reference_data.json"):
        """Export reference data to JSON file"""
        try:
            reference_data = self.load_reference_data()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(reference_data, f, indent=2, ensure_ascii=False)
            
            print(f"Reference data exported to {filename}")
            
        except Exception as e:
            print(f"Error exporting reference data: {e}")
    
    def export_reference_data_to_csv(self, filename: str = "reference_data_export.csv"):
        """Export reference data to CSV file"""
        try:
            reference_data = self.load_reference_data()
            
            # Convert to DataFrame format
            rows = []
            for quality, levels in reference_data.items():
                for level, observations in levels.items():
                    for obs in observations:
                        rows.append({
                            'Quality': quality,
                            'Level': level,
                            'Observation': obs
                        })
            
            df = pd.DataFrame(rows)
            df.to_csv(filename, index=False)
            print(f"Reference data exported to {filename}")
            
        except Exception as e:
            print(f"Error exporting reference data: {e}")
    
    def get_quality_summary(self) -> Dict[str, Dict[str, int]]:
        """Get summary of observations per quality and level"""
        reference_data = self.load_reference_data()
        
        summary = {}
        for quality, levels in reference_data.items():
            summary[quality] = {}
            for level, observations in levels.items():
                summary[quality][level] = len(observations)
        
        return summary
    
    def search_observations(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for observations containing specific terms"""
        reference_data = self.load_reference_data()
        results = []
        
        search_term_lower = search_term.lower()
        
        for quality, levels in reference_data.items():
            for level, observations in levels.items():
                for obs in observations:
                    if search_term_lower in obs.lower():
                        results.append({
                            'quality': quality,
                            'level': level,
                            'observation': obs
                        })
        
        return results

def main():
    """Test the CSV reference processor"""
    print("Testing CSV Reference Processor")
    print("=" * 50)
    
    processor = CSVReferenceProcessor()
    
    # Load reference data
    reference_data = processor.load_reference_data()
    print(f"📊 Loaded {len(reference_data)} qualities")
    
    # Show sample data
    if reference_data:
        print("\n📋 Sample Reference Data:")
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
    
    # Get summary
    summary = processor.get_quality_summary()
    print(f"\n📊 Summary:")
    total_observations = sum(sum(level_counts.values()) for level_counts in summary.values())
    print(f"Total observations: {total_observations}")
    
    # Export data
    processor.export_reference_data_to_json()
    processor.export_reference_data_to_csv()
    
    print("\n" + "=" * 50)
    print("🎉 CSV reference processor test completed!")

if __name__ == "__main__":
    main()
