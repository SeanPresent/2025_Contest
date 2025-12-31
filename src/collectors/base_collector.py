"""Base collector interface"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseCollector(ABC):
    """Base interface for paper collectors"""
    
    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 50,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for papers
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            sort_by: Sort field (e.g., 'relevance', 'submittedDate')
            sort_order: Sort order ('ascending' or 'descending')
            **kwargs: Additional source-specific parameters
            
        Returns:
            List of paper dictionaries
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get source name (e.g., 'arxiv', 'pubmed')"""
        pass

