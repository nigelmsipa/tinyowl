#!/usr/bin/env python3
"""
Test TinyOwl 1.0 - Quick inference test
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

print("🦉 TinyOwl 1.0 Test Script")
print("=" * 60)

# Paths
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
TINYOWL_ADAPTER = "/home/nigel/tinyowl/content/tinyowl-1.0"

print(f"\n📦 Loading base model: {BASE_MODEL}")
print("   (This may take a minute...)")

try:
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    # Load base model
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True
    )

    print("✅ Base model loaded")

    # Load TinyOwl adapter
    print(f"\n🦉 Loading TinyOwl adapter from: {TINYOWL_ADAPTER}")
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, TINYOWL_ADAPTER)
    print("✅ TinyOwl adapter loaded!")

    model.eval()

    print("\n" + "=" * 60)
    print("🧪 TESTING TINYOWL WITH THEOLOGICAL QUESTIONS")
    print("=" * 60)

    # Test questions
    test_questions = [
        "Who was Aaron?",
        "What does the Bible say about the Sabbath?",
        "Explain the sanctuary service.",
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n📖 Question {i}: {question}")
        print("-" * 60)

        # Format as chat
        messages = [
            {"role": "user", "content": question}
        ]

        # Tokenize
        inputs = tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True
        ).to(model.device)

        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        # Decode
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the assistant's response
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()

        print(f"🦉 TinyOwl: {response}")
        print()

    print("=" * 60)
    print("✅ TinyOwl 1.0 is working!")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\nTroubleshooting:")
    print("1. Make sure you're in the venv: source venv/bin/activate")
    print("2. Install required packages: pip install peft transformers torch")
    print("3. Check that adapter path exists: ls -la content/tinyowl-1.0/")
