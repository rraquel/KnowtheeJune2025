import os
import pytest
from pathlib import Path
from datetime import datetime
from ..services.ingest import IngestService
from ..services.parsers.cv_parser import CVParser
from ..services.parsers.assessment_parser import AssessmentParser

@pytest.fixture
def sample_cv_text():
    return """
PERSONAL INFORMATION
John Doe
john.doe@example.com
(555) 123-4567
New York, NY
linkedin.com/in/johndoe

SUMMARY
Experienced software engineer with 5 years of experience in Python and web development.

EXPERIENCE
Senior Software Engineer at Tech Corp
2020 - Present
- Led development of microservices architecture
- Mentored junior developers
- Implemented CI/CD pipelines

Software Engineer at Startup Inc
2018 - 2020
- Developed REST APIs
- Optimized database queries
- Participated in code reviews

EDUCATION
University of Technology
Bachelor of Science in Computer Science
2014 - 2018
GPA: 3.8

SKILLS
Python, SQL, Docker, AWS, Git, REST APIs
"""

@pytest.fixture
def sample_assessment_text():
    return """
Candidate Name: John Doe
Date: 2024-03-15
Assessor: Dr. Smith

HPI Score: 75
The candidate demonstrates strong leadership capabilities.

HDS Score: 25
Low risk of derailment.

MVPI Score: 80
Strong alignment with organizational values.

SUMMARY
Overall, the candidate shows excellent potential for leadership roles.
"""

@pytest.fixture
def temp_dirs(tmp_path):
    source_dir = tmp_path / "source"
    processed_dir = tmp_path / "processed"
    source_dir.mkdir()
    processed_dir.mkdir()
    return source_dir, processed_dir

def test_cv_parser(sample_cv_text):
    parser = CVParser()
    result = parser.parse_cv(sample_cv_text)
    
    assert result["first_name"] == "John"
    assert result["last_name"] == "Doe"
    assert result["email"] == "john.doe@example.com"
    assert result["phone"] == "(555) 123-4567"
    assert result["location"] == "New York, NY"
    assert "linkedin.com/in/johndoe" in result["linkedin"]
    
    # Check experience
    assert len(result["experience"]) == 2
    assert result["experience"][0]["title"] == "Senior Software Engineer"
    assert result["experience"][0]["company"] == "Tech Corp"
    
    # Check education
    assert len(result["education"]) == 1
    assert result["education"][0]["institution"] == "University of Technology"
    assert result["education"][0]["degree"] == "Bachelor of Science in Computer Science"
    
    # Check skills
    assert "Python" in result["skills"]
    assert "SQL" in result["skills"]

def test_assessment_parser(sample_assessment_text):
    parser = AssessmentParser()
    result = parser.parse_assessment(sample_assessment_text)
    
    assert result["type"] == "HPI"
    assert result["assessor"] == "Dr. Smith"
    assert result["scores"]["HPI"]["score"] == 75.0
    assert result["scores"]["HDS"]["score"] == 25.0
    assert result["scores"]["MVPI"]["score"] == 80.0

def test_ingest_service_process_single_file(temp_dirs, sample_cv_text):
    source_dir, processed_dir = temp_dirs
    
    # Create a test CV file
    cv_file = source_dir / "test_cv.txt"
    cv_file.write_text(sample_cv_text)
    
    # Initialize service
    service = IngestService(str(source_dir), str(processed_dir))
    
    # Process the file
    result = service.process_single_file("test_cv.txt")
    
    assert result["status"] == "success"
    assert result["file_type"] == "cv"
    assert (processed_dir / "test_cv.txt").exists()
    assert not (source_dir / "test_cv.txt").exists()

def test_ingest_service_process_directory(temp_dirs, sample_cv_text, sample_assessment_text):
    source_dir, processed_dir = temp_dirs
    
    # Create test files
    (source_dir / "cv1.txt").write_text(sample_cv_text)
    (source_dir / "assessment1.txt").write_text(sample_assessment_text)
    
    # Initialize service
    service = IngestService(str(source_dir), str(processed_dir))
    
    # Process directory
    stats = service.process_directory()
    
    assert stats["processed"] == 2
    assert stats["cv_files"] == 1
    assert stats["assessment_files"] == 1
    assert stats["errors"] == 0
    assert len(list(processed_dir.glob("*.txt"))) == 2
    assert len(list(source_dir.glob("*.txt"))) == 0 