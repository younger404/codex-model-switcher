#!/bin/zsh
HERE="$(cd -- "$(dirname -- "$0")" && pwd)" || exit 1
/bin/zsh -ilc 'python3 "$1" "$2"' codex-model-switch "$HERE/switch_model.py" openai
rc=$?
printf '\nPress Enter to close.'
read -r reply
exit "$rc"
