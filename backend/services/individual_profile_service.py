# individual_profile_service.py
from typing import Optional
from .data_access.employee_database import EmployeeDatabase

class IndividualProfileService:
    def __init__(self, db: Optional[EmployeeDatabase] = None):
        self.db = db or EmployeeDatabase()

    def get_employee_profile(self, full_name: str) -> Optional[dict]:
        employee = self.db.get_employee_by_name(full_name)
        if employee is not None:
            return employee
        return None
