#!/usr/bin/env python3

from backend.db.session import SessionLocal
from backend.db.models import Employee, EmployeeAssessment, HoganScore

def check_ahmed_scores():
    db = SessionLocal()
    try:
        # Find Ahmed Al-Ahmad
        emp = db.query(Employee).filter(Employee.full_name.ilike('%Ahmed Al-Ahmad%')).first()
        print(f'Employee: {emp.full_name if emp else "Not found"}')
        print(f'Employee ID: {emp.id if emp else "N/A"}')
        
        if emp:
            # Get all Hogan scores for this employee
            all_hogan_scores = db.query(HoganScore).join(EmployeeAssessment).filter(
                EmployeeAssessment.employee_id == emp.id
            ).all()
            
            print(f'\nAll Hogan scores found: {len(all_hogan_scores)}')
            for score in all_hogan_scores:
                print(f'  - {score.trait}: {score.score} (Assessment ID: {score.assessment_id})')
            
            # Get all assessments for this employee
            all_assessments = db.query(EmployeeAssessment).filter(
                EmployeeAssessment.employee_id == emp.id
            ).all()
            
            print(f'\nAll assessments found: {len(all_assessments)}')
            for assessment in all_assessments:
                print(f'  - {assessment.assessment_type}: {assessment.source_filename}')
                
            # Check for orphaned Hogan scores (without assessment)
            orphaned_scores = db.query(HoganScore).filter(
                HoganScore.assessment_id.is_(None)
            ).all()
            
            print(f'\nOrphaned Hogan scores (no assessment): {len(orphaned_scores)}')
            for score in orphaned_scores:
                print(f'  - {score.trait}: {score.score}')
                
    finally:
        db.close()

if __name__ == "__main__":
    check_ahmed_scores() 