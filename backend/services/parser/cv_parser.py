import re
from datetime import datetime
from typing import Dict, List, Any
import spacy

class CVParser:
    """Parser for extracting structured information from CV text."""
    
    def __init__(self):
        """Initialize the CV parser with spaCy model."""
        self.nlp = spacy.load("en_core_web_sm")
        
    def parse_cv(self, text: str) -> Dict[str, Any]:
        """
        Parse CV text into structured data.
        
        Args:
            text: Raw CV text
            
        Returns:
            Dictionary containing parsed CV data
        """
        sections = self._split_into_sections(text)
        
        return {
            "personal_info": self._parse_personal_info(sections.get("PERSONAL INFORMATION", "")),
            "summary": sections.get("SUMMARY", ""),
            "experience": self._parse_experience(sections.get("EXPERIENCE", "")),
            "education": self._parse_education(sections.get("EDUCATION", "")),
            "skills": self._parse_skills(sections.get("SKILLS", ""))
        }
        
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split CV text into sections based on uppercase headers."""
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
        
    def _parse_personal_info(self, text: str) -> Dict[str, str]:
        """Extract personal information from text."""
        info = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": ""
        }
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Extract email
            if '@' in line and '.' in line:
                info["email"] = line
            # Extract phone (simple pattern)
            elif re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', line):
                info["phone"] = line
            # Extract LinkedIn
            elif 'linkedin.com' in line.lower():
                info["linkedin"] = line
            # Extract location (assume city, state format)
            elif ',' in line and not '@' in line and not 'linkedin' in line.lower():
                info["location"] = line.split(',')[0].strip()
            # Assume first non-matching line is name
            elif not info["name"]:
                info["name"] = line
                
        return info
        
    def _parse_experience(self, text: str) -> List[Dict[str, Any]]:
        """Parse work experience entries."""
        experiences = []
        current_exp = {}
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_exp:
                    experiences.append(current_exp)
                    current_exp = {}
                continue
                
            # New experience entry starts with position/company
            if not current_exp or re.match(r'^[A-Z]', line):
                if current_exp:
                    experiences.append(current_exp)
                current_exp = {
                    "title": line.split(' at ')[0].strip() if ' at ' in line else line,
                    "company": line.split(' at ')[1].strip() if ' at ' in line else "",
                    "start_date": None,
                    "end_date": None,
                    "description": []
                }
            # Date range
            elif re.search(r'\d{4}', line):
                dates = re.findall(r'\b\d{4}\b', line)
                if len(dates) >= 1:
                    current_exp["start_date"] = datetime.strptime(dates[0], '%Y')
                    current_exp["end_date"] = (datetime.strptime(dates[1], '%Y') 
                                            if len(dates) > 1 else None)
            # Description
            else:
                current_exp.setdefault("description", []).append(line)
                
        if current_exp:
            experiences.append(current_exp)
            
        return experiences
        
    def _parse_education(self, text: str) -> List[Dict[str, Any]]:
        """Parse education entries."""
        education = []
        current_edu = {}
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_edu:
                    education.append(current_edu)
                    current_edu = {}
                continue
                
            # New education entry starts with institution
            if not current_edu or re.match(r'^[A-Z]', line):
                if current_edu:
                    education.append(current_edu)
                current_edu = {
                    "institution": line,
                    "degree": "",
                    "field_of_study": "",
                    "start_date": None,
                    "end_date": None
                }
            # Degree and field
            elif "degree" not in current_edu or not current_edu["degree"]:
                parts = line.split(' in ')
                current_edu["degree"] = parts[0].strip()
                if len(parts) > 1:
                    current_edu["field_of_study"] = parts[1].strip()
            # Date range
            elif re.search(r'\d{4}', line):
                dates = re.findall(r'\b\d{4}\b', line)
                if len(dates) >= 1:
                    current_edu["start_date"] = datetime.strptime(dates[0], '%Y')
                    current_edu["end_date"] = (datetime.strptime(dates[1], '%Y')
                                           if len(dates) > 1 else None)
                    
        if current_edu:
            education.append(current_edu)
            
        return education
        
    def _parse_skills(self, text: str) -> List[str]:
        """Extract skills from text."""
        # Split by common delimiters and clean up
        skills = []
        for skill in re.split(r'[,|•]', text):
            skill = skill.strip()
            if skill:
                skills.append(skill)
        return skills

