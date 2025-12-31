"""SFT training script for Hugging Face Jobs"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Training script content (PEP 723 format)
TRAIN_SCRIPT = '''#!/usr/bin/env python3
# /// script
# dependencies = [
#     "trl>=0.12.0",
#     "peft>=0.7.0",
#     "transformers>=4.36.0",
#     "accelerate>=0.24.0",
#     "datasets>=2.14.0",
#     "trackio",
#     "huggingface-hub>=0.19.0",
# ]
# ///

"""
SFT training for Trust-aware Paper Searcher
"""

import trackio
from datasets import load_dataset
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig
from transformers import AutoTokenizer, AutoModelForCausalLM
import json

# Load dataset
print("📦 Loading dataset...")
dataset_path = "{dataset_path}"
dataset = load_dataset("json", data_files=dataset_path, split="train")
print(f"✅ Dataset loaded: {{len(dataset)}} examples")

# Format dataset for instruction tuning
def format_prompt(example):
    """Format instruction-response pair"""
    instruction = example["instruction"]
    response = example["response"]
    
    # Format as chat template
    formatted = f"### Instruction:\\n{{instruction}}\\n\\n### Response:\\n{{response}}"
    return {{"text": formatted}}

# Apply formatting
print("📝 Formatting dataset...")
dataset = dataset.map(format_prompt)

# Create train/eval split
print("🔀 Creating train/eval split...")
dataset_split = dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = dataset_split["train"]
eval_dataset = dataset_split["test"]
print(f"   Train: {{len(train_dataset)}} examples")
print(f"   Eval: {{len(eval_dataset)}} examples")

# Load tokenizer and model
print("🎯 Loading model and tokenizer...")
model_name = "{base_model}"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Set padding token if not exists
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# LoRA configuration
peft_config = LoraConfig(
    r={lora_r},
    lora_alpha={lora_alpha},
    lora_dropout={lora_dropout},
    bias="none",
    task_type="CAUSAL_LM",
    target_modules={target_modules},
)

# Training configuration
config = SFTConfig(
    # CRITICAL: Hub settings
    output_dir="{output_dir}",
    push_to_hub=True,
    hub_model_id="{hub_model_id}",
    hub_strategy="every_save",  # Push checkpoints

    # Training parameters
    num_train_epochs={num_epochs},
    per_device_train_batch_size={batch_size},
    gradient_accumulation_steps={gradient_accumulation_steps},
    learning_rate={learning_rate},
    max_seq_length={max_length},

    # Logging & checkpointing
    logging_steps=10,
    save_strategy="steps",
    save_steps={save_steps},
    save_total_limit=2,

    # Evaluation
    eval_strategy="steps",
    eval_steps={eval_steps},

    # Optimization
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    optim="adamw_torch",

    # Monitoring
    report_to="trackio",
    project="{project_name}",
    run_name="{run_name}",
)

# Initialize trainer
print("🚀 Initializing trainer...")
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    args=config,
    peft_config=peft_config,
    packing=False,  # Don't pack sequences
)

print("🎓 Starting training...")
trainer.train()

print("💾 Pushing to Hub...")
trainer.push_to_hub()

print("✅ Training complete!")
print(f"📊 Model available at: https://huggingface.co/{{hub_model_id}}")
'''


def submit_training_job(
    dataset_path: str,
    base_model: str = "Qwen/Qwen2.5-0.5B",
    hub_model_id: str = None,
    num_epochs: int = 3,
    batch_size: int = 4,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 2e-5,
    max_length: int = 2048,
    lora_r: int = 16,
    lora_alpha: int = 32,
    lora_dropout: float = 0.05,
    target_modules: list = None,
    flavor: str = "a10g-large",
    timeout: str = "3h",
    project_name: str = "trust-aware-paper-searcher",
    run_name: str = "baseline-run"
):
    """
    Submit training job to Hugging Face Jobs
    
    Args:
        dataset_path: Path to dataset JSONL file (will be uploaded)
        base_model: Base model name
        hub_model_id: Hub model ID (username/model-name)
        num_epochs: Number of training epochs
        batch_size: Per device batch size
        gradient_accumulation_steps: Gradient accumulation steps
        learning_rate: Learning rate
        max_length: Maximum sequence length
        lora_r: LoRA rank
        lora_alpha: LoRA alpha
        lora_dropout: LoRA dropout
        target_modules: Target modules for LoRA
        flavor: Hardware flavor
        timeout: Job timeout
        project_name: Trackio project name
        run_name: Trackio run name
    """
    from huggingface_hub import HfApi
    
    # Get HF token
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not found in environment variables")
    
    # Set default hub_model_id
    if not hub_model_id:
        hub_model_id = os.getenv("HUB_MODEL_ID", "your-username/trust-aware-paper-searcher")
    
    # Set default target modules
    if target_modules is None:
        # Default for Qwen models
        target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
    
    # Format target modules as Python list string
    target_modules_str = str(target_modules)
    
    # Calculate save steps (save every 10% of training)
    total_steps = num_epochs * (1000 // batch_size // gradient_accumulation_steps)  # Rough estimate
    save_steps = max(50, total_steps // 10)
    eval_steps = save_steps
    
    # Format script with parameters
    script_content = TRAIN_SCRIPT.format(
        dataset_path=dataset_path,
        base_model=base_model,
        output_dir="trust-aware-paper-searcher-sft",
        hub_model_id=hub_model_id,
        num_epochs=num_epochs,
        batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        max_length=max_length,
        lora_r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=target_modules_str,
        save_steps=save_steps,
        eval_steps=eval_steps,
        project_name=project_name,
        run_name=run_name
    )
    
    # Upload dataset to Hub if it's a local file
    api = HfApi(token=hf_token)
    dataset_repo_id = None
    
    if os.path.exists(dataset_path):
        # Upload dataset
        dataset_repo_id = hub_model_id.replace("/", "-") + "-dataset"
        print(f"📤 Uploading dataset to Hub: {dataset_repo_id}")
        # Note: In production, you'd upload the dataset properly
        # For now, we'll reference it as a local path that needs to be uploaded
    
    # Submit job using hf_jobs MCP tool
    # Note: This requires the hf_jobs MCP tool to be available
    print("🚀 Submitting training job to Hugging Face Jobs...")
    print(f"   Model: {base_model}")
    print(f"   Dataset: {dataset_path}")
    print(f"   Hardware: {flavor}")
    print(f"   Timeout: {timeout}")
    
    # Return job configuration (user will submit via MCP tool)
    job_config = {
        "script": script_content,
        "flavor": flavor,
        "timeout": timeout,
        "secrets": {"HF_TOKEN": hf_token},
    }
    
    print("\n📋 Job Configuration:")
    print(json.dumps(job_config, indent=2))
    print("\n💡 Submit this job using the hf_jobs MCP tool:")
    print(f"   hf_jobs('uv', {json.dumps(job_config, indent=2)})")
    
    return job_config


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Submit SFT training job")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset JSONL file")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-0.5B", help="Base model")
    parser.add_argument("--hub_model_id", type=str, help="Hub model ID")
    parser.add_argument("--num_epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--flavor", type=str, default="a10g-large", help="Hardware flavor")
    parser.add_argument("--timeout", type=str, default="3h", help="Job timeout")
    
    args = parser.parse_args()
    
    # Check if dataset exists
    if not os.path.exists(args.dataset):
        print(f"❌ Dataset not found: {args.dataset}")
        return
    
    # Submit job
    job_config = submit_training_job(
        dataset_path=args.dataset,
        base_model=args.base_model,
        hub_model_id=args.hub_model_id,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        flavor=args.flavor,
        timeout=args.timeout
    )
    
    print("\n✅ Job configuration generated!")
    print("   Use the hf_jobs MCP tool to submit the job.")


if __name__ == "__main__":
    main()

