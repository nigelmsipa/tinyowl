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

# Check if we're in the right directory
if [ ! -f "$SCRIPT_DIR/chat_interface.py" ]; then
    echo -e "${RED}Error: chat_interface.py not found in $SCRIPT_DIR${NC}"
    echo "Make sure you're running this from the tinyowl directory"
    exit 1
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

# Check if Ollama is running
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
    # Hardcode as fallback since bashrc parsing is failing
    export OPENAI_API_KEY="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"
    echo -e "${GREEN}✓ OpenAI API key set directly${NC}"
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

# Launch the chat interface
cd "$SCRIPT_DIR"
python chat_interface.py