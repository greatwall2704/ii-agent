import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import litellm
from gepa import optimize
from gepa.core.adapter import EvaluationBatch, GEPAAdapter
from gepa.adapters.default_adapter.default_adapter import DefaultDataInst

# Path to the II Agent system prompt (relative to this file)
II_AGENT_PROMPT_PATH = Path(__file__).parent / "ii_agent_system_prompt.txt"

class IIAgentTask:
    """Represents a task for evaluating II Agent performance"""
    def __init__(self, input_text: str, expected_behavior: str, context: Dict[str, Any] = None):
        self.input = input_text
        self.expected_behavior = expected_behavior
        self.context = context or {}

class IIAgentTrajectory:
    """Trajectory data for II Agent evaluation"""
    def __init__(self, task: IIAgentTask, response: str, success: bool, reasoning: str = ""):
        self.task = task
        self.response = response
        self.success = success
        self.reasoning = reasoning

class IIAgentAdapter(GEPAAdapter):
    """Adapter for optimizing II Agent system prompts"""
    
    def __init__(self, model_name: str, base_url: str, api_key: str):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key
        
        # Configure litellm for the custom endpoint
        import os
        os.environ["OPENAI_API_BASE"] = base_url
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Set litellm debug mode for troubleshooting
        litellm.set_verbose = True
    
    def evaluate(
        self,
        batch: List[DefaultDataInst],
        candidate: Dict[str, str],
        capture_traces: bool = False,
    ) -> EvaluationBatch:
        """Evaluate II Agent with the given system prompt on a batch of tasks"""
        
        outputs = []
        scores = []
        trajectories = [] if capture_traces else None
        
        system_prompt = candidate["system_prompt"]
        
        for task_data in batch:
            try:
                # Create messages for the conversation
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task_data["input"]}
                ]
                
                # Get response from the model
                response = litellm.completion(
                    model=f"openai/{self.model_name}",  # Prefix with openai/ for custom endpoints
                    messages=messages,
                    api_base=self.base_url,
                    api_key=self.api_key,
                    temperature=0.1
                )
                
                assistant_response = response.choices[0].message.content.strip()
                
                # Evaluate the response
                score = self._evaluate_response(task_data, assistant_response)
                
                outputs.append({"response": assistant_response})
                scores.append(score)
                
                if capture_traces:
                    trajectories.append({
                        "task": task_data,
                        "response": assistant_response,
                        "score": score,
                        "messages": messages
                    })
                    
            except Exception as e:
                print(f"Error evaluating task: {e}")
                outputs.append({"response": f"Error: {str(e)}"})
                scores.append(0.0)
                
                if capture_traces:
                    trajectories.append({
                        "task": task_data,
                        "response": f"Error: {str(e)}",
                        "score": 0.0,
                        "error": str(e)
                    })
        
        return EvaluationBatch(outputs=outputs, scores=scores, trajectories=trajectories)
    
    def _evaluate_response(self, task_data: DefaultDataInst, response: str) -> float:
        """Evaluate how well the response matches expected behavior"""
        expected = task_data["answer"].lower()
        response_lower = response.lower()
        
        # Simple scoring based on keyword matching and expected behavior
        score = 0.0
        
        # Check if response contains expected keywords/phrases
        if expected in response_lower:
            score += 0.5
        
        # Check response quality indicators
        if len(response) > 50:  # Reasonable response length
            score += 0.2
        
        if "message_user" in response_lower:  # Uses appropriate tool
            score += 0.2
        
        if any(word in response_lower for word in ["plan", "step", "analyze"]):  # Shows planning
            score += 0.1
        
        return min(score, 1.0)
    
    def make_reflective_dataset(
        self,
        candidate: Dict[str, str],
        eval_batch: EvaluationBatch,
        components_to_update: List[str],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Create reflective dataset for prompt improvement"""
        
        ret_d = {}
        component = components_to_update[0]  # Should be "system_prompt"
        
        items = []
        
        for i, (trajectory, score, output) in enumerate(zip(
            eval_batch.trajectories, eval_batch.scores, eval_batch.outputs
        )):
            task = trajectory["task"]
            response = trajectory["response"]
            
            # Create feedback based on performance
            if score >= 0.8:
                feedback = f"Excellent response! The agent correctly {task['answer']} and demonstrated good planning and tool usage."
            elif score >= 0.5:
                feedback = f"Good response but could be improved. The agent should better {task['answer']} and show more structured thinking."
            else:
                feedback = f"Poor response. The agent failed to {task['answer']}. Need better understanding of task requirements and more systematic approach."
            
            # Add specific feedback about II Agent capabilities
            if "message_user" not in response.lower():
                feedback += " Remember to use message_user tool for communication."
            
            if score < 0.3:
                feedback += f" Expected behavior: {task['answer']}"
            
            item = {
                "Inputs": task["input"],
                "Generated Outputs": response,
                "Feedback": feedback,
                "Score": score,
                "Expected": task["answer"]
            }
            
            items.append(item)
        
        ret_d[component] = items
        return ret_d

def create_ii_agent_dataset():
    """Create a dataset for evaluating II Agent performance"""
    
    # Training tasks focusing on II Agent's core capabilities
    trainset = [
        {
            "input": "I need you to analyze the current market trends for renewable energy and create a comprehensive report with visualizations.",
            "answer": "provide detailed market analysis with data visualization and comprehensive reporting",
            "additional_context": {"task_type": "research_and_analysis"}
        },
        {
            "input": "Create a simple web application for task management with user authentication.",
            "answer": "build a functional web application with proper authentication and task management features",
            "additional_context": {"task_type": "web_development"}
        },
        {
            "input": "Help me process this CSV file and generate insights about customer behavior patterns.",
            "answer": "process data files and generate meaningful insights with analysis",
            "additional_context": {"task_type": "data_processing"}
        },
        {
            "input": "I want to create a presentation about AI trends in 2024 with professional slides.",
            "answer": "create professional presentation slides with comprehensive content about AI trends",
            "additional_context": {"task_type": "content_creation"}
        },
        {
            "input": "Write a research paper on machine learning applications in healthcare.",
            "answer": "write comprehensive research paper with proper citations and detailed analysis",
            "additional_context": {"task_type": "academic_writing"}
        },
        {
            "input": "Deploy a simple API service and make it publicly accessible.",
            "answer": "develop and deploy API service with public accessibility",
            "additional_context": {"task_type": "deployment"}
        },
        {
            "input": "Create an interactive dashboard showing real-time data about website analytics.",
            "answer": "build interactive dashboard with real-time data visualization capabilities",
            "additional_context": {"task_type": "dashboard_creation"}
        },
        {
            "input": "Help me automate my email workflow using Python scripts.",
            "answer": "create automation scripts for email workflow management",
            "additional_context": {"task_type": "automation"}
        }
    ]
    
    # Validation tasks
    valset = [
        {
            "input": "Research and compare different cloud providers for a startup company.",
            "answer": "provide comprehensive cloud provider comparison with recommendations",
            "additional_context": {"task_type": "research"}
        },
        {
            "input": "Build a simple e-commerce website with payment integration.",
            "answer": "develop e-commerce website with proper payment integration",
            "additional_context": {"task_type": "e-commerce_development"}
        },
        {
            "input": "Analyze this dataset and create visualizations showing sales trends.",
            "answer": "analyze dataset and create meaningful sales trend visualizations",
            "additional_context": {"task_type": "data_analysis"}
        },
        {
            "input": "Create a chatbot for customer service with natural language processing.",
            "answer": "build intelligent chatbot with NLP capabilities for customer service",
            "additional_context": {"task_type": "ai_development"}
        }
    ]
    
    return trainset, valset

def main():
    parser = argparse.ArgumentParser(description="Optimize II Agent system prompt using GEPA")
    parser.add_argument("--model_name", type=str, default="Qwen3-Coder-A35B", help="Model name for optimization")
    parser.add_argument("--base_url", type=str, default="https://95819c637082.ngrok.app/v1", help="API base URL")
    parser.add_argument("--api_key", type=str, default="dummy", help="API key")
    parser.add_argument("--max_metric_calls", type=int, default=100, help="Maximum number of metric calls")
    parser.add_argument("--reflection_minibatch_size", type=int, default=2, help="Size of reflection minibatch")
    parser.add_argument("--run_dir", type=str, default="ii_agent_optimization", help="Directory to save results")
    
    args = parser.parse_args()
    
    # Read the original II Agent system prompt
    if II_AGENT_PROMPT_PATH.exists():
        original_prompt = II_AGENT_PROMPT_PATH.read_text(encoding='utf-8')
        print(f"Loaded original prompt from {II_AGENT_PROMPT_PATH}")
    else:
        print(f"Warning: Could not find prompt file at {II_AGENT_PROMPT_PATH}")
        original_prompt = "You are II Agent, an advanced AI assistant."
    
    # Create dataset
    trainset, valset = create_ii_agent_dataset()
    
    # Setup reflection LM
    def reflection_lm(prompt: str) -> str:
        try:
            response = litellm.completion(
                model=f"openai/{args.model_name}",  # Prefix with openai/ for custom endpoints
                messages=[{"role": "user", "content": prompt}],
                api_base=args.base_url,
                api_key=args.api_key,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in reflection LM: {e}")
            return "Error in reflection"
    
    # Create adapter
    adapter = IIAgentAdapter(
        model_name=args.model_name,
        base_url=args.base_url,
        api_key=args.api_key
    )
    
    # Initial candidate with the original system prompt
    seed_candidate = {"system_prompt": original_prompt}
    
    print("Starting GEPA optimization...")
    print(f"Model: {args.model_name}")
    print(f"Base URL: {args.base_url}")
    print(f"Training set size: {len(trainset)}")
    print(f"Validation set size: {len(valset)}")
    
    # Run GEPA optimization
    result = optimize(
        seed_candidate=seed_candidate,
        trainset=trainset,
        valset=valset,
        adapter=adapter,
        reflection_lm=reflection_lm,
        max_metric_calls=args.max_metric_calls,
        reflection_minibatch_size=args.reflection_minibatch_size,
        perfect_score=1.0,
        skip_perfect_score=False,
        run_dir=args.run_dir,
        use_wandb=False,  # Set to True if you want to use Weights & Biases
        display_progress_bar=True,
        seed=42
    )
    
    # Save results
    output_dir = Path(args.run_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Save the optimized prompt
    optimized_prompt_path = output_dir / "optimized_system_prompt.txt"
    with open(optimized_prompt_path, 'w', encoding='utf-8') as f:
        f.write(result.best_candidate["system_prompt"])
    
    # Save full results
    results_path = output_dir / "optimization_results.json"
    
    # Get best score from result (check available attributes)
    best_score = getattr(result, 'best_score', None)
    if best_score is None:
        # Try to get from best_candidate_score or calculate from state
        best_score = getattr(result, 'best_candidate_score', 0.0)
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump({
            "best_score": best_score,
            "best_candidate": result.best_candidate,
            "optimization_history": getattr(result, 'history', []),
            "original_prompt_length": len(original_prompt),
            "optimized_prompt_length": len(result.best_candidate["system_prompt"]),
            "result_attributes": [attr for attr in dir(result) if not attr.startswith('_')],  # Debug info
        }, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*50)
    print("OPTIMIZATION COMPLETED!")
    print("="*50)
    print(f"Best score: {best_score:.4f}")
    print(f"Optimized prompt saved to: {optimized_prompt_path}")
    print(f"Full results saved to: {results_path}")
    print(f"Original prompt length: {len(original_prompt)} characters")
    print(f"Optimized prompt length: {len(result.best_candidate['system_prompt'])} characters")
    
    # Print a preview of the optimized prompt
    print("\n" + "-"*30)
    print("OPTIMIZED PROMPT PREVIEW:")
    print("-"*30)
    optimized_prompt = result.best_candidate["system_prompt"]
    preview = optimized_prompt[:500] + "..." if len(optimized_prompt) > 500 else optimized_prompt
    print(preview)

if __name__ == "__main__":
    main()
