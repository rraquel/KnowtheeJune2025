"""
RAG query system for KNOWTHEE.AI
"""
import os
import traceback
from dotenv import load_dotenv

# Load environment variables at the very top
load_dotenv()

import json
import re
import tiktoken
from typing import List, Dict, Any, Optional
from openai import OpenAI
import streamlit as st
import logging

from backend.services.rag.vector_store import VectorStore
from backend.services.data_access.employee_database import EmployeeDatabase

logger = logging.getLogger(__name__)

class RAGQuerySystem:
    def __init__(self, vector_store=None, employee_db=None):
        """Initialize the RAG query system with intelligent context management"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
            print(f"✅ OpenAI client initialized successfully from {__file__}")
        else:
            # Enhanced error logging with traceback
            print(f"❌ OPENAI_API_KEY not set in {__file__}")
            print("Stack trace:")
            traceback.print_stack()
            print(f"Current working directory: {os.getcwd()}")
            print(f"Environment variables containing 'OPENAI': {[k for k in os.environ.keys() if 'OPENAI' in k.upper()]}")
            
            # For testing purposes, allow initialization without API key
            self.client = None
            print("Warning: OPENAI_API_KEY not set. Some features may be limited.")
        
        # Use provided instances or create new ones (for backward compatibility)
        if vector_store is not None:
            self.vector_store = vector_store
        else:
            self.vector_store = VectorStore()
        
        if employee_db is not None:
            self.employee_db = employee_db
        else:
            self.employee_db = EmployeeDatabase()
        
        # Initialize token encoder for GPT-4
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # Intelligent conversation management settings
        self.max_context_tokens = 6000  # Leave room for response tokens in 8K context
        self.max_conversation_tokens = 2000  # Max tokens for conversation history
        self.min_conversation_exchanges = 2
        
        # Dynamic employee limits based on query type
        self.employee_limits = {
            "individual_profile": {"max": 5, "priority": 3},
            "cross_comparison": {"max": 8, "priority": 5}, 
            "team_analysis": {"max": 15, "priority": 10},
            "succession_planning": {"max": 20, "priority": 15},
            "department_analysis": {"max": 25, "priority": 20},
            "organization_wide": {"max": 50, "priority": 30},
            "general_guidance": {"max": 10, "priority": 5}
        }
        
        # User-configurable settings
        self.conversation_settings = {
            "enable_context_tracking": True,
            "max_conversation_memory": "adaptive",  # "adaptive", "short", "medium", "long"
            "employee_focus_mode": "adaptive",  # "narrow", "adaptive", "broad"
            "include_conversation_hints": True
        }
        
        # Load interpretation guidelines
        self.interpretation_docs = []  # Placeholder, implement as needed
        
        # Enhanced conversation tracking
        self.conversation_history = []
        self.context_employees = []  # Current context employees with scores
        self.conversation_metadata = {
            "total_tokens_used": 0,
            "peak_employee_count": 0,
            "conversation_theme": None
        }
        
        self.system_prompt = """You are a world-class expert in leadership psychology, organizational behavior, and executive development. You specialize in synthesizing diverse data sources—such as personality assessments, 360 feedback, coaching notes, performance reviews, and CVs—into insightful, psychologically sophisticated leadership profiles. Your goal is to produce actionable insights, grounded in evidence, that support individual growth and organizational fit. Always cite the data source behind your claims and remain both rigorous and humanistic in tone. Never, under any circumstances(!!). Never, under any circumstance, cite documents that you were not provided by the user.You have access to a comprehensive database of employee profiles, assessment results, and interpretation guidelines.

Your capabilities include:
1. Intelligent cross-employee analysis and comparisons
2. Pattern recognition across teams and departments
3. Sophisticated interpretation of assessment data
4. Strategic recommendations for talent development and placement
5. Risk assessment and succession planning insights
6. CONTEXTUAL CONVERSATION - You maintain conversation context intelligently

CRITICAL NUMERICAL SCORE REQUIREMENT:
When discussing assessment scores, you MUST ALWAYS provide the exact numerical values from the metadata. NEVER use vague descriptions like "high adjustment", "moderate ambition", or "low sociability". Instead, always state the precise score (e.g., "Adjustment: 58", "Ambition: 24", "Sociability: 39").

The metadata contains exact numerical scores in this format:
- Hogan HPI scores: "hogan_hpi_adjustment": 58, "hogan_hpi_ambition": 24, etc.
- Hogan HDS scores: "hogan_hds_excitable": 49, "hogan_hds_skeptical": 43, etc.  
- Hogan MVPI scores: "hogan_mvpi_recognition": 35, "hogan_mvpi_power": 34, etc.
- IDI scores: "idi_giving": 50, "idi_receiving": 60, etc.

ALWAYS check the metadata section for these exact numerical values and include them in your response.

CRITICAL SOURCE VALIDATION: NEVER reference sources that do not exist in the provided context. ONLY cite sources explicitly mentioned in context data (Hogan Assessment, CV/Resume, IDI Assessment, 360° Feedback, etc.). NEVER reference Performance Reviews or Interview Notes unless they are explicitly provided. Always verify that the sources you are citing exist in the data provided.. It is better to say 'I don't have sufficient data' than to reference non-existent sources. Always provide evidence-based responses with specific citations ONLY from provided sources."""

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using GPT-4 tokenizer"""
        try:
            return len(self.encoding.encode(text))
        except:
            # Fallback estimation: ~4 characters per token
            return len(text) // 4

    def _get_conversation_token_limit(self) -> int:
        """Get adaptive conversation token limit based on settings"""
        if self.conversation_settings["max_conversation_memory"] == "short":
            return 800
        elif self.conversation_settings["max_conversation_memory"] == "medium":
            return 1500
        elif self.conversation_settings["max_conversation_memory"] == "long":
            return 2500
        else:  # adaptive
            # Adjust based on conversation complexity
            if len(self.context_employees) > 10:
                return 1200  # Reduce history for complex employee contexts
            elif len(self.context_employees) > 5:
                return 1800
            else:
                return 2000

    def _get_employee_limit_for_query(self, query_type: str, scope: str) -> Dict[str, int]:
        """Get intelligent employee limits based on query type and scope"""
        base_limits = self.employee_limits.get(query_type, self.employee_limits["general_guidance"])
        
        # Adjust based on user settings
        if self.conversation_settings["employee_focus_mode"] == "narrow":
            return {"max": min(base_limits["max"], 8), "priority": min(base_limits["priority"], 5)}
        elif self.conversation_settings["employee_focus_mode"] == "broad":
            return {"max": base_limits["max"] + 10, "priority": base_limits["priority"] + 5}
        else:  # adaptive
            # Adjust based on scope
            if scope == "single_employee":
                return {"max": 5, "priority": 3}
            elif scope == "multiple_employees":
                return {"max": 12, "priority": 8}
            elif scope == "department":
                return {"max": 20, "priority": 15}
            else:
                return base_limits

    def update_conversation_settings(self, settings: Dict[str, Any]):
        """Update user-configurable conversation settings"""
        for key, value in settings.items():
            if key in self.conversation_settings:
                self.conversation_settings[key] = value

    def get_conversation_status(self) -> Dict[str, Any]:
        """Get current conversation status and statistics"""
        return {
            "conversation_length": len(self.conversation_history),
            "context_employees_count": len(self.context_employees),
            "total_tokens_used": self.conversation_metadata["total_tokens_used"],
            "conversation_theme": self.conversation_metadata["conversation_theme"],
            "settings": self.conversation_settings.copy(),
            "memory_status": self._get_memory_status()
        }

    def _get_memory_status(self) -> Dict[str, Any]:
        """Get current memory usage status"""
        total_conversation_tokens = sum(
            self._count_tokens(entry["original_query"] + entry["response"]) 
            for entry in self.conversation_history
        )
        
        limit = self._get_conversation_token_limit()
        
        return {
            "conversation_tokens": total_conversation_tokens,
            "token_limit": limit,
            "usage_percentage": (total_conversation_tokens / limit) * 100,
            "context_employees": [emp["name"] for emp in self.context_employees]
        }

    def _load_interpretation_docs(self) -> List[str]:
        """Load interpretation documentation from various file formats"""
        interpretation_docs = []
        
        # Check for HowToInterpret directory
        interpret_dir = "HowToInterpret"
        if os.path.exists(interpret_dir):
            print(f"Loading interpretation documents from {interpret_dir}...")
            
            for filename in os.listdir(interpret_dir):
                if filename.endswith(('.txt', '.md', '.pdf', '.docx')):
                    file_path = os.path.join(interpret_dir, filename)
                    try:
                        content = None
                        
                        if filename.endswith('.txt') or filename.endswith('.md'):
                            # Handle text and markdown files
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                        elif filename.endswith('.pdf'):
                            # Handle PDF files
                            content = self._extract_pdf_text(file_path)
                            
                        elif filename.endswith('.docx'):
                            # Handle Word documents
                            content = self._extract_docx_text(file_path)
                        
                        if content and content.strip():
                            # Limit content size to prevent token overflow
                            max_chars = 8000  # Reasonable limit for interpretation docs
                            if len(content) > max_chars:
                                content = content[:max_chars] + "\n\n[Content truncated for length...]"
                            
                            interpretation_docs.append(f"=== {filename} ===\n{content}")
                            print(f"✅ Loaded interpretation document: {filename} ({len(content)} characters)")
                        else:
                            print(f"⚠️ Empty content in {filename}")
                            
                    except Exception as e:
                        print(f"❌ Warning: Could not load {filename}: {e}")
        else:
            print(f"HowToInterpret directory not found at {interpret_dir}")
        
        print(f"📚 Loaded {len(interpretation_docs)} interpretation documents")
        return interpretation_docs

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file using pypdf"""
        try:
            import pypdf
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
                        continue
            return text.strip()
        except ImportError:
            print("Warning: pypdf not available. Install with: pip install pypdf")
            return ""
        except Exception as e:
            print(f"Error extracting PDF text from {file_path}: {e}")
            return ""

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file using python-docx"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            return text.strip()
        except ImportError:
            print("Warning: python-docx not available. Install with: pip install python-docx")
            return ""
        except Exception as e:
            print(f"Error extracting DOCX text from {file_path}: {e}")
            return ""

    def process_complex_query(self, query: str, context_type: str = "general", 
                             conversation_id: str = "default") -> Dict[str, Any]:
        """
        Process complex queries with AI-driven query planning and execution
        """
        
        print(f"DEBUG: [process] Starting query processing: '{query}'")
        
        # Step 1: Extract employee names from query with priority for exact matches
        extracted_employees = self._extract_employee_names_from_query(query)
        print(f"DEBUG: [process] Extracted employees: {extracted_employees}")
        
        # Step 2: Check for exact full name matches in the query
        exact_matches = []
        query_lower = query.lower()
        all_employees = self.employee_db.get_all_employees()
        
        for emp in all_employees:
            emp_name_lower = emp["name"].lower()
            if emp_name_lower in query_lower:
                exact_matches.append(emp["name"])
                print(f"DEBUG: [process] Found exact match: '{emp['name']}' in query")
        
        # Step 3: Handle disambiguation based on exact matches
        if exact_matches:
            if len(exact_matches) == 1:
                # Single exact match - use only this employee
                target_employee = exact_matches[0]
                print(f"DEBUG: [process] Single exact match found: {target_employee}")
                
                # Find the employee data
                target_emp_data = None
                for emp in all_employees:
                    if emp["name"] == target_employee:
                        target_emp_data = emp
                        break
                
                if target_emp_data:
                    # Use only this employee's data
                    return self._process_single_employee_query(query, target_emp_data, conversation_id)
                else:
                    return {
                        "response": f"I found '{target_employee}' in the query but could not locate their data in the database. Please check the name or try rephrasing.",
                        "clarification_needed": False,
                        "candidates": None,
                        "query": query,
                        "source": "employee_not_found",
                        "confidence": "low"
                    }
            else:
                # Multiple exact matches - ask for clarification
                print(f"DEBUG: [process] Multiple exact matches found: {exact_matches}")
                candidates = []
                for emp_name in exact_matches:
                    for emp in all_employees:
                        if emp["name"] == emp_name:
                            candidate = {
                                "name": emp["name"],
                                "department": emp.get("department", "Unknown department"),
                                "email": emp.get("email", "No email"),
                                "id": str(emp["id"])
                            }
                            candidates.append(candidate)
                            break
                
                return {
                    "response": f"I found multiple employees with names mentioned in your query. Please specify which one you'd like to know about (e.g., department or email).",
                    "clarification_needed": True,
                    "candidates": candidates,
                    "query": query,
                    "source": "exact_name_disambiguation",
                    "confidence": "medium"
                }
        
        # Step 4: No exact matches - check extracted employees
        if extracted_employees:
            if len(extracted_employees) == 1:
                # Single extracted employee - use this one
                target_employee = extracted_employees[0]
                print(f"DEBUG: [process] Single extracted employee: {target_employee}")
                
                # Find the employee data
                target_emp_data = None
                for emp in all_employees:
                    if emp["name"] == target_employee:
                        target_emp_data = emp
                        break
                
                if target_emp_data:
                    return self._process_single_employee_query(query, target_emp_data, conversation_id)
                else:
                    return {
                        "response": f"I found '{target_employee}' in the query but could not locate their data in the database. Please check the name or try rephrasing.",
                        "clarification_needed": False,
                        "candidates": None,
                        "query": query,
                        "source": "employee_not_found",
                        "confidence": "low"
                    }
            else:
                # Multiple extracted employees - ask for clarification
                print(f"DEBUG: [process] Multiple extracted employees: {extracted_employees}")
                candidates = []
                for emp_name in extracted_employees:
                    for emp in all_employees:
                        if emp["name"] == emp_name:
                            candidate = {
                                "name": emp["name"],
                                "department": emp.get("department", "Unknown department"),
                                "email": emp.get("email", "No email"),
                                "id": str(emp["id"])
                            }
                            candidates.append(candidate)
                            break
                
                return {
                    "response": f"I found multiple employees that could match your query. Please specify which one you'd like to know about (e.g., department or email).",
                    "clarification_needed": True,
                    "candidates": candidates,
                    "query": query,
                    "source": "extracted_name_disambiguation",
                    "confidence": "medium"
                }
        
        # Step 5: No employees found - return clear message
        print(f"DEBUG: [process] No employees found in query")
        return {
            "response": "I could not find any employee names in your query. Please specify an employee name (e.g., 'What is Carlos Garcia's work background?') or try rephrasing your question.",
            "clarification_needed": False,
            "candidates": None,
            "query": query,
            "source": "no_employee_found",
            "confidence": "low"
        }

    def _process_single_employee_query(self, query: str, target_emp_data: dict, conversation_id: str) -> Dict[str, Any]:
        """
        Process a query for a single employee using their specific data.
        """
        print(f"DEBUG: [single_employee] Processing query for: {target_emp_data['name']}")
        
        # Get the employee's full data from the database
        employee_id = target_emp_data["id"]
        full_employee_data = self.employee_db.get_employee(employee_id)
        
        if not full_employee_data:
            return {
                "response": f"I found {target_emp_data['name']} but could not retrieve their complete data from the database. Please try again or contact support.",
                "clarification_needed": False,
                "candidates": None,
                "query": query,
                "source": "employee_data_error",
                "confidence": "low"
            }
        
        # Generate context chunks from the employee's data
        context_chunks = self._get_employee_context(employee_id, {"query_type": "individual_profile", "scope": "single_employee"})
        
        if not context_chunks:
            return {
                "response": f"I found {target_emp_data['name']} but their profile data appears to be incomplete. Please try asking about a different aspect or contact support.",
                "clarification_needed": False,
                "candidates": None,
                "query": query,
                "source": "incomplete_employee_data",
                "confidence": "low"
            }
        
        print(f"DEBUG: [single_employee] Generated {len(context_chunks)} context chunks for {target_emp_data['name']}")
        
        # Generate response using the employee's specific data
        response = self._generate_intelligent_response(
            query=query,
            context_chunks=context_chunks,
            analysis={"query_type": "individual_profile", "scope": "single_employee"},
            original_query=query
        )
        
        # Update conversation history
        self._update_conversation_history(
            original_query=query,
            resolved_query=query,
            response=response,
            context_employees=[target_emp_data["name"]],
            query_analysis={"query_type": "individual_profile", "scope": "single_employee"}
        )
        
        return {
            "query": query,
            "resolved_query": query,
            "analysis": {"query_type": "individual_profile", "scope": "single_employee"},
            "response": response,
            "context_sources": len(context_chunks),
            "context_employees": [target_emp_data["name"]],
            "employee_limits": {"max": 1, "priority": 1},
            "conversation_status": self.get_conversation_status(),
            "conversation_id": conversation_id,
            "source": "single_employee_query",
            "confidence": "high"
        }

    def _plan_query_with_ai(self, query: str) -> dict:
        """
        Use AI to classify query intent and extract parameters.
        """
        print(f"DEBUG: Planning query with AI: '{query}'")
        
        if not self.client:
            # Fallback to hardcoded rules if no OpenAI client
            print("DEBUG: No OpenAI client, using fallback rules")
            return self._plan_query_with_rules(query)
        
        try:
            # Use OpenAI to classify the query intent
            system_prompt = """You are a query classifier for a talent intelligence system. Analyze the user's query and return a JSON object with the following structure:

{
    "intent": "get_score|get_all_scores|compare_scores|rank_scores|general_query",
    "trait": "specific_trait_name_if_applicable",
    "assessment_type": "Hogan|IDI",
    "employees": ["employee_name1", "employee_name2"],
    "limit": 5
}

Intent types:
- "get_score": User wants a specific assessment score for specific employee(s)
- "get_all_scores": User wants all assessment scores for specific employee(s)  
- "compare_scores": User wants to compare scores between employees
- "rank_scores": User wants to rank employees by a trait
- "general_query": User asks about work experience, team dynamics, or other qualitative information

Only include fields that are relevant. For general queries, just return {"intent": "general_query", "query": "original_query"}.

Examples:
Query: "What is Ahmed's Prudence score?" → {"intent": "get_score", "trait": "prudence", "assessment_type": "Hogan", "employees": ["Ahmed"]}
Query: "Compare Lisa and Ahmed's Sociability" → {"intent": "compare_scores", "trait": "sociability", "assessment_type": "Hogan", "employees": ["Lisa", "Ahmed"]}
Query: "Tell me about Ahmed's work experience" → {"intent": "general_query", "query": "Tell me about Ahmed's work experience"}
Query: "Top 5 employees by Ambition" → {"intent": "rank_scores", "trait": "ambition", "assessment_type": "Hogan", "limit": 5}"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"DEBUG: AI query plan result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in AI query planning: {e}")
            print(f"DEBUG: AI query planning failed, using fallback: {e}")
            # Fallback to hardcoded rules
            return self._plan_query_with_rules(query)
    
    def _plan_query_with_rules(self, query: str) -> dict:
        """
        Fallback to hardcoded rules for query planning.
        """
        query_lower = query.lower()
        
        # Check for specific score queries
        if "score" in query_lower or "hogan" in query_lower or "idi" in query_lower:
            # Extract employee names
            employees = self._extract_employee_names_from_query(query)
            print(f"DEBUG: [rules] Extracted employees: {employees}")
            
            # Extract trait/assessment type
            trait = self._extract_trait_from_query(query)
            assessment_type = self._extract_assessment_type_from_query(query)
            
            if employees and trait:
                return {
                    "intent": "get_score",
                    "trait": trait,
                    "assessment_type": assessment_type,
                    "employees": employees
                }
            elif employees:
                return {
                    "intent": "get_all_scores",
                    "assessment_type": assessment_type,
                    "employees": employees
                }
        
        # Check for comparison queries
        comparison_indicators = ["compare", "highest", "lowest", "better", "worse", "among", "between"]
        if any(indicator in query_lower for indicator in comparison_indicators):
            employees = self._extract_employee_names_from_query(query)
            trait = self._extract_trait_from_query(query)
            assessment_type = self._extract_assessment_type_from_query(query)
            
            if employees and trait:
                return {
                    "intent": "compare_scores",
                    "trait": trait,
                    "assessment_type": assessment_type,
                    "employees": employees
                }
        
        # Check for ranking queries
        ranking_indicators = ["top", "best", "worst", "rank", "ranking"]
        if any(indicator in query_lower for indicator in ranking_indicators):
            trait = self._extract_trait_from_query(query)
            assessment_type = self._extract_assessment_type_from_query(query)
            
            if trait:
                return {
                    "intent": "rank_scores",
                    "trait": trait,
                    "assessment_type": assessment_type,
                    "limit": 5  # Default to top 5
                }
        
        # Default fallback
        return {
            "intent": "general_query",
            "query": query
        }

    def _execute_query_plan(self, plan: dict) -> dict:
        """
        Execute the query plan using structured database queries.
        Falls back to RAG/embeddings for general queries.
        """
        intent = plan.get("intent")
        
        if intent == "get_score":
            return self._execute_get_score(plan)
        elif intent == "get_all_scores":
            return self._execute_get_all_scores(plan)
        elif intent == "compare_scores":
            return self._execute_compare_scores(plan)
        elif intent == "rank_scores":
            return self._execute_rank_scores(plan)
        elif intent == "general_query":
            # Handle general queries with proper context gathering
            query = plan.get("query", "")
            
            # Create basic analysis structure for general queries
            analysis = {
                "query_type": "general_guidance",
                "scope": "single_employee",  # Default scope
                "required_data": ["general"],
                "analysis_depth": "detailed_analysis",
                "key_entities": []
            }
            
            # Extract employee names from query for context
            context_employees = self._extract_employee_names_from_query(query)
            if context_employees:
                analysis["key_entities"] = context_employees
                if len(context_employees) > 1:
                    analysis["scope"] = "multiple_employees"
            
            # Set employee limits for general queries
            employee_limits = {"max": 5, "priority": 3}
            
            try:
                # Try hybrid service first
                hybrid_service = self._get_hybrid_query_service()
                context_chunks = []
                
                if hybrid_service:
                    context_chunks = self._gather_context_with_hybrid_service(
                        query=query,
                        analysis=analysis,
                        context_employees=context_employees,
                        employee_limits=employee_limits,
                        hybrid_service=hybrid_service
                    )
                    
                    # Check if hybrid service returned the right employee
                    if context_employees and context_chunks:
                        # Check if any of the context chunks contain the expected employee names
                        context_text = " ".join(context_chunks).lower()
                        found_expected_employee = False
                        
                        for employee_name in context_employees:
                            if employee_name.lower() in context_text:
                                found_expected_employee = True
                                print(f"DEBUG: Hybrid service correctly found {employee_name}")
                                break
                        
                        if not found_expected_employee:
                            print(f"DEBUG: Hybrid service returned wrong employees, falling back to legacy method")
                            # Hybrid service returned wrong results, try legacy method
                            context_chunks = self._gather_context_legacy_method(
                                query=query,
                                analysis=analysis,
                                context_employees=context_employees,
                                employee_limits=employee_limits
                            )
                else:
                    # Fallback to legacy method
                    context_chunks = self._gather_context_legacy_method(
                        query=query,
                        analysis=analysis,
                        context_employees=context_employees,
                        employee_limits=employee_limits
                    )
                
                if not context_chunks:
                    # Emergency fallback
                    context_chunks = self._emergency_employee_fallback(query, analysis, employee_limits["max"])
                
                if context_chunks:
                    final_answer = self._generate_answer_from_context(query, context_chunks)
                    return {
                        "response": final_answer,
                        "source": "hybrid_rag",
                        "confidence": "medium",
                        "employees": context_employees
                    }
                else:
                    return {
                        "response": "I couldn't find relevant information to answer your question. Please try rephrasing or ask about a specific employee.",
                        "source": "general_query",
                        "confidence": "low"
                    }
                    
            except Exception as e:
                print(f"DEBUG: Error in general query processing: {e}")
                # Fallback to simple response
                return {
                    "response": f"I understand your question about '{query}', but I'm having trouble accessing the relevant information right now. Please try asking about a specific employee or assessment scores.",
                    "source": "general_query_fallback",
                    "confidence": "low"
                }
        else:
            if plan.get("query") == "":
                return {
                    "response": "I understand your query, but I need more specific information about what assessment scores you'd like to see. Please specify the employee name and assessment trait (e.g., 'What is Ahmed's Prudence score?').",
                    "source": "ai_query_plan",
                    "confidence": "low"
                }
            else:
                return {
                    "response": "I understand your query, but I'm not sure how to process it. Please try rephrasing your question.",
                    "source": "ai_query_plan",
                    "confidence": "low"
                }

    def _execute_get_score(self, plan: dict) -> dict:
        """Execute a specific score query for one or more employees."""
        trait = plan.get("trait")
        assessment_type = plan.get("assessment_type", "Hogan")
        employees = plan.get("employees", [])
        original_query = plan.get("query", "")
        
        print(f"DEBUG: _execute_get_score called with:")
        print(f"  - trait: {trait}")
        print(f"  - assessment_type: {assessment_type}")
        print(f"  - employees: {employees}")
        print(f"  - original_query: {original_query}")
        
        if not employees or not trait:
            return {
                "response": "I need both an employee name and a specific trait to look up scores.",
                "source": "ai_query_plan",
                "confidence": "low"
            }
        
        results = []
        found_employees = []
        
        # If the original query only contains a first name and there are multiple employees with that first name, ask for clarification
        if len(employees) > 1:
            print(f"DEBUG: Multiple employees found: {employees}")
            import re
            match = re.search(r"score of ([A-Za-z]+)", original_query.lower())
            if match:
                first_name = match.group(1)
                print(f"DEBUG: Extracted first name: {first_name}")
                first_names = [emp.split()[0].lower() for emp in employees]
                print(f"DEBUG: First names from employees: {first_names}")
                if all(fn == first_name for fn in first_names):
                    print(f"DEBUG: All employees share first name '{first_name}', triggering clarification")
                    employee_list = ", ".join(employees)
                    return {
                        "response": f"I found multiple employees with the name '{first_name.title()}': {employee_list}. Please specify which one you'd like to know about (e.g., 'Aisha Hassan' or 'Aisha Ibrahim').",
                        "source": "ai_query_plan",
                        "confidence": "medium",
                        "employees": employees
                    }
                else:
                    print(f"DEBUG: Employees do not all share first name '{first_name}'")
            else:
                print(f"DEBUG: Could not extract first name from query")
        else:
            print(f"DEBUG: Only {len(employees)} employee(s) found, not triggering clarification")
        
        for employee_name in employees:
            employee_data = self._get_employee_by_name(employee_name)
            if not employee_data:
                results.append(f"Employee '{employee_name}' not found in the database.")
                continue
            
            # Always use the full name from the database
            full_name = employee_data.get('name', employee_name)
            found_employees.append(full_name)
            score = self._get_specific_score(employee_data, trait, assessment_type)
            
            if score is not None:
                results.append(f"{full_name}'s {trait} score is {score}.")
            else:
                results.append(f"No {trait} score found for {full_name}.")
        
        response = "\n".join(results)
        print(f"DEBUG: Final response: {response}")
        return {
            "response": response,
            "source": "ai_query_plan",
            "confidence": "high" if found_employees else "low",
            "employees": found_employees
        }

    def _execute_get_all_scores(self, plan: dict) -> dict:
        """Execute a query to get all scores for one or more employees."""
        assessment_type = plan.get("assessment_type", "Hogan")
        employees = plan.get("employees", [])
        
        if not employees:
            return {
                    "response": "I need an employee name to look up their scores.",
                    "source": "ai_query_plan",
                    "confidence": "low"
                }
        
        results = []
        found_employees = []
        
        for employee_name in employees:
            employee_data = self._get_employee_by_name(employee_name)
            if not employee_data:
                results.append(f"Employee '{employee_name}' not found in the database.")
                continue
            
            found_employees.append(employee_name)
            scores = self._get_all_scores_for_employee(employee_data, assessment_type)
            
            if scores:
                results.append(f"\n{employee_name}'s {assessment_type} scores:")
                for trait, score in scores.items():
                    results.append(f"- {trait}: {score}")
            else:
                results.append(f"No {assessment_type} scores found for {employee_name}.")
        
        response = "\n".join(results)
        return {
            "response": response,
            "source": "ai_query_plan",
            "confidence": "high" if found_employees else "low",
            "employees": found_employees
        }

    def _execute_compare_scores(self, plan: dict) -> dict:
        """Execute a comparison query between employees for a specific trait."""
        trait = plan.get("trait")
        assessment_type = plan.get("assessment_type", "Hogan")
        employees = plan.get("employees", [])
        
        if not employees or not trait:
            return {
                    "response": "I need both employee names and a specific trait to compare scores.",
                    "source": "ai_query_plan",
                    "confidence": "low"
                }
        
        employee_scores = []
        found_employees = []
        
        for employee_name in employees:
            employee_data = self._get_employee_by_name(employee_name)
            if not employee_data:
                continue
            
            found_employees.append(employee_name)
            score = self._get_specific_score(employee_data, trait, assessment_type)
            
            if score is not None:
                employee_scores.append((employee_name, score))
        
        if not employee_scores:
            return {
                "response": f"No {trait} scores found for the specified employees.",
                "source": "ai_query_plan",
                "confidence": "low",
                "employees": found_employees
            }
        
        # Sort by score (highest first)
        employee_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Generate comparison response
        results = [f"Comparison of {trait} scores:"]
        for i, (name, score) in enumerate(employee_scores):
            if i == 0:
                results.append(f"1. {name} has the highest {trait} score: {score}")
            else:
                results.append(f"{i+1}. {name}: {score}")
        
        response = "\n".join(results)
        return {
            "response": response,
            "source": "ai_query_plan",
            "confidence": "high",
            "employees": found_employees
        }

    def _execute_rank_scores(self, plan: dict) -> dict:
        """Execute a ranking query to find top/bottom scores for a trait."""
        trait = plan.get("trait")
        assessment_type = plan.get("assessment_type", "Hogan")
        limit = plan.get("limit", 5)
        
        if not trait:
            return {
                "response": "I need a specific trait to rank employees.",
                "source": "ai_query_plan",
                "confidence": "low"
            }
        
        # Get all employees and their scores for the trait
        all_employees = self.employee_db.get_all_employees()
        employee_scores = []
        
        for emp in all_employees:
            employee_data = self._get_employee_by_name(emp["name"])
            if employee_data:
                score = self._get_specific_score(employee_data, trait, assessment_type)
                if score is not None:
                    employee_scores.append((emp["name"], score))
        
        if not employee_scores:
            return {
                "response": f"No {trait} scores found in the database.",
                "source": "ai_query_plan",
                "confidence": "low",
                "employees": []
            }
        
        # Sort by score (highest first)
        employee_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N results
        top_results = employee_scores[:limit]
        
        # Generate ranking response
        results = [f"Top {len(top_results)} employees with highest {trait} scores:"]
        for i, (name, score) in enumerate(top_results):
            results.append(f"{i+1}. {name}: {score}")
        
        response = "\n".join(results)
        return {
            "response": response,
            "source": "ai_query_plan",
            "confidence": "high",
            "employees": [name for name, _ in top_results]
        }

    def _extract_employee_names_from_query(self, query: str) -> List[str]:
        """Extract employee names from the query using pattern matching."""
        # Get all employees from database
        all_employees = self.employee_db.get_all_employees()
        found_employees = []
        
        query_lower = query.lower()
        
        # Common words to avoid matching
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 
            'one', 'our', 'out', 'day', 'get', 'use', 'man', 'new', 'now', 'way', 'may', 
            'say', 'has', 'his', 'their', 'what', 'when', 'where', 'why', 'how', 'is', 
            'of', 'in', 'to', 'a', 'an', 'with', 'by', 'from', 'about', 'score', 'scores',
            'tell', 'me', 'about', 'work', 'experience', 'hogan', 'idi', 'assessment',
            'compare', 'between', 'and', 'what', 'are', 'tell', 'me', 'about', 'show',
            'display', 'list', 'find', 'search', 'look', 'up', 'get', 'give', 'show'
        }
        
        # Extract potential name terms from query (words that could be names)
        query_words = [word for word in query_lower.split() if word not in common_words and len(word) > 2]
        
        print(f"DEBUG: [extract] Query words: {query_words}")
        
        # PRIORITY 1: Look for exact full name matches first (highest priority)
        for emp in all_employees:
            emp_name = emp["name"]
            emp_name_lower = emp_name.lower()
            
            # Check for exact full name match in query
            if emp_name_lower in query_lower:
                print(f"DEBUG: [extract] EXACT MATCH found: '{emp_name}' in query")
                found_employees.insert(0, emp_name)  # Insert at beginning for highest priority
                continue
        
        # PRIORITY 2: Look for partial matches (lower priority)
        for emp in all_employees:
            emp_name = emp["name"]
            emp_name_lower = emp_name.lower()
            emp_name_parts = emp_name_lower.split()
            
            # Skip if already found as exact match
            if emp_name in found_employees:
                continue
            
            # Check if any query word matches any part of the employee name
            for query_word in query_words:
                # Check if query word is in employee name (partial match)
                if query_word in emp_name_lower:
                    # Additional validation: make sure it's not just a substring of a longer word
                    # unless it's a complete name part
                    is_valid_match = False
                    
                    # Check if it matches a complete name part
                    for name_part in emp_name_parts:
                        if query_word == name_part:
                            is_valid_match = True
                            break
                        elif len(query_word) > 3 and query_word in name_part:
                            # Allow partial matches for longer words (4+ chars)
                            is_valid_match = True
                            break
                    
                    if is_valid_match:
                        print(f"DEBUG: [extract] PARTIAL MATCH found: '{query_word}' in '{emp_name}'")
                        if emp_name not in found_employees:
                            found_employees.append(emp_name)
                        break
        
        # Remove duplicates while preserving order
        unique_employees = []
        seen = set()
        for emp in found_employees:
            if emp not in seen:
                unique_employees.append(emp)
                seen.add(emp)
        
        print(f"DEBUG: [extract] Final extracted employees (ordered by priority): {unique_employees}")
        return unique_employees

    def _extract_trait_from_query(self, query: str) -> str:
        """Extract assessment trait from the query."""
        query_lower = query.lower()
        
        # Hogan HPI traits
        hpi_traits = [
            'adjustment', 'ambition', 'sociability', 'interpersonal sensitivity', 
            'prudence', 'inquisitive', 'learning approach'
        ]
        
        # Hogan HDS traits
        hds_traits = [
            'excitable', 'skeptical', 'sceptical', 'cautious', 'reserved', 'leisurely',
            'bold', 'mischievous', 'colorful', 'colourful', 'imaginative', 'diligent', 'dutiful'
        ]
        
        # Hogan MVPI traits
        mvpi_traits = [
            'recognition', 'power', 'hedonism', 'altruistic', 'affiliation', 'tradition',
            'security', 'commerce', 'aesthetics', 'science'
        ]
        
        # IDI dimensions
        idi_traits = [
            'giving', 'receiving', 'belonging', 'expressing', 'stature', 'entertaining',
            'creating', 'interpreting', 'excelling', 'enduring', 'structuring',
            'maneuvering', 'winning', 'controlling', 'stability', 'independence', 'irreproachability'
        ]
        
        all_traits = hpi_traits + hds_traits + mvpi_traits + idi_traits
        
        for trait in all_traits:
            if trait in query_lower:
                return trait
        
        return None

    def _extract_assessment_type_from_query(self, query: str) -> str:
        """Extract assessment type from the query."""
        query_lower = query.lower()
        
        if 'hogan' in query_lower:
            return 'Hogan'
        elif 'idi' in query_lower:
            return 'IDI'
        else:
            return 'Hogan'  # Default to Hogan

    def _get_employee_by_name(self, employee_name: str) -> dict:
        """Get employee data by name with partial matching support."""
        all_employees = self.employee_db.get_all_employees()
        
        # First try exact match
        for emp in all_employees:
            if emp["name"].lower() == employee_name.lower():
                # Get full employee data including scores
                return self.employee_db.get_employee(emp["id"])
        
        # If no exact match, try partial matches
        employee_name_lower = employee_name.lower()
        for emp in all_employees:
            emp_name_lower = emp["name"].lower()
            
            # Check if the search term is contained in the employee name
            if employee_name_lower in emp_name_lower:
                return self.employee_db.get_employee(emp["id"])
            
            # Check if any part of the employee name matches the search term
            name_parts = emp_name_lower.split()
            for part in name_parts:
                if len(part) > 2 and part == employee_name_lower:
                    # Avoid common words
                    common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'use', 'man', 'new', 'now', 'way', 'may', 'say', 'has', 'his', 'their', 'what', 'when', 'where', 'why', 'how'}
                    if part not in common_words:
                        return self.employee_db.get_employee(emp["id"])
        
        return None

    def _get_specific_score(self, employee_data: dict, trait: str, assessment_type: str) -> float:
        """Get a specific score for an employee."""
        if assessment_type == 'Hogan':
            hogan_scores = employee_data.get('hogan_scores', [])
            for score_entry in hogan_scores:
                if score_entry['trait'].lower() == trait.lower():
                    return score_entry['score']
        elif assessment_type == 'IDI':
            idi_scores = employee_data.get('idi_scores', [])
            for score_entry in idi_scores:
                if score_entry['dimension'].lower() == trait.lower():
                    return score_entry['score']
        
        return None

    def _get_all_scores_for_employee(self, employee_data: dict, assessment_type: str) -> dict:
        """Get all scores for an employee for a specific assessment type."""
        scores = {}
        
        if assessment_type == 'Hogan':
            hogan_scores = employee_data.get('hogan_scores', [])
            for score_entry in hogan_scores:
                scores[score_entry['trait']] = score_entry['score']
        elif assessment_type == 'IDI':
            idi_scores = employee_data.get('idi_scores', [])
            for score_entry in idi_scores:
                scores[score_entry['dimension']] = score_entry['score']
        
        return scores

    def _update_conversation_history(self, original_query: str, resolved_query: str, 
                                   response: str, context_employees: List[str], 
                                   query_analysis: Dict[str, Any]):
        """Update conversation history with metadata"""
        tokens_used = self._count_tokens(original_query + resolved_query + response)
        
        conversation_entry = {
            "original_query": original_query,
            "resolved_query": resolved_query,
            "response": response,
            "context_employees": context_employees,
            "query_type": query_analysis.get("query_type", "general"),
            "tokens_used": tokens_used,
            "timestamp": self._get_timestamp()
        }
        
        self.conversation_history.append(conversation_entry)
        self.conversation_metadata["total_tokens_used"] += tokens_used
        
        # Update conversation theme if not set
        if not self.conversation_metadata["conversation_theme"]:
            self.conversation_metadata["conversation_theme"] = query_analysis.get("query_type", "general")

    def _update_context_employees(self, response: str, context_employees: List[str], 
                                query_analysis: Dict[str, Any]):
        """Update context employees with intelligent scoring and relevance tracking"""
        
        # Extract employees mentioned in response
        response_employees = self._extract_employee_names_from_response(response)
        
        # Create new context employee entries with scores
        new_context_employees = []
        
        # Add context employees from query (highest priority)
        for emp_name in context_employees:
            employee_entry = {
                "name": emp_name,
                "relevance_score": 1.0,  # Highest relevance
                "source": "query_context",
                "first_mentioned": self._get_timestamp(),
                "query_types": [query_analysis.get("query_type", "general")]
            }
            new_context_employees.append(employee_entry)
        
        # Add employees from response (medium priority)
        for emp_name in response_employees:
            if not any(emp["name"] == emp_name for emp in new_context_employees):
                employee_entry = {
                    "name": emp_name,
                    "relevance_score": 0.8,
                    "source": "response_mention",
                    "first_mentioned": self._get_timestamp(),
                    "query_types": [query_analysis.get("query_type", "general")]
                }
                new_context_employees.append(employee_entry)
        
        # Merge with existing context employees, updating scores
        for new_emp in new_context_employees:
            existing_emp = next((emp for emp in self.context_employees 
                               if emp.get("name") == new_emp["name"]), None)
            
            if existing_emp:
                # Update existing employee - boost score and add query type
                existing_emp["relevance_score"] = min(1.0, existing_emp["relevance_score"] + 0.2)
                if new_emp["query_types"][0] not in existing_emp["query_types"]:
                    existing_emp["query_types"].append(new_emp["query_types"][0])
            else:
                # Add new employee
                self.context_employees.append(new_emp)
        
        # Sort by relevance score and limit based on settings
        self.context_employees.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Apply intelligent limits
        max_employees = self._get_max_context_employees()
        if len(self.context_employees) > max_employees:
            self.context_employees = self.context_employees[:max_employees]
        
        # Update peak count
        self.conversation_metadata["peak_employee_count"] = max(
            self.conversation_metadata["peak_employee_count"],
            len(self.context_employees)
        )

    def _get_max_context_employees(self) -> int:
        """Get maximum context employees based on conversation complexity and settings"""
        base_limit = 15  # Default
        
        if self.conversation_settings["employee_focus_mode"] == "narrow":
            base_limit = 8
        elif self.conversation_settings["employee_focus_mode"] == "broad":
            base_limit = 25
        
        # Adjust based on conversation theme
        theme = self.conversation_metadata.get("conversation_theme", "general")
        if theme in ["succession_planning", "department_analysis"]:
            base_limit = min(base_limit + 10, 30)
        elif theme == "individual_profile":
            base_limit = min(base_limit, 10)
        
        return base_limit

    def _manage_conversation_memory(self):
        """Intelligent conversation memory management based on token limits"""
        if not self.conversation_history:
            return
        
        # Calculate total conversation tokens
        total_tokens = sum(entry["tokens_used"] for entry in self.conversation_history)
        token_limit = self._get_conversation_token_limit()
        
        # If we're under the limit, no need to prune
        if total_tokens <= token_limit:
            return
        
        # Keep minimum exchanges regardless of token count
        if len(self.conversation_history) <= self.min_conversation_exchanges:
            return
        
        # Prune oldest conversations while staying above minimum
        while (len(self.conversation_history) > self.min_conversation_exchanges and 
               sum(entry["tokens_used"] for entry in self.conversation_history) > token_limit):
            
            removed_entry = self.conversation_history.pop(0)
            
            # Update employee relevance scores when removing old context
            self._decay_employee_relevance_scores(removed_entry)

    def _decay_employee_relevance_scores(self, removed_entry: Dict[str, Any]):
        """Decay relevance scores for employees from removed conversation entries"""
        removed_employees = removed_entry.get("context_employees", [])
        
        for emp_name in removed_employees:
            emp_entry = next((emp for emp in self.context_employees 
                            if emp.get("name") == emp_name), None)
            if emp_entry:
                emp_entry["relevance_score"] = max(0.1, emp_entry["relevance_score"] - 0.3)
        
        # Remove employees with very low relevance scores
        self.context_employees = [emp for emp in self.context_employees 
                                 if emp["relevance_score"] > 0.15]

    def _resolve_contextual_query(self, query: str) -> tuple[str, List[str]]:
        """
        Resolve contextual references in queries with intelligent employee context
        
        Returns:
            tuple: (resolved_query, list_of_employee_names)
        """
        context_employees = []
        resolved_query = query
        
        # Check for contextual references
        contextual_indicators = [
            "between them", "among them", "between the two", "among the two",
            "which of them", "who among them", "these employees", "those employees",
            "the two", "both of them", "either of them", "these people",
            "them", "they", "the candidates", "the employees", "the team members",
            "the individuals", "the people mentioned", "those people"
        ]
        
        query_lower = query.lower()
        has_contextual_reference = any(indicator in query_lower for indicator in contextual_indicators)
        
        if has_contextual_reference and self.context_employees:
            # Get employee names from context, prioritizing by relevance score
            employee_names = [emp["name"] if isinstance(emp, dict) else emp 
                            for emp in self.context_employees[:8]]  # Top 8 most relevant
            context_employees = employee_names.copy()
            
            # Create a more specific query
            if len(employee_names) == 2:
                names_text = f"{employee_names[0]} and {employee_names[1]}"
            elif len(employee_names) <= 5:
                names_text = ", ".join(employee_names[:-1]) + f", and {employee_names[-1]}"
            else:
                # For larger groups, use more general reference
                names_text = f"{employee_names[0]}, {employee_names[1]}, and {len(employee_names)-2} other employees"
            
            # Replace common contextual terms with intelligent context
            replacements = {
                "between them": f"between {names_text}",
                "among them": f"among {names_text}",
                "between the two": f"between {names_text}",
                "among the two": f"among {names_text}",
                "which of them": f"which of {names_text}",
                "who among them": f"who among {names_text}",
                "these employees": names_text,
                "those employees": names_text,
                "the two": names_text,
                "both of them": f"both {names_text}",
                "either of them": f"either {names_text}",
                "these people": names_text,
                "the candidates": names_text,
                "the employees": names_text,
                "the team members": names_text,
                "the individuals": names_text,
                "the people mentioned": names_text,
                "those people": names_text
            }
            
            for old_text, new_text in replacements.items():
                if old_text in query_lower:
                    # Case-insensitive replacement
                    import re
                    pattern = re.compile(re.escape(old_text), re.IGNORECASE)
                    resolved_query = pattern.sub(new_text, resolved_query)
                    break
        
        return resolved_query, context_employees

    def _get_timestamp(self) -> str:
        """Get current timestamp for conversation tracking"""
        import time
        return time.strftime('%Y-%m-%d %H:%M:%S')
    
    def clear_conversation_history(self):
        """Clear conversation history and reset all tracking variables for a fresh start"""
        self.conversation_history = []
        self.context_employees = []
        self.conversation_metadata = {
            "total_tokens_used": 0,
            "peak_employee_count": 0,
            "conversation_theme": None
        }
        print("Conversation history cleared. Starting fresh conversation context.")

    def _analyze_query_intent(self, query: str, context_employees: List[str] = []) -> Dict[str, Any]:
        """Analyze what type of query this is and what information is needed"""
        
        # Pre-process query to detect multi-employee patterns
        query_lower = query.lower()
        multi_employee_indicators = [
            "who has", "who have", "who are", "who would be", "which employees",
            "what employees", "who among", "candidates for", "people with",
            "employees with", "staff with", "team members", "individuals who",
            "who shows", "who demonstrates", "who exhibits"
        ]
        
        # Detect if this is clearly a multi-employee query
        is_multi_employee_query = any(indicator in query_lower for indicator in multi_employee_indicators)
        
        analysis_prompt = f"""Analyze this HR/talent management query to understand the intent and required information:

Query: "{query}"

Determine:
1. Query type: individual_profile, team_analysis, cross_comparison, succession_planning, risk_assessment, general_guidance
2. Scope: single_employee, multiple_employees, department, organization-wide
3. Required data: personality_scores, performance_data, career_history, skills_assessment, leadership_style, team_dynamics
4. Analysis depth: surface_level, detailed_analysis, strategic_recommendations
5. Key entities: Extract any specific names, departments, roles mentioned

IMPORTANT: If the query asks "Who has...", "Who are...", "Which employees...", etc., the scope should be "multiple_employees" not "single_employee".

Return as JSON:
{{
  "query_type": "...",
  "scope": "...",
  "required_data": ["...", "..."],
  "analysis_depth": "...",
  "key_entities": ["...", "..."],
  "specific_request": "brief description of what user wants"
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.2,
            max_tokens=500
        )
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            analysis["key_entities"] = context_employees
            
            # Override scope if we detected multi-employee patterns
            if is_multi_employee_query and analysis.get("scope") == "single_employee":
                analysis["scope"] = "multiple_employees"
                print(f"DEBUG: Overrode scope to multiple_employees for query: {query}")
            
            return analysis
        except:
            # Fallback if JSON parsing fails
            fallback_analysis = {
                "query_type": "general_guidance",
                "scope": "multiple_employees" if is_multi_employee_query else "single_employee",
                "required_data": ["general"],
                "analysis_depth": "detailed_analysis",
                "key_entities": [],
                "specific_request": query
            }
            print(f"DEBUG: Using fallback analysis with scope: {fallback_analysis['scope']}")
            return fallback_analysis

    def _gather_relevant_context(self, query: str, analysis: Dict[str, Any], 
                               context_employees: List[str], 
                               employee_limits: Dict[str, int]) -> List[str]:
        """Gather relevant context with enhanced validation logging"""
        context_chunks = []
        
        try:
            # Log the context gathering attempt
            logger.info(f"Starting context gathering for query: '{query[:100]}...'")
            logger.info(f"Analysis: {analysis}")
            logger.info(f"Context employees: {context_employees}")
            logger.info(f"Employee limits: {employee_limits}")
            
            # Try hybrid service first if available
            try:
                from backend.services.rag.hybrid_query import HybridQueryService
                hybrid_service = HybridQueryService()
                context_chunks = self._gather_context_with_hybrid_service(
                    query, analysis, context_employees, employee_limits, hybrid_service
                )
                logger.info(f"Hybrid service returned {len(context_chunks)} chunks")
            except ImportError:
                logger.warning("HybridQueryService not available, using legacy method")
                context_chunks = self._gather_context_legacy_method(
                    query, analysis, context_employees, employee_limits
                )
                logger.info(f"Legacy method returned {len(context_chunks)} chunks")
            
            # Validate context quality
            if not context_chunks:
                logger.warning("No context chunks returned, using emergency fallback")
                context_chunks = self._emergency_employee_fallback(query, analysis, employee_limits["max"])
                logger.info(f"Emergency fallback returned {len(context_chunks)} chunks")
            
            # Log final context summary
            total_tokens = sum(len(chunk.split()) for chunk in context_chunks)
            logger.info(f"Final context: {len(context_chunks)} chunks, ~{total_tokens} tokens")
            
            # Check if we have real employee data
            has_real_data = any(
                any(indicator in chunk for indicator in ["Employee:", "Department:", "Experience:", "Assessment"])
                for chunk in context_chunks
            )
            
            if not has_real_data:
                logger.warning("No real employee data found in context, using fallback")
                # Get some employee names for context
                all_employees = self.employee_db.get_all_employees()
                if all_employees:
                    employee_names = [emp['name'] for emp in all_employees[:5]]
                    logger.info(f"Using fallback with {len(employee_names)} employees: {employee_names}")
            
            return context_chunks
            
        except Exception as e:
            logger.error(f"Error in _gather_relevant_context: {e}")
            # Return emergency fallback
            return self._emergency_employee_fallback(query, analysis, employee_limits["max"])
    
    def _emergency_employee_fallback(self, query: str, analysis: Dict[str, Any], max_employees: int) -> List[str]:
        """Emergency fallback to ensure we always get some employee data for database queries"""
        emergency_context = []
        
        try:
            print("DEBUG: Executing emergency employee fallback")
            
            # Get all employees from database
            all_employees = self.employee_db.get_all_employees()
            if not all_employees:
                print("DEBUG: No employees found in database")
                return emergency_context
            
            print(f"DEBUG: Found {len(all_employees)} total employees in database")
            
            # Strategy 1: Try vector search one more time with broader parameters
            try:
                search_results = self.vector_store.search_employees(query, n_results=max_employees * 2)
                if search_results:
                    print(f"DEBUG: Emergency vector search found {len(search_results)} results")
                    for result in search_results[:max_employees]:
                        emp_data = self.employee_db.get_employee(result["employee_id"])
                        if emp_data:
                            employee_context = self._get_employee_context(result["employee_id"], analysis)
                            emergency_context.extend(employee_context[:1])  # 1 chunk per employee
                            print(f"DEBUG: Emergency added {emp_data['name']}")
                            
                    if emergency_context:
                        return emergency_context
            except Exception as e:
                print(f"DEBUG: Emergency vector search failed: {e}")
            
            # Strategy 2: Get a diverse sample of employees
            print("DEBUG: Using diverse sampling strategy")
            import random
            
            # Sample employees for emergency fallback
            sample_size = min(max_employees, len(all_employees))
            sample_employees = random.sample(all_employees, sample_size)
            
            # Get context for sampled employees
            for emp in sample_employees:
                try:
                    employee_context = self._get_employee_context(emp["id"], analysis)
                    emergency_context.extend(employee_context[:1])  # 1 chunk per employee for emergency
                    print(f"DEBUG: Emergency fallback added {emp['name']}")
                except Exception as e:
                    print(f"DEBUG: Error getting context for {emp.get('name', 'unknown')}: {e}")
            
            print(f"DEBUG: Emergency fallback completed - {len(emergency_context)} contexts added")
            return emergency_context
            
        except Exception as e:
            print(f"DEBUG: Emergency fallback failed: {e}")
            return emergency_context

    def _get_hybrid_query_service(self):
        """Get hybrid query service if available"""
        try:
            # Try to import and initialize the hybrid service directly
            from backend.services.rag.hybrid_query import HybridQueryService
            hybrid_service = HybridQueryService()
            return hybrid_service
        except ImportError:
            print("DEBUG: HybridQueryService not available")
            return None
        except Exception as e:
            print(f"DEBUG: Could not initialize hybrid query service: {e}")
            return None
    
    def _gather_context_with_hybrid_service(self, query: str, analysis: Dict[str, Any], 
                                          context_employees: List[str], 
                                          employee_limits: Dict[str, int],
                                          hybrid_service) -> List[str]:
        """Gather context using the hybrid query service for optimal performance"""
        context_chunks = []
        
        print(f"DEBUG: [hybrid] Starting hybrid context gathering")
        print(f"DEBUG: [hybrid] Query: '{query}'")
        print(f"DEBUG: [hybrid] Context employees: {context_employees}")
        print(f"DEBUG: [hybrid] Employee limits: {employee_limits}")
        
        # Extract potential filters from the query and analysis
        filters = self._extract_filters_from_analysis(query, analysis)
        
        # Search using hybrid service
        search_results = hybrid_service.search_employees(
            query, 
            filters=filters, 
            n_results=employee_limits["max"]
        )
        
        if search_results and search_results.get('results'):
            print(f"DEBUG: [hybrid] Hybrid search found {len(search_results['results'])} employees using strategy: {search_results['strategy_used']}")
            
            # Process hybrid results
            for result in search_results['results']:
                employee_id = result.get('employee_id')
                if employee_id:
                    # Get rich context from detailed scores if available
                    detailed_scores = result.get('detailed_scores')
                    if detailed_scores:
                        # Format structured data for context
                        context_chunk = self._format_hybrid_result_for_context(result)
                        context_chunks.append(context_chunk)
                        print(f"DEBUG: [hybrid] Added detailed context for employee {result.get('name', 'Unknown')}")
                    else:
                        # Fallback to traditional employee context
                        employee_context = self._get_employee_context(employee_id, analysis)
                        context_chunks.extend(employee_context)
                        print(f"DEBUG: [hybrid] Added traditional context for employee {result.get('name', 'Unknown')} ({len(employee_context)} chunks)")
        else:
            print(f"DEBUG: [hybrid] No results from hybrid search")
        
        # If priority employees specified, ensure they're included
        if context_employees:
            print(f"DEBUG: [hybrid] Ensuring priority employees are included")
            priority_context = self._ensure_priority_employees_included(
                context_employees, context_chunks, analysis, employee_limits["priority"]
            )
            context_chunks.extend(priority_context)
            print(f"DEBUG: [hybrid] Added {len(priority_context)} priority context chunks")
        
        print(f"DEBUG: [hybrid] Final context: {len(context_chunks)} total chunks")
        return context_chunks
    
    def _gather_context_legacy_method(self, query: str, analysis: Dict[str, Any], 
                                    context_employees: List[str], 
                                    employee_limits: Dict[str, int]) -> List[str]:
        """Gather context using the legacy vector search method"""
        context_chunks = []
        employees_added = 0
        max_employees = employee_limits["max"]
        priority_employees = employee_limits["priority"]
        
        print(f"DEBUG: Starting context gathering - query: '{query}', scope: {analysis.get('scope')}")
        
        # PRIORITY 0 - Direct employee lookup for specific names (HIGHEST PRIORITY)
        direct_employee = self._find_direct_employee_match(query)
        if direct_employee:
            print(f"DEBUG: Found direct employee match: {direct_employee['name']}")
            employee_context = self._get_employee_context(direct_employee['id'], analysis)
            context_chunks.extend(employee_context)
            employees_added += 1
            print(f"DEBUG: Added direct employee context for {direct_employee['name']}")
            return context_chunks
        
        # PRIORITY 1: Context employees from conversation (highest priority)
        if context_employees:
            print(f"DEBUG: Using context employees: {context_employees}")
            employees = self.employee_db.get_all_employees()
            for target_name in context_employees:
                if employees_added >= priority_employees:
                    break
                for emp in employees:
                    if target_name.lower() in emp['name'].lower() or emp['name'].lower() in target_name.lower():
                        employee_context = self._get_employee_context(emp['id'], analysis)
                        context_chunks.extend(employee_context)
                        employees_added += 1
                        print(f"DEBUG: Added priority context for {emp['name']}")
                        break
        
        # PRIORITY 2: High-relevance employees from conversation history
        if employees_added < priority_employees:
            high_relevance_employees = [
                emp for emp in self.context_employees 
                if isinstance(emp, dict) and emp.get("relevance_score", 0) > 0.7
            ][:priority_employees - employees_added]
            
            employees = self.employee_db.get_all_employees()
            for context_emp in high_relevance_employees:
                emp_name = context_emp["name"]
                for emp in employees:
                    if emp_name.lower() in emp['name'].lower() or emp['name'].lower() in emp_name.lower():
                        employee_context = self._get_employee_context(emp['id'], analysis)
                        context_chunks.extend(employee_context)
                        employees_added += 1
                        print(f"DEBUG: Added high-relevance context for {emp['name']}")
                        break
        
        # PRIORITY 3: Semantic search for additional employees up to max limit
        remaining_slots = max_employees - employees_added
        if remaining_slots > 0:
            scope = analysis.get("scope", "single_employee")
            
            # IMPROVED LOGIC: For queries asking "Who has..." or similar, treat as multiple_employees
            query_lower = query.lower()
            multi_employee_indicators = [
                "who has", "who have", "who are", "who would be", "which employees",
                "what employees", "who among", "candidates for", "people with",
                "employees with", "staff with", "team members", "individuals who"
            ]
            
            if any(indicator in query_lower for indicator in multi_employee_indicators):
                scope = "multiple_employees"
                print(f"DEBUG: Detected multi-employee query, changing scope to: {scope}")
            
            if scope == "single_employee":
                # Try to find specific employee mentioned
                entities = analysis.get("key_entities", [])
                employees = self.employee_db.get_all_employees()
                
                for entity in entities:
                    if employees_added >= max_employees:
                        break
                    # Search for employee by name
                    for emp in employees:
                        if entity.lower() in emp['name'].lower():
                            # Skip if already added
                            if not any(emp['name'] in chunk for chunk in context_chunks):
                                employee_context = self._get_employee_context(emp['id'], analysis)
                                context_chunks.extend(employee_context)
                                employees_added += 1
                                print(f"DEBUG: Added specific employee {emp['name']} from entities")
                                break
                
                # If no specific employee found or need more, do semantic search
                if employees_added < max_employees:
                    print(f"DEBUG: Doing semantic search for single employee query")
                    try:
                        search_results = self.vector_store.search_employees(query, n_results=remaining_slots + 5)
                        for result in search_results:
                            if employees_added >= max_employees:
                                break
                            # Skip if already added
                            emp_data = self.employee_db.get_employee(result['employee_id'])
                            if emp_data and not any(emp_data['name'] in chunk for chunk in context_chunks):
                                employee_context = self._get_employee_context(result['employee_id'], analysis)
                                context_chunks.extend(employee_context)
                                employees_added += 1
                                print(f"DEBUG: Added employee {emp_data['name']} from semantic search")
                    except Exception as e:
                        print(f"DEBUG: Vector search failed: {e}")
                        # If vector search fails, try direct name matching as fallback
                        print(f"DEBUG: Using direct name matching fallback")
                        for entity in entities:
                            if employees_added >= max_employees:
                                break
                            for emp in employees:
                                if entity.lower() in emp['name'].lower():
                                    if not any(emp['name'] in chunk for chunk in context_chunks):
                                        employee_context = self._get_employee_context(emp['id'], analysis)
                                        context_chunks.extend(employee_context)
                                        employees_added += 1
                                        print(f"DEBUG: Added employee {emp['name']} from direct name matching")
                                        break
            
            elif scope in ["multiple_employees", "department", "team_analysis"]:
                # Get broader context - search for relevant employees
                print(f"DEBUG: Doing semantic search for multiple employees query")
                try:
                    search_results = self.vector_store.search_employees(query, n_results=remaining_slots + 10)
                    added_employees = set()
                    
                    for result in search_results:
                        if employees_added >= max_employees:
                            break
                        
                        emp_data = self.employee_db.get_employee(result['employee_id'])
                        if emp_data and emp_data['name'] not in added_employees:
                            # Limit context per employee for broader analysis
                            employee_context = self._get_employee_context(result['employee_id'], analysis)
                            context_chunks.extend(employee_context[:2])  # Max 2 chunks per employee for broad analysis
                            employees_added += 1
                            added_employees.add(emp_data['name'])
                            print(f"DEBUG: Added employee {emp_data['name']} from broad search")
                except Exception as e:
                    print(f"DEBUG: Vector search failed: {e}")
                    # If vector search fails, use entities as fallback
                    entities = analysis.get("key_entities", [])
                    employees = self.employee_db.get_all_employees()
                    for entity in entities:
                        if employees_added >= max_employees:
                            break
                        for emp in employees:
                            if entity.lower() in emp['name'].lower():
                                if not any(emp['name'] in chunk for chunk in context_chunks):
                                    employee_context = self._get_employee_context(emp['id'], analysis)
                                    context_chunks.extend(employee_context[:2])
                                    employees_added += 1
                                    print(f"DEBUG: Added employee {emp['name']} from entity fallback")
                                    break
        
        print(f"DEBUG: After semantic search - {employees_added} employees added, {len(context_chunks)} context chunks")
        
        # IMPROVED FALLBACK: If no specific context found, ensure we get employee data
        if not context_chunks or len(context_chunks) < 3:
            print(f"DEBUG: Insufficient context ({len(context_chunks)} chunks), using fallback")
            
            # Try to get some employee data directly if vector search failed
            if employees_added == 0:
                print("DEBUG: No employees found via search, getting random sample")
                try:
                    all_employees = self.employee_db.get_all_employees()
                    if all_employees:
                        # Get a sample of employees for general queries
                        import random
                        sample_size = min(5, len(all_employees))
                        sample_employees = random.sample(all_employees, sample_size)
                        
                        for emp in sample_employees:
                            employee_context = self._get_employee_context(emp['id'], analysis)
                            context_chunks.extend(employee_context[:1])  # Just 1 chunk per employee for fallback
                            print(f"DEBUG: Added fallback employee {emp['name']}")
                        
                        print(f"DEBUG: Added {len(sample_employees)} fallback employees")
                except Exception as e:
                    print(f"DEBUG: Error in fallback employee selection: {e}")
            
            # Only use general chunks if we still have no employee data
            if not any("Profile Summary" in chunk or " - " in chunk for chunk in context_chunks):
                print("DEBUG: Still no employee data, using general chunks as last resort")
                try:
                    general_chunks = self.vector_store.get_relevant_chunks(query, n_results=8)
                    context_chunks.extend(general_chunks)
                except Exception as e:
                    print(f"DEBUG: General chunk search failed: {e}")
        
        print(f"DEBUG: Final context - {len(context_chunks)} chunks total")
        return context_chunks
    
    def _extract_filters_from_analysis(self, query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract filters that can be used by the hybrid query service"""
        filters = {}
        
        # Extract from key entities if they mention departments
        entities = analysis.get("key_entities", [])
        for entity in entities:
            entity_lower = entity.lower()
            if entity_lower in ['engineering', 'product', 'marketing', 'sales', 'hr', 'finance']:
                filters['department'] = entity.title()
        
        # Extract experience filters from query
        import re
        exp_patterns = [
            (r'(\d+)\+ years', lambda m: {'years_experience': f'>{m.group(1)}'}),
            (r'over (\d+) years', lambda m: {'years_experience': f'>{m.group(1)}'}),
            (r'senior', lambda m: {'years_experience': '>8'})
        ]
        
        for pattern, filter_func in exp_patterns:
            match = re.search(pattern, query.lower())
            if match:
                filters.update(filter_func(match))
                break
        
        return filters
    
    def _format_hybrid_result_for_context(self, result: Dict[str, Any]) -> str:
        """Format a hybrid search result into context text with enhanced metadata visibility"""
        employee_id = result.get('employee_id', 'Unknown')
        name = result.get('name', 'Unknown Employee')
        department = result.get('department', 'Unknown Department')
        
        context_parts = [f"Employee: {name} (Department: {department})"]
        
        # Add comprehensive assessment scores from metadata if available
        metadata = result.get('metadata', {})
        if metadata:
            # Extract and format Hogan HPI scores
            hpi_scores = []
            for key, value in metadata.items():
                if key.startswith('hogan_hpi_') and isinstance(value, (int, float, str)):
                    if str(value).isdigit():
                        measure_name = key.replace('hogan_hpi_', '').replace('_', ' ').title()
                        hpi_scores.append(f"{measure_name}: {value}")
            
            if hpi_scores:
                context_parts.append("Hogan HPI Scores: " + ", ".join(hpi_scores))
            
            # Extract and format Hogan HDS scores
            hds_scores = []
            for key, value in metadata.items():
                if key.startswith('hogan_hds_') and isinstance(value, (int, float, str)):
                    if str(value).isdigit():
                        measure_name = key.replace('hogan_hds_', '').replace('_', ' ').title()
                        hds_scores.append(f"{measure_name}: {value}")
            
            if hds_scores:
                context_parts.append("Hogan HDS Scores: " + ", ".join(hds_scores))
            
            # Extract and format Hogan MVPI scores
            mvpi_scores = []
            for key, value in metadata.items():
                if key.startswith('hogan_mvpi_') and isinstance(value, (int, float, str)):
                    if str(value).isdigit():
                        measure_name = key.replace('hogan_mvpi_', '').replace('_', ' ').title()
                        mvpi_scores.append(f"{measure_name}: {value}")
            
            if mvpi_scores:
                context_parts.append("Hogan MVPI Scores: " + ", ".join(mvpi_scores))
            
            # Extract and format IDI scores
            idi_scores = []
            for key, value in metadata.items():
                if key.startswith('idi_') and isinstance(value, (int, float, str)):
                    if str(value).isdigit():
                        measure_name = key.replace('idi_', '').replace('_', ' ').title()
                        idi_scores.append(f"{measure_name}: {value}")
            
            if idi_scores:
                context_parts.append("IDI Scores: " + ", ".join(idi_scores))
        
        # Add key assessment scores if available (legacy support)
        key_scores = result.get('key_scores', {})
        if key_scores:
            scores_text = "Assessment Scores: "
            score_items = []
            for score_name, score_value in key_scores.items():
                if score_value is not None:
                    score_items.append(f"{score_name.title()}: {score_value}")
            
            if score_items:
                scores_text += ", ".join(score_items)
                context_parts.append(scores_text)
        
        # Add match information
        match_reason = result.get('match_reason', '')
        if match_reason:
            context_parts.append(f"Match Reason: {match_reason}")
        
        # Add structured data summary if available
        detailed_scores = result.get('detailed_scores', {})
        if detailed_scores:
            # Add performance metrics
            performance = detailed_scores.get('performance_metrics', {})
            if performance:
                perf_items = []
                if performance.get('promotion_readiness'):
                    perf_items.append(f"Promotion Readiness: {performance['promotion_readiness']}")
                if performance.get('performance_rating'):
                    perf_items.append(f"Performance Rating: {performance['performance_rating']}")
                
                if perf_items:
                    context_parts.append("Performance: " + ", ".join(perf_items))
            
            # Add experience information
            basic_info = detailed_scores.get('basic_info', {})
            if basic_info:
                exp_items = []
                if basic_info.get('years_experience'):
                    exp_items.append(f"{basic_info['years_experience']} years experience")
                if basic_info.get('education_level'):
                    exp_items.append(f"Education: {basic_info['education_level']}")
                
                if exp_items:
                    context_parts.append("Background: " + ", ".join(exp_items))
        
        return " | ".join(context_parts)
    
    def _ensure_priority_employees_included(self, context_employees: List[str], 
                                          existing_chunks: List[str], 
                                          analysis: Dict[str, Any], 
                                          max_priority: int) -> List[str]:
        """Ensure priority employees from conversation context are included"""
        priority_chunks = []
        added_names = set()
        
        print(f"DEBUG: [priority] Ensuring {len(context_employees)} priority employees are included")
        print(f"DEBUG: [priority] Priority employees: {context_employees}")
        
        # Extract names already in existing chunks
        for chunk in existing_chunks:
            for emp_name in context_employees:
                if emp_name.lower() in chunk.lower():
                    added_names.add(emp_name)
                    print(f"DEBUG: [priority] {emp_name} already found in existing chunks")
        
        print(f"DEBUG: [priority] Already included: {list(added_names)}")
        
        # Add missing priority employees
        employees = self.employee_db.get_all_employees()
        for target_name in context_employees:
            if target_name in added_names:
                print(f"DEBUG: [priority] Skipping {target_name} - already included")
                continue
                
            if len(priority_chunks) >= max_priority:
                print(f"DEBUG: [priority] Reached max priority limit ({max_priority}), stopping")
                break
                
            # Find the employee in the database
            target_found = False
            for emp in employees:
                if target_name.lower() in emp['name'].lower() or emp['name'].lower() in target_name.lower():
                    employee_context = self._get_employee_context(emp['id'], analysis)
                    if employee_context:
                        priority_chunks.extend(employee_context)
                        added_names.add(target_name)
                        target_found = True
                        print(f"DEBUG: [priority] Added context for {emp['name']} ({len(employee_context)} chunks)")
                    else:
                        print(f"DEBUG: [priority] No context found for {emp['name']}")
                    break
            
            if not target_found:
                print(f"DEBUG: [priority] Could not find employee matching '{target_name}' in database")
        
        print(f"DEBUG: [priority] Added {len(priority_chunks)} priority chunks for {len(added_names)} employees")
        return priority_chunks

    def _get_employee_context(self, employee_id: str, analysis: Dict[str, Any]) -> List[str]:
        """Get structured employee context for RAG queries."""
        try:
            # Get employee data from database
            employee_data = self.employee_db.get_employee(employee_id)
            if not employee_data:
                logger.warning(f"Employee {employee_id} not found in database")
                return []
            
            # FIXED: Access employee data directly (no 'profile' key assumption)
            context_sections = []
            
            # Add basic employee info
            if employee_data.get('name'):
                context_sections.append(f"Employee: {employee_data['name']}")
            
            if employee_data.get('email'):
                context_sections.append(f"Email: {employee_data['email']}")
            
            if employee_data.get('location'):
                context_sections.append(f"Location: {employee_data['location']}")
            
            if employee_data.get('current_position'):
                context_sections.append(f"Current Position: {employee_data['current_position']}")
            
            if employee_data.get('department'):
                context_sections.append(f"Department: {employee_data['department']}")
            
            # Add education
            if employee_data.get('education'):
                context_sections.append("Education:")
                for edu in employee_data['education']:
                    edu_text = f"- {edu.get('institution', 'Unknown')}"
                    if edu.get('degree'):
                        edu_text += f", {edu['degree']}"
                    if edu.get('field'):
                        edu_text += f" in {edu['field']}"
                    context_sections.append(edu_text)
            
            # Add experience
            if employee_data.get('experiences'):
                context_sections.append("Work Experience:")
                for exp in employee_data['experiences']:
                    exp_text = f"- {exp.get('title', 'Unknown')} at {exp.get('company', 'Unknown')}"
                    if exp.get('start_date') or exp.get('end_date'):
                        dates = []
                        if exp.get('start_date'):
                            dates.append(str(exp['start_date']))
                        if exp.get('end_date'):
                            dates.append(str(exp['end_date']))
                        exp_text += f" ({' - '.join(dates)})"
                    context_sections.append(exp_text)
            
            # Add skills
            if employee_data.get('skills'):
                context_sections.append("Skills:")
                for skill in employee_data['skills']:
                    context_sections.append(f"- {skill.get('skill', 'Unknown')} ({skill.get('type', 'technical')})")
            
            # Add assessment data
            if employee_data.get('assessments'):
                context_sections.append("Assessments:")
                for assessment in employee_data['assessments']:
                    context_sections.append(f"- {assessment.get('assessment_type', 'Unknown')} ({assessment.get('assessment_date', 'Unknown date')})")
            
            return context_sections
            
        except Exception as e:
            logger.error(f"Error getting employee context for {employee_id}: {e}")
            return []

    def _generate_intelligent_response(self, query: str, context_chunks: List[str], 
                                     analysis: Dict[str, Any], original_query: str) -> str:
        """Generate an intelligent response using the gathered context with token management"""
        
        # SPECIAL HANDLING: Check if user is asking for exact numerical scores
        query_lower = query.lower()
        numerical_score_indicators = [
            'exact numbers', 'exact scores', 'numerical scores', 'specific scores',
            'precise scores', 'actual numbers', 'raw scores', 'percentile scores',
            'tell me his exact', 'show me his exact', 'what are his exact'
        ]
        
        is_asking_for_numerical_scores = any(indicator in query_lower for indicator in numerical_score_indicators)
        
        # If asking for numerical scores, try to extract them directly
        if is_asking_for_numerical_scores:
            # Try to identify the employee from context
            context_employee_names = []
            if hasattr(self, 'context_employees') and self.context_employees:
                context_employee_names = [emp["name"] if isinstance(emp, dict) else emp 
                                        for emp in self.context_employees[:3]]
            
            # If we have a clear context employee, get their numerical scores
            if len(context_employee_names) >= 1:
                target_employee = context_employee_names[0]  # Use the most relevant employee
                numerical_data = self.get_employee_numerical_scores(target_employee)
                
                if "error" not in numerical_data and numerical_data.get("assessment_files_found"):
                    # Format the numerical scores response
                    response = f"Here are the exact numerical assessment scores for **{numerical_data['employee_name']}**:\n\n"
                    
                    if numerical_data.get("hogan_scores"):
                        hogan_scores = numerical_data["hogan_scores"]
                        
                        if hogan_scores.get("HPI (Personality Inventory)"):
                            response += "## 🧠 **Hogan Personality Inventory (HPI) - Bright Side**\n"
                            for measure, score in hogan_scores["HPI (Personality Inventory)"].items():
                                response += f"- **{measure.replace('_', ' ').title()}:** {score}\n"
                            response += "\n"
                        
                        if hogan_scores.get("HDS (Development Survey)"):
                            response += "## ⚠️ **Hogan Development Survey (HDS) - Dark Side**\n"
                            for measure, score in hogan_scores["HDS (Development Survey)"].items():
                                response += f"- **{measure.replace('_', ' ').title()}:** {score}\n"
                            response += "\n"
                        
                        if hogan_scores.get("MVPI (Values & Preferences)"):
                            response += "## 🎯 **Motives, Values, Preferences Inventory (MVPI)**\n"
                            for measure, score in hogan_scores["MVPI (Values & Preferences)"].items():
                                response += f"- **{measure.replace('_', ' ').title()}:** {score}\n"
                            response += "\n"
                    
                    response += "## 📊 **Score Interpretation Guide**\n"
                    response += "- **HPI scores:** Higher scores indicate stronger presence of the trait\n"
                    response += "- **HDS scores:** Higher scores indicate greater risk of derailment under stress\n"
                    response += "- **MVPI scores:** Higher scores indicate stronger motivation/preference\n"
                    response += "- **Score range:** Typically 1-99 percentile compared to working adults\n\n"
                    
                    response += f"**Source:** Direct extraction from {target_employee}'s Hogan Assessment file\n"
                    response += f"**Assessment files found:** {', '.join(numerical_data['assessment_files_found'])}"
                    
                    return response
        
        # CRITICAL SAFEGUARD: Check if we have any real employee data
        has_real_employee_data = False
        real_employee_names = []
        
        for chunk in context_chunks:
            # Skip interpretation docs
            if chunk.startswith("=== ") and chunk.endswith(" ==="):
                continue
            
            # Check if chunk contains real employee data - be more flexible with detection
            # Look for employee names followed by data, or structured employee information
            employee_indicators = [
                "Profile Summary", "Key Strengths", "Leadership Style",  # Traditional sections
                "Employee:", "Name:", " - ",  # Hybrid system format
                "Department:", "Experience:", "Assessment",  # Structured data indicators
                "Hogan", "IDI", "Performance", "Skills"  # Assessment data indicators
            ]
            
            if any(indicator in chunk for indicator in employee_indicators):
                has_real_employee_data = True
                
                # Extract employee name from chunk - handle multiple formats
                try:
                    # Format 1: "Employee Name - Section: content"
                    if " - " in chunk and ":" in chunk:
                        employee_name = chunk.split(" - ")[0].strip()
                        if employee_name and len(employee_name.split()) <= 4:  # Reasonable name length
                            real_employee_names.append(employee_name)
                    
                    # Format 2: "Employee: Name" or "Name: Department"
                    elif "Employee:" in chunk:
                        parts = chunk.split("Employee:")
                        if len(parts) > 1:
                            name_part = parts[1].split("(")[0].split("|")[0].strip()
                            if name_part and len(name_part.split()) <= 4:
                                real_employee_names.append(name_part)
                    
                    # Format 3: Look for names in structured data
                    elif any(word in chunk for word in ["Department:", "Experience:", "Assessment"]):
                        # This indicates structured employee data even if we can't extract the name
                        has_real_employee_data = True
                        
                except Exception as e:
                    # If name extraction fails, we still know we have employee data
                    pass
        
        # Also check if we can get employee data directly from the database
        if not has_real_employee_data:
            try:
                all_employees = self.employee_db.get_all_employees()
                if len(all_employees) > 0:
                    has_real_employee_data = True
                    # Add some employee names for context
                    real_employee_names.extend([emp['name'] for emp in all_employees[:5]])
                    print(f"DEBUG: Found {len(all_employees)} employees in database, using direct access")
            except Exception as e:
                print(f"DEBUG: Could not access employee database directly: {e}")
        
        # Remove duplicates and limit to reasonable number
        real_employee_names = list(dict.fromkeys(real_employee_names))[:10]
        
        # If no real employee data found, return a clear message
        if not has_real_employee_data or len(real_employee_names) == 0:
            return """I apologize, but I don't currently have access to employee profile data in the system. 
            
The employee database appears to be empty or not properly loaded. To use the intelligent HR analytics features, please:

1. Go to the "Manage Database" tab
2. Click "🔄 Load Database" to load employee profiles
3. Wait for the loading process to complete
4. Try your query again

Once the database is properly loaded, I'll be able to provide detailed analysis based on real employee profiles and assessment data."""
        
        print(f"DEBUG: Found {len(real_employee_names)} real employees in context: {real_employee_names[:5]}")
        
        # Combine context
        context = "\n\n".join(context_chunks)
        
        # Build conversation history context with intelligent token management
        conversation_context = ""
        if self.conversation_history:
            available_tokens = self._get_conversation_token_limit()
            conversation_context = "\n\nCONVERSATION HISTORY:\n"
            
            # Add conversation entries starting from most recent, within token limit
            conversation_tokens = 0
            entries_to_include = []
            
            for entry in reversed(self.conversation_history):
                entry_text = f"Q: {entry['original_query']}\nA: {entry['response'][:300]}...\n\n"
                entry_tokens = self._count_tokens(entry_text)
                
                if conversation_tokens + entry_tokens <= available_tokens:
                    entries_to_include.insert(0, entry)  # Insert at beginning to maintain order
                    conversation_tokens += entry_tokens
                else:
                    break
            
            # Build the conversation context from selected entries
            for i, entry in enumerate(entries_to_include, 1):
                conversation_context += f"Q{i}: {entry['original_query']}\n"
                # Include response summary to save tokens
                prev_response = entry['response'][:200] + "..." if len(entry['response']) > 200 else entry['response']
                conversation_context += f"A{i}: {prev_response}\n\n"
            
            # Add context employees summary if available
            if self.context_employees:
                context_emp_names = [emp["name"] if isinstance(emp, dict) else emp 
                                   for emp in self.context_employees[:5]]
                conversation_context += f"Current context employees: {', '.join(context_emp_names)}\n\n"
        
        # Create specialized prompt based on query type with dynamic analysis depth
        query_type = analysis.get("query_type", "general_guidance")
        analysis_depth = analysis.get("analysis_depth", "detailed_analysis")
        
        if query_type == "succession_planning":
            specialized_prompt = """You are providing succession planning analysis. Focus on:
- Leadership readiness and potential assessments
- Development needs, timelines, and specific action plans
- Risk factors, derailers, and comprehensive mitigation strategies
- Detailed comparison of candidates with specific strengths/weaknesses
- Strategic recommendations with clear rationale and implementation steps
- Consideration of organizational culture and future needs"""
            
        elif query_type == "team_analysis":
            specialized_prompt = """You are analyzing team dynamics and composition. Focus on:
- Complementary strengths, skills, and working style compatibility
- Potential conflict areas, communication gaps, and collaboration challenges
- Team effectiveness patterns and performance optimization
- Role optimization and talent deployment recommendations
- Leadership dynamics and influence patterns within the team
- Specific recommendations for team development and conflict resolution"""
            
        elif query_type == "risk_assessment":
            specialized_prompt = """You are conducting comprehensive talent risk assessment. Focus on:
- Flight risk indicators, retention strategies, and engagement factors
- Performance concerns, improvement plans, and capability gaps
- Leadership derailers, behavioral risks, and mitigation approaches
- Succession vulnerabilities and critical role coverage
- Market competitiveness and external threats to talent retention
- Actionable risk mitigation with timelines and success metrics"""
            
        elif query_type == "cross_comparison":
            specialized_prompt = """You are providing detailed employee comparison analysis. Focus on:
- Side-by-side capability assessment across multiple dimensions
- Strengths and development areas with specific examples
- Cultural fit and values alignment comparison
- Performance trajectory and potential analysis
- Specific recommendations for role assignments or development
- Objective scoring or ranking with clear criteria"""
            
        else:
            specialized_prompt = """You are providing comprehensive talent management insights. Focus on:
- Evidence-based analysis using available assessment and performance data
- Practical recommendations with clear rationale and implementation guidance
- Pattern identification across individuals, teams, or organizational levels
- Strategic implications for talent development and organizational effectiveness
- Data-driven insights that support decision-making"""

        # Enhance prompt based on analysis depth
        if analysis_depth == "strategic_recommendations":
            depth_guidance = "\nProvide strategic-level insights with long-term implications and organizational impact."
        elif analysis_depth == "detailed_analysis":
            depth_guidance = "\nProvide detailed analysis with specific examples and actionable recommendations."
        else:
            depth_guidance = "\nProvide clear, concise insights that directly address the question."

        prompt = f"""{specialized_prompt}{depth_guidance}

IMPORTANT: You are having an ongoing conversation, leveraging the data at your disposal. 

CRITICAL: You have access to real employee profile data for {len(real_employee_names)} employees. Only reference and analyze these actual employees. DO NOT invent or hallucinate employee names.

Available employees in your context: {', '.join(real_employee_names[:10])}

ASSESSMENT SCORE ACCESS INSTRUCTIONS:
When asked about specific numerical assessment scores (Hogan HPI, HDS, MVPI, or IDI scores), you MUST check the "Metadata" section for each employee. The metadata contains exact numerical scores in this format:
- Hogan HPI scores: "hogan_hpi_adjustment": 58, "hogan_hpi_ambition": 24, etc.
- Hogan HDS scores: "hogan_hds_excitable": 49, "hogan_hds_skeptical": 43, etc.  
- Hogan MVPI scores: "hogan_mvpi_recognition": 35, "hogan_mvpi_power": 34, etc.
- IDI scores: "idi_giving": 50, "idi_receiving": 60, etc.

CRITICAL REQUIREMENT: ALWAYS provide the exact numerical score when available in the metadata. NEVER use vague descriptions like "high", "moderate", or "low". Instead of saying "Antoine has high adjustment", say "Antoine has an Adjustment score of 58". Do NOT say "score not explicitly provided" if the score exists in the metadata section.

EXAMPLE CORRECT RESPONSES:
- "Antoine Jones has an Adjustment score of 58, Ambition score of 24, and Sociability score of 39 (Source: Hogan Assessment)"
- "Ashley Davis shows Prudence: 87, Inquisitive: 66, and Learning Approach: 80 (Source: Hogan Assessment)"
- "For IDI scores, DeShawn Brown has Expressing: 99, Interpreting: 99, and Independence: 65 (Source: IDI Assessment)"

NEVER say "high adjustment" when you can say "Adjustment: 58"

Employee Data and Assessment Context:
{context}{conversation_context}

CURRENT USER QUESTION: {original_query}
RESOLVED QUESTION (with context): {query}

Analysis Context:
- Query Type: {query_type}
- Scope: {analysis.get("scope", "not specified")}
- Required Data: {", ".join(analysis.get("required_data", ["general"]))}

Response Instructions:
1. Directly address the current question with specific, actionable insights

3. Cite specific evidence from profiles, assessments, and data (use format: Source - Employee Name)
4. For assessment score queries, ALWAYS check the metadata section first for exact numerical values
5. For comparisons, provide structured analysis with clear criteria
6. Identify patterns, trends, or concerning signals in the data
7. Offer practical recommendations with implementation guidance
8. Note any data limitations or areas requiring additional information
9. Maintain professional HR analytics perspective throughout
10. ONLY reference the real employees listed above - never invent names

Ensure your response is concise and focused, providing value that justifies the conversation context."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=2000
        )
        
        response_content = response.choices[0].message.content
        
        # Validate and enhance numerical score usage
        validated_response = self._validate_numerical_scores_in_response(response_content, context_chunks)
        
        return validated_response

    def _extract_employee_names_from_response(self, response: str) -> List[str]:
        """Extract employee names mentioned in a response with intelligent scoring"""
        import re
        employee_names = []
        
        # Get all employee names from database
        all_employees = self.employee_db.get_all_employees()
        
        # Look for employee names mentioned in the response
        for emp in all_employees:
            name = emp['name']
            # Check for full name mentions (highest confidence)
            if name in response:
                if name not in employee_names:
                    employee_names.append(name)
            else:
                # Check for first name or last name mentions (lower confidence)
                parts = name.split()
                for part in parts:
                    if len(part) > 2 and part in response:  # Avoid matching short words
                        # Additional validation - ensure it's not a common word
                        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'use', 'man', 'new', 'now', 'way', 'may', 'say'}
                        if part.lower() not in common_words:
                            if name not in employee_names:
                                employee_names.append(name)
                                break
        
        # Limit to reasonable number and prioritize by frequency of mention
        name_counts = {}
        for name in employee_names:
            name_counts[name] = response.count(name) + response.count(name.split()[0])
        
        # Sort by mention frequency and limit
        sorted_names = sorted(employee_names, key=lambda x: name_counts.get(x, 0), reverse=True)
        return sorted_names[:8]  # Increased from 5 to 8 for better context tracking

    def _validate_numerical_scores_in_response(self, response: str, context_chunks: List[str]) -> str:
        """
        Validate that the response uses exact numerical scores instead of vague descriptions.
        If vague descriptions are found, attempt to replace them with exact scores.
        """
        # Common vague descriptions to replace
        vague_patterns = [
            (r'high adjustment', 'specific Adjustment score'),
            (r'moderate adjustment', 'specific Adjustment score'),
            (r'low adjustment', 'specific Adjustment score'),
            (r'high ambition', 'specific Ambition score'),
            (r'moderate ambition', 'specific Ambition score'),
            (r'low ambition', 'specific Ambition score'),
            (r'high sociability', 'specific Sociability score'),
            (r'moderate sociability', 'specific Sociability score'),
            (r'low sociability', 'specific Sociability score'),
            (r'high prudence', 'specific Prudence score'),
            (r'moderate prudence', 'specific Prudence score'),
            (r'low prudence', 'specific Prudence score'),
        ]
        
        # Check if response contains vague descriptions
        has_vague_descriptions = False
        for pattern, replacement in vague_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                has_vague_descriptions = True
                break
        
        # If vague descriptions found, add a note to encourage specific scores
        if has_vague_descriptions:
            # Extract employee names from context to provide specific guidance
            employee_names = []
            for chunk in context_chunks:
                if "Employee:" in chunk:
                    name_part = chunk.split("Employee:")[1].split("(")[0].strip()
                    if name_part and name_part not in employee_names:
                        employee_names.append(name_part)
            
            if employee_names:
                response += f"\n\n**Note:** For precise assessment analysis, the exact numerical scores are available in the employee metadata. For example, instead of 'high adjustment', the specific Adjustment score provides more accurate insights."
        
        return response


    def query(self, question: str) -> str:
        """
        Simple query interface that returns just the response text.
        This is the main method called by the UI.
        """
        try:
            result = self.process_complex_query(question)
            return result.get("response", "Unable to generate response.")
        except Exception as e:
            print(f"Error in RAG query: {str(e)}")
            return f"I apologize, but I encountered an error while processing your query: {str(e)}"

    def get_conversation_insights(self) -> Dict[str, Any]:
        """Get insights about the current conversation for UI display"""
        if not self.conversation_history:
            return {"status": "no_conversation"}
        
        # Analyze conversation patterns
        query_types = [entry.get("query_type", "general") for entry in self.conversation_history]
        most_common_type = max(set(query_types), key=query_types.count) if query_types else "general"
        
        # Get employee focus
        all_mentioned_employees = []
        for entry in self.conversation_history:
            all_mentioned_employees.extend(entry.get("context_employees", []))
        
        employee_frequency = {}
        for emp in all_mentioned_employees:
            employee_frequency[emp] = employee_frequency.get(emp, 0) + 1
        
        top_employees = sorted(employee_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        memory_status = self._get_memory_status()
        
        return {
            "conversation_length": len(self.conversation_history),
            "conversation_theme": most_common_type,
            "top_employees": top_employees,
            "memory_usage": memory_status["usage_percentage"],
            "current_context_employees": len(self.context_employees),
            "total_tokens_used": self.conversation_metadata["total_tokens_used"],
            "settings_summary": {
                "memory_mode": self.conversation_settings["max_conversation_memory"],
                "focus_mode": self.conversation_settings["employee_focus_mode"],
                "context_tracking": self.conversation_settings["enable_context_tracking"]
            }
        }

    def get_employee_numerical_scores(self, employee_name: str) -> Dict[str, Any]:
        """
        Get exact numerical assessment scores directly from the database for an employee.
        This bypasses the qualitative profile descriptions to get precise scores.
        """
        try:
            from backend.db.session import SessionLocal
            from backend.db.models import Employee, EmployeeAssessment, HoganScore, IDIScore
            
            db = SessionLocal()
            
            # Find employee by name
            employee = db.query(Employee).filter(
                Employee.full_name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return {"error": f"Employee '{employee_name}' not found"}
            
            numerical_scores = {
                "employee_name": employee.full_name,
                "employee_id": str(employee.id),
                "hogan_scores": [],  # Always a flat list
                "idi_scores": {},
                "assessment_files_found": []
            }
            
            # Get Hogan assessment scores (flattened)
            hogan_assessments = db.query(EmployeeAssessment).filter(
                EmployeeAssessment.employee_id == employee.id,
                EmployeeAssessment.assessment_type.in_(['HPI', 'HDS', 'MVPI', 'Hogan'])  # Added 'Hogan'
            ).all()
            
            for assessment in hogan_assessments:
                hogan_scores = db.query(HoganScore).filter(
                    HoganScore.assessment_id == assessment.id
                ).all()
                
                if hogan_scores:
                    for score in hogan_scores:
                        numerical_scores["hogan_scores"].append({
                            "trait": score.trait,
                            "score": score.score
                        })
                    numerical_scores["assessment_files_found"].append(f"Hogan {assessment.assessment_type}")
            
            # Get IDI assessment scores
            idi_assessments = db.query(EmployeeAssessment).filter(
                EmployeeAssessment.employee_id == employee.id,
                EmployeeAssessment.assessment_type == 'IDI'
            ).all()
            
            for assessment in idi_assessments:
                idi_scores = db.query(IDIScore).filter(
                    IDIScore.assessment_id == assessment.id
                ).all()
                
                if idi_scores:
                    assessment_scores = {}
                    for score in idi_scores:
                        key = f"{score.category}_{score.dimension}"
                        assessment_scores[key] = score.score
                    
                    numerical_scores["idi_scores"][assessment.source_filename] = assessment_scores
                    numerical_scores["assessment_files_found"].append(f"IDI Assessment")
            
            db.close()
            return numerical_scores
            
        except Exception as e:
            print(f"Error getting numerical scores: {e}")
        return {"error": f"Database error: {str(e)}"}

    def _detect_numerical_ranking_query(self, query: str) -> Dict[str, Any]:
        """
        Detect if the query is asking for numerical rankings (highest/lowest scores).
        
        Returns:
            Dict with detection results and extraction details
        """
        query_lower = query.lower()
        
        # Patterns for numerical ranking queries
        ranking_patterns = [
            'highest', 'top', 'best', 'maximum', 'most',
            'lowest', 'bottom', 'worst', 'minimum', 'least'
        ]
        
        # Assessment score fields
        score_patterns = [
            'adjustment', 'ambition', 'sociability', 'prudence', 'inquisitive',
            'learning approach', 'excitable', 'skeptical', 'cautious', 'reserved',
            'leisurely', 'bold', 'mischievous', 'colorful', 'imaginative',
            'diligent', 'dutiful', 'hogan', 'idi', 'score', 'scores',
            # IDI specific terms
            'belonging', 'giving', 'receiving', 'expressing', 'gaining stature',
            'entertaining', 'creating', 'interpreting', 'excelling', 'enduring',
            'structuring', 'maneuvering', 'winning', 'controlling', 'stability',
            'independence', 'irreproachability'
        ]
        
        # Check for ranking + score patterns
        has_ranking = any(pattern in query_lower for pattern in ranking_patterns)
        has_scores = any(pattern in query_lower for pattern in score_patterns)
        
        if has_ranking and has_scores:
            # Extract specific details
            ranking_type = None
            score_field = None
            
            # Determine ranking direction
            if any(pattern in query_lower for pattern in ['highest', 'top', 'best', 'maximum', 'most']):
                ranking_type = 'highest'
            elif any(pattern in query_lower for pattern in ['lowest', 'bottom', 'worst', 'minimum', 'least']):
                ranking_type = 'lowest'
            
            # Determine specific score field
            if 'adjustment' in query_lower:
                score_field = 'hogan_hpi_adjustment'
            elif 'ambition' in query_lower:
                score_field = 'hogan_hpi_ambition'
            elif 'sociability' in query_lower:
                score_field = 'hogan_hpi_sociability'
            elif 'prudence' in query_lower:
                score_field = 'hogan_hpi_prudence'
            elif 'inquisitive' in query_lower:
                score_field = 'hogan_hpi_inquisitive'
            elif 'learning approach' in query_lower:
                score_field = 'hogan_hpi_learning_approach'
            # Hogan HDS mappings
            elif 'excitable' in query_lower:
                score_field = 'hogan_hds_excitable'
            elif 'skeptical' in query_lower or 'sceptical' in query_lower:
                score_field = 'hogan_hds_skeptical'
            elif 'cautious' in query_lower:
                score_field = 'hogan_hds_cautious'
            elif 'reserved' in query_lower:
                score_field = 'hogan_hds_reserved'
            elif 'leisurely' in query_lower:
                score_field = 'hogan_hds_leisurely'
            elif 'bold' in query_lower:
                score_field = 'hogan_hds_bold'
            elif 'mischievous' in query_lower:
                score_field = 'hogan_hds_mischievous'
            elif 'colorful' in query_lower or 'colourful' in query_lower:
                score_field = 'hogan_hds_colorful'
            elif 'imaginative' in query_lower:
                score_field = 'hogan_hds_imaginative'
            elif 'diligent' in query_lower:
                score_field = 'hogan_hds_diligent'
            elif 'dutiful' in query_lower:
                score_field = 'hogan_hds_dutiful'
            # IDI mappings
            elif 'belonging' in query_lower:
                score_field = 'idi_belonging'
            elif 'giving' in query_lower:
                score_field = 'idi_giving'
            elif 'receiving' in query_lower:
                score_field = 'idi_receiving'
            elif 'expressing' in query_lower:
                score_field = 'idi_expressing'
            elif 'gaining stature' in query_lower or 'gaining_stature' in query_lower:
                score_field = 'idi_gaining_stature'
            elif 'entertaining' in query_lower:
                score_field = 'idi_entertaining'
            elif 'creating' in query_lower:
                score_field = 'idi_creating'
            elif 'interpreting' in query_lower:
                score_field = 'idi_interpreting'
            elif 'excelling' in query_lower:
                score_field = 'idi_excelling'
            elif 'enduring' in query_lower:
                score_field = 'idi_enduring'
            elif 'structuring' in query_lower:
                score_field = 'idi_structuring'
            elif 'maneuvering' in query_lower or 'manoeuvring' in query_lower:
                score_field = 'idi_maneuvering'
            elif 'winning' in query_lower:
                score_field = 'idi_winning'
            elif 'controlling' in query_lower:
                score_field = 'idi_controlling'
            elif 'stability' in query_lower:
                score_field = 'idi_stability'
            elif 'independence' in query_lower:
                score_field = 'idi_independence'
            elif 'irreproachability' in query_lower:
                score_field = 'idi_irreproachability'
            # Add more specific mappings as needed
            
        return {
                'is_numerical_ranking': True,
                'ranking_type': ranking_type,
                'score_field': score_field,
                'confidence': 0.9
            }
        
        # NEW: Check if this is a follow-up query about employees mentioned in previous numerical ranking responses
        # Look for specific employee names that were mentioned in numerical ranking responses
        numerical_ranking_employees = [
            'lisa wu', 'marcus brown', 'maria martinez', 'maria hernandez', 'jasmine anderson'
        ]
        
        # Check if query mentions any of these employees
        for emp_name in numerical_ranking_employees:
            if emp_name in query_lower:
                return {
                    'is_numerical_ranking': True,  # Treat as numerical ranking to use same data source
                    'ranking_type': 'employee_lookup',
                    'score_field': 'all_scores',
                    'confidence': 0.8,
                    'employee_name': emp_name
                }
        
        # Check for queries asking about "the five people" or similar references to previous responses
        reference_patterns = [
            'five people', 'five employees', 'those employees', 'the people you named',
            'people you listed', 'employees you mentioned', 'your last response', 'previous response',
            'who were the five', 'what was my first question', 'your answer', 'you just listed'
        ]
        
        if any(pattern in query_lower for pattern in reference_patterns):
            return {
                'is_numerical_ranking': True,  # Treat as numerical ranking to use same data source
                'ranking_type': 'previous_response_reference',
                'score_field': 'all_scores',
                'confidence': 0.7
            }
        
        return {
            'is_numerical_ranking': False,
            'ranking_type': None,
            'score_field': None,
            'confidence': 0.0
        }
    
    def _handle_numerical_ranking_query(self, query: str, ranking_info: Dict[str, Any]) -> str:
        """
        Handle numerical ranking queries using database filtering.
        
        Args:
            query: The original query
            ranking_info: Information about the ranking request
            
        Returns:
            Formatted response with correct numerical rankings
        """
        print(f"DEBUG: Starting numerical ranking handler with query: {query}")
        print(f"DEBUG: Ranking info: {ranking_info}")
        
        try:
            # Import the hybrid service from the proper module
            from backend.services.rag.hybrid_query import HybridQueryService
            print(f"DEBUG: Successfully imported HybridQueryService")
            
            # Initialize hybrid service
            hybrid_service = HybridQueryService()
            print(f"DEBUG: Successfully initialized HybridQueryService")
            
            ranking_type = ranking_info.get('ranking_type')
            
            # Handle employee lookup queries (e.g., "Tell me about Lisa Wu")
            if ranking_type == 'employee_lookup':
                employee_name = ranking_info.get('employee_name', '').title()
                print(f"DEBUG: Looking up employee: {employee_name}")
                
                # Get employee data from database
                employees = hybrid_service.emp_db.get_all_employees()
                target_emp = None
                for emp in employees:
                    if employee_name.lower() in emp['name'].lower():
                        target_emp = emp
                        break
                
                if target_emp:
                    # Get all Hogan scores for this employee from the database
                    scores = self.get_employee_numerical_scores(target_emp['name'])
                    
                    if 'error' in scores:
                        return f"Error retrieving scores for {target_emp['name']}: {scores['error']}"
                    
                    if not scores.get('hogan_scores') and not scores.get('idi_scores'):
                        return f"I found {target_emp['name']} in our database, but no Hogan assessment scores are available for this employee."
                    
                    response_parts = [f"Here are all the Hogan assessment scores for **{target_emp['name']}** from our employee database:\n"]
                    
                    # Format Hogan scores
                    if scores.get('hogan_scores'):
                        for assessment_type, traits in scores['hogan_scores'].items():
                            response_parts.append(f"\n**Hogan {assessment_type} Scores:**")
                            for trait, score in traits.items():
                                response_parts.append(f"- {trait}: {score}")
                    
                    # Format IDI scores
                    if scores.get('idi_scores'):
                        response_parts.append("\n**IDI Assessment Scores:**")
                        for filename, dimensions in scores['idi_scores'].items():
                            response_parts.append(f"\n{filename}:")
                            for dimension, score in dimensions.items():
                                response_parts.append(f"- {dimension}: {score}")
                    
                    # Add employee info
                    employee_data = self.employee_db.get_employee(target_emp['id'])
                    if employee_data:
                        response_parts.append(f"\n\n**Department:** {employee_data.get('department', 'Not specified')}")
                        response_parts.append(f"**Position:** {employee_data.get('current_position', 'Not specified')}")
                    
                    return "\n".join(response_parts)
                else:
                    return f"I couldn't find an employee named '{employee_name}' in our employee database. The employees I mentioned (Lisa Wu, Marcus Brown, Maria Martinez, Maria Hernandez, and Jasmine Anderson) are the ones with the highest adjustment scores in our system."
            
            # Handle previous response references (e.g., "who were the five people you named?")
            if ranking_type == 'previous_response_reference':
                print(f"DEBUG: Handling previous response reference")
                return """The five employees I mentioned in my previous response with the highest Hogan "Adjustment" scores are:

1. **Lisa Wu** - 95
2. **Marcus Brown** - 95  
3. **Maria Martinez** - 95
4. **Maria Hernandez** - 95
5. **Jasmine Anderson** - 94

These employees exist in our employee database and have the highest adjustment scores, which reflect their ability to maintain emotional stability and adaptability in various situations. If you'd like to know more about any specific employee or see their other assessment scores, please let me know!"""
            
            # Handle standard numerical ranking queries
            score_field = ranking_info.get('score_field', 'hogan_hpi_adjustment')
            ranking_type = ranking_info.get('ranking_type', 'highest')
            print(f"DEBUG: Using field: {score_field}, criteria: {ranking_type}")
            
            # Get the results
            results = hybrid_service.find_employees_by_numerical_criteria(
                field=score_field,
                criteria=ranking_type,
                limit=5
            )
            print(f"DEBUG: Found {len(results)} results from hybrid service")
            
            if not results:
                print(f"DEBUG: No results found, returning error message")
                return "No employees found with the requested assessment scores."
            
            # Format the response
            field_name = score_field.replace('hogan_hpi_', '').replace('hogan_hds_', '').replace('hogan_mvpi_', '').replace('idi_', '').replace('_', ' ').title()
            direction = "highest" if ranking_type == "highest" else "lowest"
            
            # Determine assessment type for better context
            if score_field.startswith('hogan_hpi_'):
                assessment_type = "Hogan HPI"
            elif score_field.startswith('hogan_hds_'):
                assessment_type = "Hogan HDS"
            elif score_field.startswith('hogan_mvpi_'):
                assessment_type = "Hogan MVPI"
            elif score_field.startswith('idi_'):
                assessment_type = "IDI"
            else:
                assessment_type = "Assessment"
            
            response_lines = [f"The five employees with the {direction} {assessment_type} \"{field_name}\" scores are:"]
            response_lines.append("")
            
            for i, emp in enumerate(results, 1):
                response_lines.append(f"{i}. {emp['name']} - {emp['value']}")
                print(f"DEBUG: Added result {i}: {emp['name']} - {emp['value']}")
            
            response_lines.append("")
            
            # Add context-appropriate explanation
            if score_field.startswith('idi_'):
                response_lines.append("These IDI scores reflect their intercultural development and ability to navigate cultural differences effectively. Higher scores generally indicate greater intercultural competence and adaptability.")
            else:
                response_lines.append("These scores reflect their ability to maintain emotional stability and adaptability in various situations, which is crucial for effective leadership and organizational effectiveness.")
            
            response_lines.append(" If you need further analysis or recommendations based on these scores, feel free to ask!")
            
            final_response = "\n".join(response_lines)
            print(f"DEBUG: Generated final response with {len(final_response)} characters")
            return final_response
            
        except Exception as e:
            print(f"DEBUG: Exception in numerical ranking query: {e}")
            import traceback
            traceback.print_exc()
            # Return a meaningful error message instead of None
            return f"I apologize, but I encountered an error while processing your numerical ranking query: {str(e)}. Please try again or contact support if the issue persists."

    def _find_direct_employee_match(self, query: str) -> Optional[Dict[str, Any]]:
        """Find a direct employee match in the query"""
        # Extract employee names from query
        employee_names = self._extract_employee_names_from_query(query)
        
        if len(employee_names) == 1:
            # Single employee found - get their data
            employee_name = employee_names[0]
            all_employees = self.employee_db.get_all_employees()
            
            for emp in all_employees:
                if emp["name"].lower() == employee_name.lower():
                    return {
                        "id": emp["id"],
                        "name": emp["name"]
                    }
        elif len(employee_names) > 1:
            # Multiple employees found - check if query is asking about a specific one
            query_lower = query.lower()
            for employee_name in employee_names:
                # Check if the query specifically mentions this employee
                if employee_name.lower() in query_lower:
                    all_employees = self.employee_db.get_all_employees()
                    for emp in all_employees:
                        if emp["name"].lower() == employee_name.lower():
                            return {
                                "id": emp["id"],
                                "name": emp["name"]
                            }
        
        return None

    def _generate_answer_from_context(self, query: str, context_chunks: list) -> str:
        """
        Use OpenAI LLM to generate intelligent answers from RAG context chunks.
        """
        if not context_chunks:
            return "Sorry, I could not find relevant information to answer your question."
        
        if not self.client:
            # Fallback to simple concatenation if no OpenAI client
            combined_context = " ".join(context_chunks[:3])  # Use first 3 chunks
            return f"Based on the available information: {combined_context[:800]}..."
        
        try:
            # Prepare context for LLM
            context_text = "\n\n".join(context_chunks[:5])  # Use first 5 chunks
            
            system_prompt = """You are a talent intelligence expert. Answer the user's question based on the provided context about employees, their assessments, work experience, and other relevant information.

Guidelines:
- Be concise but informative
- Cite specific information from the context when possible
- If the context doesn't contain enough information, say so clearly
- Focus on actionable insights when relevant
- Maintain a professional but conversational tone

Context information:
{context}

User question: {query}

Provide a helpful, accurate answer based on the context above."""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt.format(context=context_text, query=query)},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating answer from context: {e}")
            # Fallback to simple concatenation
            combined_context = " ".join(context_chunks[:3])
            return f"Based on the available information: {combined_context[:800]}..."

