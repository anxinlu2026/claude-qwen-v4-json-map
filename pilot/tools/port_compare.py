#!/usr/bin/env python3
"""Compare the RTL-side port JSON (filled by the HDL engineer) with the architecture model: what is missing, extra, different, still TODO/unknown.
Only lists differences; judging them (fix the model? assumption?) is the architecture's job.
usage: port_compare.py out/model_dp.json BLOCK_ports.json [report.json]"""
import json, re, sys
d = json.load(open(sys.argv[1])); r = json.load(open(sys.argv[2]))
b = [x for x in d['blocks'] if x['id'] == r['block']][0]
def norm_arch(p):
    k = p['kind']; vw = None
    m = re.match(r'data-valid-with\((.*)\)', k)
    if m: k, vw = 'data', m.group(1)
    elif k == 'one-cycle pulse': k = 'pulse'
    clk = p['clock']; clk = 'none' if clk.startswith('none') else clk
    return {"width": p['width'], "kind": k, "valid_when": vw if vw else (p.get('valid_when') or 'n/a'), "clock": clk, "edge": p['edge'],
            "storage": p['storage'], "latency_min_cycles": p['latency_min_cycles'], "latency_max_cycles": p['latency_max_cycles']}
def same(a, b):
    f = lambda x: re.sub(r'\s+', '', str(x)).lower()
    return f(a) == f(b)
rep = {"block": r['block'], "ports": [], "missing_in_rtl": [], "rtl_extra_ports": r.get('rtl_extra_ports', []), "todo": []}
for side in ('inputs', 'outputs'):
    arch = {p['name']: p for p in b['ports_detail'][side]}
    for e in r[side]:
        a = norm_arch(arch[e['arch_port']]); x = e['rtl']
        if x['signal'] in ('none', 'no rtl signal'): rep['missing_in_rtl'].append({"side": side, "arch_port": e['arch_port']}); continue
        diffs = {}; unknown = list(x.get('unknown', []))
        for k, av in a.items():
            if x[k] == 'TODO': rep['todo'].append(f"{side}.{e['arch_port']}.{k}"); continue
            if k in unknown: continue
            if k == 'valid_when' and a['kind'] != 'data' and x[k] in ('n/a', ''): continue
            if not same(av, x[k]): diffs[k] = {"architecture": av, "rtl": x[k]}
        rep['ports'].append({"side": side, "arch_port": e['arch_port'], "rtl_signal": x['signal'], "different": diffs, "unknown": unknown,
                             "same_attributes": [k for k in a if k not in diffs and k not in unknown]})
json.dump(rep, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1) if len(sys.argv) > 3 else None
print(f"block {rep['block']}")
for p in rep['ports']:
    print(f"  {p['side'][:-1]:6} {p['arch_port']:10} <-> {p['rtl_signal']}: " + ('same' if not p['different'] else 'DIFFERENT'))
    for k, v in p['different'].items(): print(f"        {k}: architecture={v['architecture']!r}  rtl={v['rtl']!r}")
    if p['unknown']: print(f"        unknown (recorded by HDL): {p['unknown']}")
for m in rep['missing_in_rtl']: print(f"  MISSING in RTL: {m['side']} {m['arch_port']}")
for e in rep['rtl_extra_ports']: print(f"  EXTRA in RTL: {e.get('signal')} ({e.get('kind')}, width {e.get('width')})")
if rep['todo']: print(f"  still TODO: {len(rep['todo'])} slots")
