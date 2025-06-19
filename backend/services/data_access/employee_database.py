import os
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from backend.db.session import SessionLocal
from backend.db.models import (
    Employee, EmployeeExperience, EmployeeEducation, EmployeeAssessment,
    HoganScore, IDIScore, EmployeeCV, EmployeeSkill
)

logger = logging.getLogger(__name__)

class EmployeeDatabase:
    def __init__(self):
        """Initialize the employee database with error handling."""
        self._employee_name_index = {}  # Cache for employee name lookups
        self._index_initialized = False
        
    def _initialize_name_index(self):
        """Initialize the employee name index for faster lookups."""
        try:
            with SessionLocal() as db:
                employees = db.query(Employee).all()
                self._employee_name_index = {
                    emp.full_name.lower(): {
                        "id": str(emp.id),
                        "name": emp.full_name,
                        "email": emp.email,
                        "department": emp.department
                    }
                    for emp in employees
                }
                self._index_initialized = True
                logger.info(f"Initialized employee name index with {len(employees)} employees")
        except Exception as e:
            logger.error(f"Failed to initialize employee name index: {e}")
            self._employee_name_index = {}

    def get_all_employees(self) -> List[Dict[str, Any]]:
        """Return list of all employees with id, name, position, etc."""
        try:
            with SessionLocal() as db:
                employees = db.query(Employee).all()
                result = [
                    {
                        "id": str(emp.id),
                        "name": emp.full_name,
                        "email": emp.email,
                        "location": emp.location,
                        "current_position": emp.current_position,
                        "department": emp.department
                    }
                    for emp in employees
                ]
                logger.debug(f"Retrieved {len(result)} employees from database")
                return result
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_all_employees: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_all_employees: {e}")
            return []

    def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Return full profile including name, experiences, education, assessments, metadata."""
        try:
            with SessionLocal() as db:
                emp = db.query(Employee).filter(Employee.id == employee_id).first()
                if not emp:
                    logger.warning(f"Employee with ID {employee_id} not found")
                    return None
                
                # Get related data with error handling
                experiences = self._get_employee_experiences(db, employee_id)
                education = self._get_employee_education(db, employee_id)
                skills = self._get_employee_skills(db, employee_id)
                assessments = self._get_employee_assessments(db, employee_id)
                hogan_scores = self._get_employee_hogan_scores(db, employee_id)
                idi_scores = self._get_employee_idi_scores(db, employee_id)
                cvs = self._get_employee_cvs(db, employee_id)
                
                result = {
                    "id": str(emp.id),
                    "name": emp.full_name,
                    "email": emp.email,
                    "location": emp.location,
                    "current_position": emp.current_position,
                    "department": emp.department,
                    "experiences": experiences,
                    "education": education,
                    "skills": skills,
                    "assessments": assessments,
                    "hogan_scores": hogan_scores,  # Now properly structured
                    "idi_scores": idi_scores,      # Now properly structured
                    "cvs": cvs
                }
                
                logger.debug(f"Retrieved complete profile for employee {emp.full_name}")
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_employee for ID {employee_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_employee for ID {employee_id}: {e}")
            return None

    def _get_employee_experiences(self, db: Session, employee_id: str) -> List[Dict[str, Any]]:
        """Get employee experiences with error handling."""
        try:
            experiences = db.query(EmployeeExperience).filter(
                EmployeeExperience.employee_id == employee_id
            ).all()
            return [
                {
                    "company": exp.company,
                    "title": exp.title,
                    "start_date": str(exp.start_date) if exp.start_date else None,
                    "end_date": str(exp.end_date) if exp.end_date else None,
                    "description": exp.description
                } for exp in experiences
            ]
        except Exception as e:
            logger.error(f"Error getting experiences for employee {employee_id}: {e}")
            return []

    def _get_employee_education(self, db: Session, employee_id: str) -> List[Dict[str, Any]]:
        """Get employee education with error handling."""
        try:
            education = db.query(EmployeeEducation).filter(
                EmployeeEducation.employee_id == employee_id
            ).all()
            return [
                {
                    "institution": edu.institution,
                    "degree": edu.degree,
                    "field": edu.field,
                    "start_date": str(edu.start_date) if edu.start_date else None,
                    "end_date": str(edu.end_date) if edu.end_date else None
                } for edu in education
            ]
        except Exception as e:
            logger.error(f"Error getting education for employee {employee_id}: {e}")
            return []

    def _get_employee_skills(self, db: Session, employee_id: str) -> List[Dict[str, Any]]:
        """Get employee skills with error handling."""
        try:
            skills = db.query(EmployeeSkill).filter(
                EmployeeSkill.employee_id == employee_id
            ).all()
            return [
                {
                    "skill": skill.skill,
                    "type": skill.type
                } for skill in skills
            ]
        except Exception as e:
            logger.error(f"Error getting skills for employee {employee_id}: {e}")
            return []

    def _get_employee_assessments(self, db: Session, employee_id: str) -> List[Dict[str, Any]]:
        """Get employee assessments with error handling."""
        try:
            assessments = db.query(EmployeeAssessment).filter(
                EmployeeAssessment.employee_id == employee_id
            ).all()
            return [
                {
                    "type": ass.assessment_type,
                    "date": str(ass.assessment_date) if ass.assessment_date else None,
                    "status": ass.status,
                    "notes": ass.notes,
                    "source_filename": ass.source_filename
                } for ass in assessments
            ]
        except Exception as e:
            logger.error(f"Error getting assessments for employee {employee_id}: {e}")
            return []

    def _get_employee_hogan_scores(self, db: Session, employee_id: str) -> Dict[str, Dict[str, float]]:
        """Get employee Hogan scores properly structured by assessment type."""
        try:
            # Get all Hogan assessments for the employee
            hogan_assessments = db.query(EmployeeAssessment).filter(
                EmployeeAssessment.employee_id == employee_id,
                EmployeeAssessment.assessment_type.in_(['HPI', 'HDS', 'MVPI', 'Hogan'])
            ).all()
            
            structured_scores = {
                "HPI (Personality Inventory)": {},
                "HDS (Development Survey)": {},
                "MVPI (Values & Preferences)": {}
            }
            
            for assessment in hogan_assessments:
                hogan_scores = db.query(HoganScore).filter(
                    HoganScore.assessment_id == assessment.id
                ).all()
                
                # Determine assessment type for categorization
                if assessment.assessment_type == 'HPI' or 'personality' in assessment.source_filename.lower():
                    category = "HPI (Personality Inventory)"
                elif assessment.assessment_type == 'HDS' or 'development' in assessment.source_filename.lower():
                    category = "HDS (Development Survey)"
                elif assessment.assessment_type == 'MVPI' or 'values' in assessment.source_filename.lower():
                    category = "MVPI (Values & Preferences)"
                else:
                    # Default to HPI if unclear
                    category = "HPI (Personality Inventory)"
                
                for score in hogan_scores:
                    structured_scores[category][score.trait] = score.score
            
            # Remove empty categories
            structured_scores = {k: v for k, v in structured_scores.items() if v}
            
            return structured_scores
            
        except Exception as e:
            logger.error(f"Error getting Hogan scores for employee {employee_id}: {e}")
            return {}

    def _get_employee_idi_scores(self, db: Session, employee_id: str) -> Dict[str, Dict[str, float]]:
        """Get employee IDI scores properly structured by assessment."""
        try:
            idi_assessments = db.query(EmployeeAssessment).filter(
                EmployeeAssessment.employee_id == employee_id,
                EmployeeAssessment.assessment_type == 'IDI'
            ).all()
            
            structured_scores = {}
            
            for assessment in idi_assessments:
                idi_scores = db.query(IDIScore).filter(
                    IDIScore.assessment_id == assessment.id
                ).all()
                
                assessment_scores = {}
                for score in idi_scores:
                    key = f"{score.category}_{score.dimension}"
                    assessment_scores[key] = score.score
                
                if assessment_scores:
                    structured_scores[assessment.source_filename] = assessment_scores
            
            return structured_scores
            
        except Exception as e:
            logger.error(f"Error getting IDI scores for employee {employee_id}: {e}")
            return {}

    def _get_employee_cvs(self, db: Session, employee_id: str) -> List[Dict[str, Any]]:
        """Get employee CVs with error handling."""
        try:
            cvs = db.query(EmployeeCV).filter(
                EmployeeCV.employee_id == employee_id
            ).all()
            return [
                {
                    "filename": cv.filename,
                    "upload_date": str(cv.upload_date) if cv.upload_date else None,
                    "source": cv.source
                } for cv in cvs
            ]
        except Exception as e:
            logger.error(f"Error getting CVs for employee {employee_id}: {e}")
            return []

    def find_employees_by_name(self, name_query: str, fuzzy_match: bool = True) -> List[Dict[str, Any]]:
        """Find employees by name with fuzzy matching support."""
        try:
            if not self._index_initialized:
                self._initialize_name_index()
            
            name_query_lower = name_query.lower().strip()
            matches = []
            
            if fuzzy_match:
                # Fuzzy matching using simple string operations
                for emp_name, emp_data in self._employee_name_index.items():
                    # Exact match
                    if name_query_lower == emp_name:
                        matches.append(emp_data)
                        continue
                    
                    # Partial match (first name or last name)
                    name_parts = emp_name.split()
                    query_parts = name_query_lower.split()
                    
                    # Check if any part of the query matches any part of the name
                    for query_part in query_parts:
                        for name_part in name_parts:
                            if query_part in name_part or name_part in query_part:
                                if emp_data not in matches:
                                    matches.append(emp_data)
                                break
            else:
                # Exact matching only
                if name_query_lower in self._employee_name_index:
                    matches.append(self._employee_name_index[name_query_lower])
            
            logger.debug(f"Found {len(matches)} employees matching '{name_query}'")
            return matches
            
        except Exception as e:
            logger.error(f"Error in find_employees_by_name for '{name_query}': {e}")
            return []

    def get_employee_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get employee by exact name match."""
        try:
            matches = self.find_employees_by_name(name, fuzzy_match=False)
            if matches:
                return self.get_employee(matches[0]["id"])
            return None
        except Exception as e:
            logger.error(f"Error getting employee by name '{name}': {e}")
            return None

    def refresh_name_index(self):
        """Refresh the employee name index."""
        self._index_initialized = False
        self._initialize_name_index()

    def _extract_hogan_measures(self, text):
        """Extract Hogan measures from text. (To be implemented)"""
        # Minimal implementation: return empty dict
        return {}

    def _extract_idi_measures(self, text):
        """Extract IDI measures from text. (To be implemented)"""
        # Minimal implementation: return empty dict
        return {} 