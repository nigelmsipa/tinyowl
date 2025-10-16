#!/usr/bin/env python3
"""
Quick test of TinyOwl GGUF model
"""

from llama_cpp import Llama

print("🦉 Loading TinyOwl model...")
print("=" * 60)

# Load the model
llm = Llama(
    model_path="packaging/models/tinyowl-q4.gguf",
    n_ctx=2048,  # Context window
    n_threads=4,  # Number of CPU threads
)

print("✅ Model loaded successfully!")
print()

# Test question
question = "Who was Aaron?"

print(f"Question: {question}")
print("-" * 60)

# Generate response
response = llm.create_chat_completion(
    messages=[
        {"role": "user", "content": question}
    ],
    max_tokens=200,
    temperature=0.7,
)

# Extract and print the response
answer = response['choices'][0]['message']['content']
print(f"TinyOwl: {answer}")
print()
print("=" * 60)
print("✅ TinyOwl GGUF model is working!")
