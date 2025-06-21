# analytics_dashboard_service.py
from .data_access.employee_database import EmployeeDatabase
import pandas as pd
from typing import Dict, List, Any

class AnalyticsDashboardService:
    def __init__(self, db: EmployeeDatabase = None):
        self.db = db or EmployeeDatabase()

    def get_score_distribution(self, assessment_type: str, trait: str) -> List[float]:
        """Get distribution of scores for a specific trait across all employees."""
        all_employees = self.db.get_all_employees()
        scores = []
        
        for employee in all_employees:
            full_profile = self.db.get_employee(employee['id'])
            if full_profile and 'hogan_scores' in full_profile:
                if assessment_type in full_profile['hogan_scores']:
                    assessment_scores = full_profile['hogan_scores'][assessment_type]
                    if trait in assessment_scores:
                        scores.append(assessment_scores[trait])
        
        return scores

    def get_grouped_averages(self, group_by: str, assessment_type: str, trait: str) -> List[Dict[str, Any]]:
        """Get average scores grouped by department or other criteria."""
        all_employees = self.db.get_all_employees()
        grouped_data = {}
        
        for employee in all_employees:
            full_profile = self.db.get_employee(employee['id'])
            if full_profile and 'hogan_scores' in full_profile:
                if assessment_type in full_profile['hogan_scores']:
                    assessment_scores = full_profile['hogan_scores'][assessment_type]
                    if trait in assessment_scores:
                        group_value = employee.get(group_by, 'Unknown')
                        if group_value not in grouped_data:
                            grouped_data[group_value] = []
                        grouped_data[group_value].append(assessment_scores[trait])
        
        # Calculate averages
        result = []
        for group, scores in grouped_data.items():
            if scores:
                result.append({
                    group_by: group,
                    f"avg_{trait}": sum(scores) / len(scores),
                    "count": len(scores)
                })
        
        return result
