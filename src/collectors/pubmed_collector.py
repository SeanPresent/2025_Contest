"""PubMed paper collector using Entrez API"""

import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from Bio import Entrez
from Bio.Entrez import efetch, esearch

from .base_collector import BaseCollector
from ..utils.retry import retry_with_backoff
from ..utils.cache import Cache


class PubMedCollector(BaseCollector):
    """Collector for PubMed papers"""
    
    def __init__(
        self,
        email: Optional[str] = None,
        api_key: Optional[str] = None,
        cache: Optional[Cache] = None,
        use_cache: bool = True
    ):
        """
        Initialize PubMed collector
        
        Args:
            email: Email for Entrez (required by NCBI)
            api_key: API key for higher rate limits (optional)
            cache: Cache instance (optional)
            use_cache: Whether to use caching
        """
        self.email = email or os.getenv("NCBI_EMAIL", "your_email@example.com")
        self.api_key = api_key or os.getenv("NCBI_API_KEY")
        self.cache = cache
        self.use_cache = use_cache
        
        # Set Entrez parameters
        Entrez.email = self.email
        if self.api_key:
            Entrez.api_key = self.api_key
    
    def get_source_name(self) -> str:
        return "pubmed"
    
    @retry_with_backoff(max_attempts=3, initial_wait=2.0)
    def search(
        self,
        query: str,
        max_results: int = 50,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search PubMed papers
        
        Args:
            query: Search query (PubMed query syntax)
            max_results: Maximum number of results
            sort_by: 'relevance', 'pub_date', 'first_author', 'last_author', 'title', 'journal'
            sort_order: 'asc' or 'desc'
            **kwargs: Additional parameters
            
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
            cached = self.cache.get("pubmed", query, cache_params)
            if cached is not None:
                return cached
        
        # Step 1: Search for IDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": min(max_results, 10000),  # PubMed limit
            "retmode": "xml",
            "usehistory": "y"
        }
        
        if sort_by:
            # Map sort_by to PubMed sort options
            sort_map = {
                "relevance": "relevance",
                "pub_date": "pub_date",
                "first_author": "first_author",
                "last_author": "last_author",
                "title": "title",
                "journal": "journal"
            }
            if sort_by in sort_map:
                search_params["sort"] = sort_map[sort_by]
        
        search_handle = esearch(**search_params)
        search_results = Entrez.read(search_handle)
        search_handle.close()
        
        pmids = search_results["IdList"]
        if not pmids:
            return []
        
        # Step 2: Fetch details for IDs
        papers = self._fetch_details(pmids[:max_results])
        
        # Cache results
        if self.use_cache and self.cache:
            self.cache.set("pubmed", query, papers, cache_params)
        
        # Rate limiting: 3 requests per second without API key, 10 with API key
        delay = 0.34 if self.api_key else 1.0
        time.sleep(delay)
        
        return papers
    
    @retry_with_backoff(max_attempts=3, initial_wait=2.0)
    def _fetch_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch detailed information for PubMed IDs"""
        if not pmids:
            return []
        
        # Fetch in batches of 100 (Entrez limit)
        all_papers = []
        batch_size = 100
        
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            
            fetch_handle = efetch(
                db="pubmed",
                id=",".join(batch),
                retmode="xml",
                rettype="abstract"
            )
            records = Entrez.read(fetch_handle)
            fetch_handle.close()
            
            # Parse records
            if "PubmedArticle" in records:
                for record in records["PubmedArticle"]:
                    paper = self._parse_record(record)
                    if paper:
                        all_papers.append(paper)
            elif "PubmedBookArticle" in records:
                # Handle book articles differently if needed
                pass
            
            # Rate limiting
            time.sleep(0.34 if self.api_key else 1.0)
        
        return all_papers
    
    def _parse_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse PubMed XML record to paper dictionary"""
        try:
            medline = record.get("MedlineCitation", {})
            article = medline.get("Article", {})
            
            # Extract PubMed ID
            pmid = str(medline.get("PMID", {}))
            
            # Extract title
            title = ""
            if "ArticleTitle" in article:
                title = article["ArticleTitle"]
            
            # Extract authors
            authors = []
            if "AuthorList" in article:
                for author in article["AuthorList"]:
                    last_name = author.get("LastName", "")
                    first_name = author.get("ForeName", "")
                    initials = author.get("Initials", "")
                    if last_name:
                        author_name = f"{last_name} {first_name or initials}".strip()
                        authors.append(author_name)
            
            # Extract journal
            journal = None
            journal_iso = None
            if "Journal" in article:
                journal_info = article["Journal"]
                journal = journal_info.get("Title", "")
                journal_iso = journal_info.get("ISOAbbreviation", "")
            
            # Extract publication date
            pub_date = None
            year = None
            if "PubDate" in article:
                pub_date_info = article["PubDate"]
                year_str = pub_date_info.get("Year", "")
                if year_str:
                    try:
                        year = int(year_str)
                        month = pub_date_info.get("Month", "01")
                        day = pub_date_info.get("Day", "01")
                        # Try to parse full date
                        try:
                            pub_date = datetime(year, int(month), int(day))
                        except:
                            pub_date = datetime(year, 1, 1)
                    except:
                        pass
            
            # Extract abstract
            abstract = ""
            if "Abstract" in article:
                abstract_parts = []
                for text_obj in article["Abstract"].get("AbstractText", []):
                    if isinstance(text_obj, dict):
                        label = text_obj.get("Label", "")
                        text = text_obj.get("Text", "")
                        if label:
                            abstract_parts.append(f"{label}: {text}")
                        else:
                            abstract_parts.append(text)
                    else:
                        abstract_parts.append(str(text_obj))
                abstract = " ".join(abstract_parts)
            
            # Extract MeSH terms (keywords)
            mesh_terms = []
            if "MeshHeadingList" in medline:
                for mesh in medline["MeshHeadingList"]:
                    descriptor = mesh.get("DescriptorName", {})
                    if isinstance(descriptor, dict):
                        mesh_terms.append(descriptor.get("#text", ""))
            
            # Extract DOI
            doi = None
            if "ELocationID" in article:
                for eloc in article["ELocationID"]:
                    if eloc.get("@EIdType") == "doi":
                        doi = eloc.get("#text", "")
            
            # Extract URL
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            paper = {
                "source": "pubmed",
                "id": pmid,
                "title": title,
                "authors": authors,
                "published": pub_date.isoformat() if pub_date else None,
                "year": year,
                "abstract": abstract,
                "categories": [],
                "primary_category": None,
                "pdf_url": None,  # PubMed doesn't provide direct PDF links
                "url": url,
                "venue": journal_iso or journal or "PubMed",
                "journal": journal,
                "keywords": mesh_terms,
                "doi": doi,
            }
            
            return paper
            
        except Exception as e:
            print(f"Error parsing PubMed record: {e}")
            return None
    
    def get_by_id(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Get paper by PubMed ID
        
        Args:
            pmid: PubMed ID
            
        Returns:
            Paper dictionary or None if not found
        """
        papers = self._fetch_details([pmid])
        return papers[0] if papers else None

