#!/usr/bin/env bash
# TinyOwl Chat Launcher for Rofi Integration
set -euo pipefail

# TinyOwl directory
TINYOWL_DIR="/home/nigel/tinyowl"
VENV_PATH="$TINYOWL_DIR/venv"

# Check if virtual environment exists
if [[ ! -d "$VENV_PATH" ]]; then
    notify-send "TinyOwl Error" "Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Launch TinyOwl Chat in a new terminal window
exec kitty --title="TinyOwl Chat" --working-directory="$TINYOWL_DIR" bash -c "
    source '$VENV_PATH/bin/activate' &&
    echo 'Welcome to TinyOwl Chat - Professional Biblical Research Tool' &&
    echo 'Commands: @aaron (concordance), @strong:175 (Strong'\''s), &john3:16 (verses), #prophecy (topical), /ai status|models|model <name>|on|off|toggle' &&
    echo '' &&
    python -m chat_app.main
"
