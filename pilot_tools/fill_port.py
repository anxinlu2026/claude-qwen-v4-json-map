#!/usr/bin/env python3
"""Fill values of the RTL-side port JSON without touching keys or structure.
usage: fill_port.py FILE inputs|outputs ARCH_PORT key=value [key=value ...]
       fill_port.py FILE extra key=value [key=value ...]        (appends one rtl_extra_ports item)
keys: signal width kind valid_when clock edge storage latency_min_cycles latency_max_cycles source
value 'unknown' also adds the key to the port's "unknown" list. Values are checked (kind/edge/storage words, integers)."""
import json, sys
f, sec = sys.argv[1], sys.argv[2]; d = json.load(open(f))
if sec == 'extra': target = {}; kv = sys.argv[3:]
else:
    ap = sys.argv[3]; kv = sys.argv[4:]
    hits = [p for p in d[sec] if p['arch_port'] == ap]
    if not hits: sys.exit(f"no arch_port {ap!r} in {sec}; have: {[p['arch_port'] for p in d[sec]]}")
    target = hits[0]['rtl']
ENUM = {'kind': {'pulse', 'level', 'held', 'data', 'n/a', 'unknown'}, 'edge': {'rising', 'falling', 'n/a', 'unknown'}, 'storage': {'combinational', 'register', 'n/a', 'unknown'}}
INT = {'width', 'latency_min_cycles', 'latency_max_cycles'}; OK = set(ENUM) | INT | {'signal', 'valid_when', 'clock', 'source'}
for item in kv:
    k, _, v = item.partition('=')
    if k not in OK: sys.exit(f'unknown key {k!r}; allowed: {sorted(OK)}')
    if k in ENUM and v not in ENUM[k]: sys.exit(f'{k} must be one of {sorted(ENUM[k])}, got {v!r}')
    if k in INT: v = v if v in ('unknown', 'n/a') else int(v)
    target[k] = v
    if v == 'unknown' and sec != 'extra':
        u = target.setdefault('unknown', [])
        if k not in u: u.append(k)
if sec == 'extra': d.setdefault('rtl_extra_ports', []).append(target)
json.dump(d, open(f, 'w'), ensure_ascii=False, indent=1); print('ok:', sec, sys.argv[3] if sec != 'extra' else target.get('signal'))
