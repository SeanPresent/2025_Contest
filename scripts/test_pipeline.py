"""Test script for the paper search pipeline"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PaperSearchPipeline


def test_basic_search():
    """Test basic search functionality"""
    print("🧪 Testing Paper Search Pipeline...")
    print("=" * 60)
    
    # Initialize pipeline
    print("\n1. Initializing pipeline...")
    pipeline = PaperSearchPipeline(use_cache=True)
    print("   ✅ Pipeline initialized")
    
    # Test search
    print("\n2. Testing search...")
    query = "transformer attention mechanism"
    print(f"   Query: {query}")
    
    try:
        results = pipeline.search(
            query=query,
            sources=["arxiv"],  # Start with arxiv only for faster testing
            max_results=10,
            top_k=5
        )
        
        papers = results["papers"]
        breakdowns = results["breakdowns"]
        charts = results["charts"]
        summary = results["summary"]
        
        print(f"   ✅ Search completed")
        print(f"   Found {len(papers)} papers")
        print(f"   Summary: {summary}")
        
        # Display top 3 papers
        print("\n3. Top 3 papers:")
        for i, (paper, breakdown) in enumerate(zip(papers[:3], breakdowns[:3]), 1):
            print(f"\n   [{i}] {paper.get('title', 'No title')[:80]}...")
            print(f"       Score: {breakdown.total_score:.3f}")
            print(f"       Year: {paper.get('year', 'N/A')}")
            print(f"       Venue: {paper.get('venue', 'N/A')}")
        
        # Check charts
        print("\n4. Charts generated:")
        for chart_name in charts.keys():
            print(f"   ✅ {chart_name}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_basic_search()
    sys.exit(0 if success else 1)

