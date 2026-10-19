#!/usr/bin/env python3
"""Smoke test of the permission rules with the local model: what must succeed and what must be refused. usage: test_permissions.py CELL_DIR OUTDIR (starts the model run in the background; read OUTDIR/out.json)"""
import os, subprocess, sys
cell, T = os.path.abspath(sys.argv[1]), sys.argv[2]; here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.normpath(os.path.join(here, '..')); ex = cell + '/exchange'
sys.path.insert(0, here); import cc_permissions
prompt = f"""權限煙霧測試。請依序執行，每一步回報「成功」或「被拒絕」，被拒絕不要換方法：
1) Bash：export PATH={cell}/hdl_bin:$PATH; rtl status
2) Read：{ex}/README_HDL.md 的第一行
3) Read：{cell}/runlog.md 的第一行
4) Read：{repo}/results/v5a_round1/REVIEW_SUMMARY.zh.md 的第一行
5) Bash：ls {repo}/results
6) Write：在 {ex}/smoke_perm.txt 寫入 ok
7) Bash：python3 {repo}/flow/validate_json.py {ex}
8) Bash：head -3 {cell}/state/rtlwork/state.json
9) Bash：cat {ex}/README_HDL.md | head -2
10) Bash：ls -la {ex}"""
m = 'qwen3.8:27b-mxfp8-v3-ctx262144'
env = dict(os.environ, PATH=cell + '/hdl_bin:' + os.environ['PATH'], FLOW_ACTOR='hdl', CLAUDE_CONFIG_DIR=T + '/cfg', ANTHROPIC_BASE_URL='http://127.0.0.1:11435', ANTHROPIC_AUTH_TOKEN='ollama', ANTHROPIC_API_KEY='',
           ANTHROPIC_MODEL=m, ANTHROPIC_DEFAULT_OPUS_MODEL=m, ANTHROPIC_DEFAULT_SONNET_MODEL=m, ANTHROPIC_DEFAULT_HAIKU_MODEL=m, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
p = subprocess.Popen(['claude', '-p', prompt, '--output-format', 'json', '--max-turns', '20', '--permission-mode', 'dontAsk', '--allowedTools'] + cc_permissions.allowed(cell, repo),
                     cwd=ex, env=env, stdout=open(T + '/out.json', 'w'), stderr=open(T + '/err.txt', 'w'), stdin=subprocess.DEVNULL)
open(T + '/pid', 'w').write(str(p.pid)); print('started', p.pid)
