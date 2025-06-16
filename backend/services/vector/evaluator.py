from typing import List, Dict, Any, Optional
import numpy as np
from .embedders import BaseEmbedder

class EmbeddingEvaluator:
    """Evaluates embedding quality using various metrics."""
    
    def __init__(self, embedder: BaseEmbedder):
        self.embedder = embedder
    
    def evaluate(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate a single query and its results."""
        return self.evaluate_query(query, results)
    
    def calculate_metrics(self, query: str, results: List[Dict[str, Any]], k: int = 3) -> Dict[str, float]:
        """Calculate all metrics for a query."""
        metrics = {}
        for i in range(1, k + 1):
            metrics[f'precision@{i}'] = self.calculate_precision_at_k(query, results, i)
            metrics[f'recall@{i}'] = self.calculate_recall_at_k(query, results, i)
            metrics[f'ndcg@{i}'] = self.calculate_ndcg_at_k(query, results, i)
        return metrics
    
    def calculate_precision_at_k(self, query: str, results: List[Dict[str, Any]], k: int) -> float:
        """Calculate precision@k for a query."""
        if not results:
            return 0.0
        
        k = min(k, len(results))
        relevant = sum(1 for r in results[:k] if r.get('relevant', False))
        return relevant / k
    
    def calculate_recall_at_k(self, query: str, results: List[Dict[str, Any]], k: int) -> float:
        """Calculate recall@k for a query."""
        if not results:
            return 0.0
        
        total_relevant = sum(1 for r in results if r.get('relevant', False))
        if total_relevant == 0:
            return 0.0
        
        k = min(k, len(results))
        relevant_found = sum(1 for r in results[:k] if r.get('relevant', False))
        return relevant_found / total_relevant
    
    def calculate_ndcg_at_k(self, query: str, results: List[Dict[str, Any]], k: int) -> float:
        """Calculate NDCG@k for a query."""
        if not results:
            return 0.0
        
        k = min(k, len(results))
        dcg = 0.0
        idcg = 0.0
        
        # Calculate DCG
        for i, result in enumerate(results[:k]):
            if result.get('relevant', False):
                dcg += 1.0 / np.log2(i + 2)  # i+2 because log2(1) = 0
        
        # Calculate IDCG (ideal case where all relevant docs are at the top)
        relevant_count = sum(1 for r in results if r.get('relevant', False))
        for i in range(min(k, relevant_count)):
            idcg += 1.0 / np.log2(i + 2)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def evaluate_query(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate a single query and return its metrics."""
        return self.calculate_metrics(query, results)
    
    def evaluate_batch(self, queries: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """Evaluate multiple queries and return their metrics."""
        return [self.evaluate_query(q['query'], q['results']) for q in queries] 