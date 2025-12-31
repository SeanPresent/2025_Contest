"""Paper collectors for arXiv and PubMed"""

from .arxiv_collector import ArxivCollector
from .pubmed_collector import PubMedCollector
from .base_collector import BaseCollector

__all__ = ["ArxivCollector", "PubMedCollector", "BaseCollector"]

