#!/usr/bin/env python3
"""
Debug script to check Carlos Garcia's actual data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.data_access.employee_database import EmployeeDatabase

def debug_carlos_data():
    """Check Carlos Garcia's actual data in the database"""
    
    print("=== DEBUGGING CARLOS GARCIA DATA ===")
    
    # Initialize the employee database
    employee_db = EmployeeDatabase()
    
    # Get Carlos Garcia's data
    all_employees = employee_db.get_all_employees()
    carlos_employees = [emp for emp in all_employees if "carlos" in emp["name"].lower()]
    
    print(f"\nAll Carlos employees found: {[emp['name'] for emp in carlos_employees]}")
    
    # Get detailed data for Carlos Garcia
    carlos_garcia = None
    for emp in carlos_employees:
        if emp["name"] == "Carlos Garcia":
            carlos_garcia = emp
            break
    
    if carlos_garcia:
        print(f"\nCarlos Garcia ID: {carlos_garcia['id']}")
        
        # Get full employee data
        full_data = employee_db.get_employee(carlos_garcia['id'])
        
        print(f"\nFull Carlos Garcia Data:")
        print(f"Name: {full_data.get('name', 'Not found')}")
        print(f"Email: {full_data.get('email', 'Not found')}")
        print(f"Department: {full_data.get('department', 'Not found')}")
        print(f"Position: {full_data.get('current_position', 'Not found')}")
        print(f"Location: {full_data.get('location', 'Not found')}")
        
        # Check experiences
        experiences = full_data.get('experiences', [])
        print(f"\nWork Experiences ({len(experiences)} entries):")
        for i, exp in enumerate(experiences, 1):
            print(f"  {i}. {exp.get('title', 'Unknown')} at {exp.get('company', 'Unknown')}")
            if exp.get('start_date') or exp.get('end_date'):
                dates = []
                if exp.get('start_date'):
                    dates.append(str(exp['start_date']))
                if exp.get('end_date'):
                    dates.append(str(exp['end_date']))
                print(f"     Dates: {' - '.join(dates)}")
            if exp.get('description'):
                print(f"     Description: {exp['description'][:100]}...")
        
        # Check education
        education = full_data.get('education', [])
        print(f"\nEducation ({len(education)} entries):")
        for i, edu in enumerate(education, 1):
            print(f"  {i}. {edu.get('institution', 'Unknown')}")
            if edu.get('degree'):
                print(f"     Degree: {edu['degree']}")
            if edu.get('field'):
                print(f"     Field: {edu['field']}")
        
        # Check skills
        skills = full_data.get('skills', [])
        print(f"\nSkills ({len(skills)} entries):")
        for i, skill in enumerate(skills, 1):
            print(f"  {i}. {skill.get('skill', 'Unknown')} ({skill.get('type', 'Unknown')})")
        
        # Check assessments
        assessments = full_data.get('assessments', [])
        print(f"\nAssessments ({len(assessments)} entries):")
        for i, assessment in enumerate(assessments, 1):
            print(f"  {i}. {assessment.get('assessment_type', 'Unknown')} ({assessment.get('assessment_date', 'Unknown date')})")
        
        # Check Hogan scores
        hogan_scores = full_data.get('hogan_scores', [])
        print(f"\nHogan Scores ({len(hogan_scores)} entries):")
        for score in hogan_scores:
            print(f"  {score.get('trait', 'Unknown')}: {score.get('score', 'Unknown')}")
        
        # Check IDI scores
        idi_scores = full_data.get('idi_scores', [])
        print(f"\nIDI Scores ({len(idi_scores)} entries):")
        for score in idi_scores:
            print(f"  {score.get('dimension', 'Unknown')}: {score.get('score', 'Unknown')}")
        
    else:
        print("Carlos Garcia not found in database")

if __name__ == "__main__":
    debug_carlos_data() 