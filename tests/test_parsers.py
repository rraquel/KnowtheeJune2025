import pytest
from app.services.parser.cv_parser import CVParser
from app.services.parser.assessment_parser import AssessmentParser

@pytest.fixture
def cv_parser():
    return CVParser()

@pytest.fixture
def assessment_parser():
    return AssessmentParser()

def test_cv_parser_extracts_personal_info(cv_parser):
    """Test that CV parser correctly extracts personal information."""
    sample_cv = """
    PERSONAL INFORMATION
    John Doe
    john.doe@email.com
    (123) 456-7890
    San Francisco, CA
    linkedin.com/in/johndoe
    """
    
    result = cv_parser.parse_cv(sample_cv)
    personal_info = result["personal_info"]
    
    assert personal_info["name"] == "John Doe"
    assert personal_info["email"] == "john.doe@email.com"
    assert personal_info["phone"] == "(123) 456-7890"
    assert personal_info["location"] == "San Francisco"
    assert personal_info["linkedin"] == "linkedin.com/in/johndoe"

def test_assessment_parser_extracts_scores(assessment_parser):
    """Test that assessment parser correctly extracts scores."""
    sample_assessment = """
    Candidate Name: Jane Smith
    Date: 2024-03-14
    
    HPI Score: 85.5
    Leadership potential demonstrated through...
    
    HDS Score: 72.3
    Areas of development include...
    
    MVPI Score: 91.2
    Strong alignment with company values...
    """
    
    result = assessment_parser.parse_assessment(sample_assessment)
    scores = result["scores"]
    
    assert scores["hpi"] == 85.5
    assert scores["hds"] == 72.3
    assert scores["mvpi"] == 91.2
    assert result["candidate_info"]["name"] == "Jane Smith" 