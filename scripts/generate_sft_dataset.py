"""Generate SFT dataset from paper search queries"""

import argparse
import json
import random
from pathlib import Path
from typing import List, Dict, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PaperSearchPipeline


# Query templates for different domains and question types
QUERY_TEMPLATES = {
    "domain_method": [
        "What are the latest methods for {topic}?",
        "How does {method} work in {domain}?",
        "What are the state-of-the-art approaches to {problem}?",
        "Compare different methods for {task}",
    ],
    "comparison": [
        "What are the differences between {method1} and {method2}?",
        "Compare {approach1} vs {approach2} for {task}",
        "What are the advantages of {method} over traditional approaches?",
    ],
    "trend": [
        "What are the recent trends in {field}?",
        "How has {topic} evolved over the past 5 years?",
        "What are the emerging topics in {domain}?",
    ],
    "meta_analysis": [
        "What do systematic reviews say about {topic}?",
        "What is the evidence for {intervention}?",
        "What are the meta-analysis results for {treatment}?",
    ],
    "technical": [
        "How to implement {technique}?",
        "What are the technical details of {method}?",
        "Explain the architecture of {system}",
    ],
}

# Domain keywords
DOMAINS = [
    "machine learning", "deep learning", "transformer", "attention mechanism",
    "neural networks", "computer vision", "natural language processing",
    "reinforcement learning", "generative models", "large language models",
    "medical imaging", "drug discovery", "clinical trials", "biomedical",
    "cancer treatment", "vaccine development", "genetics", "neuroscience",
]


def generate_queries(num_queries: int) -> List[str]:
    """Generate diverse queries"""
    queries = []
    
    for _ in range(num_queries):
        template_type = random.choice(list(QUERY_TEMPLATES.keys()))
        template = random.choice(QUERY_TEMPLATES[template_type])
        
        # Fill template - order matters! Check more specific patterns first
        try:
            if "{approach1}" in template and "{approach2}" in template:
                approaches = random.sample(["supervised", "unsupervised", "semi-supervised", "self-supervised"], 2)
                task = random.choice(["classification", "generation"])
                query = template.format(approach1=approaches[0], approach2=approaches[1], task=task)
            elif "{method1}" in template and "{method2}" in template:
                methods = random.sample(["transformer", "CNN", "RNN", "LSTM", "BERT"], 2)
                query = template.format(method1=methods[0], method2=methods[1])
            elif "{method}" in template and "{domain}" in template:
                method = random.choice(["transformer", "attention", "CNN", "RNN", "GAN"])
                domain = random.choice(DOMAINS)
                query = template.format(method=method, domain=domain)
            elif "{topic}" in template:
                topic = random.choice(DOMAINS)
                query = template.format(topic=topic)
            elif "{problem}" in template:
                problem = random.choice(["classification", "generation", "detection", "segmentation"])
                query = template.format(problem=problem)
            elif "{task}" in template:
                task = random.choice(["image classification", "text generation", "object detection"])
                query = template.format(task=task)
            elif "{method}" in template:
                method = random.choice(["transformer", "attention", "CNN", "RNN"])
                query = template.format(method=method)
            elif "{field}" in template:
                field = random.choice(DOMAINS)
                query = template.format(field=field)
            elif "{intervention}" in template:
                intervention = random.choice(["vaccination", "treatment", "therapy", "screening"])
                query = template.format(intervention=intervention)
            elif "{treatment}" in template:
                treatment = random.choice(["chemotherapy", "immunotherapy", "surgery", "radiation"])
                query = template.format(treatment=treatment)
            elif "{technique}" in template:
                technique = random.choice(["attention mechanism", "transfer learning", "fine-tuning"])
                query = template.format(technique=technique)
            elif "{system}" in template:
                system = random.choice(["BERT", "GPT", "Transformer", "ResNet"])
                query = template.format(system=system)
            else:
                query = template
        except KeyError as e:
            # Fallback if template has unexpected placeholders
            print(f"Warning: Could not format template '{template}': {e}")
            query = template.replace("{", "").replace("}", "")
        
        queries.append(query)
    
    return queries


def format_response(papers: List[Dict[str, Any]], breakdowns: List, summary: Dict[str, Any], query: str) -> str:
    """Format response in the expected output format"""
    
    # Evidence Table
    evidence_table = []
    for i, (paper, breakdown) in enumerate(zip(papers, breakdowns), 1):
        evidence_table.append({
            "rank": i,
            "title": paper.get("title", ""),
            "authors": ", ".join(paper.get("authors", [])[:3]),
            "year": paper.get("year"),
            "venue": paper.get("venue", ""),
            "study_type": paper.get("study_type", "other"),
            "score": breakdown.total_score,
            "url": paper.get("url", "")
        })
    
    # Ranking breakdown
    ranking_breakdown = []
    for breakdown in breakdowns:
        ranking_breakdown.append({
            "paper_id": breakdown.paper_id,
            "title": breakdown.title,
            "total_score": breakdown.total_score,
            "query_match": breakdown.query_match,
            "recency": breakdown.recency,
            "study_type_priority": breakdown.study_type_priority,
            "evidence_completeness": breakdown.evidence_completeness,
            "duplicate_penalty": breakdown.duplicate_penalty
        })
    
    # Summary
    answer_summary = f"""
검색 질문: {query}

검색 결과 요약:
- 총 {summary['total']}개의 논문이 검색되었습니다.
- 소스별 분포: {', '.join([f'{k}({v})' for k, v in summary['sources'].items()])}
- 연도 범위: {summary['year_range'][0]}-{summary['year_range'][1] if summary.get('year_range') else 'N/A'}
- 평균 랭킹 점수: {summary['avg_score']:.3f}

주요 발견:
- 상위 논문들은 주로 {', '.join([p.get('venue', '') for p in papers[:3]])}에서 발표되었습니다.
- 연구 유형 분포: {', '.join([f'{k}({v})' for k, v in summary.get('study_types', {}).items()])}
"""
    
    # Format as JSON structure
    response = {
        "evidence_table": evidence_table,
        "ranking_breakdown": ranking_breakdown,
        "answer_summary": answer_summary.strip(),
        "charts": {
            "year_trend": "연도별 트렌드 차트",
            "venue_distribution": "저널 분포 차트",
            "study_type_distribution": "연구 유형 분포 차트"
        }
    }
    
    return json.dumps(response, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Generate SFT dataset")
    parser.add_argument("--num_queries", type=int, default=100, help="Number of queries to generate")
    parser.add_argument("--output", type=str, default="./data/sft_dataset/train.jsonl",
                       help="Output JSONL file path")
    parser.add_argument("--max_results", type=int, default=50, help="Max results per source")
    parser.add_argument("--top_k", type=int, default=10, help="Top K results")
    parser.add_argument("--sources", nargs="+", choices=["arxiv", "pubmed"],
                       default=["arxiv", "pubmed"], help="Data sources")
    
    args = parser.parse_args()
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize pipeline
    pipeline = PaperSearchPipeline(use_cache=True)
    
    # Generate queries
    print(f"📝 Generating {args.num_queries} queries...")
    queries = generate_queries(args.num_queries)
    
    # Process queries and generate dataset
    dataset = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{args.num_queries}] Processing query: {query}")
        
        try:
            # Search and rank
            results = pipeline.search(
                query=query,
                sources=args.sources,
                max_results=args.max_results,
                top_k=args.top_k
            )
            
            if not results["papers"]:
                print(f"   ⚠️ No results found, skipping...")
                continue
            
            # Format instruction and response
            instruction = f"""다음 질문에 대해 논문을 검색하고 랭킹하여 결과를 제시하세요.

질문: {query}

출력 형식:
1. Evidence Table (Top-K): 검색된 논문의 상위 K개를 테이블 형식으로 제시
2. Ranking Breakdown: 각 논문의 랭킹 점수 구성 요소를 공개
3. Answer Summary: 검색 결과를 요약하여 제시
4. Charts: 연도별 트렌드, 저널 분포, 연구 유형 분포 차트에 대한 설명

모든 주장은 Evidence Table의 논문에 근거해야 하며, 랭킹 근거를 명시해야 합니다."""
            
            response = format_response(
                results["papers"],
                results["breakdowns"],
                results["summary"],
                query
            )
            
            # Create training example
            example = {
                "instruction": instruction,
                "response": response,
                "query": query,
                "num_papers": len(results["papers"])
            }
            
            dataset.append(example)
            print(f"   ✅ Added example with {len(results['papers'])} papers")
            
        except Exception as e:
            print(f"   ❌ Error processing query: {e}")
            continue
    
    # Save dataset
    print(f"\n💾 Saving {len(dataset)} examples to {args.output}...")
    with open(output_path, "w", encoding="utf-8") as f:
        for example in dataset:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"✅ Done! Generated {len(dataset)} training examples")


if __name__ == "__main__":
    main()

