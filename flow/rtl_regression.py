#!/usr/bin/env python3
"""RTL regression = rerun the top testbench (rtl sim) and write tool-top-regression-v<K>.json. Run by the HDL engineer after its edits (rtl on PATH).
The official test is run by the orchestrator only when the testbench passes (flow/official_test.sh).
usage: rtl_regression.py EXCHANGE_DIR ROUND"""
import json, re, subprocess, sys, time
ex, K = sys.argv[1], int(sys.argv[2])
t = subprocess.run(['rtl', 'sim'], capture_output=True, text=True); text = t.stdout + t.stderr
m = re.search(r'result: (\w+) \((\d+) FAIL, (\d+) PASS\)', text)
exp = re.findall(r'Expected output: ([0-9a-fx]+)', text); obs = re.findall(r'Observed output: ([0-9a-fx]+)', text)
r = {"from": "tool", "to": "arch", "round": K, "block": "top", "time": time.strftime('%Y-%m-%d %H:%M:%S'),
     "testbench": {"result": m.group(1) if m else "unknown", "fail": int(m.group(2)) if m else None, "pass": int(m.group(3)) if m else None, "expected": exp[:1], "observed": obs[:2]},
     "official_harness": {"result": "not_run", "detail": "run only when the testbench passes (orchestrator)"}, "design_changes_since_previous": []}
json.dump(r, open(f'{ex}/tool-top-regression-v{K}.json', 'w'), indent=1)
print(f"testbench: {r['testbench']['result']}  ({r['testbench']['fail']} FAIL, {r['testbench']['pass']} PASS)  observed {r['testbench']['observed'][:1]} expected {r['testbench']['expected'][:1]}")
