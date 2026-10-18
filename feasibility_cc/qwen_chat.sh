#!/bin/bash
# 直接與 Qwen 對話(不經雲端 Claude 模型):Claude Code 介面,後端是本機 Ollama 的 Qwen。
# 用法:
#   ./qwen_chat.sh            新的互動 session
#   ./qwen_chat.sh resume     接續最近一個 session(可挑選)
#   ./qwen_chat.sh SESSION_ID 接續指定 session(例如測試 session dcb6fc3f-214a-4e91-8c28-86c4215a8654)
# Qwen 可用的工具:rtl(容器 orders_v4e 內)與 dsh "指令"(在容器內執行 shell)。容器需在執行中:docker start orders_v4e
HERE="$(cd "$(dirname "$0")" && pwd)"
docker start orders_v4e >/dev/null 2>&1
export PATH="$HERE/bin:$PATH" CLAUDE_CONFIG_DIR="$HERE/cfg" \
  ANTHROPIC_BASE_URL=http://localhost:11434 ANTHROPIC_AUTH_TOKEN=ollama ANTHROPIC_API_KEY= \
  ANTHROPIC_MODEL=qwen3.8:27b-mxfp8 ANTHROPIC_DEFAULT_OPUS_MODEL=qwen3.8:27b-mxfp8 \
  ANTHROPIC_DEFAULT_SONNET_MODEL=qwen3.8:27b-mxfp8 ANTHROPIC_DEFAULT_HAIKU_MODEL=qwen3.8:27b-mxfp8 \
  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
cd "$HERE"
case "$1" in
  "") exec claude --model qwen3.8:27b-mxfp8 --allowedTools "Bash(rtl:*)" "Bash(dsh:*)" ;;
  resume) exec claude --resume --model qwen3.8:27b-mxfp8 --allowedTools "Bash(rtl:*)" "Bash(dsh:*)" ;;
  *) exec claude --resume "$1" --model qwen3.8:27b-mxfp8 --allowedTools "Bash(rtl:*)" "Bash(dsh:*)" ;;
esac
