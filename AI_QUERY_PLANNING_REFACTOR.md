# AI-Driven Query Planning Refactoring

## Overview

This document describes the refactoring of the backend query service to replace legacy pattern-matching logic with a cleaner, AI-driven architecture for handling structured assessment queries.

## What Was Changed

### Before: Legacy Pattern Matching
The original `process_complex_query()` method used rigid pattern matching with these legacy methods:
- `_find_direct_employee_match()` - Hardcoded employee name extraction
- `_handle_specific_assessment_query()` - Rigid assessment query handling
- `_extract_specific_score_request()` - Pattern-based score extraction

### After: AI-Driven Two-Step Architecture
The new system uses a clean two-step approach:

1. **Query Planning** (`_plan_query_with_ai()`)
   - Simulates LLM understanding of user intent
   - Extracts structured parameters (employees, traits, assessment types)
   - Returns a query plan dictionary

2. **Query Execution** (`_execute_query_plan()`)
   - Uses the plan to execute structured database queries
   - Bypasses RAG/vector search for structured data
   - Returns formatted responses

## New Architecture Components

### 1. Query Planning (`_plan_query_with_ai()`)

**Purpose**: Understand user intent and extract parameters

**Input**: Natural language query
**Output**: Structured query plan dictionary

**Example Plan**:
```python
{
    "intent": "compare_scores",
    "trait": "Prudence", 
    "assessment_type": "Hogan",
    "employees": ["Ahmed Al-Ahmad", "Lisa Wu"]
}
```

**Supported Intents**:
- `get_score` - Get specific score for employee(s)
- `get_all_scores` - Get all scores for employee(s)
- `compare_scores` - Compare scores between employees
- `rank_scores` - Rank employees by trait scores

### 2. Query Execution (`_execute_query_plan()`)

**Purpose**: Execute the planned query using database operations

**Methods**:
- `_execute_get_score()` - Get specific trait scores
- `_execute_get_all_scores()` - Get all assessment scores
- `_execute_compare_scores()` - Compare scores between employees
- `_execute_rank_scores()` - Rank employees by trait

### 3. Helper Methods

**Parameter Extraction**:
- `_extract_employee_names_from_query()` - Extract employee names
- `_extract_trait_from_query()` - Extract assessment traits
- `_extract_assessment_type_from_query()` - Determine assessment type

**Data Access**:
- `_get_employee_by_name()` - Get employee data by name
- `_get_specific_score()` - Get specific trait score
- `_get_all_scores_for_employee()` - Get all scores for employee

## Supported Query Types

### 1. Specific Score Queries
```
"What is Ahmed Al-Ahmad's Prudence score?"
"Show me Lisa's Ambition score"
```

### 2. Comparison Queries
```
"Who has the highest Prudence score among Ahmed and Lisa?"
"Compare the Sociability scores of Ahmed and Lisa"
```

### 3. Ranking Queries
```
"Show me the top 5 employees with highest Ambition scores"
"Who has the best Adjustment scores?"
```

### 4. All Scores Queries
```
"What are Ahmed's Hogan scores?"
"Show me Lisa's IDI scores"
```

## Database Integration

The new system uses the existing `EmployeeDatabase` class to access structured data:

- **Employees**: `employee_db.get_all_employees()`
- **Employee Data**: `employee_db.get_employee(employee_id)`
- **Scores**: Accessed via `hogan_scores` and `idi_scores` arrays

## Benefits of the New Architecture

### 1. **Cleaner Code**
- Removed 200+ lines of legacy pattern matching
- Clear separation of concerns (planning vs execution)
- More maintainable and extensible

### 2. **Better Performance**
- Bypasses RAG/vector search for structured queries
- Direct database access for assessment scores
- Faster response times for numerical queries

### 3. **Extensibility**
- Easy to add new query intents
- Simple to extend trait recognition
- Modular design for future enhancements

### 4. **Explainability**
- Clear query plans show system understanding
- Structured responses with confidence levels
- Better debugging and monitoring

## Testing

Run the test script to verify the new architecture:

```bash
python test_ai_query_planning.py
```

This will test various query types and show the planning and execution results.

## Future Enhancements

### 1. **Real LLM Integration**
Replace hardcoded rules with actual LLM calls:
```python
def _plan_query_with_ai(self, query: str) -> dict:
    # Call OpenAI API to understand intent
    response = self.client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a query planner..."},
            {"role": "user", "content": query}
        ]
    )
    return json.loads(response.choices[0].message.content)
```

### 2. **Additional Query Types**
- Team analysis queries
- Department comparisons
- Succession planning queries
- Risk assessment queries

### 3. **Enhanced Parameter Extraction**
- Fuzzy name matching
- Synonym recognition for traits
- Context-aware assessment type detection

## Migration Notes

### Removed Methods
- `_find_direct_employee_match()`
- `_handle_specific_assessment_query()`
- `_extract_specific_score_request()`

### Preserved Methods
- All conversation management methods
- RAG/vector search methods (for non-structured queries)
- Utility methods for token counting, etc.

### Backward Compatibility
The `process_complex_query()` method signature remains the same, ensuring existing frontend code continues to work.

## Example Usage

```python
# Initialize the system
employee_db = EmployeeDatabase()
query_system = RAGQuerySystem(employee_db=employee_db)

# Process a query
result = query_system.process_complex_query(
    "What is Ahmed Al-Ahmad's Prudence score?"
)

print(result["response"])
# Output: "Ahmed Al-Ahmad's Prudence score is 46.0."
```

## Conclusion

This refactoring successfully replaces the legacy pattern-matching approach with a cleaner, AI-driven architecture that is more maintainable, extensible, and performant. The new system provides better separation of concerns and sets the foundation for future enhancements with real LLM integration. 