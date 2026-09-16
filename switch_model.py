#!/usr/bin/env python3
"""Safely switch Codex's user-level default model/provider on macOS.

The tool only edits the root-level `model`, `model_provider`, and
`model_catalog_json` keys in ~/.codex/config.toml. It does not edit auth files,
AGENTS, Skills, MCP configuration, repositories, or conversation history.
"""
from __future__ import annotations

import getpass
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from datetime import datetime

try:
    import tomllib
except ImportError:
    raise SystemExit("Python 3.11+ is required. No configuration was changed.")

OPENAI_MODEL = os.environ.get("CODEX_SWITCHER_OPENAI_MODEL", "gpt-6-astra")
KIMI_MODEL = os.environ.get("CODEX_SWITCHER_KIMI_MODEL", "k3-256k")
KIMI_PROVIDER = "kimi"
OPENAI_PROVIDER = "openai"
KIMI_BASE_URL = "https://api.kimi.com/coding/v1"
KIMI_ENV_KEY = "KIMI_API_KEY"


def patch_config(text: str, target: str, catalog: Path) -> str:
    """Edit only three root-level single-line keys and verify all else is unchanged."""
    before = tomllib.loads(text)
    changes = {
        "model": KIMI_MODEL if target == "kimi" else OPENAI_MODEL,
        "model_provider": KIMI_PROVIDER if target == "kimi" else OPENAI_PROVIDER,
        "model_catalog_json": str(catalog) if target == "kimi" else None,
    }

    first_table = re.search(r"(?m)^[ \t]*\[", text)
    boundary = first_table.start() if first_table else len(text)
    root, tables = text[:boundary], text[boundary:]
    newline = "\r\n" if "\r\n" in text else "\n"
    expected = dict(before)

    for key, value in changes.items():
        pattern = re.compile(
            rf"(?m)^[ \t]*(?:{key}|\"{key}\"|'{key}')[ \t]*=[^\r\n]*(?:\r?\n|$)"
        )
        matches = list(pattern.finditer(root))
        if len(matches) > 1 or (key in before and len(matches) != 1):
            raise ValueError(
                f"{key} is not a safely editable root-level single-line key; file unchanged."
            )

        replacement = (
            "" if value is None else f"{key} = {json.dumps(value, ensure_ascii=False)}{newline}"
        )
        if matches:
            root = pattern.sub(lambda _: replacement, root, count=1)
        elif value is not None:
            root = replacement + root

        if value is None:
            expected.pop(key, None)
        else:
            expected[key] = value

    candidate = root + tables
    if tomllib.loads(candidate) != expected:
        raise ValueError("Unexpected configuration changes detected; file unchanged.")
    return candidate


def validate_kimi(current: dict, catalog: Path) -> None:
    provider = current.get("model_providers", {}).get(KIMI_PROVIDER, {})
    required = {"base_url": KIMI_BASE_URL, "env_key": KIMI_ENV_KEY}
    if any(provider.get(k) != v for k, v in required.items()):
        raise ValueError("Kimi provider base_url/env_key does not match the expected direct setup.")
    if provider.get("wire_api", "responses") != "responses":
        raise ValueError("Kimi provider wire_api must be 'responses'.")
    if provider.get("requires_openai_auth", False):
        raise ValueError("Kimi provider must not require OpenAI authentication.")
    if "auth" in provider or "experimental_bearer_token" in provider:
        raise ValueError("Kimi provider has an additional auth setting; review it before switching.")

    try:
        models = json.loads(catalog.read_text(encoding="utf-8"))["models"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("Kimi models.json is missing or invalid.") from exc
    if not any(m.get("slug") == KIMI_MODEL for m in models):
        raise ValueError(f"models.json does not contain the selected Kimi model: {KIMI_MODEL}")


def resolve_kimi_key() -> str:
    key = os.environ.get(KIMI_ENV_KEY, "").strip()
    if not key:
        result = subprocess.run(
            ["/bin/launchctl", "getenv", KIMI_ENV_KEY], capture_output=True, text=True
        )
        key = result.stdout.strip() if result.returncode == 0 else ""
    if not key:
        key = getpass.getpass(
            "KIMI_API_KEY not found. Paste your Kimi Code key (hidden, not saved to file): "
        ).strip()
    if not key:
        raise ValueError("Kimi API key is empty; file unchanged.")
    return key


def main() -> None:
    if sys.platform != "darwin":
        raise SystemExit("This shortcut currently supports macOS only.")
    if len(sys.argv) != 2 or sys.argv[1] not in {"kimi", "openai"}:
        raise SystemExit("Usage: python3 switch_model.py kimi|openai")

    target = sys.argv[1]
    home = Path.home() / ".codex"
    configured_home = Path(os.environ.get("CODEX_HOME") or str(home)).expanduser()
    if configured_home.resolve() != home.resolve():
        raise SystemExit(
            "Non-default CODEX_HOME detected. Confirm the active config directory first; no changes made."
        )

    config = (home / "config.toml").resolve()
    catalog = home / "models.json"
    raw = config.read_bytes()
    text = raw.decode("utf-8")
    current = tomllib.loads(text)

    key: str | None = None
    if target == "kimi":
        validate_kimi(current, catalog)
        key = resolve_kimi_key()

    candidate = patch_config(text, target, catalog)
    label = f"Kimi ({KIMI_MODEL})" if target == "kimi" else f"OpenAI ({OPENAI_MODEL})"

    print(f"Target: {label}\nConfig: {config}")
    input(
        "Finish active tasks and quit Codex Desktop with Cmd+Q. "
        "Press Enter to continue, or Ctrl+C to cancel: "
    )

    if config.read_bytes() != raw:
        raise ValueError("config.toml changed while waiting; it was not overwritten.")

    if candidate != text:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = home / f"config.toml.before-switch-{stamp}"
        with os.fdopen(os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as f:
            f.write(raw)

        fd, temporary = tempfile.mkstemp(prefix=".config-switch-", dir=config.parent)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(candidate.encode("utf-8"))
                f.flush()
                os.fsync(f.fileno())
            os.chmod(temporary, stat.S_IMODE(config.stat().st_mode))
            os.replace(temporary, config)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        print(f"Saved. Backup: {backup}")
    else:
        print("Configuration already matches this target; no rewrite performed.")

    if key is not None:
        subprocess.run(["/bin/launchctl", "setenv", KIMI_ENV_KEY, key], check=True)
        print("Kimi key is available to the current macOS user session (key not displayed).")

    print(f"Switched default configuration to {label}.")
    print("Reopen Codex Desktop and start a new thread after switching providers.")
    print("This does not migrate existing threads or verify API connectivity.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)
    except Exception as exc:
        if isinstance(exc, (ValueError, FileNotFoundError)):
            print(f"Stopped: {exc}", file=sys.stderr)
        else:
            print(
                f"Operation did not complete ({type(exc).__name__}); do not treat it as a successful switch.",
                file=sys.stderr,
            )
        sys.exit(1)
