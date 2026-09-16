# Codex Model Switcher

A minimal macOS utility for safely switching Codex Desktop's user-level default between OpenAI and a custom Kimi provider.

It was built for one narrow problem: keep one Codex workspace, AGENTS, Skills and MCP setup, while changing the model provider without repeatedly hand-editing `~/.codex/config.toml`.

## What it changes

Only these root-level keys in `~/.codex/config.toml`:

- `model`
- `model_provider`
- `model_catalog_json`

It does **not** edit Codex auth files, AGENTS, Skills, MCP configuration, permissions, repositories, or conversation history.

Before writing, it creates an owner-only backup and verifies that no other parsed TOML values changed.

## Requirements

- macOS
- Python 3.11+
- An existing Codex configuration at `~/.codex/config.toml`
- For Kimi: an existing `[model_providers.kimi]` provider configured for `https://api.kimi.com/coding/v1`, `env_key = "KIMI_API_KEY"`, and Responses API
- For Kimi: `~/.codex/models.json` containing the selected Kimi model

The tool does not create provider configuration for you. Follow the provider's current official Codex integration guide first.

## Install

```bash
git clone https://github.com/younger404/codex-model-switcher.git
cd codex-model-switcher
chmod u+x ./*.command
```

## Use

1. Finish any active Codex task.
2. Quit Codex Desktop with `Cmd+Q`.
3. Double-click one of:
   - `Switch-to-Kimi.command`
   - `Switch-to-OpenAI.command`
4. Reopen Codex Desktop.
5. When switching providers, start a **new thread**. Existing threads can retain provider/auth context from when they were created.

You can also run the Python entry point directly:

```bash
python3 switch_model.py kimi
python3 switch_model.py openai
```

## Defaults

- OpenAI model: `gpt-6-astra`
- Kimi model: `k3-256k`

Override either default without editing the script:

```bash
export CODEX_SWITCHER_OPENAI_MODEL="gpt-6-astra"
export CODEX_SWITCHER_KIMI_MODEL="k3"
```

The selected Kimi model must exist in your `~/.codex/models.json`.

## API key handling

The repository contains no API keys.

For Kimi, the script checks `KIMI_API_KEY` in the current shell, then the current macOS `launchctl` environment. If neither exists, it prompts with hidden input and exposes the value only to the current macOS user session via `launchctl setenv`.

The key is not printed and is not written to this repository or to `config.toml` by the switcher.

## Safety behavior

The switcher stops instead of guessing when:

- `CODEX_HOME` points somewhere other than the default `~/.codex`
- the Kimi provider does not match the expected direct provider settings
- `models.json` is missing/invalid or lacks the selected Kimi model
- a target root key cannot be safely edited as a single-line TOML value
- `config.toml` changes while the tool is waiting for confirmation
- the candidate TOML changes anything outside the three intended root keys

A successful switch means the local configuration was updated. It does **not** prove that a provider API is reachable or that an existing thread can migrate across providers.

## Kimi setup reference

Kimi's current Codex integration documentation:

https://www.kimi.com/code/docs/third-party-tools/codex.html

## Scope

This is intentionally small. It is not a general provider manager, router, proxy, credential vault, or session migration tool.

## License

MIT
