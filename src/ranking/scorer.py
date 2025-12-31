"""Feature-based ranking scorer"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
from datetime import datetime


@dataclass
class RankingBreakdown:
    """Breakdown of ranking score components"""
    paper_id: str
    title: str
    total_score: float
    query_match: float
    recency: float
    study_type_priority: float
    evidence_completeness: float
    duplicate_penalty: float
    weights: Dict[str, float]


class PaperScorer:
    """Score and rank papers based on multiple features"""
    
    def __init__(
        self,
        query_match_weight: float = 0.4,
        recency_weight: float = 0.2,
        study_type_weight: float = 0.2,
        evidence_completeness_weight: float = 0.15,
        duplicate_penalty_weight: float = 0.05
    ):
        """
        Initialize scorer
        
        Args:
            query_match_weight: Weight for query matching score
            recency_weight: Weight for recency score
            study_type_weight: Weight for study type priority
            evidence_completeness_weight: Weight for evidence completeness
            duplicate_penalty_weight: Weight for duplicate penalty
        """
        self.weights = {
            "query_match": query_match_weight,
            "recency": recency_weight,
            "study_type": study_type_weight,
            "evidence_completeness": evidence_completeness_weight,
            "duplicate_penalty": duplicate_penalty_weight
        }
        
        # Normalize weights
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def score_and_rank(
        self,
        papers: List[Dict[str, Any]],
        query: str,
        top_k: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], List[RankingBreakdown]]:
        """
        Score and rank papers
        
        Args:
            papers: List of normalized papers
            query: Search query
            top_k: Return top K results (None for all)
            
        Returns:
            Tuple of (ranked papers, breakdowns)
        """
        if not papers:
            return [], []
        
        # Calculate scores
        scored_papers = []
        breakdowns = []
        
        # Detect duplicates
        duplicate_groups = self._detect_duplicates(papers)
        
        for paper in papers:
            # Calculate individual feature scores
            query_match = self._calculate_query_match(paper, query)
            recency = self._calculate_recency(paper)
            study_type_priority = paper.get("study_type_priority", 0.4)
            evidence_completeness = paper.get("evidence_completeness", 0.0)
            duplicate_penalty = self._calculate_duplicate_penalty(
                paper, duplicate_groups
            )
            
            # Calculate weighted total score
            total_score = (
                self.weights["query_match"] * query_match +
                self.weights["recency"] * recency +
                self.weights["study_type"] * study_type_priority +
                self.weights["evidence_completeness"] * evidence_completeness -
                self.weights["duplicate_penalty"] * duplicate_penalty
            )
            
            # Store score
            paper["retrieval_score"] = max(0.0, total_score)  # Ensure non-negative
            
            # Create breakdown
            breakdown = RankingBreakdown(
                paper_id=paper.get("id", ""),
                title=paper.get("title", "")[:100],  # Truncate for display
                total_score=paper["retrieval_score"],
                query_match=query_match,
                recency=recency,
                study_type_priority=study_type_priority,
                evidence_completeness=evidence_completeness,
                duplicate_penalty=duplicate_penalty,
                weights=self.weights.copy()
            )
            
            scored_papers.append(paper)
            breakdowns.append(breakdown)
        
        # Sort by score (descending)
        sorted_pairs = sorted(
            zip(scored_papers, breakdowns),
            key=lambda x: x[0]["retrieval_score"],
            reverse=True
        )
        
        ranked_papers = [p for p, _ in sorted_pairs]
        ranked_breakdowns = [b for _, b in sorted_pairs]
        
        # Return top K if specified
        if top_k is not None:
            ranked_papers = ranked_papers[:top_k]
            ranked_breakdowns = ranked_breakdowns[:top_k]
        
        return ranked_papers, ranked_breakdowns
    
    def _calculate_query_match(self, paper: Dict[str, Any], query: str) -> float:
        """
        Calculate query matching score
        
        Returns:
            Score between 0.0 and 1.0
        """
        if not query:
            return 0.5  # Neutral score if no query
        
        query_lower = query.lower()
        query_terms = set(re.findall(r'\b\w+\b', query_lower))
        
        if not query_terms:
            return 0.5
        
        # Check title
        title = paper.get("title", "").lower()
        title_terms = set(re.findall(r'\b\w+\b', title))
        title_match = len(query_terms & title_terms) / len(query_terms)
        
        # Check abstract
        abstract = paper.get("abstract", "").lower()
        abstract_terms = set(re.findall(r'\b\w+\b', abstract))
        abstract_match = len(query_terms & abstract_terms) / len(query_terms)
        
        # Check keywords
        keywords = " ".join(paper.get("keywords", [])).lower()
        keyword_terms = set(re.findall(r'\b\w+\b', keywords))
        keyword_match = len(query_terms & keyword_terms) / len(query_terms)
        
        # Weighted combination (title is most important)
        score = (
            0.5 * title_match +
            0.3 * abstract_match +
            0.2 * keyword_match
        )
        
        return min(score, 1.0)
    
    def _calculate_recency(self, paper: Dict[str, Any]) -> float:
        """
        Calculate recency score
        
        Returns:
            Score between 0.0 and 1.0 (1.0 = most recent)
        """
        year = paper.get("year")
        if not year:
            return 0.5  # Neutral if year unknown
        
        current_year = datetime.now().year
        
        # Papers from current year = 1.0
        # Papers from 10+ years ago = 0.0
        # Linear interpolation
        age = current_year - year
        score = max(0.0, 1.0 - (age / 10.0))
        
        return score
    
    def _detect_duplicates(self, papers: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """
        Detect duplicate papers (same title or DOI)
        
        Returns:
            Dictionary mapping paper ID to list of duplicate indices
        """
        duplicate_groups = {}
        
        # Group by normalized title
        title_groups = {}
        for i, paper in enumerate(papers):
            title = paper.get("title", "").lower().strip()
            # Remove special characters for comparison
            title_normalized = re.sub(r'[^\w\s]', '', title)
            
            if title_normalized not in title_groups:
                title_groups[title_normalized] = []
            title_groups[title_normalized].append(i)
        
        # Group by DOI
        doi_groups = {}
        for i, paper in enumerate(papers):
            doi = paper.get("doi")
            if doi:
                if doi not in doi_groups:
                    doi_groups[doi] = []
                doi_groups[doi].append(i)
        
        # Combine groups
        all_groups = list(title_groups.values()) + list(doi_groups.values())
        
        # Map each paper to its group
        for group in all_groups:
            if len(group) > 1:  # Only groups with duplicates
                for idx in group:
                    paper_id = papers[idx].get("id", str(idx))
                    if paper_id not in duplicate_groups:
                        duplicate_groups[paper_id] = []
                    duplicate_groups[paper_id].extend([i for i in group if i != idx])
        
        return duplicate_groups
    
    def _calculate_duplicate_penalty(
        self,
        paper: Dict[str, Any],
        duplicate_groups: Dict[str, List[int]]
    ) -> float:
        """
        Calculate penalty for being a duplicate
        
        Returns:
            Penalty score (0.0 = no penalty, 1.0 = maximum penalty)
        """
        paper_id = paper.get("id", "")
        
        if paper_id in duplicate_groups:
            # If there are duplicates, give penalty based on position
            # (assumes papers are already sorted by some criteria)
            return 0.5  # Moderate penalty
        
        return 0.0

