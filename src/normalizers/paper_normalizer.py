"""Paper normalization to common schema"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime


def infer_study_type(paper: Dict[str, Any]) -> str:
    """
    Infer study type from paper metadata
    
    Args:
        paper: Paper dictionary
        
    Returns:
        Study type: 'systematic_review', 'meta_analysis', 'randomized_trial',
                   'case_study', 'survey', 'experimental', 'theoretical', 'other'
    """
    title = paper.get("title", "").lower()
    abstract = paper.get("abstract", "").lower()
    keywords = " ".join(paper.get("keywords", [])).lower()
    text = f"{title} {abstract} {keywords}"
    
    # Systematic review / Meta-analysis
    if any(term in text for term in ["systematic review", "meta-analysis", "meta analysis"]):
        if "meta-analysis" in text or "meta analysis" in text:
            return "meta_analysis"
        return "systematic_review"
    
    # Randomized controlled trial
    if any(term in text for term in ["randomized", "randomised", "rct", "controlled trial"]):
        return "randomized_trial"
    
    # Case study
    if any(term in text for term in ["case study", "case report", "case series"]):
        return "case_study"
    
    # Survey
    if any(term in text for term in ["survey", "questionnaire", "cross-sectional"]):
        return "survey"
    
    # Experimental
    if any(term in text for term in ["experiment", "experimental", "empirical"]):
        return "experimental"
    
    # Theoretical
    if any(term in text for term in ["theoretical", "theory", "framework", "model"]):
        return "theoretical"
    
    return "other"


class PaperNormalizer:
    """Normalize papers from different sources to common schema"""
    
    # Study type priority (higher = better for evidence)
    STUDY_TYPE_PRIORITY = {
        "meta_analysis": 1.0,
        "systematic_review": 0.9,
        "randomized_trial": 0.8,
        "experimental": 0.7,
        "case_study": 0.6,
        "survey": 0.6,
        "theoretical": 0.5,
        "other": 0.4
    }
    
    def normalize(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize paper to common schema
        
        Args:
            paper: Raw paper dictionary from collector
            
        Returns:
            Normalized paper dictionary
        """
        normalized = {
            "source": paper.get("source", "unknown"),
            "id": paper.get("id", ""),
            "title": self._normalize_text(paper.get("title", "")),
            "authors": paper.get("authors", []),
            "year": paper.get("year"),
            "venue": paper.get("venue", ""),
            "journal": paper.get("journal"),
            "abstract": self._normalize_text(paper.get("abstract", "")),
            "url": paper.get("url", ""),
            "keywords": paper.get("keywords", []),
            "study_type": infer_study_type(paper),
            "retrieval_score": 0.0,  # Will be set by ranking
            "doi": paper.get("doi"),
            "pdf_url": paper.get("pdf_url"),
            "categories": paper.get("categories", []),
            "primary_category": paper.get("primary_category"),
        }
        
        # Add study type priority
        normalized["study_type_priority"] = self.STUDY_TYPE_PRIORITY.get(
            normalized["study_type"], 0.4
        )
        
        # Add evidence completeness score
        normalized["evidence_completeness"] = self._calculate_completeness(normalized)
        
        return normalized
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text (remove extra whitespace, etc.)"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _calculate_completeness(self, paper: Dict[str, Any]) -> float:
        """
        Calculate evidence completeness score
        
        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        
        # Title (required)
        if paper.get("title"):
            score += 0.1
        
        # Abstract (important)
        abstract = paper.get("abstract", "")
        if abstract:
            score += 0.3
            # Longer abstracts are better
            if len(abstract) > 500:
                score += 0.1
        
        # Authors
        if paper.get("authors"):
            score += 0.1
        
        # Year
        if paper.get("year"):
            score += 0.1
        
        # Venue/Journal
        if paper.get("venue") or paper.get("journal"):
            score += 0.1
        
        # Keywords
        if paper.get("keywords"):
            score += 0.1
        
        # DOI
        if paper.get("doi"):
            score += 0.1
        
        # PDF URL
        if paper.get("pdf_url"):
            score += 0.05
        
        return min(score, 1.0)
    
    def normalize_batch(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize a batch of papers"""
        return [self.normalize(paper) for paper in papers]

