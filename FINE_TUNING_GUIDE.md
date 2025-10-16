# TinyOwl Fine-Tuning Guide

## Complete Pipeline: From 403K Chunks to Trained Model

This guide walks through the complete fine-tuning process for TinyOwl.

---

## Overview

**Goal**: Fine-tune TinyLlama-1.1B on your 403K theological chunks

**Approach**: Two-phase training
1. **Phase 1**: Domain Adaptation (absorb theological knowledge)
2. **Phase 2**: Instruction Tuning (learn to answer questions)

**Hardware Requirements**:
- **Minimum**: 16GB RAM (CPU training, very slow)
- **Recommended**: GPU with 16GB+ VRAM
- **Best**: Google Colab (free T4 GPU) or RunPod ($0.50/hour)

**Time Estimate**:
- Data preparation: 2-3 hours
- Phase 1 training: 8-16 hours
- Phase 2 training: 4-8 hours
- **Total**: 1-2 days

---

## Step-by-Step Process

### Step 1: Prepare Domain Adaptation Dataset

Extract all 403K chunks and format for training:

```bash
source venv/bin/activate
python scripts/prepare_domain_adaptation_data.py
```

**Output**: `training_data/domain_adaptation.jsonl` (~150MB)

**What this does**:
- Loads all chunk JSON files (Bible, SOP, Strong's, etc.)
- Extracts text content
- Formats as simple JSONL (one chunk per line)
- Creates training data for Phase 1

---

### Step 2: Generate Q&A Pairs

Use AI to generate question-answer pairs from chunks:

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"

# Generate Q&A pairs
python scripts/generate_qa_pairs.py
```

**Output**: `training_data/instruction_tuning.jsonl`

**What this does**:
- Samples ~30K representative chunks
- Uses Claude/GPT to generate 2-3 questions per chunk
- Creates ~60-90K Q&A pairs for Phase 2
- **Cost**: ~$15-30 in API credits

**Options**:
- Edit script to use more/fewer chunks
- Adjust `max_chunks` parameter
- Use Anthropic (cheaper) or OpenAI

---

### Step 3: Install Fine-Tuning Dependencies

**Option A: Google Colab (Recommended)**
- Free T4 GPU (16GB VRAM)
- No local installation needed
- Upload your datasets to Colab
- Run training notebook

**Option B: Local Installation**
```bash
# Install Unsloth and dependencies
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps trl peft accelerate bitsandbytes

# If you have CUDA GPU
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Option C: RunPod/Vast.ai Cloud GPU**
- Rent A6000 GPU: ~$0.50/hour
- ~20 hours = $10 total
- Pre-configured templates available

---

### Step 4: Run Phase 1 Training (Domain Adaptation)

Teach TinyLlama theological knowledge:

```bash
python scripts/finetune_tinyowl.py phase1
```

**What this does**:
- Loads TinyLlama-1.1B-Chat-v1.0
- Adds LoRA adapters (efficient fine-tuning)
- Trains on ~400K theological chunks
- Saves to `models/tinyowl-phase1/`

**Training time**:
- T4 GPU (Colab): ~8-12 hours
- A6000 GPU: ~4-6 hours
- CPU: ~3-5 days (not recommended!)

**Settings**:
- QLoRA (4-bit quantization)
- LoRA rank: 16
- Batch size: 4 (fits 16GB VRAM)
- Learning rate: 2e-4
- Max steps: 1000 (adjust based on data)

---

### Step 5: Run Phase 2 Training (Instruction Tuning)

Teach model to answer questions:

```bash
python scripts/finetune_tinyowl.py phase2
```

**What this does**:
- Loads Phase 1 model
- Trains on ~60-90K Q&A pairs
- Learns question-answering format
- Saves to `models/tinyowl-1.0/`

**Training time**:
- T4 GPU: ~4-6 hours
- A6000 GPU: ~2-3 hours

**Settings**:
- 2 epochs over Q&A pairs
- Learning rate: 2e-5 (lower than Phase 1)
- Instruction-tuning format

---

### Step 6: Test Your Model

```bash
python scripts/test_tinyowl.py
```

Test queries:
- "What does the Bible say about the Sabbath?"
- "Who was Aaron?"
- "Explain the sanctuary service"

---

### Step 7: Quantize to GGUF (for distribution)

Convert to efficient format for llama.cpp:

```bash
# Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Convert model
python convert.py ../models/tinyowl-1.0/ --outtype f16 --outfile ../models/tinyowl-1.0-f16.gguf

# Quantize to 4-bit (2GB final size)
./quantize ../models/tinyowl-1.0-f16.gguf ../models/tinyowl-1.0-Q4_K_M.gguf Q4_K_M
```

**Output**: `tinyowl-1.0-Q4_K_M.gguf` (~2GB)

---

### Step 8: Package for Distribution

Create desktop application:

```bash
# Bundle model + vectordb + chat interface
# Package as Electron app
# Create installers for Windows/Mac/Linux
```

**Final package**:
- TinyOwl model (2GB GGUF)
- Vector database (6GB)
- Chat interface
- **Total**: ~10GB installer

---

## Alternative: Run Both Phases Together

```bash
# Run complete pipeline
python scripts/finetune_tinyowl.py
```

This runs Phase 1 → Phase 2 automatically.

---

## Monitoring Training

**Watch GPU usage**:
```bash
nvidia-smi -l 1
```

**Watch training progress**:
- Loss should decrease over time
- Check `models/phase1_output/` for logs
- TensorBoard: `tensorboard --logdir models/phase1_output/`

**Expected loss values**:
- Phase 1 start: ~3.0
- Phase 1 end: ~1.5-2.0
- Phase 2 start: ~1.5
- Phase 2 end: ~0.8-1.2

---

## Troubleshooting

**Out of memory**:
- Reduce batch size to 2
- Use gradient checkpointing
- Try smaller LoRA rank (8 instead of 16)

**Training too slow**:
- Use Google Colab with GPU
- Rent cloud GPU (RunPod/Vast.ai)
- Reduce dataset size for testing

**Model not improving**:
- Check loss is decreasing
- Verify dataset format is correct
- Try adjusting learning rate
- Train for more epochs

**Poor quality responses**:
- Generate more Q&A pairs
- Improve Q&A quality (better prompts)
- Train for more epochs in Phase 2
- Check if Phase 1 completed successfully

---

## Cost Breakdown

**Free option** (Google Colab):
- GPU: Free (T4)
- Q&A generation: ~$15-30 (Claude API)
- **Total**: $15-30

**Cloud GPU option** (RunPod):
- GPU rental: ~$10 (20 hours @ $0.50/hour)
- Q&A generation: ~$15-30
- **Total**: $25-40

**Local GPU option**:
- No rental costs
- Q&A generation: ~$15-30
- **Total**: $15-30 (if you have GPU)

---

## Next Steps After Training

1. Test model thoroughly with theological queries
2. Compare quality vs RAG-only approach
3. Quantize to GGUF for distribution
4. Package as desktop application
5. Beta test with SDA community
6. Iterate based on feedback

---

## Support

**Issues?**
- Check training logs in `models/phase*_output/`
- Verify dataset files exist in `training_data/`
- Ensure dependencies installed correctly
- GPU drivers up to date

**Questions?**
- TinyOwl is based on TinyLlama-1.1B-Chat-v1.0
- Uses Unsloth for efficient training
- LoRA/QLoRA for parameter-efficient fine-tuning

---

**You've got this! Your 403K chunks are ready to train the model.**
