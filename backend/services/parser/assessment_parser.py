import re
from datetime import datetime
from typing import Dict, Any

class AssessmentParser:
    """Parser for extracting structured information from assessment reports."""
    
    def parse_assessment(self, text: str) -> Dict[str, Any]:
        """
        Parse assessment text into structured data.
        
        Args:
            text: Raw assessment text
            
        Returns:
            Dictionary containing parsed assessment data
        """
        sections = self._split_into_sections(text)
        
        return {
            "candidate_info": self._parse_candidate_info(text),
            "scores": self._parse_scores(text),
            "recommendations": sections.get("RECOMMENDATIONS", ""),
            "summary": sections.get("SUMMARY", "")
        }
        
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split assessment text into sections."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section header (all uppercase)
            if line.isupper() and len(line) > 3:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line
                current_content = []
            elif current_section:
                current_content.append(line)
                
        # Add last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
            
        return sections
        
    def _parse_candidate_info(self, text: str) -> Dict[str, Any]:
        """Extract candidate information."""
        info = {
            "name": "",
            "assessment_date": None
        }
        
        # Extract name
        name_match = re.search(r'Candidate Name:\s*(.+)', text)
        if name_match:
            info["name"] = name_match.group(1).strip()
            
        # Extract date
        date_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', text)
        if date_match:
            info["assessment_date"] = datetime.strptime(date_match.group(1), '%Y-%m-%d')
            
        return info
        
    def _parse_scores(self, text: str) -> Dict[str, float]:
        """Extract assessment scores."""
        scores = {
            "hpi": 0.0,  # Bright side personality
            "hds": 0.0,  # Dark side personality
            "mvpi": 0.0  # Values and motives
        }
        
        # Extract HPI score
        hpi_match = re.search(r'HPI Score:\s*(\d+\.?\d*)', text)
        if hpi_match:
            scores["hpi"] = float(hpi_match.group(1))
            
        # Extract HDS score
        hds_match = re.search(r'HDS Score:\s*(\d+\.?\d*)', text)
        if hds_match:
            scores["hds"] = float(hds_match.group(1))
            
        # Extract MVPI score
        mvpi_match = re.search(r'MVPI Score:\s*(\d+\.?\d*)', text)
        if mvpi_match:
            scores["mvpi"] = float(mvpi_match.group(1))
            
        return scores

