#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${XDG_SESSION_TYPE:-}" != "x11" || -z "${DISPLAY:-}" ]]; then
  echo "Desktop AI currently requires an X11 session. Log into your Cinnamon X11 session and run this without sudo."
  exit 1
fi
sudo apt update
sudo apt install -y python3 python3-pip python3-tk xinput xclip libx11-6 libxi6 libxtst6
python3 -m pip install --user --break-system-packages -r requirements.txt
mkdir -p "$HOME/.config/desktop-ai"
if [[ ! -f "$HOME/.config/desktop-ai/env" ]]; then
  cat > "$HOME/.config/desktop-ai/env" <<'EOF'
# Paste your NVIDIA NIM API key below.
export NVIDIA_NIM_API_KEY=""
# Choose a vision-capable model available to your NVIDIA NIM account.
export NVIDIA_NIM_MODEL="nvidia/llama-3.2-90b-vision-instruct"
EOF
  chmod 600 "$HOME/.config/desktop-ai/env"
fi
cat > "$HOME/.local/bin/desktop-ai" <<EOF
#!/usr/bin/env bash
set -a
source "$HOME/.config/desktop-ai/env"
set +a
cd "$HOME/desktop-ai"
exec python3 app.py
EOF
mkdir -p "$HOME/.local/bin"
chmod +x "$HOME/.local/bin/desktop-ai"
echo
echo "Installed. Add ~/.local/bin to PATH if needed."
echo "Edit ~/.config/desktop-ai/env and add your NVIDIA NIM API key."
echo "Run: ~/desktop-ai/run.sh"
