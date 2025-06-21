# individual_profile_services.py
import os
import tempfile
from typing import List, Any
from .data_access.employee_database import EmployeeDatabase

def save_uploaded_files(uploaded_files: List[Any]) -> List[str]:
    """
    Save uploaded files to a temporary directory and return the file paths.
    
    Args:
        uploaded_files: List of Streamlit uploaded file objects
        
    Returns:
        List of saved file paths
    """
    saved_paths = []
    
    # Create a temporary directory for uploaded files
    temp_dir = tempfile.mkdtemp(prefix="knowthee_uploads_")
    
    for uploaded_file in uploaded_files:
        if uploaded_file is not None:
            # Create a safe filename
            safe_filename = uploaded_file.name.replace(" ", "_").replace("/", "_")
            file_path = os.path.join(temp_dir, safe_filename)
            
            # Save the file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            saved_paths.append(file_path)
    
    return saved_paths

class IndividualProfileService:
    def __init__(self, db: EmployeeDatabase = None):
        self.db = db or EmployeeDatabase()
    
    def get_employee_profile(self, full_name: str) -> dict:
        """Get employee profile by name."""
        employee = self.db.get_employee_by_name(full_name)
        if employee is not None:
            return employee
        return None
    
    def analyze_uploaded_files(self, file_paths: List[str]) -> dict:
        """
        Analyze uploaded files for individual profile insights.
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        # This would integrate with the RAG system or other analysis tools
        # For now, return a placeholder structure
        return {
            "files_processed": len(file_paths),
            "analysis_status": "pending",
            "insights": [],
            "recommendations": []
        } 