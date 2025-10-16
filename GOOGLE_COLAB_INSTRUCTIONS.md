# 🦉 TinyOwl Google Colab Training Guide

## What is Google Colab?

**Google Colab** = Free cloud computer with GPU that runs in your browser

**Think of it like**:
- A powerful computer in the cloud
- You don't need to install anything
- You get a FREE GPU (graphics card) for training AI
- Everything runs in your web browser
- No technical setup required

**Why we're using it**: Training AI models needs a GPU. Your laptop might not have one (or it's not powerful enough). Google gives you a free one!

---

## Step-by-Step: Train TinyOwl (Super Easy)

### STEP 1: Upload Your Notebook

1. Go to **https://colab.research.google.com/**
2. Sign in with your Google account
3. Click **File** → **Upload notebook**
4. Upload: `/home/nigel/tinyowl/TinyOwl_Training.ipynb`

**That's it!** The notebook is now open in your browser.

---

### STEP 2: Enable Free GPU

1. In Colab, click **Runtime** (top menu)
2. Click **Change runtime type**
3. Under "Hardware accelerator", select **T4 GPU**
4. Click **Save**

**What this does**: Gives you a free powerful GPU for ~12-20 hours

---

### STEP 3: Upload Your Training Files

You need to upload 2 files to Colab:

**Files to upload**:
1. `/home/nigel/tinyowl/training_data/domain_adaptation.jsonl` (281 MB)
2. `/home/nigel/tinyowl/training_data/instruction_tuning.jsonl` (~10-15 MB when Q&A generation finishes)

**How to upload**:
1. Look at the **left sidebar** in Colab
2. Click the **folder icon** 📁
3. Click the **upload button** ⬆️
4. Select both files
5. Wait for upload to complete (~2-5 minutes for large file)

---

### STEP 4: Run the Training (Just Click Buttons!)

Now the fun part - training your AI!

**How to run**:
1. **Click the first code cell** (has a ▶️ play button)
2. **Wait for it to finish** (you'll see a green checkmark ✓)
3. **Click the next code cell**
4. **Repeat** for each cell, top to bottom

**What happens**:
- **Cell 1-3**: Setup (5 minutes total)
- **Cell 4-7**: Phase 1 training (~8-12 hours)
- **Cell 8-11**: Phase 2 training (~4-8 hours)
- **Cell 12**: Test your model!
- **Cell 13**: Download TinyOwl 1.0

---

### STEP 5: Let It Train (Walk Away!)

**Training takes ~12-20 hours total.**

**You can**:
- Close the browser (training continues!)
- Do other things
- Check back later
- Colab will email you when done (if you set that up)

**IMPORTANT**:
- Don't let your computer go to sleep (or training stops)
- OR: Keep the Colab tab open
- OR: Use Colab Pro ($10/month) for background execution

---

### STEP 6: Download Your Trained Model

When training finishes:

1. **Run the download cell** (last cell in notebook)
2. This creates `tinyowl-1.0.zip`
3. **Look at left sidebar** (folder icon)
4. **Find `tinyowl-1.0.zip`**
5. **Right-click** → **Download**

**⚠️ CRITICAL**: Download BEFORE closing Colab!
- Colab deletes everything when you close it
- You lose your trained model if you don't download
- The download is ~500MB-1GB

---

## What You're Actually Doing

**In simple terms**:

1. **Phase 1** (8-12 hours):
   - Feeding TinyLlama your 373K theological chunks
   - Model learns: Bible verses, SDA theology, Strong's concordance
   - Like teaching it to "read" your entire theological library

2. **Phase 2** (4-8 hours):
   - Teaching it to answer questions
   - Uses your Q&A pairs
   - Like teaching it to be a helpful assistant

3. **Result**:
   - TinyOwl 1.0 = TinyLlama that "knows" SDA theology
   - Can answer biblical questions
   - Works 100% offline
   - Ready to package and distribute

---

## Troubleshooting

### "GPU not available"
→ Go to Runtime → Change runtime type → Select T4 GPU

### "File not found"
→ Make sure you uploaded both .jsonl files to Colab

### "Out of memory"
→ This shouldn't happen with T4, but if it does:
- Restart runtime (Runtime → Restart runtime)
- Try again

### "Session disconnected"
→ Colab times out after 12 hours of inactivity
- You may need to restart from where it stopped
- Or: Use Colab Pro for longer sessions

### Training is taking too long
→ This is normal! AI training takes hours
- Phase 1: 8-12 hours is expected
- Phase 2: 4-8 hours is expected
- Be patient! You're training an entire AI model

---

## After Training

### What you'll have:
- **tinyowl-1.0.zip** = Your trained model (~500MB-1GB)

### What to do next:
1. **Unzip it** on your computer
2. **Test it** with the inference script (I'll create this)
3. **Quantize to GGUF** (make it smaller/faster)
4. **Package with chat app**
5. **Ship TinyOwl to the world!**

---

## Cost

**Google Colab Free**:
- $0 for GPU
- ~12-20 hours of training
- Limits: Can disconnect after 12 hours idle

**Google Colab Pro** ($10/month):
- Better GPUs (A100 if available)
- Longer sessions (24+ hours)
- Background execution
- Worth it if free tier gives you issues

**Your actual costs so far**:
- Q&A generation: ~$10-20 (OpenAI API)
- Colab training: $0 (free tier) or $10 (Pro for 1 month)
- **Total**: $10-30 to train complete TinyOwl model

---

## Questions?

**"Do I need to watch it train?"**
→ No! Just start it and walk away. Check back in 12-20 hours.

**"What if something fails?"**
→ The notebook saves checkpoints. You can resume from last save.

**"Can I use my own computer?"**
→ Yes, but only if you have a GPU with 16GB+ VRAM. Colab is easier.

**"How do I know it's working?"**
→ You'll see loss values decreasing. That means it's learning!

**"Can I stop and resume later?"**
→ Yes! Each phase saves checkpoints. You can continue from where you stopped.

---

## Ready to Train?

1. ✅ Go to https://colab.research.google.com/
2. ✅ Upload `TinyOwl_Training.ipynb`
3. ✅ Enable T4 GPU
4. ✅ Upload your 2 training files
5. ✅ Click play on first cell
6. ✅ Let it run!

**You're about to create TinyOwl 1.0. This is happening. 🦉**
