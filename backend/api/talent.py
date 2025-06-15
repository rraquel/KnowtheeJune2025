from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import tempfile
import os

from database import get_db
from database.models import Employee
from services.parser.cv_parser import CVParser
from services.parser.assessment_parser import AssessmentParser
from utils.validators import validate_file

router = APIRouter()

@router.post("/upload/cv")
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Upload and process a CV file.
    
    Args:
        file: Uploaded CV file
        db: Database session
        
    Returns:
        Processing result with employee ID if successful
    """
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
        
    try:
        # Validate file
        is_valid, error = validate_file(temp_path)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
            
        # Process CV
        with open(temp_path, 'r', encoding='utf-8') as f:
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
        db.commit()
        
        return {"success": True, "employee_id": str(employee.id)}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        os.unlink(temp_path)

@router.post("/upload/assessment")
async def upload_assessment(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Upload and process an assessment file.
    
    Args:
        file: Uploaded assessment file
        db: Database session
        
    Returns:
        Processing result with assessment ID if successful
    """
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
        
    try:
        # Validate file
        is_valid, error = validate_file(temp_path)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
            
        # Process assessment
        with open(temp_path, 'r', encoding='utf-8') as f:
            assessment_text = f.read()
            
        parser = AssessmentParser()
        assessment_data = parser.parse_assessment(assessment_text)
        
        # Find employee by name
        candidate_name = assessment_data["candidate_info"]["name"]
        employee = db.query(Employee).filter_by(name=candidate_name).first()
        
        if not employee:
            raise HTTPException(status_code=404, detail=f"Employee not found: {candidate_name}")
            
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
        
        return {"success": True, "assessment_id": str(assessment.id)}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        os.unlink(temp_path)

@router.get("/employees")
async def list_employees(
    db: Session = Depends(get_db)
) -> List[Dict]:
    """
    List all employees.
    
    Args:
        db: Database session
        
    Returns:
        List of employee records
    """
    employees = db.query(Employee).all()
    return [
        {
            "id": str(emp.id),
            "name": emp.name,
            "email": emp.email,
            "location": emp.location,
            "summary": emp.summary,
            "skills": [skill.skill.name for skill in emp.skills],
            "assessment_count": len(emp.assessments)
        }
        for emp in employees
    ] 