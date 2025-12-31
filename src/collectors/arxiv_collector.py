"""arXiv paper collector using arXiv API"""

import feedparser
import requests
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from datetime import datetime

from .base_collector import BaseCollector
from ..utils.retry import retry_with_backoff
from ..utils.cache import Cache


class ArxivCollector(BaseCollector):
    """Collector for arXiv papers"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self, cache: Optional[Cache] = None, use_cache: bool = True):
        """
        Initialize arXiv collector
        
        Args:
            cache: Cache instance (optional)
            use_cache: Whether to use caching
        """
        self.cache = cache
        self.use_cache = use_cache
    
    def get_source_name(self) -> str:
        return "arxiv"
    
    @retry_with_backoff(max_attempts=3, initial_wait=2.0)
    def search(
        self,
        query: str,
        max_results: int = 50,
        sort_by: Optional[str] = "relevance",
        sort_order: Optional[str] = "descending",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search arXiv papers
        
        Args:
            query: Search query (supports arXiv query syntax)
            max_results: Maximum number of results
            sort_by: 'relevance', 'lastUpdatedDate', or 'submittedDate'
            sort_order: 'ascending' or 'descending'
            **kwargs: Additional parameters (e.g., id_list, start)
            
        Returns:
            List of paper dictionaries
        """
        # Check cache
        cache_params = {
            "max_results": max_results,
            "sort_by": sort_by,
            "sort_order": sort_order,
            **kwargs
        }
        
        if self.use_cache and self.cache:
            cached = self.cache.get("arxiv", query, cache_params)
            if cached is not None:
                return cached
        
        # Build query parameters
        params = {
            "search_query": query,
            "start": kwargs.get("start", 0),
            "max_results": min(max_results, 2000),  # arXiv API limit
            "sortBy": sort_by or "relevance",
            "sortOrder": sort_order or "descending"
        }
        
        # Add id_list if provided
        if "id_list" in kwargs:
            params["id_list"] = kwargs["id_list"]
        
        # Make request
        url = f"{self.BASE_URL}?{urlencode(params)}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse feed
        feed = feedparser.parse(response.content)
        
        # Extract papers
        papers = []
        for entry in feed.entries[:max_results]:
            paper = self._parse_entry(entry)
            if paper:
                papers.append(paper)
        
        # Cache results
        if self.use_cache and self.cache:
            self.cache.set("arxiv", query, papers, cache_params)
        
        # Rate limiting: arXiv requests 3 seconds between requests
        time.sleep(3)
        
        return papers
    
    def _parse_entry(self, entry: feedparser.FeedParserDict) -> Optional[Dict[str, Any]]:
        """Parse arXiv feed entry to paper dictionary"""
        try:
            # Extract arXiv ID
            arxiv_id = entry.id.split("/")[-1].split("v")[0]
            
            # Parse authors
            authors = [author.name for author in entry.get("authors", [])]
            
            # Parse published date
            published = None
            if hasattr(entry, "published"):
                try:
                    published = datetime(*entry.published_parsed[:6])
                except:
                    pass
            
            # Parse categories (primary and secondary)
            categories = []
            if "tags" in entry:
                categories = [tag.term for tag in entry.tags]
            primary_category = categories[0] if categories else None
            
            # Extract abstract
            abstract = entry.get("summary", "").strip()
            
            # Extract links
            pdf_url = None
            abs_url = None
            for link in entry.get("links", []):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href")
                elif "abs" in link.get("href", ""):
                    abs_url = link.get("href")
            
            paper = {
                "source": "arxiv",
                "id": arxiv_id,
                "title": entry.get("title", "").replace("\n", " ").strip(),
                "authors": authors,
                "published": published.isoformat() if published else None,
                "year": published.year if published else None,
                "abstract": abstract,
                "categories": categories,
                "primary_category": primary_category,
                "pdf_url": pdf_url,
                "url": abs_url or entry.get("id", ""),
                "venue": "arXiv",
                "journal": None,
                "keywords": categories,  # Use categories as keywords
                "doi": None,  # arXiv entries may have DOI in comments
            }
            
            return paper
            
        except Exception as e:
            print(f"Error parsing arXiv entry: {e}")
            return None
    
    def get_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get paper by arXiv ID
        
        Args:
            arxiv_id: arXiv ID (e.g., "2301.12345")
            
        Returns:
            Paper dictionary or None if not found
        """
        results = self.search(f"id:{arxiv_id}", max_results=1)
        return results[0] if results else None

