#!/usr/bin/env python3
"""List the candidate cut points of a block from the tool-extracted RTL structure: every named signal on the way from the block's inputs to its output
(the fan-in cone of the output, stopping at the inputs). usage: cut_candidates.py rtl_structure.json MODULE OUTPUT_SIGNAL INPUT_SIGNAL [INPUT_SIGNAL ...]"""
import json, sys
st = json.load(open(sys.argv[1])); mod = st['modules'][sys.argv[2]]
sig = {s['name']: s for s in mod['signals']}
out, ins = sys.argv[3], set(sys.argv[4:])
seen, order = set(), []
def walk(n):
    if n in seen or n in ins or n not in sig: return
    seen.add(n)
    for d in sig[n]['depends_on']: walk(d)
    order.append(n)           # post-order: dependencies first
walk(out)
res = [{'signal': n, 'kind': sig[n]['kind'], 'width': sig[n]['width'], 'shape': sig[n]['shape'], 'depends_on': sig[n]['depends_on']} for n in order]
print(json.dumps({'block_output': out, 'block_inputs': sorted(ins), 'candidates_in_dependency_order': res}, indent=1))
