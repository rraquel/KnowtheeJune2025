# team_builder_service.py
from .data_access.employee_database import EmployeeDatabase
import pandas as pd
from typing import List

class TeamBuilderService:
    def __init__(self, db: EmployeeDatabase = None):
        self.db = db or EmployeeDatabase()

    def find_candidates_by_trait(self, trait: str, min_score: float) -> List[dict]:
        # Get all employees and filter by trait
        all_employees = self.db.get_all_employees()
        candidates = []
        
        for employee in all_employees:
            # Get full employee profile to check Hogan scores
            full_profile = self.db.get_employee(employee['id'])
            if full_profile and 'hogan_scores' in full_profile:
                # Check if trait exists in any Hogan assessment
                for assessment_type, scores in full_profile['hogan_scores'].items():
                    if trait in scores and scores[trait] >= min_score:
                        candidates.append(employee)
                        break
        
        return candidates

    def suggest_teams(self, size: int = 5) -> List[dict]:
        all_employees = self.db.get_all_employees()
        if len(all_employees) <= size:
            return all_employees
        
        # Simple random selection - could be enhanced with more sophisticated logic
        import random
        return random.sample(all_employees, size)
