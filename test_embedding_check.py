#!/usr/bin/env python3
"""
Test script to check if Carlos Garcia's data is properly embedded
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.rag.vector_store import VectorStore
from backend.services.data_access.employee_database import EmployeeDatabase
from backend.db.session import SessionLocal
from backend.db.models import Employee, EmbeddingDocument, EmbeddingChunk

def check_carlos_garcia_embedding():
    """Check if Carlos Garcia's data is properly embedded"""
    
    print("=== CHECKING CARLOS GARCIA EMBEDDING ===")
    
    # Initialize services
    vector_store = VectorStore()
    employee_db = EmployeeDatabase()
    
    # Get Carlos Garcia from database
    all_employees = employee_db.get_all_employees()
    carlos_garcia = None
    
    for emp in all_employees:
        if "carlos garcia" in emp["name"].lower():
            carlos_garcia = emp
            break
    
    if not carlos_garcia:
        print("❌ Carlos Garcia not found in employee database")
        return
    
    print(f"✅ Found Carlos Garcia in database: {carlos_garcia['name']} (ID: {carlos_garcia['id']})")
    
    # Check if Carlos Garcia has embeddings in the database
    print("\n=== CHECKING EMBEDDINGS IN DATABASE ===")
    db = SessionLocal()
    try:
        # Check EmbeddingDocument table
        documents = db.query(EmbeddingDocument).filter(
            EmbeddingDocument.employee_id == carlos_garcia['id']
        ).all()
        
        print(f"Found {len(documents)} embedding documents for Carlos Garcia")
        
        if documents:
            for i, doc in enumerate(documents[:3]):  # Show first 3
                print(f"  {i+1}. Document: {doc.source_filename}")
                print(f"     Type: {doc.document_type}")
                print(f"     Created: {doc.created_at}")
                
                # Check chunks for this document
                chunks = db.query(EmbeddingChunk).filter(
                    EmbeddingChunk.external_document_id == doc.external_document_id
                ).count()
                print(f"     Has {chunks} chunks")
        else:
            print("❌ No embedding documents found for Carlos Garcia")
            
        # Check if Carlos Garcia exists in Employee table
        employee = db.query(Employee).filter(
            Employee.id == carlos_garcia['id']
        ).first()
        
        if employee:
            print(f"✅ Carlos Garcia found in Employee table: {employee.full_name}")
        else:
            print("❌ Carlos Garcia NOT found in Employee table")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        db.close()
    
    # Test direct vector search with Carlos Garcia's ID
    print(f"\n=== TESTING DIRECT VECTOR SEARCH ===")
    try:
        # Get all embeddings for Carlos Garcia
        results = vector_store.search_employees_by_id(carlos_garcia['id'], n_results=10)
        print(f"Direct search by ID found {len(results)} results")
        
        if results:
            for i, result in enumerate(results[:3]):
                print(f"  {i+1}. {result.get('content', 'No content')[:100]}...")
        else:
            print("❌ No results found in direct search by ID")
            
    except Exception as e:
        print(f"❌ Error in direct vector search: {e}")
    
    # Check what other Carlos employees are found
    print(f"\n=== CHECKING OTHER CARLOS EMPLOYEES ===")
    carlos_employees = []
    for emp in all_employees:
        if "carlos" in emp["name"].lower():
            carlos_employees.append(emp)
    
    print(f"Found {len(carlos_employees)} Carlos employees:")
    for emp in carlos_employees:
        print(f"  - {emp['name']} (ID: {emp['id']})")
        
        # Check if this Carlos has embedding documents
        db = SessionLocal()
        try:
            documents = db.query(EmbeddingDocument).filter(
                EmbeddingDocument.employee_id == emp['id']
            ).count()
            print(f"    Has {documents} embedding documents")
        except Exception as e:
            print(f"    Error checking documents: {e}")
        finally:
            db.close()

if __name__ == "__main__":
    check_carlos_garcia_embedding() 