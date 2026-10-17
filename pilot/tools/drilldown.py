#!/usr/bin/env python3
"""Drill-down run for inv_mix_columns (inside the agent container, where `rtl`, iverilog and the design are).
Reads 6_sub_skeleton.json; the 'HDL part' (signal lists in the architecture layout, byte n = [n%4][n//4]) is made here by script.
For every candidate signal X: which GF constant k gives X == k * AddRoundKey (byte-wise)? Then: MixColumns == mix_combine(RTL's own products)?
usage: drilldown.py SKELETON.json REPORT.json"""
import json, re, subprocess, sys
sk = json.load(open(sys.argv[1]))
def seq(name): return '+'.join(f'{name}[{n % 4}][{n // 4}]' for n in range(16))
WHEN = 'round_ff==2 || round_ff==3 || round_ff==4'
def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True); text = p.stdout + p.stderr
    rows = []
    for line in text.splitlines():
        c = [x.strip() for x in line.split('|')]
        if len(c) >= 5 and c[0].isdigit(): rows.append((int(c[0]), c[-1]))
    ok = sum(1 for _, r in rows if r == 'match'); bad = sum(1 for _, r in rows if r.startswith('MISMATCH'))
    return ok, bad, text
rep = {'parent': sk['parent_block'], 'when': WHEN, 'products': {}, 'combine': None}
prod = [b for b in sk['sub_blocks'] if b['id'] == 'product'][0]
for X in prod['for_each_candidate']:
    res = {}
    for k in sk['constants_of_the_standard']:
        ok, bad, _ = run(['rtl', 'blockcheck', '--in', seq(sk['input_signal']), f'={k}', '--out', seq(X), '--model', prod['python'], '--when', WHEN, '--max', '12'])
        res[k] = {'match': ok, 'mismatch': bad}
    hit = [k for k, v in res.items() if v['match'] > 0 and v['mismatch'] == 0]
    name_k = X[len('xtimes'):]
    rep['products'][X] = {'by_constant': res, 'matches_constant': hit, 'constant_in_the_name': name_k,
                          'verdict': ('equals the product by ' + hit[0] + (' (as the name says)' if hit[0] == name_k else ' (NOT what the name says)')) if hit else 'equals the product by NO constant of the standard'}
comb = [b for b in sk['sub_blocks'] if b['id'] == 'combine'][0]
ins = ['--in'] + [seq(x) for x in comb['inputs_from_rtl']]
ok, bad, text = run(['rtl', 'blockcheck'] + ins + ['--out', seq(comb['output_signal']), '--model', comb['python'], '--when', WHEN, '--max', '12'])
rep['combine'] = {'match': ok, 'mismatch': bad, 'verdict': 'MATCH' if bad == 0 and ok else 'MISMATCH' if bad else 'not exercised'}
json.dump(rep, open(sys.argv[2], 'w'), indent=1)
print(f"{'candidate':10} verdict")
for X, r in rep['products'].items(): print(f'{X:10} {r["verdict"]}')
print('combine   ', rep['combine'])
