#!/usr/bin/env python3
"""RTL-side port skeleton of one block, from the architecture model (names and connections only; the architecture's attribute values are NOT shown,
so the HDL engineer records what the RTL has instead of copying the model).
usage: make_port_skeleton.py out/model_dp.json BLOCK > BLOCK_ports.json"""
import json, sys
d = json.load(open(sys.argv[1])); b = [x for x in d['blocks'] if x['id'] == sys.argv[2]][0]
SLOTS = {"signal": "TODO", "width": "TODO", "kind": "TODO", "valid_when": "TODO", "clock": "TODO", "edge": "TODO", "storage": "TODO",
         "latency_min_cycles": "TODO", "latency_max_cycles": "TODO", "source": "TODO", "unknown": []}
def port(p): return {"arch_port": p['name'], "arch_connected_to": ', '.join(f"{c['block']}.{c['port']}" for c in p['connected_to']), "rtl": dict(SLOTS)}
sk = {"block": b['id'], "inputs": [port(p) for p in b['ports_detail']['inputs']], "outputs": [port(p) for p in b['ports_detail']['outputs']], "rtl_extra_ports": []}
print(json.dumps(sk, ensure_ascii=False, indent=1))
