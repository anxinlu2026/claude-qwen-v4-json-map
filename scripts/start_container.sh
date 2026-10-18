#!/bin/bash
# 為一個 cell 啟動容器 orders_<TAG>，掛載其 RTL 工作區與狀態。用法: scripts/start_container.sh CELL_DIR [exchange|strict]
# exchange（預設）：檔案交換流程，每次修改後有單元 harness 與回歸守護，關卡只要求「修改後有過一次比對」；strict：原本的一次只改一處關卡。
D="$(cd "$(dirname "$0")/.." && pwd)"; E=$1; MODE=${2:-exchange}; TAG=$(basename "$E" | sed 's/.*-qc-\(.*\)-[0-9]*$/\1/'); W=$(ls -d "$E"/work/*/harness/5)
FM=""; [ "$MODE" = exchange ] && FM=exchange
docker rm -f orders_$TAG >/dev/null 2>&1
docker run -d --name orders_$TAG --entrypoint sleep -e RTL_FLOW_MODE=$FM -v "$W/rtl":/code/rtl -v "$W/verif":/code/verif -v "$W/docs":/code/docs -v "$W/rundir":/code/rundir -v "$E/state":/tmp -w /code multi-ai/cvdp-qwen-agent:0.26.0-v4-ports infinity >/dev/null && echo "orders_$TAG ($MODE)"
