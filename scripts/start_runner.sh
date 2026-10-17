#!/bin/bash
# 啟動(或重啟)一個 cell 的 runner。用法: scripts/start_runner.sh RUNDIR [單張工單上限秒數(預設900)] [思考強度(預設none)]
D="$(cd "$(dirname "$0")/.." && pwd)"; RUN=$1; T=${2:-900}; EFF=${3:-none}; S=$((T*87/100))
pkill -f "resume.*$(basename $RUN)" 2>/dev/null; sleep 1
cd $D; nohup python3 tools/agentic/run_orders.py qwen8-qc --resume $RUN --image multi-ai/cvdp-qwen-agent:0.26.0-v4-ports --kickoff $D/kickoff/hdl_debug_agent_v18.txt --order-timeout $T --order-soft $S --temperature 0.6 --presence-penalty 0.5 --frequency-penalty 0.5 --repeat-penalty 1.1 --reasoning-effort $EFF --loop-limit 1 > /tmp/runner_$(basename $RUN).out 2>&1 &
sleep 8; tail -1 $RUN/console.log | cut -c1-120
