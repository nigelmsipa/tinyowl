#!/bin/bash

# TinyOwl Chat Launcher
# Activates virtual environment and starts the chat interface

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# TinyOwl ASCII art
echo -e "${BLUE}"
echo "    🦉"
echo "   /___\\"
echo "  (  o o  )"
echo "   \\  <  /"
echo "    \\___/"
echo -e "${NC}"

echo -e "${BLUE}TinyOwl Chat Launcher${NC}"
echo "========================"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Determine entrypoint
ENTRY="chat_interface.py"
if [ ! -f "$SCRIPT_DIR/$ENTRY" ]; then
    echo -e "${YELLOW}Note: $ENTRY not found; falling back to scripts/chat.py${NC}"
    ENTRY="scripts/chat.py"
fi

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not found at $SCRIPT_DIR/venv${NC}"
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    
    echo "Installing dependencies..."
    source "$SCRIPT_DIR/venv/bin/activate"
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# If using local chat_interface.py, we might rely on Ollama; for scripts/chat.py we skip this check
if [ "$ENTRY" = "chat_interface.py" ]; then
  echo -e "${BLUE}Checking Ollama status...${NC}"
  if ! curl -s http://localhost:11434/api/tags > /dev/null; then
      echo -e "${RED}Error: Ollama is not running${NC}"
      echo "Please start Ollama first:"
      echo "  ollama serve"
      echo ""
      echo "Then make sure you have some models installed:"
      echo "  ollama pull qwen2.5-coder:3b"
      echo "  ollama pull mistral:latest"
      exit 1
  fi
  echo -e "${GREEN}✓ Ollama is running${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$SCRIPT_DIR/venv/bin/activate"

# Load API keys from bashrc
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# Explicitly export API keys if found in bashrc
GROQ_KEY=$(grep "GROQ_API_KEY" ~/.bashrc | cut -d'"' -f2)
if [ ! -z "$GROQ_KEY" ]; then
    export GROQ_API_KEY="$GROQ_KEY"
    echo -e "${GREEN}✓ Groq API key loaded${NC}"
fi

OPENAI_KEY=$(grep "OPENAI_API_KEY" ~/.bashrc | tail -1 | cut -d'"' -f2)
if [ ! -z "$OPENAI_KEY" ]; then
    export OPENAI_API_KEY="$OPENAI_KEY"
    echo -e "${GREEN}✓ OpenAI API key loaded (length: ${#OPENAI_API_KEY})${NC}"
else
    echo -e "${YELLOW}Warning: OPENAI_API_KEY not found in environment${NC}"
    echo "Set it in your shell profile or export before launching if needed."
fi

# Check if ChromaDB exists
if [ ! -d "$SCRIPT_DIR/vectordb" ]; then
    echo -e "${RED}Error: Vector database not found${NC}"
    echo "Run the ingestion script first to create the database"
    exit 1
fi

echo -e "${GREEN}✓ Vector database found${NC}"
echo -e "${GREEN}✓ Starting TinyOwl Chat...${NC}"
echo ""

# Launch
cd "$SCRIPT_DIR"
python "$ENTRY"
