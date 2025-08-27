# TinyOwl Interactive Chat Usage Guide

## 🦉 What You've Built

You now have a beautiful, interactive chat interface for your TinyOwl RAG system with:

✨ **Features:**
- 🎨 Beautiful terminal UI with colors and animations
- 🤖 Switch between 4+ local LLM models on the fly  
- 📚 Toggle RAG (knowledge base search) on/off
- ⚡ Cool loading spinners with random "thinking" words like Claude
- 💬 Persistent chat history during session
- 🎯 Smart context retrieval from your theology database

## 🚀 How to Launch

### Option 1: Desktop Shortcut
Double-click the **"TinyOwl Chat"** shortcut on your desktop

### Option 2: Command Line
```bash
cd /home/nigel/tinyowl
./launch_tinyowl.sh
```

### Option 3: Direct Python (if venv already activated)
```bash
cd /home/nigel/tinyowl
source venv/bin/activate
python chat_interface.py
```

## 💻 Interface Overview

When you launch, you'll see:

```
🦉 TinyOwl Interactive Chat
============================================================
Your personal theological knowledge assistant
============================================================

✓ Connected to theology database (371 documents)
✓ Found 7 available models
✓ System ready!

Status:
  🤖 Model: qwen2.5-coder:3b
  📚 RAG: ON
  💬 History: 0 messages

Commands:
  /models    - List available models
  /switch    - Switch model
  /rag       - Toggle RAG on/off
  /status    - Show current status
  /clear     - Clear chat history
  /help      - Show this help
  /quit      - Exit chat

Ready to chat! Ask me anything about theology or type /help for commands.

You: _
```

## 🎮 Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/models` | Shows all available Ollama models | Lists your 7 models |
| `/switch` | Interactive model switching | Choose 1-7 from menu |
| `/rag` | Toggle knowledge base search | Turns RAG ON/OFF |
| `/status` | Show current settings | Model, RAG status, history |
| `/clear` | Clear chat history | Fresh start |
| `/help` | Show commands | This help menu |
| `/quit` | Exit chat | Goodbye! |

## 🔮 Loading Animations

While thinking, you'll see fun animations like:
- 🔄 `⠋ philosophizing...`
- 🔄 `⠙ contemplating sacred texts...`  
- 🔄 `⠹ channeling ancient wisdom...`
- 🔄 `⠸ parsing scripture...`

## 🤖 Available Models (From Your Test Results)

Based on performance testing:

1. **qwen2.5-coder:3b** 🥇 (Default - Fastest & Most Consistent)
2. **phi3:mini** 🥈 (Good Balance) 
3. **mistral:latest** 🥉 (High Quality)
4. **qwen2.5:7b** (Slower but Accurate)
5. **qwen2.5-coder:7b**
6. **mistral:7b** 
7. **phi3:latest**

## 📚 RAG System Details

**When RAG is ON:**
- Searches your 371-document theology database
- Finds relevant passages from Bible + Ellen G. White books
- Provides contextual answers based on sources
- Shows source attribution

**When RAG is OFF:**
- Uses model's general knowledge only
- Faster responses
- No source citations
- Good for general theological discussions

## 💡 Example Conversations

### Basic Theology Question (RAG ON)
```
You: What does the Bible say about the Sabbath?

🔄 searching knowledge base...
🔄 contemplating scripture...

🦉 TinyOwl: Based on the biblical passages, the Sabbath is the seventh day 
of the week set apart for worship and rest. The Bible teaches that God 
blessed and sanctified the seventh day after creation, and commands us 
to remember the Sabbath day to keep it holy...

[Sources: King James Version Bible, The Desire of Ages by Ellen G. White]
```

### Model Switching
```
You: /switch

Switch Model:
* 1. qwen2.5-coder:3b
  2. phi3:mini
  3. mistral:latest
  4. qwen2.5:7b
  ...

Enter model number (1-7): 3
✓ Switched to mistral:latest
```

## 🔧 Technical Requirements

**Prerequisites:**
- Ollama running (`ollama serve`)
- At least one model installed
- TinyOwl vector database exists
- Virtual environment with dependencies

**System Check on Launch:**
- ✅ Ollama connectivity
- ✅ Model availability  
- ✅ Vector database presence
- ✅ Virtual environment activation

## 🎯 Best Practices

1. **Start with RAG ON** for theological questions
2. **Use qwen2.5-coder:3b** for fastest responses
3. **Use mistral:latest** for highest quality answers
4. **Toggle RAG OFF** for general discussions
5. **Use /clear** to start fresh topics
6. **Type /quit** or Ctrl+C to exit cleanly

## 🐛 Troubleshooting

**"No models available"**
- Start Ollama: `ollama serve`
- Pull models: `ollama pull qwen2.5-coder:3b`

**"Database not found"** 
- Run ingestion first: `python scripts/ingest.py`

**EOF errors in background**
- Normal - run interactively from terminal

**Slow responses**
- Try smaller model (phi3:mini)
- Toggle RAG OFF for faster general responses

## 🎉 Enjoy Your Personal Theology Assistant!

You've successfully created a sophisticated RAG-powered chat system that can:
- Answer questions from 371 theological documents
- Switch between multiple AI models instantly
- Provide beautiful, engaging user experience
- Search and cite sources automatically

Have fun exploring your knowledge base! 🦉✨