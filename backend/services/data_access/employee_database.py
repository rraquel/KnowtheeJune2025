import os
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.db.models import (
    Employee, EmployeeExperience, EmployeeEducation, EmployeeAssessment,
    HoganScore, IDIScore, EmployeeCV
)

class EmployeeDatabase:
    def __init__(self):
        # Optionally, you can add custom init logic or config here
        pass

    def get_all_employees(self):
        """Return list of all employees with id, name, position, etc."""
        with SessionLocal() as db:
            employees = db.query(Employee).all()
            return [
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

    def get_employee(self, employee_id):
        """Return full profile including name, experiences, education, assessments, metadata."""
        with SessionLocal() as db:
            emp = db.query(Employee).filter(Employee.id == employee_id).first()
            if not emp:
                return None
            # Experiences
            experiences = db.query(EmployeeExperience).filter(EmployeeExperience.employee_id == employee_id).all()
            # Education
            education = db.query(EmployeeEducation).filter(EmployeeEducation.employee_id == employee_id).all()
            # Assessments
            assessments = db.query(EmployeeAssessment).filter(EmployeeAssessment.employee_id == employee_id).all()
            # Hogan Scores
            hogan_scores = db.query(HoganScore).join(EmployeeAssessment, HoganScore.assessment_id == EmployeeAssessment.id).filter(EmployeeAssessment.employee_id == employee_id).all()
            # IDI Scores
            idi_scores = db.query(IDIScore).join(EmployeeAssessment, IDIScore.assessment_id == EmployeeAssessment.id).filter(EmployeeAssessment.employee_id == employee_id).all()
            # CVs
            cvs = db.query(EmployeeCV).filter(EmployeeCV.employee_id == employee_id).all()
            return {
                "id": str(emp.id),
                "name": emp.full_name,
                "email": emp.email,
                "location": emp.location,
                "current_position": emp.current_position,
                "department": emp.department,
                "experiences": [
                    {
                        "company": exp.company,
                        "title": exp.title,
                        "start_date": str(exp.start_date),
                        "end_date": str(exp.end_date),
                        "description": exp.description
                    } for exp in experiences
                ],
                "education": [
                    {
                        "institution": edu.institution,
                        "degree": edu.degree,
                        "field": edu.field,
                        "start_date": str(edu.start_date),
                        "end_date": str(edu.end_date)
                    } for edu in education
                ],
                "assessments": [
                    {
                        "type": ass.assessment_type,
                        "date": str(ass.assessment_date),
                        "status": ass.status,
                        "notes": ass.notes
                    } for ass in assessments
                ],
                "hogan_scores": [
                    {
                        "trait": hs.trait,
                        "score": hs.score
                    } for hs in hogan_scores
                ],
                "idi_scores": [
                    {
                        "category": idi.category,
                        "dimension": idi.dimension,
                        "score": idi.score
                    } for idi in idi_scores
                ],
                "cvs": [
                    {
                        "filename": cv.filename,
                        "upload_date": str(cv.upload_date),
                        "source": cv.source
                    } for cv in cvs
                ]
            }

    def _extract_hogan_measures(self, text):
        """Extract Hogan measures from text. (To be implemented)"""
        # Minimal implementation: return empty dict
        return {}

    def _extract_idi_measures(self, text):
        """Extract IDI measures from text. (To be implemented)"""
        # Minimal implementation: return empty dict
        return {} 