import gspread
import pandas as pd
import os
from typing import Dict, List, Any, Optional
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError
import json

class GoogleSheetsIntegration:
    """Integration with Google Sheets for reference data"""
    
    def __init__(self):
        self.sheets_id = "1B6A11n2tpFBioUZ57h-0NQ3hdSNF0eHu"
        self.client = None
        self.sheet = None
        
    def authenticate(self, credentials_file: str = None) -> bool:
        """Authenticate with Google Sheets API"""
        try:
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            if credentials_file and os.path.exists(credentials_file):
                # Use service account credentials
                creds = Credentials.from_service_account_file(
                    credentials_file, scopes=scope
                )
            else:
                # Try to use environment variable or default credentials
                creds = None
                if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                    creds = Credentials.from_service_account_file(
                        os.getenv('GOOGLE_APPLICATION_CREDENTIALS'), scopes=scope
                    )
            
            if creds:
                self.client = gspread.authorize(creds)
            else:
                # Try to use default credentials (for development)
                self.client = gspread.service_account()
            
            return True
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def get_reference_data(self) -> Dict[str, Dict[str, str]]:
        """Fetch reference data from Google Sheets"""
        try:
            if not self.client:
                if not self.authenticate():
                    return self.get_fallback_reference_data()
            
            # Open the spreadsheet
            self.sheet = self.client.open_by_key(self.sheets_id)
            
            # Get the first worksheet
            worksheet = self.sheet.get_worksheet(0)
            
            # Get all values
            all_values = worksheet.get_all_values()
            
            if not all_values:
                print("No data found in Google Sheets")
                return self.get_fallback_reference_data()
            
            # Parse the data
            reference_data = {}
            
            # Assuming the structure is: Quality | Low | Middle | High
            for row in all_values[1:]:  # Skip header row
                if len(row) >= 4:
                    quality = row[0].strip()
                    low_obs = row[1].strip()
                    middle_obs = row[2].strip()
                    high_obs = row[3].strip()
                    
                    if quality:  # Only add if quality name exists
                        reference_data[quality] = {
                            'LOW': low_obs,
                            'MIDDLE': middle_obs,
                            'HIGH': high_obs
                        }
            
            print(f"Successfully loaded {len(reference_data)} qualities from Google Sheets")
            return reference_data
            
        except Exception as e:
            print(f"Error fetching from Google Sheets: {e}")
            return self.get_fallback_reference_data()
    
    def get_fallback_reference_data(self) -> Dict[str, Dict[str, str]]:
        """Fallback reference data if Google Sheets is not available"""
        return {
            "Adaptability": {
                "LOW": "Student shows resistance to change, struggles with new situations, prefers routine",
                "MIDDLE": "Student adapts to some changes, shows moderate flexibility, occasional resistance",
                "HIGH": "Student easily adapts to new situations, shows flexibility, embraces change"
            },
            "Academic achievement": {
                "LOW": "Student shows poor academic performance, lacks motivation, struggles with studies",
                "MIDDLE": "Student shows average academic performance, moderate motivation, some engagement",
                "HIGH": "Student shows excellent academic performance, high motivation, strong engagement"
            },
            "Boldness": {
                "LOW": "Student is shy, avoids taking risks, lacks confidence in new situations",
                "MIDDLE": "Student shows moderate confidence, takes calculated risks, some assertiveness",
                "HIGH": "Student is confident, takes initiative, shows courage in challenging situations"
            },
            "Competition": {
                "LOW": "Student avoids competitive situations, lacks drive to win, passive in group activities",
                "MIDDLE": "Student participates in competitions, shows moderate drive, balanced approach",
                "HIGH": "Student actively seeks competitive situations, strong drive to win, highly motivated"
            },
            "Creativity": {
                "LOW": "Student shows limited imagination, prefers conventional approaches, struggles with new ideas",
                "MIDDLE": "Student shows some creativity, occasional innovative thinking, moderate imagination",
                "HIGH": "Student shows high creativity, innovative thinking, rich imagination, original ideas"
            },
            "Enthusiasm": {
                "LOW": "Student shows low energy, lack of interest, passive participation",
                "MIDDLE": "Student shows moderate energy, some interest, balanced participation",
                "HIGH": "Student shows high energy, great interest, active participation, excitement"
            },
            "Excitability": {
                "LOW": "Student shows calm demeanor, low emotional response, steady behavior",
                "MIDDLE": "Student shows moderate emotional response, balanced reactions, some excitement",
                "HIGH": "Student shows high emotional response, easily excited, reactive behavior"
            },
            "General ability": {
                "LOW": "Student shows limited cognitive skills, struggles with complex tasks, basic understanding",
                "MIDDLE": "Student shows average cognitive skills, handles moderate complexity, good understanding",
                "HIGH": "Student shows high cognitive skills, excels at complex tasks, deep understanding"
            },
            "Guilt proneness": {
                "LOW": "Student shows little remorse, doesn't acknowledge mistakes, lacks accountability",
                "MIDDLE": "Student shows some remorse, occasionally acknowledges mistakes, moderate accountability",
                "HIGH": "Student shows strong remorse, readily acknowledges mistakes, high accountability"
            },
            "Individualism": {
                "LOW": "Student heavily relies on others, follows group decisions, lacks independent thinking",
                "MIDDLE": "Student shows some independence, balanced individual/group thinking, moderate autonomy",
                "HIGH": "Student shows strong independence, makes own decisions, high autonomy, self-reliant"
            },
            "Innovation": {
                "LOW": "Student prefers traditional methods, resistant to new approaches, conventional thinking",
                "MIDDLE": "Student shows some openness to new methods, moderate innovation, balanced approach",
                "HIGH": "Student actively seeks new methods, highly innovative, embraces change, creative solutions"
            },
            "Leadership": {
                "LOW": "Student avoids leading roles, follows others, lacks initiative in group settings",
                "MIDDLE": "Student shows some leadership qualities, occasional initiative, moderate influence",
                "HIGH": "Student naturally takes leadership roles, strong initiative, high influence, guides others"
            },
            "Maturity": {
                "LOW": "Student shows immature behavior, poor decision-making, lacks responsibility",
                "MIDDLE": "Student shows moderate maturity, reasonable decisions, some responsibility",
                "HIGH": "Student shows high maturity, wise decisions, strong responsibility, thoughtful behavior"
            },
            "Mental health": {
                "LOW": "Student shows signs of stress, anxiety, poor emotional regulation, behavioral issues",
                "MIDDLE": "Student shows moderate emotional stability, some stress management, balanced behavior",
                "HIGH": "Student shows excellent emotional stability, good stress management, positive behavior"
            },
            "Morality": {
                "LOW": "Student shows poor ethical judgment, dishonest behavior, lacks integrity",
                "MIDDLE": "Student shows moderate ethical judgment, generally honest, some integrity",
                "HIGH": "Student shows strong ethical judgment, highly honest, strong integrity, principled"
            },
            "Self control": {
                "LOW": "Student shows poor impulse control, easily distracted, lacks discipline",
                "MIDDLE": "Student shows moderate self-control, some focus, balanced discipline",
                "HIGH": "Student shows excellent self-control, high focus, strong discipline, self-regulated"
            },
            "Sensitivity": {
                "LOW": "Student shows low emotional awareness, insensitive to others' feelings, lacks empathy",
                "MIDDLE": "Student shows moderate emotional awareness, some empathy, balanced sensitivity",
                "HIGH": "Student shows high emotional awareness, strong empathy, highly sensitive to others"
            },
            "Self sufficiency": {
                "LOW": "Student heavily depends on others, lacks confidence in abilities, needs constant support",
                "MIDDLE": "Student shows some independence, moderate confidence, balanced self-reliance",
                "HIGH": "Student shows high independence, strong confidence, highly self-reliant, capable"
            },
            "Social warmth": {
                "LOW": "Student shows cold behavior, avoids social interaction, lacks friendliness",
                "MIDDLE": "Student shows moderate social behavior, some interaction, balanced friendliness",
                "HIGH": "Student shows warm behavior, actively social, highly friendly, approachable"
            },
            "Tension": {
                "LOW": "Student shows relaxed demeanor, low stress, calm behavior, comfortable",
                "MIDDLE": "Student shows moderate tension, some stress, balanced behavior, occasional anxiety",
                "HIGH": "Student shows high tension, visible stress, anxious behavior, nervous, worried"
            }
        }
    
    def format_reference_data_for_vector_db(self) -> str:
        """Format reference data for vector database ingestion"""
        reference_data = self.get_reference_data()
        
        formatted_text = "PERSONALITY QUALITY REFERENCE SHEET\n\n"
        
        for quality, levels in reference_data.items():
            formatted_text += f"QUALITY: {quality}\n"
            formatted_text += f"LOW: {levels['LOW']}\n"
            formatted_text += f"MIDDLE: {levels['MIDDLE']}\n"
            formatted_text += f"HIGH: {levels['HIGH']}\n\n"
        
        return formatted_text
    
    def update_reference_data(self, quality: str, level: str, observation: str) -> bool:
        """Update reference data in Google Sheets (for future use)"""
        try:
            if not self.client:
                if not self.authenticate():
                    return False
            
            # Find the row for the quality and update the specific level
            worksheet = self.sheet.get_worksheet(0)
            all_values = worksheet.get_all_values()
            
            for i, row in enumerate(all_values):
                if row[0].strip() == quality:
                    # Update the appropriate column based on level
                    col_map = {"LOW": 1, "MIDDLE": 2, "HIGH": 3}
                    if level in col_map:
                        worksheet.update_cell(i + 1, col_map[level] + 1, observation)
                        return True
            
            return False
            
        except Exception as e:
            print(f"Error updating reference data: {e}")
            return False
    
    def export_reference_data_to_csv(self, filename: str = "reference_data_export.csv"):
        """Export reference data to CSV file"""
        try:
            reference_data = self.get_reference_data()
            
            # Convert to DataFrame
            rows = []
            for quality, levels in reference_data.items():
                rows.append({
                    'Quality': quality,
                    'Low': levels['LOW'],
                    'Middle': levels['MIDDLE'],
                    'High': levels['HIGH']
                })
            
            df = pd.DataFrame(rows)
            df.to_csv(filename, index=False)
            print(f"Reference data exported to {filename}")
            
        except Exception as e:
            print(f"Error exporting reference data: {e}")

def main():
    """Test the Google Sheets integration"""
    print("Testing Google Sheets Integration")
    print("=" * 40)
    
    integration = GoogleSheetsIntegration()
    
    # Try to authenticate
    if integration.authenticate():
        print("✅ Authentication successful")
    else:
        print("⚠️ Authentication failed, using fallback data")
    
    # Get reference data
    reference_data = integration.get_reference_data()
    print(f"📊 Loaded {len(reference_data)} qualities")
    
    # Show sample data
    if reference_data:
        sample_quality = list(reference_data.keys())[0]
        print(f"\nSample data for '{sample_quality}':")
        for level, obs in reference_data[sample_quality].items():
            print(f"  {level}: {obs[:100]}...")
    
    # Export to CSV
    integration.export_reference_data_to_csv()

if __name__ == "__main__":
    main()
