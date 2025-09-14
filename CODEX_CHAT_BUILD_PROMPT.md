# TinyOwl Chat Application - Complete Build Specification for Codex

## Project Overview
Build a professional CLI chat application for TinyOwl - a theological research tool with 166K embedded biblical chunks. The chat app should work perfectly without AI, with optional Ollama integration for enhanced responses.

## Current TinyOwl Foundation (Already Built)
- **166,395 theological chunks** fully embedded with BGE-large-en-v1.5
- **ChromaDB collections**:
  - `kjv_verses` (31,102 chunks)
  - `kjv_pericopes` (9,968 chunks)
  - `kjv_chapters` (1,189 chunks)
  - `web_verses` (31,098 chunks)
  - `web_pericopes` (9,967 chunks)
  - `web_chapters` (1,189 chunks)
  - `strongs_concordance_entries` (81,882 chunks)
- **OSIS canonical system** for verse references
- **Proven retrieval router** (`scripts/retrieval_router.py`) with RRF fusion
- **Virtual environment** at `/home/nigel/tinyowl/venv/` with all dependencies

## Core Requirements

### 1. CLI Interface Design
- **Terminal aesthetic** like Claude Code/Codex CLI
- **Rich/Textual framework** for professional styling
- **Monospace fonts**, minimal color palette
- **Keyboard-driven**: Arrow keys, tab completion, command history
- **Launch via Rofi** - clean desktop integration

### 2. Intelligent Typeahead System (CRITICAL FEATURE)
When user types `@a`, show dropdown list:
```bash
> @a
   aaron (218 occurrences)
   abomination (65 occurrences)
   abraham (297 occurrences)
   altar (433 occurrences)
   [↓ arrow keys to navigate, Enter to select]

> @aa
   aaron (218 occurrences)
   [filters in real-time as you type]
```

**Typeahead Data Source**: Build from existing Strong's concordance data in:
- `/home/nigel/tinyowl/domains/theology/chunks/strongs_concordance_entries_chunks.json`

### 3. Command System
```bash
# Biblical lookup commands
@aaron → "Found 218 verses mentioning Aaron across Scripture..."
@strong:175 → "H175 (Aaron): אַהֲרֹן - brother of Moses, first high priest"
&john3:16 → Direct verse display with cross-references
#prophecy → Topical search across all indexed content

# Chat-specific commands
/history → Show recent chat sessions
/export → Export current conversation
/clear → Clear current session
/help → Show all available commands
/stats → Show database statistics (166K chunks ready)
```

### 4. Dual Response Modes

#### Mode 1: Pure Concordance (No AI Required)
- Fast database lookups from ChromaDB
- Formatted biblical text with references
- Strong's number integration
- Cross-references between translations

#### Mode 2: AI-Enhanced (Optional Ollama Integration)
- Check if Ollama is running on localhost:11434
- If available, enhance responses with AI analysis
- If not available, fall back to pure concordance mode
- User can toggle AI on/off with `/ai toggle`

### 5. Technical Architecture

#### Core Files Structure
```
tinyowl-chat/
├── main.py                 # Entry point, Rich/Textual app
├── database_manager.py     # ChromaDB integration
├── typeahead_engine.py     # Smart autocomplete system
├── command_parser.py       # Parse @, &, #, / commands
├── response_formatter.py   # Terminal output styling
├── chat_history.py         # SQLite session storage
├── ollama_integration.py   # Optional AI enhancement
└── config.py              # Configuration settings
```

#### Database Integration
- **Primary**: Direct ChromaDB queries (no FastAPI)
- **Fast lookups**: Pre-built concordance index from Strong's JSON
- **Chat history**: SQLite for session persistence
- **Virtual env**: Always use `/home/nigel/tinyowl/venv/`

### 6. Response Format Template
```
TinyOwl: Found 47 verses connecting Aaron with priestly duties:

Scripture References:
• KJV Exod.28.01 [H175]: "Take Aaron thy brother, and his sons..."
• WEB Exod.28.01 [H175]: "Take Aaron your brother, and his sons..."
• KJV Lev.08.12 [H175]: "And he poured of the anointing oil..."

Strong's Context:
• H175 (Aaron): אַהֲרֹן - Light bringer, brother of Moses, first High Priest
• Usage: 347 occurrences across 27 books

Related Topics: @priest, @tabernacle, @moses
[showing 5 of 47 results - type 'more' for additional results]
```

## Existing Codebase Integration

### Key Files to Reference/Use
- **Virtual Environment**: `/home/nigel/tinyowl/venv/` (must activate first)
- **ChromaDB Location**: `/home/nigel/tinyowl/vectordb/`
- **Retrieval Router**: `/home/nigel/tinyowl/scripts/retrieval_router.py` (proven query system)
- **OSIS Config**: `/home/nigel/tinyowl/configs/osis_canonical.yaml`
- **Strong's Data**: `/home/nigel/tinyowl/domains/theology/chunks/strongs_concordance_entries_chunks.json`

### Dependencies (Already Installed)
```python
chromadb==1.0.20
sentence-transformers==5.1.0
rich>=13.0.0
textual>=0.40.0
anthropic
fastapi  # (not needed for this build)
requests  # for Ollama integration
```

### Sample Query Code Pattern (Use This Approach)
```python
# Always activate venv first
import sys
sys.path.append('/home/nigel/tinyowl')

import chromadb
from scripts.retrieval_router import RetrievalRouter

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="/home/nigel/tinyowl/vectordb")

# Use existing retrieval system
router = RetrievalRouter(client)
results = router.query("aaron priest", query_type="concordance")
```

## Critical Implementation Notes

### 1. Virtual Environment Handling
**ALWAYS** ensure virtual environment is activated:
```bash
source /home/nigel/tinyowl/venv/bin/activate
```

### 2. Typeahead Performance
- Pre-load all Strong's concordance words on startup
- Build fast lookup index (word → occurrences count)
- Real-time filtering with fuzzy matching
- Keyboard navigation (↑↓ arrows, Enter to select)

### 3. Ollama Integration Strategy
```python
# Check if Ollama is available
def check_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

# Enhance response if AI available
def enhance_response(concordance_results, query):
    if check_ollama():
        # Send concordance data + query to Ollama
        # Return AI-enhanced response
    else:
        # Return pure concordance results
        return concordance_results
```

### 4. CLI Interface Requirements
- **Professional styling** with Rich panels and syntax highlighting
- **Persistent chat history** across sessions
- **Command history** (up/down arrows)
- **Tab completion** for commands
- **Status indicators** (AI available/unavailable, database stats)

### 5. Error Handling & Graceful Degradation
- If ChromaDB unavailable → Show helpful error
- If Ollama unavailable → Pure concordance mode
- If no results found → Suggest similar terms
- Handle malformed commands gracefully

## Success Criteria

### Must Work Perfectly
1. **`@aaron`** → Returns all 218 Aaron verses with proper formatting
2. **Typeahead system** → Real-time filtering as user types
3. **Command history** → Up/down arrows work like terminal
4. **Chat persistence** → Sessions saved/restored
5. **Rofi launch** → Clean desktop integration
6. **No-AI mode** → Full functionality without Ollama

### Should Work Well
1. **AI enhancement** → Better responses when Ollama available
2. **Cross-references** → Related terms suggested
3. **Export functionality** → Save conversations
4. **Performance** → Sub-second response times

## Development Approach
1. **Start with Pure CLI** → Build typeahead + concordance lookup first
2. **Add ChromaDB integration** → Use existing retrieval router
3. **Implement chat history** → SQLite persistence
4. **Add Ollama layer** → Optional AI enhancement
5. **Polish UI/UX** → Perfect the terminal aesthetic

## File Locations & Context
- **Project Root**: `/home/nigel/tinyowl/`
- **Build Directory**: `/home/nigel/tinyowl/chat-app/` (create this)
- **Existing Database**: `/home/nigel/tinyowl/vectordb/`
- **Virtual Environment**: `/home/nigel/tinyowl/venv/`

## Final Notes
- **Follow TinyOwl's systematic approach** - build systematically, test thoroughly
- **Leverage existing infrastructure** - don't rebuild what's working
- **CLI-first design** - keyboard-driven, professional terminal aesthetic
- **Graceful degradation** - works perfectly without AI, enhanced with AI
- **Rofi integration** - should launch cleanly from desktop

Build this as a professional, production-ready CLI application that showcases TinyOwl's theological research capabilities with modern terminal UX.