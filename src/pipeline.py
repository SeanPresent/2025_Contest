"""Main pipeline for paper search and ranking"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from .collectors import ArxivCollector, PubMedCollector
from .normalizers import PaperNormalizer
from .ranking import PaperScorer
from .visualization import ChartGenerator
from .utils.cache import Cache

load_dotenv()


class PaperSearchPipeline:
    """End-to-end pipeline for paper search and ranking"""
    
    def __init__(
        self,
        use_cache: bool = True,
        cache_dir: Optional[str] = None,
        ranking_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize pipeline
        
        Args:
            use_cache: Whether to use caching
            cache_dir: Cache directory path
            ranking_weights: Custom ranking weights
        """
        # Initialize cache
        cache_dir = cache_dir or os.getenv("CACHE_DIR", "./data/cache")
        self.cache = Cache(cache_dir=cache_dir) if use_cache else None
        
        # Initialize collectors
        self.arxiv_collector = ArxivCollector(cache=self.cache, use_cache=use_cache)
        self.pubmed_collector = PubMedCollector(
            email=os.getenv("NCBI_EMAIL"),
            api_key=os.getenv("NCBI_API_KEY"),
            cache=self.cache,
            use_cache=use_cache
        )
        
        # Initialize normalizer
        self.normalizer = PaperNormalizer()
        
        # Initialize scorer
        if ranking_weights:
            self.scorer = PaperScorer(**ranking_weights)
        else:
            # Load from env or use defaults
            weights_str = os.getenv("RANKING_WEIGHTS", "0.4,0.2,0.2,0.15,0.05")
            weights_list = [float(w) for w in weights_str.split(",")]
            self.scorer = PaperScorer(
                query_match_weight=weights_list[0],
                recency_weight=weights_list[1],
                study_type_weight=weights_list[2],
                evidence_completeness_weight=weights_list[3],
                duplicate_penalty_weight=weights_list[4]
            )
        
        # Initialize chart generator
        self.chart_generator = ChartGenerator(backend="plotly")
    
    def search(
        self,
        query: str,
        sources: List[str] = None,
        max_results: int = 50,
        top_k: int = 10,
        year_filter: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Search and rank papers
        
        Args:
            query: Search query
            sources: List of sources ('arxiv', 'pubmed', or both)
            max_results: Maximum results per source
            top_k: Top K results to return
            year_filter: Tuple of (min_year, max_year) or None
            
        Returns:
            Dictionary with:
            - papers: Ranked list of papers
            - breakdowns: Ranking breakdowns
            - charts: Generated charts
            - summary: Summary statistics
        """
        if sources is None:
            sources = ["arxiv", "pubmed"]
        
        # Collect papers from all sources
        all_papers = []
        
        if "arxiv" in sources:
            print(f"🔍 Searching arXiv for: {query}")
            arxiv_papers = self.arxiv_collector.search(
                query=query,
                max_results=max_results
            )
            all_papers.extend(arxiv_papers)
            print(f"   Found {len(arxiv_papers)} papers")
        
        if "pubmed" in sources:
            print(f"🔍 Searching PubMed for: {query}")
            pubmed_papers = self.pubmed_collector.search(
                query=query,
                max_results=max_results
            )
            all_papers.extend(pubmed_papers)
            print(f"   Found {len(pubmed_papers)} papers")
        
        if not all_papers:
            return {
                "papers": [],
                "breakdowns": [],
                "charts": {},
                "summary": {"total": 0, "sources": {}}
            }
        
        # Normalize papers
        print(f"📝 Normalizing {len(all_papers)} papers...")
        normalized_papers = self.normalizer.normalize_batch(all_papers)
        
        # Apply year filter if specified
        if year_filter:
            min_year, max_year = year_filter
            normalized_papers = [
                p for p in normalized_papers
                if p.get("year") and min_year <= p.get("year") <= max_year
            ]
        
        # Score and rank
        print(f"🏆 Ranking {len(normalized_papers)} papers...")
        ranked_papers, breakdowns = self.scorer.score_and_rank(
            normalized_papers,
            query=query,
            top_k=top_k
        )
        
        # Generate charts
        print("📊 Generating charts...")
        charts = self.chart_generator.generate_all_charts(
            ranked_papers,
            output_format="plotly"
        )
        
        # Generate summary
        summary = self._generate_summary(ranked_papers, sources)
        
        return {
            "papers": ranked_papers,
            "breakdowns": breakdowns,
            "charts": charts,
            "summary": summary,
            "query": query
        }
    
    def _generate_summary(self, papers: List[Dict[str, Any]], sources: List[str]) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not papers:
            return {"total": 0, "sources": {}}
        
        # Count by source
        source_counts = {}
        for paper in papers:
            source = paper.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Year range
        years = [p.get("year") for p in papers if p.get("year")]
        year_range = (min(years), max(years)) if years else None
        
        # Study types
        study_types = [p.get("study_type", "other") for p in papers]
        study_type_counts = {}
        for st in study_types:
            study_type_counts[st] = study_type_counts.get(st, 0) + 1
        
        return {
            "total": len(papers),
            "sources": source_counts,
            "year_range": year_range,
            "study_types": study_type_counts,
            "avg_score": sum(p.get("retrieval_score", 0) for p in papers) / len(papers) if papers else 0
        }

