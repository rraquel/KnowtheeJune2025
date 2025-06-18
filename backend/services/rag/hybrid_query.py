#!/usr/bin/env python3
"""
Hybrid Query Service - Combines database filtering with vector search for optimal results
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.db.models import Employee, EmployeeAssessment, HoganScore, IDIScore
from backend.services.data_access.employee_database import EmployeeDatabase
from backend.services.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

class HybridQueryService:
    """Service that combines database queries with vector search for better results."""
    
    def __init__(self):
        self.emp_db = EmployeeDatabase()
        self.vector_store = VectorStore()
    
    def find_employees_by_numerical_criteria(self, field: str, criteria: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find employees based on numerical criteria from the database.
        
        Args:
            field: The assessment field to filter on (e.g., 'hogan_hpi_adjustment')
            criteria: The criteria (e.g., 'highest', 'lowest', '>80', '<50')
            limit: Maximum number of results
            
        Returns:
            List of employees matching the criteria
        """
        try:
            db = SessionLocal()
            
            # Parse the field to determine assessment type and trait
            if field.startswith('hogan_hpi_'):
                assessment_type = 'HPI'
                trait = field.replace('hogan_hpi_', '')
            elif field.startswith('hogan_hds_'):
                assessment_type = 'HDS'
                trait = field.replace('hogan_hds_', '')
            elif field.startswith('hogan_mvpi_'):
                assessment_type = 'MVPI'
                trait = field.replace('hogan_mvpi_', '')
            elif field.startswith('idi_'):
                assessment_type = 'IDI'
                trait = field.replace('idi_', '')
            else:
                # Default to HPI if field format is unclear
                assessment_type = 'HPI'
                trait = field
            
            # Query the database for employees with the specified assessment scores
            query = db.query(Employee, HoganScore.score).join(
                EmployeeAssessment, Employee.id == EmployeeAssessment.employee_id
            ).join(
                HoganScore, EmployeeAssessment.id == HoganScore.assessment_id
            ).filter(
                EmployeeAssessment.assessment_type == assessment_type,
                HoganScore.trait == trait
            )
            
            # Apply criteria
            if criteria == 'highest':
                query = query.order_by(HoganScore.score.desc())
            elif criteria == 'lowest':
                query = query.order_by(HoganScore.score.asc())
            elif criteria.startswith('>'):
                threshold = float(criteria[1:])
                query = query.filter(HoganScore.score > threshold).order_by(HoganScore.score.desc())
            elif criteria.startswith('<'):
                threshold = float(criteria[1:])
                query = query.filter(HoganScore.score < threshold).order_by(HoganScore.score.asc())
            
            # Get results
            results = []
            for emp, score in query.limit(limit).all():
                results.append({
                    'employee_id': str(emp.id),
                    'name': emp.full_name,
                    'value': score,
                    'assessment_type': assessment_type,
                    'trait': trait
                })
            
            db.close()
            return results
            
        except Exception as e:
            logger.error(f"Error in find_employees_by_numerical_criteria: {e}")
            return []
    
    def search_employees(self, query: str, filters: Dict[str, Any] = None, n_results: int = 10) -> Dict[str, Any]:
        """
        Enhanced employee search that combines filtering with vector search.
        
        Args:
            query: Search query
            filters: Optional filters to apply
            n_results: Maximum number of results
            
        Returns:
            Dictionary with search results and metadata
        """
        # For now, use basic vector search
        # This can be enhanced later with more sophisticated filtering
        try:
            vector_results = self.vector_store.search_employees(query, n_results=n_results)
            
            results = []
            for result in vector_results:
                emp_data = self.emp_db.get_employee(result['employee_id'])
                if emp_data:
                    results.append({
                        'employee_id': result['employee_id'],
                        'name': emp_data['name'],
                        'score': result.get('score', 0.0)
                    })
            
            return {
                'results': results,
                'strategy_used': 'vector_search',
                'total_found': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return {
                'results': [],
                'strategy_used': 'error',
                'total_found': 0,
                'error': str(e)
            }
    
    def query_highest_adjustment_scores(self, limit: int = 5) -> str:
        """
        Find employees with highest adjustment scores and format for AI response.
        
        Args:
            limit: Number of top employees to return
            
        Returns:
            Formatted string with employee names and scores
        """
        # Find employees with highest adjustment scores
        top_employees = self.find_employees_by_numerical_criteria(
            field='hogan_hpi_adjustment',
            criteria='highest',
            limit=limit
        )
        
        if not top_employees:
            return "No employees found with adjustment scores."
        
        # Format the response
        response_lines = [f"The {limit} employees with the highest Hogan 'adjustment' scores are:"]
        response_lines.append("")
        
        for i, emp in enumerate(top_employees, 1):
            response_lines.append(f"{i}. {emp['name']} - {emp['value']}")
        
        response_lines.append("")
        response_lines.append("These scores reflect their ability to maintain emotional stability and adaptability in various situations, which is crucial for effective leadership and organizational effectiveness.")
        
        return "\n".join(response_lines) 