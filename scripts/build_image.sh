#!/bin/bash
# Build the agent image of the walk5 environment from this checkout (tool, skills, resources, agent wrapper).
# usage: scripts/build_image.sh [IMAGE_TAG]    default: multi-ai/cvdp-qwen-agent:0.26.0-v4-ports
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:-multi-ai/cvdp-qwen-agent:0.26.0-v4-ports}"
BASE=multi-ai/cvdp-qwen-agent:0.25.0
SIM=multi-ai/cvdp-sim:8e894cf-arm64
if ! docker image inspect "$SIM" >/dev/null 2>&1; then
  echo "Missing grader/simulator image $SIM (iverilog 13, verilator, yosys, cocotb). Build it once (long, needs network):"
  echo "  docker build -f $HERE/tools/agentic/Dockerfile.sim -t $SIM $HERE/tools/agentic"; exit 2
fi
if ! docker image inspect "$BASE" >/dev/null 2>&1; then
  echo "Base image $BASE missing: building it from tools/agentic/Dockerfile.qwen (needs network for Node and Qwen Code 0.25.0)"
  CTX=$(mktemp -d); cp "$HERE/tools/agentic/agent_qwen.py" "$CTX/"
  docker build -f "$HERE/tools/agentic/Dockerfile.qwen" -t "$BASE" "$CTX"; rm -rf "$CTX"
fi
CTX=$(mktemp -d)
cp "$HERE/tools/rtl/rtl" "$CTX/rtl"; cp "$HERE/tools/agentic/agent_qwen.py" "$CTX/"
cp -R "$HERE/image_skills" "$CTX/skills"; cp -R "$HERE/pilot_tools" "$CTX/pilot_tools"; cp -R "$HERE/resources" "$CTX/resources"
docker build -f "$HERE/tools/agentic/Dockerfile.qwen-rtl" -t "$TAG" "$CTX"
rm -rf "$CTX"; echo "built $TAG"
