#!/usr/bin/env python3
"""
Merge TinyOwl LoRA adapter with base model and prepare for packaging
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os

print("🦉 TinyOwl Packaging: Step 1 - Merge LoRA with Base Model")
print("=" * 70)

# Paths
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
ADAPTER_PATH = "/home/nigel/tinyowl/content/tinyowl-1.0"
OUTPUT_PATH = "/home/nigel/tinyowl/packaging/models/tinyowl-merged"

print(f"\n📦 Loading base model: {BASE_MODEL}")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    device_map="cpu",
    low_cpu_mem_usage=True
)

print(f"\n🔗 Loading LoRA adapter from: {ADAPTER_PATH}")
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)

print("\n⚡ Merging adapter with base model...")
merged_model = model.merge_and_unload()

print(f"\n💾 Saving merged model to: {OUTPUT_PATH}")
os.makedirs(OUTPUT_PATH, exist_ok=True)
merged_model.save_pretrained(OUTPUT_PATH)
tokenizer.save_pretrained(OUTPUT_PATH)

print("\n✅ Merge complete!")
print(f"📁 Merged TinyOwl model saved at: {OUTPUT_PATH}")
print("\nNext: Convert to GGUF format using llama.cpp")
