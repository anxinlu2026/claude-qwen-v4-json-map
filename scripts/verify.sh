#!/bin/bash
# Simple verification of a fresh checkout: image content, simulator on the original and on the reference solution,
# the official grader on both, and the work-order runner (start and close, no model is called).
# usage: scripts/verify.sh [IMAGE_TAG]
HERE="$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:-multi-ai/cvdp-qwen-agent:0.26.0-v4-ports}"
SIM=multi-ai/cvdp-sim:8e894cf-arm64
W="$HERE/seed_run/work/cvdp_agentic_AES_encryption_decryption/harness/5"
"$HERE/scripts/prepare_seed.sh"
TMP=$(mktemp -d); fail=0
ok(){ echo "PASS  $1"; }; bad(){ echo "FAIL  $1"; fail=1; }
sha(){ shasum -a 256 "$1" | cut -c1-64; }
tree(){ (cd "$1" && find . -type f | sort | xargs shasum -a 256 | shasum -a 256 | cut -c1-64); }

# 1. image content equals the files of this checkout
read -r h1 h2 h3 h4 < <(docker run --rm --entrypoint sh "$TAG" -c 'a=$(sha256sum /usr/local/bin/rtl|cut -c1-64); b=$(sha256sum /app/agent_qwen.py|cut -c1-64); c=$(cd /opt/skills && find . -type f|sort|xargs sha256sum|sha256sum|cut -c1-64); d=$(cd /opt/resources && find . -type f|sort|xargs sha256sum|sha256sum|cut -c1-64); echo $a $b $c $d')
[ "$h1" = "$(sha "$HERE/tools/rtl/rtl")" ] && ok "image tool rtl = checkout" || bad "image tool rtl differs"
[ "$h2" = "$(sha "$HERE/tools/agentic/agent_qwen.py")" ] && ok "image agent wrapper = checkout" || bad "agent wrapper differs"
[ "$h3" = "$(tree "$HERE/image_skills")" ] && ok "image skills = checkout (image_skills/)" || bad "image skills differ"
# the runner reads the skill text of every order type from skills/ on the host
miss=$(python3 - "$HERE" <<'PY'
import re,sys,os
h=sys.argv[1]; t=open(h+"/tools/agentic/run_orders.py").read()
names=set(re.findall(r"': '([a-z-]+)'",t[t.index("types = {"):t.index("skill = ''")]))|{"uncertainty"}
print(" ".join(n for n in sorted(names) if not os.path.exists(f"{h}/skills/{n}/SKILL.md")))
PY
)
[ -z "$miss" ] && ok "runner skills present on the host (skills/)" || bad "runner skills missing: $miss"
[ "$h4" = "$(tree "$HERE/resources")" ] && ok "image resources = checkout" || bad "image resources differ"
docker run --rm --entrypoint sh "$TAG" -c 'command -v iverilog verilator yosys qwen >/dev/null' && ok "iverilog, verilator, yosys, qwen present" || bad "tools missing in image"

# 2. rtl sim in the image: original design must FAIL (2 FAIL), reference solution must PASS (2 PASS)
for case in original reference; do
  D="$TMP/$case"; mkdir -p "$D"/{rtl,verif,docs,rundir,state}; chmod -R 777 "$D"
  cp "$W"/before/verif/* "$D/verif/"; cp -R "$W"/before/docs/. "$D/docs/" 2>/dev/null
  if [ $case = original ]; then cp "$W"/before/rtl/* "$D/rtl/"; else cp "$HERE"/reference_solution/*.sv "$D/rtl/"; fi
  out=$(docker run --rm -e RTL_NO_GATES=1 -v "$D/rtl":/code/rtl -v "$D/verif":/code/verif -v "$D/docs":/code/docs -v "$D/rundir":/code/rundir -v "$D/state":/tmp -w /code --entrypoint sh "$TAG" -c 'rtl sim 2>&1' )
  if [ $case = original ]; then echo "$out" | grep -q "FAIL" && ok "rtl sim, original design fails as expected" || { bad "rtl sim, original design"; echo "$out" | head -5; }
  else echo "$out" | grep -q "0 FAIL, 2 PASS" && ok "rtl sim, reference solution 0 FAIL, 2 PASS" || { bad "rtl sim, reference solution"; echo "$out" | head -5; }; fi
done

# 3. official grader (cocotb test of the problem) on both
for case in original reference; do
  G="$TMP/g_$case"; mkdir -p "$G/rtl" "$G/rundir"; cp -R "$W/src" "$G/src"; rm -rf "$G/src/__pycache__"; cp -R "$W/before/verif" "$G/verif"; cp -R "$W/before/docs" "$G/docs"
  if [ $case = original ]; then cp "$W"/before/rtl/* "$G/rtl/"; else cp "$HERE"/reference_solution/*.sv "$G/rtl/"; fi
  chmod -R 777 "$G"
  res=$(docker run --rm -e "VERILOG_SOURCES=/code/rtl/aes128_decrypt.sv /code/rtl/aes128_key_expansion.sv /code/rtl/sbox.sv /code/rtl/inv_sbox.sv" -e TOPLEVEL=aes128_decrypt -e MODULE=test_aes128_decrypt -e SIM=icarus -e TOPLEVEL_LANG=verilog -e PYTHONPATH=/src -e HASH=5-debug-and-fix-aes128_decrypt -e WAVE=true -v "$G/src":/src -v "$G/rtl":/code/rtl -v "$G/verif":/code/verif -v "$G/docs":/code/docs -v "$G/rundir":/code/rundir -w /code/rundir "$SIM" pytest /src/test_runner.py -o cache_dir=/code/rundir/.cache 2>&1 | tail -3)
  if [ $case = original ]; then echo "$res" | grep -q "failed" && ok "official grader fails the original design" || { bad "official grader, original"; echo "$res"; }
  else echo "$res" | grep -q "1 passed" && ok "official grader passes the reference solution" || { bad "official grader, reference"; echo "$res"; }; fi
done

# 4. runner: create a run, check the container and the mounts, close it (no case file, so no model is called)
RUNS="$HERE/runs"; python3 "$HERE/tools/agentic/run_orders.py" qwen8-qc --from-run "$HERE/seed_run" --tag snapcheck --image "$TAG" --kickoff "$HERE/kickoff/hdl_debug_agent_v18.txt" --order-timeout 480 --order-soft 360 --reasoning-effort none --loop-limit 1 > "$TMP/runner.out" 2>&1 &
RP=$!; run=""
for i in $(seq 1 30); do sleep 2; run=$(ls -d "$RUNS"/orders-*snapcheck* 2>/dev/null | head -1); [ -n "$run" ] && docker ps --format '{{.Names}}' | grep -q '^orders_snapcheck$' && break; done
if docker ps --format '{{.Names}}' | grep -q '^orders_snapcheck$'; then ok "runner created run and container orders_snapcheck"; \
   docker exec orders_snapcheck sh -c 'test -x /usr/local/bin/rtl && test -d /opt/skills && ls /code/rtl | grep -q aes128_decrypt' && ok "container has the tool, skills and the original design" || bad "container content"
else bad "runner did not start a container"; sed -n 1,15p "$TMP/runner.out"; fi
kill $RP 2>/dev/null; python3 "$HERE/tools/agentic/run_orders.py" qwen8-qc --close "$run" >/dev/null 2>&1; docker rm -f orders_snapcheck >/dev/null 2>&1
[ -n "$run" ] && rm -rf "$run"
rm -rf "$TMP"; [ $fail = 0 ] && echo "ALL CHECKS PASSED" || echo "SOME CHECKS FAILED"; exit $fail
