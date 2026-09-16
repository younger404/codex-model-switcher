# Codex Model Switcher

[English](README.md) | 简体中文

一个面向 macOS 的轻量工具，用于安全地在 OpenAI 与自定义 Kimi Provider 之间切换 Codex Desktop 的用户级默认模型。

它只解决一个明确的问题：保留同一套 Codex 工作区、AGENTS、Skills 和 MCP 配置，同时切换模型 Provider，而不必反复手动编辑 `~/.codex/config.toml`。

## 它会修改什么

仅修改 `~/.codex/config.toml` 中以下三个根级字段：

- `model`
- `model_provider`
- `model_catalog_json`

它**不会**修改 Codex 认证文件、AGENTS、Skills、MCP 配置、权限、仓库或历史会话。

写入前，工具会创建仅当前用户可读的备份，并验证解析后的 TOML 中除上述三个目标字段外没有其他值发生变化。

## 使用要求

- macOS
- Python 3.11+
- 已存在 Codex 配置文件：`~/.codex/config.toml`
- 使用 Kimi 时：已配置 `[model_providers.kimi]`，其中包含 `https://api.kimi.com/coding/v1`、`env_key = "KIMI_API_KEY"` 和 Responses API
- 使用 Kimi 时：`~/.codex/models.json` 中已包含要使用的 Kimi 模型

本工具不会替你创建 Provider 配置。首次使用某个 Provider 前，请先按照该 Provider 当前最新的官方 Codex 接入文档完成配置。

## 安装

```bash
git clone https://github.com/younger404/codex-model-switcher.git
cd codex-model-switcher
chmod u+x ./*.command
```

## 使用方法

1. 完成当前正在执行的 Codex 任务。
2. 使用 `Cmd+Q` 完全退出 Codex Desktop。
3. 双击以下任一文件：
   - `Switch-to-Kimi.command`
   - `Switch-to-OpenAI.command`
4. 重新打开 Codex Desktop。
5. 跨 Provider 切换后，请新建**新会话**。已有会话可能会保留创建时的 Provider / 认证上下文。

也可以直接运行 Python 入口：

```bash
python3 switch_model.py kimi
python3 switch_model.py openai
```

## 默认模型

- OpenAI：`gpt-6-astra`
- Kimi：`k3-256k`

无需修改脚本即可通过环境变量覆盖默认模型：

```bash
export CODEX_SWITCHER_OPENAI_MODEL="gpt-6-astra"
export CODEX_SWITCHER_KIMI_MODEL="k3"
```

所选择的 Kimi 模型必须已经存在于 `~/.codex/models.json` 中。

## API Key 处理

仓库中不包含任何 API Key。

使用 Kimi 时，脚本会先检查当前 shell 中的 `KIMI_API_KEY`，再检查当前 macOS `launchctl` 环境。如果两者都不存在，脚本会通过隐藏输入请求 Key，并只通过 `launchctl setenv` 将它暴露给当前 macOS 用户会话。

API Key 不会被打印，也不会由本工具写入仓库或 `config.toml`。

## 安全行为

出现以下情况时，工具会停止执行，而不是自行猜测：

- `CODEX_HOME` 指向默认 `~/.codex` 以外的位置
- Kimi Provider 与预期的直连配置不一致
- `models.json` 缺失、格式无效，或不包含所选 Kimi 模型
- 目标根级字段无法安全地作为单行 TOML 值修改
- 工具等待确认期间 `config.toml` 被其他进程修改
- 候选 TOML 修改了三个目标字段以外的任何配置

切换成功只代表本地配置已经更新。它**不代表** Provider API 一定可访问，也不代表已有会话可以在不同 Provider 之间直接迁移。

## Kimi 配置参考

Kimi 当前的 Codex 接入文档：

https://www.kimi.com/code/docs/third-party-tools/codex.html

## 项目范围

这个项目刻意保持小而明确。它不是通用 Provider 管理器、路由器、代理、凭据保险库，也不是会话迁移工具。

## 许可证

MIT
