#!/usr/bin/env python3
"""
Hybrid Query Service - Combines database filtering with vector search for optimal results
"""

from typing import List, Dict, Any

from backend.services.employee.employee_database import EmployeeDatabase
from backend.services.rag.vector_store import VectorStore
from frontend.utils.error_handler import logger
from frontend.config.config_loader import get_config

class HybridQueryService:
    """Service that combines database queries with vector search for better results."""
    
    def __init__(self):
        self.emp_db = EmployeeDatabase()
        self.vector_store = VectorStore()
    
    def find_employees_by_numerical_criteria(self, field: str, criteria: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find employees based on numerical criteria.
        
        Args:
            field: The metadata field to filter on (e.g., 'hogan_hpi_adjustment')
            criteria: The criteria (e.g., 'highest', 'lowest', '>80', '<50')
            limit: Maximum number of results
            
        Returns:
            List of employees matching the criteria
        """
        employees = self.emp_db.get_all_employees()
        
        # Filter employees who have the specified field
        employees_with_field = []
        for emp in employees:
            value = emp['metadata'].get(field)
            if value is not None and isinstance(value, (int, float)):
                employees_with_field.append({
                    'employee': emp,
                    'value': value
                })
        
        # Apply criteria
        if criteria == 'highest':
            employees_with_field.sort(key=lambda x: x['value'], reverse=True)
        elif criteria == 'lowest':
            employees_with_field.sort(key=lambda x: x['value'])
        elif criteria.startswith('>'):
            threshold = float(criteria[1:])
            employees_with_field = [e for e in employees_with_field if e['value'] > threshold]
            employees_with_field.sort(key=lambda x: x['value'], reverse=True)
        elif criteria.startswith('<'):
            threshold = float(criteria[1:])
            employees_with_field = [e for e in employees_with_field if e['value'] < threshold]
            employees_with_field.sort(key=lambda x: x['value'])
        
        # Return top results
        results = []
        for item in employees_with_field[:limit]:
            emp = item['employee']
            results.append({
                'employee_id': emp['id'],
                'name': emp['name'],
                'value': item['value'],
                'metadata': emp['metadata']
            })
        
        return results
    
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
                        'metadata': emp_data['metadata'],
                        'score': result.get('score', 0.0)
                    })
            
            return {
                'results': results,
                'strategy_used': 'vector_search',
                'total_found': len(results)
            }
            
        except Exception as e:
            print(f"Error in hybrid search: {e}")
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