#!/usr/bin/env bash
# TinyOwl Chat Launcher for Rofi Integration (GPU-Enabled by Default)
set -euo pipefail

# Enable HIP kernels on Navi 23 (gfx1031) - AMD RX 6600 GPU acceleration
export HSA_OVERRIDE_GFX_VERSION=${HSA_OVERRIDE_GFX_VERSION:-10.3.0}

# TinyOwl directory
TINYOWL_DIR="/home/nigel/tinyowl"

# Prefer local venvs; fall back to a common path if present
VENV_PATH=""
for cand in \
  "$TINYOWL_DIR/.venv311" \
  "$TINYOWL_DIR/.venv" \
  "$TINYOWL_DIR/venv" \
  "$HOME/tinyowl/venv"
do
  if [[ -d "$cand" ]]; then VENV_PATH="$cand"; break; fi
done

if [[ -z "$VENV_PATH" ]]; then
  echo "No Python venv found (.venv311/.venv/venv). Create one or run the ROCm setup script:"
  echo "  bash tinyowl/scripts/arch_rocm_setup.sh --mode aur --yes"
  exit 1
fi

# Optional: nudge Ollama to use GPU if available
export TINYOWL_OLLAMA_NUM_GPU=${TINYOWL_OLLAMA_NUM_GPU:-1}

# Launch TinyOwl Chat in a new terminal window with GPU acceleration
if command -v kitty >/dev/null 2>&1; then
  exec kitty --title="TinyOwl Chat (GPU)" --working-directory="$TINYOWL_DIR" bash -c "
    source '$VENV_PATH/bin/activate' &&
    echo 'Welcome to TinyOwl Chat - GPU-Accelerated Biblical Research Tool' &&
    echo 'GPU: AMD RX 6600 | ROCm: Enabled | Models: 9 available via Ollama' &&
    echo 'Commands: @aaron, @strong:175, &john3:16, #prophecy, /help' &&
    echo '' &&
    python -m chat_app.main
  "
else
  # Fallback for systems without kitty
  cd "$TINYOWL_DIR"
  source "$VENV_PATH/bin/activate"
  echo 'Welcome to TinyOwl Chat - GPU-Accelerated Biblical Research Tool'
  echo 'GPU: AMD RX 6600 | ROCm: Enabled | Models: 9 available via Ollama'
  echo 'Commands: @aaron, @strong:175, &john3:16, #prophecy, /help'
  echo ''
  exec python -m chat_app.main
fi
