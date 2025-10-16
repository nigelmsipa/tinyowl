# Creating a TinyOwl Release

## Quick Guide to Ship TinyOwl

### Step 1: Create the Release Package

The Linux package is ready at:
```
/home/nigel/tinyowl/packaging/dist/TinyOwl/
```

Create the downloadable archive:
```bash
cd /home/nigel/tinyowl/packaging/dist
tar -czf TinyOwl-v1.0-Linux.tar.gz TinyOwl/
```

This creates a ~1GB file that users can download.

### Step 2: Create GitHub Release

1. Go to: https://github.com/nigelmsipa/tinyowl/releases/new

2. Fill in:
   - **Tag**: `v1.0.0`
   - **Title**: `TinyOwl v1.0 - First Release 🦉`
   - **Description**: (copy below)

3. **Attach file**: Upload `TinyOwl-v1.0-Linux.tar.gz`

4. **Publish release**

**Release Description:**
```markdown
# TinyOwl v1.0 🦉

Your personal theological AI assistant - completely offline, completely free.

## What is TinyOwl?

TinyOwl is a fine-tuned AI model trained on 373,000 chunks of biblical and Seventh-day Adventist theological content. Ask questions about Scripture, theology, or biblical topics and get informed answers based on:

- King James Version & World English Bible
- Complete Strong's Concordance (Hebrew & Greek)
- Spirit of Prophecy complete collection
- Curated SDA sermons

## Downloads

### 🐧 Linux
- **File**: `TinyOwl-v1.0-Linux.tar.gz`
- **Size**: ~1GB
- **Install**: Extract and run `./TinyOwl/TinyOwl`

### 🍎 Mac (Coming Soon)
Mac build requires building on a Mac computer.

### 🪟 Windows (Coming Soon)
Windows build requires building on Windows.

## Quick Start

```bash
# Extract
tar -xzf TinyOwl-v1.0-Linux.tar.gz

# Run
./TinyOwl/TinyOwl
```

## System Requirements

- 8GB RAM minimum (16GB recommended)
- 2GB disk space
- Modern CPU (no GPU required)
- Linux (Mac/Windows builds coming soon)

## Features

✅ 100% offline - no internet required
✅ Free and open source
✅ Trained on 373K theological chunks
✅ Desktop chat interface
✅ Fast CPU-only inference

## What's Included

- Fine-tuned TinyLlama 1.1B model
- Theological knowledge base
- Desktop chat application
- All dependencies bundled

## Support

- 📘 [Documentation](https://github.com/nigelmsipa/tinyowl)
- 🐛 [Report Issues](https://github.com/nigelmsipa/tinyowl/issues)

---

*"Freely you have received, freely give." - Matthew 10:8*

🦉 Built with Claude Code
```

### Step 3: Enable GitHub Pages

1. Go to: https://github.com/nigelmsipa/tinyowl/settings/pages

2. **Source**: Deploy from a branch

3. **Branch**: `main`

4. **Folder**: `/docs`

5. Click **Save**

Your download page will be live at:
**https://nigelmsipa.github.io/tinyowl/download.html**

### Step 4: Share!

Once GitHub Pages is enabled (takes ~2 minutes), share the link:

```
https://nigelmsipa.github.io/tinyowl/download.html
```

Users can:
1. Visit the page
2. Click "Download for Linux"
3. Extract and run TinyOwl
4. Start chatting!

## Building for Other Platforms

### Mac Build (requires a Mac)

```bash
git clone https://github.com/nigelmsipa/tinyowl.git
cd tinyowl

# You'll need to transfer the model files first
# Then follow the same packaging steps

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller

cd packaging
python merge_and_quantize.py
pyinstaller tinyowl.spec
```

### Windows Build (requires Windows)

Same process as Mac, but on Windows machine.

## That's It!

You now have:
- ✅ Packaged desktop app
- ✅ GitHub Release for downloads
- ✅ Beautiful landing page
- ✅ Distribution ready

Share the link and let people download TinyOwl!
