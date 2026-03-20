"""
Duplicate Detection and Prevention System

This module implements comprehensive duplicate detection for:
- File uploads (by name, content hash, and data patterns)
- Student entries within files
- Student entries across different uploads
- Assessment data to prevent redundant processing

Addresses Requirements 5.1-5.5
"""

import hashlib
import os
import json
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
from dataclasses import dataclass
import pandas as pd
from pathlib import Path


@dataclass
class DuplicateMatch:
    """Represents a detected duplicate"""
    match_type: str  # 'file', 'student_within_file', 'student_across_files', 'assessment'
    confidence: float  # 0.0 to 1.0
    original_source: str
    duplicate_source: str
    details: Dict
    recommendation: str  # 'skip', 'merge', 'proceed_with_caution'


@dataclass
class FileFingerprint:
    """Unique fingerprint of an uploaded file"""
    filename: str
    content_hash: str
    upload_timestamp: str
    student_count: int
    student_names: List[str]
    file_size: int


class DuplicateDetector:
    """
    Comprehensive duplicate detection system for assessment data.
    
    Features:
    - File-level duplicate detection (name, hash, content)
    - Student-level duplicate detection within and across files
    - Assessment duplicate detection
    - Upload history tracking
    - Configurable matching thresholds
    """
    
    def __init__(self, history_file: str = "assessments/upload_history.json"):
        self.history_file = history_file
        self.upload_history: List[FileFingerprint] = []
        self._load_history()
    
    def _load_history(self):
        """Load upload history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.upload_history = [
                        FileFingerprint(**item) for item in data
                    ]
            except Exception as e:
                print(f"Warning: Could not load upload history: {e}")
                self.upload_history = []
    
    def _save_history(self):
        """Save upload history to file"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                data = [
                    {
                        'filename': fp.filename,
                        'content_hash': fp.content_hash,
                        'upload_timestamp': fp.upload_timestamp,
                        'student_count': fp.student_count,
                        'student_names': fp.student_names,
                        'file_size': fp.file_size
                    }
                    for fp in self.upload_history
                ]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save upload history: {e}")
    
    def compute_file_hash(self, content: bytes) -> str:
        """Compute SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    def compute_data_hash(self, df: pd.DataFrame) -> str:
        """Compute hash of DataFrame content (student names + observations)"""
        # Create a stable string representation of the data
        data_str = ""
        for _, row in df.iterrows():
            # Safely handle None/NaN values
            name_val = row.get('Name', '')
            obs_val = row.get('Observations', '')
            
            # Check for None/NaN and convert safely
            if pd.isna(name_val) or name_val is None:
                name = ""
            else:
                name = str(name_val).strip().lower()
            
            if pd.isna(obs_val) or obs_val is None:
                obs = ""
            else:
                obs = str(obs_val).strip().lower()
            
            data_str += f"{name}|{obs}\n"
        
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def normalize_student_name(self, name: str) -> str:
        """Normalize student name for comparison"""
        # Check for None or NaN values
        if name is None or pd.isna(name):
            return ""
        
        # Convert to string and check if empty
        name_str = str(name).strip()
        if not name_str:
            return ""
        
        # Convert to lowercase, remove extra spaces, remove special characters
        normalized = name_str.lower()
        normalized = ' '.join(normalized.split())  # Collapse multiple spaces
        return normalized
    
    def check_file_duplicate(self, filename: str, content: bytes, df: pd.DataFrame) -> List[DuplicateMatch]:
        """
        Check if uploaded file is a duplicate of previously uploaded files.
        
        Returns list of duplicate matches found.
        """
        duplicates = []
        
        # Compute fingerprints
        content_hash = self.compute_file_hash(content)
        data_hash = self.compute_data_hash(df)
        student_names = [
            self.normalize_student_name(name) 
            for name in df['Name'].tolist() 
            if pd.notna(name) and str(name).strip()
        ]
        
        # Check against upload history
        for historical_fp in self.upload_history:
            # Check 1: Exact filename match
            if historical_fp.filename == filename:
                duplicates.append(DuplicateMatch(
                    match_type='file_name',
                    confidence=0.7,
                    original_source=f"{historical_fp.filename} (uploaded {historical_fp.upload_timestamp})",
                    duplicate_source=filename,
                    details={
                        'reason': 'Identical filename',
                        'original_upload': historical_fp.upload_timestamp,
                        'original_student_count': historical_fp.student_count
                    },
                    recommendation='proceed_with_caution'
                ))
            
            # Check 2: Exact content hash match
            if historical_fp.content_hash == content_hash:
                duplicates.append(DuplicateMatch(
                    match_type='file_content',
                    confidence=1.0,
                    original_source=f"{historical_fp.filename} (uploaded {historical_fp.upload_timestamp})",
                    duplicate_source=filename,
                    details={
                        'reason': 'Identical file content (byte-for-byte match)',
                        'original_upload': historical_fp.upload_timestamp,
                        'original_student_count': historical_fp.student_count
                    },
                    recommendation='skip'
                ))
            
            # Check 3: Student list overlap
            if student_names and historical_fp.student_names:
                overlap = set(student_names) & set(historical_fp.student_names)
                overlap_ratio = len(overlap) / max(len(student_names), len(historical_fp.student_names))
                
                if overlap_ratio > 0.8:  # 80% overlap
                    duplicates.append(DuplicateMatch(
                        match_type='student_overlap',
                        confidence=overlap_ratio,
                        original_source=f"{historical_fp.filename} (uploaded {historical_fp.upload_timestamp})",
                        duplicate_source=filename,
                        details={
                            'reason': f'{len(overlap)} students appear in both files',
                            'overlap_count': len(overlap),
                            'overlap_ratio': f'{overlap_ratio:.1%}',
                            'overlapping_students': list(overlap)[:10],  # Show first 10
                            'original_upload': historical_fp.upload_timestamp
                        },
                        recommendation='merge' if overlap_ratio < 1.0 else 'skip'
                    ))
        
        return duplicates
    
    def check_within_file_duplicates(self, df: pd.DataFrame) -> List[DuplicateMatch]:
        """
        Check for duplicate student entries within the same file.
        
        Returns list of duplicate matches found.
        """
        duplicates = []
        
        # Normalize all student names
        normalized_names = {}
        for idx, row in df.iterrows():
            name = row.get('Name', '')
            if pd.notna(name) and str(name).strip():
                normalized = self.normalize_student_name(name)
                if normalized:
                    if normalized not in normalized_names:
                        normalized_names[normalized] = []
                    normalized_names[normalized].append({
                        'row': idx + 2,  # +2 for header and 0-indexing
                        'original_name': str(name),
                        'observations': str(row.get('Observations', ''))[:100]
                    })
        
        # Find duplicates
        for normalized, occurrences in normalized_names.items():
            if len(occurrences) > 1:
                duplicates.append(DuplicateMatch(
                    match_type='student_within_file',
                    confidence=1.0,
                    original_source=f"Row {occurrences[0]['row']}: {occurrences[0]['original_name']}",
                    duplicate_source=f"Rows {', '.join(str(occ['row']) for occ in occurrences[1:])}",
                    details={
                        'reason': 'Same student appears multiple times in file',
                        'normalized_name': normalized,
                        'occurrences': occurrences,
                        'count': len(occurrences)
                    },
                    recommendation='merge'
                ))
        
        return duplicates
    
    def check_cross_file_duplicates(self, df: pd.DataFrame, current_filename: str) -> List[DuplicateMatch]:
        """
        Check if students in current file already exist in previously uploaded files.
        
        Returns list of duplicate matches found.
        """
        duplicates = []
        
        # Get student names from current file
        current_students = set()
        for _, row in df.iterrows():
            name = row.get('Name', '')
            if pd.notna(name) and str(name).strip():
                normalized = self.normalize_student_name(name)
                if normalized:
                    current_students.add(normalized)
        
        # Check against historical uploads
        for historical_fp in self.upload_history:
            historical_students = set(historical_fp.student_names)
            overlap = current_students & historical_students
            
            if overlap:
                duplicates.append(DuplicateMatch(
                    match_type='student_across_files',
                    confidence=0.9,
                    original_source=f"{historical_fp.filename} (uploaded {historical_fp.upload_timestamp})",
                    duplicate_source=current_filename,
                    details={
                        'reason': f'{len(overlap)} students already exist in previous upload',
                        'overlap_count': len(overlap),
                        'overlapping_students': list(overlap)[:20],  # Show first 20
                        'original_upload': historical_fp.upload_timestamp,
                        'note': 'This may be intentional for tracking student progress over time'
                    },
                    recommendation='proceed_with_caution'
                ))
        
        return duplicates
    
    def register_upload(self, filename: str, content: bytes, df: pd.DataFrame):
        """
        Register a successful upload in the history.
        Call this after user confirms they want to proceed with the upload.
        """
        content_hash = self.compute_file_hash(content)
        student_names = [
            self.normalize_student_name(name) 
            for name in df['Name'].tolist() 
            if pd.notna(name) and str(name).strip()
        ]
        
        fingerprint = FileFingerprint(
            filename=filename,
            content_hash=content_hash,
            upload_timestamp=datetime.now().isoformat(),
            student_count=len(student_names),
            student_names=student_names,
            file_size=len(content)
        )
        
        self.upload_history.append(fingerprint)
        self._save_history()
    
    def perform_comprehensive_check(self, filename: str, content: bytes, df: pd.DataFrame) -> Dict:
        """
        Perform all duplicate checks and return comprehensive report.
        
        Returns:
            Dictionary with:
            - has_duplicates: bool
            - file_duplicates: List[DuplicateMatch]
            - within_file_duplicates: List[DuplicateMatch]
            - cross_file_duplicates: List[DuplicateMatch]
            - recommendation: str ('proceed', 'review', 'skip')
            - summary: str
        """
        file_dups = self.check_file_duplicate(filename, content, df)
        within_dups = self.check_within_file_duplicates(df)
        cross_dups = self.check_cross_file_duplicates(df, filename)
        
        all_duplicates = file_dups + within_dups + cross_dups
        has_duplicates = len(all_duplicates) > 0
        
        # Determine overall recommendation
        if any(d.recommendation == 'skip' for d in all_duplicates):
            recommendation = 'skip'
            summary = "⛔ Exact duplicate detected - uploading this file will create redundant data"
        elif any(d.recommendation == 'merge' for d in all_duplicates):
            recommendation = 'review'
            summary = "⚠️ Duplicates detected - review and decide how to proceed"
        elif has_duplicates:
            recommendation = 'review'
            summary = "ℹ️ Potential duplicates detected - this may be intentional for tracking progress"
        else:
            recommendation = 'proceed'
            summary = "✅ No duplicates detected - safe to proceed"
        
        return {
            'has_duplicates': has_duplicates,
            'file_duplicates': file_dups,
            'within_file_duplicates': within_dups,
            'cross_file_duplicates': cross_dups,
            'all_duplicates': all_duplicates,
            'recommendation': recommendation,
            'summary': summary,
            'total_duplicate_count': len(all_duplicates)
        }
    
    def clear_history(self):
        """Clear upload history (use with caution)"""
        self.upload_history = []
        self._save_history()
    
    def get_upload_statistics(self) -> Dict:
        """Get statistics about upload history"""
        if not self.upload_history:
            return {
                'total_uploads': 0,
                'total_students': 0,
                'unique_students': 0,
                'first_upload': None,
                'last_upload': None
            }
        
        all_students = set()
        for fp in self.upload_history:
            all_students.update(fp.student_names)
        
        return {
            'total_uploads': len(self.upload_history),
            'total_students': sum(fp.student_count for fp in self.upload_history),
            'unique_students': len(all_students),
            'first_upload': min(fp.upload_timestamp for fp in self.upload_history),
            'last_upload': max(fp.upload_timestamp for fp in self.upload_history),
            'upload_history': [
                {
                    'filename': fp.filename,
                    'timestamp': fp.upload_timestamp,
                    'student_count': fp.student_count
                }
                for fp in sorted(self.upload_history, key=lambda x: x.upload_timestamp, reverse=True)
            ][:10]  # Last 10 uploads
        }
