#!/usr/bin/env bash
# Launch TinyOwl Chat with AMD ROCm GPU enabled (Arch Linux, RX 6600 / Navi 23)
set -euo pipefail

# Enable HIP kernels on Navi 23 (gfx1031)
export HSA_OVERRIDE_GFX_VERSION=${HSA_OVERRIDE_GFX_VERSION:-10.3.0}

# Prefer local venvs; fall back to a common path if present
VENV_PATH=""
for cand in \
  ".venv311" \
  ".venv" \
  "venv" \
  "$HOME/tinyowl/venv"
do
  if [[ -d "$cand" ]]; then VENV_PATH="$cand"; break; fi
done

if [[ -z "$VENV_PATH" ]]; then
  echo "No Python venv found (.venv/venv). Create one or run the ROCm setup script:"
  echo "  bash tinyowl/scripts/arch_rocm_setup.sh --mode aur --yes"
  exit 1
fi

source "$VENV_PATH/bin/activate"

# Optional: nudge Ollama to use GPU if available
export TINYOWL_OLLAMA_NUM_GPU=${TINYOWL_OLLAMA_NUM_GPU:-1}

# Run in kitty if available for a nice titled window, else in current terminal
if command -v kitty >/dev/null 2>&1; then
  exec kitty --title="TinyOwl Chat (GPU)" --working-directory="$(pwd)" bash -lc "python -m chat_app.main"
else
  exec python -m chat_app.main
fi
