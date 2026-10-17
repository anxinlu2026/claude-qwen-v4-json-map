#!/usr/bin/env python3
"""Byte/bit-level drill-down of one failing sub-block (inside the agent container).
Runs `rtl blockcheck` for OUT == k * IN (bytes, GF(2^8)), then for every compared row and byte: xor(rtl, model), which bytes are wrong, and
which candidate explanations (written by the architecture from the algebra, not from the RTL) reproduce the RTL output for ALL bytes.
usage: bytediff.py OUT_SIGNAL IN_SIGNAL K_HEX REPORT.json"""
import collections, json, subprocess, sys
out, inp, k, rep = sys.argv[1:5]
def seq(n): return '+'.join(f'{n}[{i % 4}][{i // 4}]' for i in range(16))
WHEN = 'round_ff==2 || round_ff==3 || round_ff==4'
text = subprocess.run(['rtl', 'blockcheck', '--in', seq(inp), f'={k}', '--out', seq(out), '--model',
    'python3 /tmp/ip_work/arch/model_cli_sub.py block gmul_state', '--when', WHEN, '--max', '12'], capture_output=True, text=True).stdout
rows = []
for l in text.splitlines():
    c = [x.strip() for x in l.split('|')]
    if len(c) >= 6 and c[0].isdigit(): rows.append((int(c[0]), c[1], c[3], c[4]))
def B(s, n): return int(s[2*n:2*n+2], 16)
def xt(b): return ((b << 1) & 0xff) ^ (0x1b if b & 0x80 else 0)
# explanations: functions of the input byte; the first is the standard (what the model does), the others are architecture's candidate faults
EXPL = {
 'standard (model)': {'02': xt, '04': lambda b: xt(xt(b)), '08': lambda b: xt(xt(xt(b)))},
 'every later doubling reduces on bit7 of the ORIGINAL byte': {
   '02': xt,
   '04': lambda b: ((xt(b) << 1) & 0xff) ^ (0x1b if b & 0x80 else 0),
   '08': lambda b: ((((xt(b) << 1) & 0xff) ^ (0x1b if b & 0x80 else 0)) << 1 & 0xff) ^ (0x1b if b & 0x80 else 0)},
 'later doublings never reduce': {'02': xt, '04': lambda b: (xt(b) << 1) & 0xff, '08': lambda b: (xt(b) << 3) & 0xff},
 'plain shifts, no reduction': {'02': lambda b: (b << 1) & 0xff, '04': lambda b: (b << 2) & 0xff, '08': lambda b: (b << 3) & 0xff}}
xor_hist = collections.Counter(); bad = collections.Counter(); per_row = []; total = 0
for t, i, o, m in rows:
    wrong = []
    for n in range(16):
        total += 1; d = B(o, n) ^ B(m, n)
        if d: xor_hist[format(d, '08b')] += 1; bad[n] += 1; wrong.append(n)
    per_row.append({'t': t, 'wrong_bytes': wrong})
res = {'block': out, 'input': inp, 'constant': k, 'rows': len(rows), 'bytes_compared': total, 'bytes_wrong': sum(bad.values()),
       'xor_pattern_rtl_vs_model': dict(xor_hist), 'per_row': per_row, 'explanations': {}}
for name, fs in EXPL.items():
    f = fs.get(k)
    if f: res['explanations'][name] = {'bytes_reproduced': sum(f(B(i, n)) == B(o, n) for _, i, o, _ in rows for n in range(16)), 'of': total}
json.dump(res, open(rep, 'w'), indent=1)
print(f'{out} vs {k}*{inp}: {res["bytes_wrong"]}/{total} bytes wrong; xor patterns {dict(xor_hist)}')
for n, v in res['explanations'].items(): print(f'  {v["bytes_reproduced"]:3}/{v["of"]}  {n}')
