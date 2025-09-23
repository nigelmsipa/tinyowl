#!/usr/bin/env bash
# TinyOwl Rofi Integration Script
# Bind this to a keyboard shortcut (e.g., Super+T) for quick access

# Check if TinyOwl is already running
if pgrep -f "chat_app.main" > /dev/null; then
    # Focus existing TinyOwl window if running
    wmctrl -a "TinyOwl Chat" 2>/dev/null || true
else
    # Launch new TinyOwl instance
    exec /home/nigel/tinyowl/launch_tinyowl_chat.sh
fi