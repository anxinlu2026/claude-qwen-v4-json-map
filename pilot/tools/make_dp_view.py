#!/usr/bin/env python3
"""HDL view of the architecture model: data-path blocks only. The control blocks (key_counter, round_counter, done_gen, key_done_flag), the control section and the schedule are left out;
every connection to a control block becomes 'control (RTL's own, not specified by the architecture)'. usage: make_dp_view.py arch/model.json out/model_dp.json"""
import json, sys
CONTROL = {'key_counter', 'round_counter', 'done_gen', 'key_done_flag'}
m = json.load(open(sys.argv[1]))
CTL = "control (RTL's own; not specified by the architecture)"
def fix_conn(conns):
    out, seen = [], set()
    for c in conns:
        if c.get('block') in CONTROL:
            c = {'block': CTL, 'port': c.get('port')}
        key = (c['block'], c.get('port'))
        if key not in seen:
            seen.add(key); out.append(c)
    return out
blocks = []
for b in m['blocks']:
    if b['id'] in CONTROL:
        continue
    b = json.loads(json.dumps(b))
    for side in ('inputs', 'outputs'):
        for p in b['ports_detail'][side]:
            p['connected_to'] = fix_conn(p.get('connected_to', []))
            if any(c['block'] == CTL for c in p['connected_to']):
                p['note'] = (p.get('note', '') + ' [the control that produces or consumes this signal is not specified for the HDL engineer: describe the RTL\'s own]').strip()
    for side in ('upstream_blocks', 'downstream_blocks'):
        merged, ctl_sig = [], []
        for e in b.get(side, []):
            if e['block'] in CONTROL:
                ctl_sig += e['signals']
            else:
                merged.append(e)
        if ctl_sig:
            merged.append({'block': CTL, 'signals': sorted(set(ctl_sig)), 'count': len(set(ctl_sig))})
        b[side] = merged
    blocks.append(b)
view = {'design': m['design'], 'parameters': m.get('parameters'), 'byte_layout': m.get('byte_layout'), 'interface': m['interface'],
        'blocks': blocks, 'edges': [e for e in m['edges'] if e.get('from', '').split('.')[0] not in CONTROL and e.get('to', '').split('.')[0] not in CONTROL],
        'note': 'HDL view: data-path blocks only. Control (counters, done, key_done) is not specified here; describe the RTL\'s own control.'}
json.dump(view, open(sys.argv[2], 'w'), indent=1)
print('blocks', len(blocks), [b['id'] for b in blocks])
