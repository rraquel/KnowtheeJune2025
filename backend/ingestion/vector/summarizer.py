from typing import Dict, Any

class SummaryGenerator:
    """Generates semantic summaries from assessment data."""
    
    def __init__(self):
        pass

    def summarize(self, text, assessment_type=None):
        return f"Summary for {assessment_type or 'unknown'}: {text[:50]}..."

    def summarize_hogan(self, scores: Dict[str, int]) -> str:
        """
        Generate a summary of Hogan assessment scores.
        
        Args:
            scores: Dictionary of Hogan scale scores
            
        Returns:
            Natural language summary of assessment
        """
        # Define scale descriptions
        scale_descriptions = {
            "Adjustment": "emotional stability and self-confidence",
            "Ambition": "leadership potential and career focus",
            "Sociability": "interpersonal skills and social confidence",
            "Interpersonal Sensitivity": "empathy and relationship building",
            "Prudence": "conscientiousness and rule-following",
            "Inquisitive": "learning orientation and intellectual curiosity",
            "Learning Approach": "training receptivity and development potential"
        }
        
        # Generate summary
        summary = []
        summary.append("Hogan Assessment Summary:")
        
        # Add overall impression
        high_scores = {k: v for k, v in scores.items() if v >= 70}
        low_scores = {k: v for k, v in scores.items() if v <= 30}
        
        if high_scores:
            summary.append("\nKey Strengths:")
            for scale, score in high_scores.items():
                desc = scale_descriptions.get(scale, scale.lower())
                summary.append(f"- Strong {desc} (score: {score})")
        
        if low_scores:
            summary.append("\nDevelopment Areas:")
            for scale, score in low_scores.items():
                desc = scale_descriptions.get(scale, scale.lower())
                summary.append(f"- Limited {desc} (score: {score})")
        
        # Add moderate scores
        moderate_scores = {k: v for k, v in scores.items() if 30 < v < 70}
        if moderate_scores:
            summary.append("\nModerate Areas:")
            for scale, score in moderate_scores.items():
                desc = scale_descriptions.get(scale, scale.lower())
                summary.append(f"- Average {desc} (score: {score})")
        
        return "\n".join(summary)
    
    def summarize_idi(self, scores: Dict[str, int]) -> str:
        """
        Generate a summary of IDI assessment scores.
        
        Args:
            scores: Dictionary of IDI scale scores
            
        Returns:
            Natural language summary of assessment
        """
        # Define scale descriptions
        scale_descriptions = {
            "Denial": "awareness of cultural differences",
            "Defense": "reaction to cultural differences",
            "Minimization": "understanding of cultural commonalities",
            "Acceptance": "appreciation of cultural differences",
            "Adaptation": "ability to adapt to different cultures"
        }
        
        # Generate summary
        summary = []
        summary.append("IDI Assessment Summary:")
        
        # Add overall impression
        high_scores = {k: v for k, v in scores.items() if v >= 70}
        low_scores = {k: v for k, v in scores.items() if v <= 30}
        
        if high_scores:
            summary.append("\nKey Strengths:")
            for scale, score in high_scores.items():
                desc = scale_descriptions.get(scale, scale.lower())
                summary.append(f"- Strong {desc} (score: {score})")
        
        if low_scores:
            summary.append("\nDevelopment Areas:")
            for scale, score in low_scores.items():
                desc = scale_descriptions.get(scale, scale.lower())
                summary.append(f"- Limited {desc} (score: {score})")
        
        # Add moderate scores
        moderate_scores = {k: v for k, v in scores.items() if 30 < v < 70}
        if moderate_scores:
            summary.append("\nModerate Areas:")
            for scale, score in moderate_scores.items():
                desc = scale_descriptions.get(scale, scale.lower())
                summary.append(f"- Average {desc} (score: {score})")
        
        return "\n".join(summary) 