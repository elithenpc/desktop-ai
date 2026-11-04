#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
set -a
[[ -f "$HOME/.config/desktop-ai/env" ]] && source "$HOME/.config/desktop-ai/env"
set +a
exec python3 app.py
