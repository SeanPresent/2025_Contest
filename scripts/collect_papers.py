"""Script to collect papers from arXiv and PubMed"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors import ArxivCollector, PubMedCollector
from src.normalizers import PaperNormalizer
from src.utils.cache import Cache


def main():
    parser = argparse.ArgumentParser(description="Collect papers from arXiv and PubMed")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--sources", nargs="+", choices=["arxiv", "pubmed"], 
                       default=["arxiv", "pubmed"], help="Data sources")
    parser.add_argument("--max_results", type=int, default=50, help="Max results per source")
    parser.add_argument("--output", type=str, default="./data/raw/papers.json",
                       help="Output JSON file path")
    parser.add_argument("--normalize", action="store_true", help="Normalize papers")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    
    args = parser.parse_args()
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize collectors
    cache = None if args.no_cache else Cache()
    arxiv_collector = ArxivCollector(cache=cache, use_cache=not args.no_cache)
    pubmed_collector = PubMedCollector(cache=cache, use_cache=not args.no_cache)
    
    # Collect papers
    all_papers = []
    
    if "arxiv" in args.sources:
        print(f"🔍 Searching arXiv: {args.query}")
        arxiv_papers = arxiv_collector.search(
            query=args.query,
            max_results=args.max_results
        )
        all_papers.extend(arxiv_papers)
        print(f"   Found {len(arxiv_papers)} papers")
    
    if "pubmed" in args.sources:
        print(f"🔍 Searching PubMed: {args.query}")
        pubmed_papers = pubmed_collector.search(
            query=args.query,
            max_results=args.max_results
        )
        all_papers.extend(pubmed_papers)
        print(f"   Found {len(pubmed_papers)} papers")
    
    # Normalize if requested
    if args.normalize:
        print("📝 Normalizing papers...")
        normalizer = PaperNormalizer()
        all_papers = normalizer.normalize_batch(all_papers)
    
    # Save to file
    print(f"💾 Saving {len(all_papers)} papers to {args.output}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2, default=str)
    
    print("✅ Done!")


if __name__ == "__main__":
    main()

