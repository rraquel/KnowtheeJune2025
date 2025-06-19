#!/usr/bin/env python3

from backend.services.rag.query_service import RAGQuerySystem
import re

def debug_aisha_query():
    """Debug the Aisha query to see what's happening."""
    rag_system = RAGQuerySystem()
    
    query = "what is the ambition score of Aisha"
    print(f"Original query: {query}")
    
    # Test the AI query planning
    plan = rag_system._plan_query_with_ai(query)
    plan["query"] = query
    print(f"Plan: {plan}")
    
    # Test the regex extraction
    match = re.search(r"score of ([A-Za-z]+)", query.lower())
    print(f"Regex match: {match}")
    if match:
        first_name = match.group(1)
        print(f"Extracted first name: {first_name}")
    
    # Test employee extraction
    employees = rag_system._extract_employee_names_from_query(query)
    print(f"Extracted employees: {employees}")
    
    # Test the clarification logic
    if len(employees) > 1:
        first_names = [emp.split()[0].lower() for emp in employees]
        print(f"First names: {first_names}")
        
        if match:
            first_name = match.group(1)
            all_same = all(fn == first_name for fn in first_names)
            print(f"All same first name: {all_same}")
            
            if all_same:
                employee_list = ", ".join(employees)
                response = f"I found multiple employees with the name '{first_name.title()}': {employee_list}. Please specify which one you'd like to know about (e.g., 'Aisha Hassan' or 'Aisha Ibrahim')."
                print(f"Should return: {response}")
            else:
                print("Not all same first name, proceeding with normal execution")
    
    # Test the full execution
    print("\n=== Full execution ===")
    result = rag_system.query(query)
    print(f"Final result: {result}")

if __name__ == "__main__":
    debug_aisha_query() 