
import os
import shutil
from typing import Dict, List, Any
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime

class ReportCardGenerator:
    """Class to generate report cards by filling an Excel template"""
    
    def __init__(self):
        self.template_path = "report_card_template.xlsx"
        
    def set_template(self, template_file):
        """Save the uploaded template for use"""
        with open(self.template_path, "wb") as f:
            f.write(template_file.getbuffer())
            
    def generate_report_card(self, student_name: str, school_name: str, swot_data: Dict[str, Any], output_dir: str = "generated_reports") -> str:
        """
        Generate a single student's report card.
        Returns the path to the generated Excel file.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Input validation
        if not student_name or not student_name.strip():
            raise ValueError("Student name cannot be empty")
        
        if not os.path.exists(self.template_path):
            raise FileNotFoundError("Template file not found. Please upload a template first.")

        # Ensure output directory exists (using report_cards/ folder to keep it clean)
        actual_output_dir = os.path.join(output_dir)
        os.makedirs(actual_output_dir, exist_ok=True)
        
        # Determine output filename with safety limits
        safe_name = "".join([c for c in student_name if c.isalnum() or c in (' ', '-', '_')]).strip()
        # Limit filename length to prevent filesystem issues
        max_name_length = 100
        if len(safe_name) > max_name_length:
            safe_name = safe_name[:max_name_length]
        # Fallback if name becomes empty after sanitization
        if not safe_name:
            safe_name = f"Student_{hash(student_name) % 100000}"
        
        filename = f"{safe_name}_ReportCard.xlsx"
        output_path = os.path.join(actual_output_dir, filename)
        
        # Copy template to output path
        shutil.copy2(self.template_path, output_path)
        
        # Load workbook
        try:
            wb = load_workbook(output_path)
            ws = wb.active  # Assume first sheet is the target
            
            # --- CELL MAPPINGS (Based on visual inspection) ---
            
            def _safe_write(worksheet, cell_address, value):
                """Safely write to a cell, handling merged cells automatically."""
                # Check if cell is part of a merged range
                for merged_range in worksheet.merged_cells.ranges:
                    if cell_address in merged_range:
                        # If merged, write to the top-left cell of the range
                        top_left = merged_range.start_cell
                        worksheet[top_left.coordinate] = value
                        return
                # If not merged, write directly
                worksheet[cell_address] = value

            # Name: S2
            _safe_write(ws, 'S2', student_name)
            # School: Not specified in new request, keeping N2 or removing if not needed. 
            # User only mentioned Name S2. I'll keep N2 as safe backup or remove if it conflicts. 
            # Given the image, School is at right. Let's keep N2 or find its new place if known? 
            # User said "The name should be in the cell S2". I will trust that.
            
            # SWOT Sections Mappings
            # Strengths: Q4, Q6, Q8, Q13, Q17
            strength_cells = ['Q4', 'Q6', 'Q8', 'Q13', 'Q17']
            
            # Weaknesses: Y4, Y5, Y6, Y7
            weakness_cells = ['Y4', 'Y5', 'Y6', 'Y7']
            
            # Opportunities: AG4, AG5, AG6, AG7
            opportunity_cells = ['AG4', 'AG5', 'AG6', 'AG7']
            
            # Threats: AO4, AO5, AO6, AO7
            threat_cells = ['AO4', 'AO5', 'AO6', 'AO7']
            
            items = swot_data.get('swot_items', [])
            
            # Filter items by category
            strengths = [i for i in items if i['category'] == 'STRENGTH']
            weaknesses = [i for i in items if i['category'] == 'WEAKNESS']
            opportunities = [i for i in items if i['category'] == 'OPPORTUNITY']
            threats = [i for i in items if i['category'] == 'THREAT']
            
            def fill_section(data_items, cell_list):
                for idx, cell in enumerate(cell_list):
                    if idx < len(data_items):
                        # Write ONLY the point as requested (Abstract Traits Only)
                        # Ignoring explanation/evidence text completely.
                        item = data_items[idx]
                        text = item['point']
                        _safe_write(ws, cell, text)
                    else:
                        # Clear cell if no data
                        _safe_write(ws, cell, "")

            fill_section(strengths, strength_cells)
            fill_section(weaknesses, weakness_cells)
            fill_section(opportunities, opportunity_cells)
            fill_section(threats, threat_cells)
            
            # Leave Personality Ratings & Guidance empty as requested
            
            wb.save(output_path)
            return output_path
            
        except Exception as e:
            # Clean up if failed
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception as cleanup_err:
                    logger.warning(f"Could not remove failed output file {output_path}: {cleanup_err}")
            raise e

    def batch_generate(self, batch_data: List[Dict[str, Any]]) -> str:
        """
        Generate reports for a batch of students.
        batch_data: List of dicts with keys 'name', 'school', 'swot_data'
        Returns path to a ZIP file containing all reports.
        """
        output_dir = "report_cards_batch_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = []
        errors = []
        
        for student in batch_data:
            try:
                path = self.generate_report_card(
                    student['name'], 
                    student.get('school', 'N/A'), 
                    student['swot_data'], 
                    output_dir
                )
                generated_files.append(path)
            except Exception as e:
                errors.append(f"Failed for {student['name']}: {e}")
        
        # Create ZIP
        zip_filename = f"{output_dir}.zip"
        shutil.make_archive(output_dir, 'zip', output_dir)
        
        # Clean up folder (optional, keeping zip)
        # shutil.rmtree(output_dir) 
        
        return zip_filename, errors
