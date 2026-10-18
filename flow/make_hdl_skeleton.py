#!/usr/bin/env python3
"""HDL-side skeleton for every block: hdl-blk<N>-rtl-v<K>.json with the architecture's port names and connections (no attribute values) and TODO slots.
usage: make_hdl_skeleton.py EXCHANGE_DIR OUTDIR [ROUND]"""
import glob, json, os, sys
ex, out = sys.argv[1], sys.argv[2]; K = int(sys.argv[3]) if len(sys.argv) > 3 else 0
os.makedirs(out, exist_ok=True)
SLOT = lambda: {"signal": "TODO", "width": "TODO", "kind": "TODO", "valid_when": "TODO", "clock": "TODO", "edge": "TODO", "storage": "TODO", "latency_min_cycles": "TODO", "latency_max_cycles": "TODO", "source": "TODO", "unknown": []}
for f in sorted(glob.glob(os.path.join(ex, f'arch-blk*-model-v{K}.json'))):
    M = json.load(open(f)); n = int(M['block'][3:])
    port = lambda p, side: {"arch_port": p['name'], ("upstream" if side == 'in' else "downstream"): "TODO", "arch_connected_to": p.get('connected_to', ''), "rtl": SLOT()}
    S = {"from": "hdl", "to": "arch", "round": K, "block": M['block'], "name": M['name'], "active_when": "TODO",
         "rtl_map": [{"file": "TODO", "lines": "TODO", "kind": "TODO", "drives": [], "source": "TODO"}],
         "ports": {"inputs": [port(p, 'in') for p in M['ports']['inputs']], "outputs": [port(p, 'out') for p in M['ports']['outputs']]},
         "extra_ports": [], "harness_result": {}, "confidence": {"level": "TODO", "reason": "TODO"}, "difficulty": {"level": "TODO", "reason": "TODO"},
         "control": {"assessment": "TODO", "items": []}, "questions": [], "assumptions": [], "replies": [], "rtl_changes": [], "status": "TODO", "unknown": [], "no_change": False}
    json.dump(S, open(os.path.join(out, f'hdl-blk{n}-rtl-v{K}.json'), 'w'), ensure_ascii=False, indent=1)
top = {"from": "hdl", "to": "arch", "round": K, "block": "top", "module": "TODO",
       "ports": [{"name": "TODO", "dir": "TODO", "width": "TODO", "kind": "TODO", "clock": "TODO", "edge": "TODO", "reset": "TODO", "source": "TODO"}],
       "hierarchy": [], "control_registers": [], "testbench_timeline": {"raw": "TODO", "source": "TODO"}, "unknown": []}
json.dump(top, open(os.path.join(out, f'hdl-top-rtl-v{K}.json'), 'w'), ensure_ascii=False, indent=1)
print('skeletons written to', out)
