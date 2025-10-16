#!/usr/bin/env python3
"""
Fine-tune TinyLlama on TinyOwl theological dataset.

Phase 1: Domain adaptation (learn theological knowledge)
Phase 2: Instruction tuning (learn to answer questions)

Uses Unsloth for efficient QLoRA training on consumer hardware.
"""

import json
from pathlib import Path
from typing import List, Dict
import torch

# Check if we're on a system with GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️  Training device: {device}")

if device == "cpu":
    print("⚠️  WARNING: Training on CPU will be VERY slow!")
    print("   Recommended: Use Google Colab (free T4 GPU)")
    print("   or RunPod/Vast.ai (~$0.50/hour for A6000)")
    print()


def load_dataset(filepath: Path) -> List[Dict]:
    """Load JSONL dataset"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def phase1_domain_adaptation():
    """Phase 1: Teach TinyLlama theological knowledge"""

    print("=" * 60)
    print("PHASE 1: DOMAIN ADAPTATION")
    print("Teaching TinyLlama theological knowledge from 403K chunks")
    print("=" * 60)
    print()

    try:
        from unsloth import FastLanguageModel
    except ImportError:
        print("❌ Unsloth not installed!")
        print("   Install: pip install unsloth")
        print("   Or run in Google Colab: https://colab.research.google.com/")
        return None

    # Load TinyLlama with 4-bit quantization
    print("📥 Loading TinyLlama-1.1B-Chat-v1.0...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        max_seq_length=2048,
        dtype=None,  # Auto-detect
        load_in_4bit=True,  # QLoRA - fits in 16GB RAM
    )

    print("✅ Model loaded")

    # Add LoRA adapters
    print("🔧 Adding LoRA adapters...")

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,  # LoRA rank
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing=True,
        random_state=3407,
    )

    print("✅ LoRA adapters added")

    # Load training data
    dataset_path = Path("/home/nigel/tinyowl/training_data/domain_adaptation.jsonl")

    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        print("   Run: python scripts/prepare_domain_adaptation_data.py")
        return None

    print(f"📚 Loading dataset: {dataset_path}")
    train_data = load_dataset(dataset_path)
    print(f"✅ Loaded {len(train_data):,} training examples")

    # Format for training
    from datasets import Dataset

    def formatting_func(examples):
        texts = []
        for text in examples["text"]:
            # Simple continuation format for domain adaptation
            texts.append(f"<|im_start|>system\nYou are a theological research assistant trained on biblical and SDA content.<|im_end|>\n<|im_start|>text\n{text}<|im_end|>")
        return {"text": texts}

    dataset = Dataset.from_list(train_data)
    dataset = dataset.map(formatting_func, batched=True)

    # Training arguments
    from transformers import TrainingArguments
    from trl import SFTTrainer

    print("🚀 Starting Phase 1 training...")
    print(f"   Epochs: 1")
    print(f"   Batch size: 4")
    print(f"   Learning rate: 2e-4")
    print()

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        args=TrainingArguments(
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            warmup_steps=10,
            max_steps=1000,  # Adjust based on dataset size
            learning_rate=2e-4,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=10,
            output_dir="/home/nigel/tinyowl/models/phase1_output",
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=3407,
        ),
    )

    trainer.train()

    print("✅ Phase 1 training complete!")

    # Save model
    model_path = Path("/home/nigel/tinyowl/models/tinyowl-phase1")
    model_path.mkdir(parents=True, exist_ok=True)

    print(f"💾 Saving model to {model_path}")
    model.save_pretrained(str(model_path))
    tokenizer.save_pretrained(str(model_path))

    print("✅ Phase 1 model saved")

    return model, tokenizer


def phase2_instruction_tuning(model=None, tokenizer=None):
    """Phase 2: Teach TinyLlama to answer questions"""

    print()
    print("=" * 60)
    print("PHASE 2: INSTRUCTION TUNING")
    print("Teaching TinyLlama to answer theological questions")
    print("=" * 60)
    print()

    from unsloth import FastLanguageModel

    # Load Phase 1 model if not provided
    if model is None:
        print("📥 Loading Phase 1 model...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name="/home/nigel/tinyowl/models/tinyowl-phase1",
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        print("✅ Model loaded")

    # Load Q&A dataset
    dataset_path = Path("/home/nigel/tinyowl/training_data/instruction_tuning.jsonl")

    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        print("   Run: python scripts/generate_qa_pairs.py")
        return

    print(f"📚 Loading Q&A dataset: {dataset_path}")
    train_data = load_dataset(dataset_path)
    print(f"✅ Loaded {len(train_data):,} Q&A pairs")

    # Format for instruction tuning
    from datasets import Dataset

    def formatting_func(examples):
        texts = []
        for instruction, output in zip(examples["instruction"], examples["output"]):
            text = f"""<|im_start|>system
You are TinyOwl, a theological research assistant trained on biblical Scripture, Spirit of Prophecy, and Strong's concordance. Answer questions accurately based on this knowledge.<|im_end|>
<|im_start|>user
{instruction}<|im_end|>
<|im_start|>assistant
{output}<|im_end|>"""
            texts.append(text)
        return {"text": texts}

    dataset = Dataset.from_list(train_data)
    dataset = dataset.map(formatting_func, batched=True)

    # Training
    from transformers import TrainingArguments
    from trl import SFTTrainer

    print("🚀 Starting Phase 2 training...")
    print(f"   Epochs: 2")
    print(f"   Batch size: 4")
    print(f"   Learning rate: 2e-5")
    print()

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        args=TrainingArguments(
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            num_train_epochs=2,
            learning_rate=2e-5,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=10,
            output_dir="/home/nigel/tinyowl/models/phase2_output",
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=3407,
        ),
    )

    trainer.train()

    print("✅ Phase 2 training complete!")

    # Save final model
    model_path = Path("/home/nigel/tinyowl/models/tinyowl-1.0")
    model_path.mkdir(parents=True, exist_ok=True)

    print(f"💾 Saving TinyOwl 1.0 to {model_path}")
    model.save_pretrained(str(model_path))
    tokenizer.save_pretrained(str(model_path))

    print()
    print("=" * 60)
    print("🎉 TINYOWL 1.0 TRAINING COMPLETE!")
    print("=" * 60)
    print()
    print(f"Model saved: {model_path}")
    print()
    print("Next steps:")
    print("1. Test the model: python scripts/test_tinyowl.py")
    print("2. Quantize to GGUF: python scripts/quantize_tinyowl.py")
    print("3. Package for distribution")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        phase = sys.argv[1]
        if phase == "phase1":
            phase1_domain_adaptation()
        elif phase == "phase2":
            phase2_instruction_tuning()
        else:
            print("Usage: python finetune_tinyowl.py [phase1|phase2]")
    else:
        # Run both phases
        print("🦉 TINYOWL COMPLETE FINE-TUNING PIPELINE")
        print()
        model, tokenizer = phase1_domain_adaptation()
        if model:
            phase2_instruction_tuning(model, tokenizer)
