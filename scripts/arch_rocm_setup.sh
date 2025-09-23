#!/usr/bin/env bash
# Arch Linux AMD ROCm setup for TinyOwl (RX 6600 Navi 23 / gfx1031)
# - Installs ROCm runtime + PyTorch (ROCm)
# - Sets HSA override for Navi 23
# - Prepares TinyOwl venv configured to use GPU

set -euo pipefail

YES=0
MODE="aur"   # aur | pip
VENV=".venv"
GPU_GFX_OVERRIDE="10.3.0"   # Navi 23 (RX 6600/6600XT) = gfx1031

usage() {
  cat <<EOF
Usage: $0 [--yes] [--mode aur|pip] [--venv .venv]

Modes:
  aur  (default) Install ROCm + python-pytorch-rocm via AUR helper (yay/paru)
  pip  Install ROCm PyTorch wheel in the TinyOwl venv directly

Examples:
  $0 --yes --mode aur
  $0 --mode pip --venv .venv
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes) YES=1; shift;;
    --mode) MODE="$2"; shift 2;;
    --venv) VENV="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

run_or_exit() {
  echo "+ $*"
  eval "$@"
}

confirm() {
  if [[ $YES -eq 1 ]]; then return 0; fi
  read -rp "$* [y/N]: " ans
  [[ "$ans" == "y" || "$ans" == "Y" ]]
}

# Ensure we're in repo root
cd "$(dirname "$0")/.."

echo "==> Detecting GPU"
lspci | grep -E 'VGA|3D' || true
echo "==> This script targets AMD (ROCm) on Arch for RX 6600 (Navi 23)."

echo "==> Ensuring HSA override for Navi 23 (gfx1031)"
EXPORT_LINE="export HSA_OVERRIDE_GFX_VERSION=${GPU_GFX_OVERRIDE}"
if ! grep -qs "HSA_OVERRIDE_GFX_VERSION" "$HOME/.bashrc" "$HOME/.zshrc" 2>/dev/null; then
  if confirm "Append HSA override to your shell rc? (${EXPORT_LINE})"; then
    if [[ -f "$HOME/.zshrc" ]]; then echo "$EXPORT_LINE" >> "$HOME/.zshrc"; fi
    if [[ -f "$HOME/.bashrc" ]]; then echo "$EXPORT_LINE" >> "$HOME/.bashrc"; else echo "$EXPORT_LINE" >> "$HOME/.bashrc"; fi
    echo "Appended to shell rc. Restart your shell or 'source ~/.bashrc'."
  else
    echo "Skipping rc modification. You must export it before running GPU jobs:"
    echo "  $EXPORT_LINE"
  fi
else
  echo "HSA override already present in your shell rc."
fi

echo "==> Installing ROCm toolchain packages"
HELPER=""
if command -v yay >/dev/null 2>&1; then HELPER="yay"; fi
if [[ -z "$HELPER" ]] && command -v paru >/dev/null 2>&1; then HELPER="paru"; fi
if [[ -z "$HELPER" ]]; then
  echo "No AUR helper (yay/paru) found. Install one, or run in --mode pip."
  if [[ "$MODE" == "aur" ]]; then exit 1; fi
fi

if [[ "$MODE" == "aur" ]]; then
  echo "==> Using AUR helper: $HELPER"
  run_or_exit "$HELPER -S --needed rocminfo rocm-smi-lib rocm-hip-runtime hip-runtime-amd rocm-opencl-runtime"
  echo "==> Installing PyTorch ROCm via AUR"
  run_or_exit "$HELPER -S --needed python-pytorch-rocm"
fi

echo "==> Creating TinyOwl venv: $VENV"
if [[ -d "$VENV" ]]; then echo "(venv exists)"; else python -m venv "$VENV"; fi
source "$VENV/bin/activate"

if [[ "$MODE" == "pip" ]]; then
  echo "==> Installing PyTorch (ROCm) wheels via pip"
  # Adjust rocm version if needed (e.g., rocm5.7, rocm6.0, rocm6.1)
  run_or_exit "pip install --upgrade pip"
  run_or_exit "pip install --index-url https://download.pytorch.org/whl/rocm6.0 torch torchvision torchaudio"
fi

echo "==> Installing TinyOwl Python requirements"
run_or_exit "pip install -r tinyowl/requirements.txt"

echo "==> Verifying ROCm + PyTorch"
python - <<'PY'
import torch
print('cuda_available:', torch.cuda.is_available())
print('hip_version:', getattr(torch.version, 'hip', None))
if torch.cuda.is_available():
    try:
        print('torch_device:', torch.cuda.get_device_name(0))
    except Exception:
        pass
PY

echo "==> Quick HIP matmul test (GPU)"
python - <<'PY'
import torch
if not torch.cuda.is_available():
    print('GPU not available in torch. Check ROCm install or venv torch build.')
    raise SystemExit(0)
x = torch.rand((2048,2048), device='cuda')
y = torch.rand((2048,2048), device='cuda')
z = x @ y
print('ok, mean:', float(z.mean().item()))
PY

echo "==> TinyOwl GPU status command in chat: /gpu"
echo "==> To run embeddings on GPU:"
echo "    source $VENV/bin/activate"
echo "    python tinyowl/scripts/generate_strongs_embeddings.py --device auto --embed-batch-size 512"
echo "==> Done."

