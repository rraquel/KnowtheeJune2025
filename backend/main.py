import os
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from database import get_db, engine
from database.models import Base, Employee, Experience, Education, Skill, EmployeeSkill, Assessment
from services.parser.cv_parser import CVParser
from services.parser.assessment_parser import AssessmentParser
from utils.validators import validate_file

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create database tables."""
    Base.metadata.create_all(bind=engine)

def process_cv(db: Session, file_path: str) -> Dict[str, Any]:
    """
    Process a CV file and store data in the database.
    
    Args:
        db: Database session
        file_path: Path to CV file
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Validate file
        is_valid, error = validate_file(file_path)
        if not is_valid:
            return {"success": False, "error": error}
            
        # Read and parse CV
        with open(file_path, 'r', encoding='utf-8') as f:
            cv_text = f.read()
            
        parser = CVParser()
        cv_data = parser.parse_cv(cv_text)
        
        # Create employee record
        employee = Employee(
            name=cv_data["personal_info"]["name"],
            email=cv_data["personal_info"]["email"],
            phone=cv_data["personal_info"]["phone"],
            location=cv_data["personal_info"]["location"],
            linkedin_url=cv_data["personal_info"]["linkedin"],
            summary=cv_data["summary"]
        )
        db.add(employee)
        db.flush()  # Get employee ID
        
        # Add experiences
        for exp in cv_data["experience"]:
            experience = Experience(
                employee_id=employee.id,
                title=exp["title"],
                company=exp["company"],
                start_date=exp["start_date"],
                end_date=exp["end_date"],
                description='\n'.join(exp.get("description", []))
            )
            db.add(experience)
            
        # Add education
        for edu in cv_data["education"]:
            education = Education(
                employee_id=employee.id,
                institution=edu["institution"],
                degree=edu["degree"],
                field_of_study=edu["field_of_study"],
                start_date=edu["start_date"],
                end_date=edu["end_date"]
            )
            db.add(education)
            
        # Add skills
        for skill_name in cv_data["skills"]:
            # Get or create skill
            skill = db.query(Skill).filter_by(name=skill_name).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.add(skill)
                db.flush()
                
            # Link skill to employee
            employee_skill = EmployeeSkill(
                employee_id=employee.id,
                skill_id=skill.id
            )
            db.add(employee_skill)
            
        db.commit()
        return {"success": True, "employee_id": employee.id}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing CV {file_path}: {str(e)}")
        return {"success": False, "error": str(e)}

def process_assessment(db: Session, file_path: str) -> Dict[str, Any]:
    """
    Process an assessment file and store data in the database.
    
    Args:
        db: Database session
        file_path: Path to assessment file
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Validate file
        is_valid, error = validate_file(file_path)
        if not is_valid:
            return {"success": False, "error": error}
            
        # Read and parse assessment
        with open(file_path, 'r', encoding='utf-8') as f:
            assessment_text = f.read()
            
        parser = AssessmentParser()
        assessment_data = parser.parse_assessment(assessment_text)
        
        # Find employee by name
        candidate_name = assessment_data["candidate_info"]["name"]
        employee = db.query(Employee).filter_by(name=candidate_name).first()
        
        if not employee:
            return {"success": False, "error": f"Employee not found: {candidate_name}"}
            
        # Create assessment record
        assessment = Assessment(
            employee_id=employee.id,
            assessment_date=assessment_data["candidate_info"]["assessment_date"],
            hpi_score=assessment_data["scores"]["hpi"],
            hds_score=assessment_data["scores"]["hds"],
            mvpi_score=assessment_data["scores"]["mvpi"],
            recommendations=assessment_data["recommendations"],
            summary=assessment_data["summary"]
        )
        
        db.add(assessment)
        db.commit()
        
        return {"success": True, "assessment_id": assessment.id}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing assessment {file_path}: {str(e)}")
        return {"success": False, "error": str(e)}

def process_directory(import_dir: str = "data/imports") -> List[Dict[str, Any]]:
    """
    Process all files in the import directory.
    
    Args:
        import_dir: Directory containing files to process
        
    Returns:
        List of processing results
    """
    results = []
    
    # Create database tables if they don't exist
    create_tables()
    
    # Process each file
    for filename in os.listdir(import_dir):
        file_path = os.path.join(import_dir, filename)
        
        # Skip if not a file
        if not os.path.isfile(file_path):
            continue
            
        db = next(get_db())
        try:
            # Determine file type and process accordingly
            if "assessment" in filename.lower():
                result = process_assessment(db, file_path)
            else:
                result = process_cv(db, file_path)
                
            results.append({
                "file": filename,
                **result
            })
            
        finally:
            db.close()
            
    return results

if __name__ == "__main__":
    # Process all files in the import directory
    results = process_directory()

