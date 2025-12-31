"""Evaluation script for trained model"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import sys
import torch

sys.path.insert(0, str(Path(__file__).parent.parent))

from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


def parse_json_response(text: str) -> Dict[str, Any]:
    """Try to parse JSON from model response"""
    # Try to extract JSON from response
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return None


def check_evidence_table(response: Dict[str, Any]) -> bool:
    """Check if response contains evidence table"""
    return "evidence_table" in response or "Evidence Table" in str(response)


def check_ranking_breakdown(response: Dict[str, Any]) -> bool:
    """Check if response contains ranking breakdown"""
    return "ranking_breakdown" in response or "Ranking Breakdown" in str(response)


def check_hallucination(response: Dict[str, Any], papers: List[Dict[str, Any]]) -> float:
    """
    Check for hallucination (claims not supported by evidence)
    
    Returns:
        Ratio of unsupported claims (0.0 = no hallucination, 1.0 = all hallucinated)
    """
    if not papers:
        return 1.0
    
    # Extract titles from papers
    paper_titles = {p.get("title", "").lower() for p in papers}
    
    # Extract claims from response
    response_text = json.dumps(response, ensure_ascii=False).lower()
    
    # Simple heuristic: check if response mentions titles
    mentioned_titles = sum(1 for title in paper_titles if title in response_text)
    
    if len(paper_titles) == 0:
        return 1.0
    
    # Ratio of papers not mentioned
    hallucination_ratio = 1.0 - (mentioned_titles / len(paper_titles))
    
    return hallucination_ratio


def evaluate_model(
    model_path: str,
    test_dataset_path: str,
    base_model: str = None
) -> Dict[str, Any]:
    """
    Evaluate trained model
    
    Args:
        model_path: Path to trained model (or Hub ID)
        test_dataset_path: Path to test dataset JSONL
        base_model: Base model path (if using PEFT)
        
    Returns:
        Evaluation metrics
    """
    # Load model
    print(f"📦 Loading model from {model_path}...")
    
    if base_model:
        # Load PEFT model
        base = AutoModelForCausalLM.from_pretrained(base_model)
        model = PeftModel.from_pretrained(base, model_path)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_path)
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # Load test dataset
    print(f"📝 Loading test dataset from {test_dataset_path}...")
    test_examples = []
    with open(test_dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            test_examples.append(json.loads(line))
    
    print(f"   Loaded {len(test_examples)} test examples")
    
    # Evaluation metrics
    metrics = {
        "total_examples": len(test_examples),
        "format_compliance": 0,  # JSON parse success rate
        "evidence_inclusion": 0,  # Evidence table inclusion rate
        "ranking_breakdown_inclusion": 0,  # Ranking breakdown inclusion rate
        "avg_hallucination_ratio": 0.0,  # Average hallucination ratio
        "trust_score": 0.0  # Overall trust score
    }
    
    format_success = 0
    evidence_success = 0
    breakdown_success = 0
    hallucination_scores = []
    
    print("\n🔍 Evaluating model...")
    for i, example in enumerate(test_examples, 1):
        instruction = example["instruction"]
        expected_response = json.loads(example["response"])
        
        # Generate response
        prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response_text = generated_text.split("### Response:\n")[-1].strip()
        
        # Parse JSON
        parsed_response = parse_json_response(response_text)
        
        if parsed_response:
            format_success += 1
            
            # Check evidence table
            if check_evidence_table(parsed_response):
                evidence_success += 1
            
            # Check ranking breakdown
            if check_ranking_breakdown(parsed_response):
                breakdown_success += 1
            
            # Check hallucination
            # Note: This requires access to actual papers, which we'd need to extract from expected_response
            papers = expected_response.get("evidence_table", [])
            hallucination_ratio = check_hallucination(parsed_response, papers)
            hallucination_scores.append(hallucination_ratio)
        
        if i % 10 == 0:
            print(f"   Processed {i}/{len(test_examples)} examples...")
    
    # Calculate metrics
    metrics["format_compliance"] = format_success / len(test_examples)
    metrics["evidence_inclusion"] = evidence_success / len(test_examples)
    metrics["ranking_breakdown_inclusion"] = breakdown_success / len(test_examples)
    metrics["avg_hallucination_ratio"] = sum(hallucination_scores) / len(hallucination_scores) if hallucination_scores else 1.0
    
    # Calculate trust score (weighted combination)
    metrics["trust_score"] = (
        0.3 * metrics["format_compliance"] +
        0.3 * metrics["evidence_inclusion"] +
        0.2 * metrics["ranking_breakdown_inclusion"] +
        0.2 * (1.0 - metrics["avg_hallucination_ratio"])
    )
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained model")
    parser.add_argument("--model_path", type=str, required=True, help="Path to trained model")
    parser.add_argument("--base_model", type=str, help="Base model path (if using PEFT)")
    parser.add_argument("--test_dataset", type=str, required=True, help="Path to test dataset JSONL")
    parser.add_argument("--output", type=str, help="Output metrics JSON file")
    
    args = parser.parse_args()
    
    # Evaluate
    metrics = evaluate_model(
        model_path=args.model_path,
        test_dataset_path=args.test_dataset,
        base_model=args.base_model
    )
    
    # Print results
    print("\n📊 Evaluation Results:")
    print(f"   Format Compliance: {metrics['format_compliance']:.2%}")
    print(f"   Evidence Inclusion: {metrics['evidence_inclusion']:.2%}")
    print(f"   Ranking Breakdown Inclusion: {metrics['ranking_breakdown_inclusion']:.2%}")
    print(f"   Avg Hallucination Ratio: {metrics['avg_hallucination_ratio']:.2%}")
    print(f"   Trust Score: {metrics['trust_score']:.2%}")
    
    # Save metrics
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Metrics saved to {args.output}")


if __name__ == "__main__":
    main()

