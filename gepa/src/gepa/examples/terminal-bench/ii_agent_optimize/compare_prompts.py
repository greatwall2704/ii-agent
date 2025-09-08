#!/usr/bin/env python3
"""
Script to compare original vs optimized prompt performance
"""

import json
from pathlib import Path
import sys
import os

# Add the parent directory to path to import GEPA modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from gepa.core.adapter import EvaluationBatch
from optimize_ii_agent_prompt import IIAgentAdapter, create_ii_agent_dataset

def load_prompts():
    """Load both original and optimized prompts"""
    
    # Get the script directory
    script_dir = Path(__file__).parent
    
    # Load original prompt
    original_prompt_path = script_dir / "ii_agent_system_prompt.txt"
    with open(original_prompt_path, 'r', encoding='utf-8') as f:
        original_prompt = f.read().strip()
    
    # Load optimized prompt
    optimized_prompt_path = script_dir / "ii_agent_optimization" / "optimized_system_prompt.txt"
    with open(optimized_prompt_path, 'r', encoding='utf-8') as f:
        optimized_prompt = f.read().strip()
    
    return original_prompt, optimized_prompt

def evaluate_prompt(adapter, prompt, valset, prompt_name):
    """Evaluate a single prompt on validation set"""
    
    print(f"\n=== Evaluating {prompt_name} ===")
    print(f"Prompt length: {len(prompt)} characters")
    print(f"Number of validation tasks: {len(valset)}")
    
    candidate = {"system_prompt": prompt}
    
    print("Starting evaluation...")
    
    # Evaluate on validation set
    eval_result = adapter.evaluate(
        batch=valset,
        candidate=candidate,
        capture_traces=False
    )
    
    scores = eval_result.scores
    avg_score = sum(scores) / len(scores) if scores else 0
    
    print(f"Individual task scores: {scores}")
    print(f"Average score: {avg_score:.4f}")
    
    return scores, avg_score

def main():
    print("🔍 Comparing Original vs Optimized Prompt Performance")
    print("=" * 60)
    
    # Setup
    model_name = "Qwen3-Coder-A35B"
    base_url = "https://95819c637082.ngrok.app/v1"
    api_key = "dummy"
    
    # Create adapter
    adapter = IIAgentAdapter(
        model_name=model_name,
        base_url=base_url,
        api_key=api_key
    )
    
    # Load dataset
    trainset, valset = create_ii_agent_dataset()
    
    print(f"Validation tasks:")
    for i, task in enumerate(valset):
        print(f"  Task {i}: {task['input'][:50]}...")
    
    # Load prompts
    try:
        original_prompt, optimized_prompt = load_prompts()
        print(f"\nPrompt lengths:")
        print(f"  Original: {len(original_prompt)} characters")
        print(f"  Optimized: {len(optimized_prompt)} characters")
        print(f"  Size reduction: {((len(original_prompt) - len(optimized_prompt)) / len(original_prompt) * 100):.1f}%")
        
    except FileNotFoundError as e:
        print(f"Error loading prompts: {e}")
        return
    
    # Evaluate original prompt
    try:
        original_scores, original_avg = evaluate_prompt(
            adapter, original_prompt, valset, "Original Prompt"
        )
    except Exception as e:
        print(f"Error evaluating original prompt: {e}")
        original_scores, original_avg = None, 0
    
    # Evaluate optimized prompt
    try:
        optimized_scores, optimized_avg = evaluate_prompt(
            adapter, optimized_prompt, valset, "Optimized Prompt"
        )
    except Exception as e:
        print(f"Error evaluating optimized prompt: {e}")
        optimized_scores, optimized_avg = None, 0
    
    # Comparison summary
    print("\n" + "=" * 60)
    print("📊 COMPARISON SUMMARY")
    print("=" * 60)
    
    if original_scores and optimized_scores:
        print(f"{'Task':<6} {'Original':<10} {'Optimized':<10} {'Improvement':<12}")
        print("-" * 50)
        
        total_improvement = 0
        for i, (orig, opt) in enumerate(zip(original_scores, optimized_scores)):
            improvement = opt - orig
            total_improvement += improvement
            print(f"Task {i:<2} {orig:<10.4f} {opt:<10.4f} {improvement:+.4f}")
        
        print("-" * 50)
        print(f"{'Avg':<6} {original_avg:<10.4f} {optimized_avg:<10.4f} {optimized_avg - original_avg:+.4f}")
        
        print(f"\n🎯 Results:")
        print(f"  • Original average score: {original_avg:.4f}")
        print(f"  • Optimized average score: {optimized_avg:.4f}")
        print(f"  • Total improvement: {optimized_avg - original_avg:+.4f}")
        print(f"  • Improvement percentage: {((optimized_avg - original_avg) / original_avg * 100) if original_avg > 0 else 0:+.1f}%")
        
        if optimized_avg > original_avg:
            print("  ✅ Optimization was SUCCESSFUL!")
        elif optimized_avg == original_avg:
            print("  ➡️  Performance remained the same")
        else:
            print("  ❌ Performance decreased")
    
    else:
        print("Unable to complete comparison due to evaluation errors")
    
    # Save results
    script_dir = Path(__file__).parent
    results_path = script_dir / "prompt_comparison_results.json"
    
    results = {
        "original_prompt_length": len(original_prompt),
        "optimized_prompt_length": len(optimized_prompt),
        "original_scores": original_scores,
        "optimized_scores": optimized_scores,
        "original_average": original_avg,
        "optimized_average": optimized_avg,
        "improvement": optimized_avg - original_avg if original_scores and optimized_scores else None
    }
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved to: {results_path}")

if __name__ == "__main__":
    main()
