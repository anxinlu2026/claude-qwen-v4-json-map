#!/usr/bin/env python3
"""Run inside the agent container (where `rtl`, iverilog and the design are). Reads an rtl_map block (architecture skeleton + the part the HDL engineer filled),
checks the structure, builds the `rtl blockcheck` command from it (iverilog runs the RTL, the architecture's Python runs the model), runs it and writes a report.
usage: align_check.py BLOCK_JSON REPORT_JSON [STRUCTURE_JSON]"""
import json, re, subprocess, sys
blk = json.load(open(sys.argv[1])); out_path = sys.argv[2]
rep = {'arch_id': blk['arch_id'], 'checks': [], 'result': None}
r = blk['rtl']
def sigs(lst): return '+'.join(lst)
# 1. structure: every argument filled, widths add up, no TODO
width_rtl = {}
problems = []
for a in r['args']:
    w = len(a['signals']) * 8
    want = [x for x in blk['args'] if x['name'] == a['arg']]
    if not want: problems.append(f"argument {a['arg']} is not in the skeleton")
    elif want[0]['width'] != w: problems.append(f"argument {a['arg']}: {len(a['signals'])} signals x 8 bit = {w} bit, the architecture says {want[0]['width']}")
w_out = len(r['output']['signals']) * 8
if w_out != blk['output'][0]['width']: problems.append(f"output: {w_out} bit, the architecture says {blk['output'][0]['width']}")
if 'TODO' in json.dumps(r): problems.append('TODO left in the rtl part')
rep['checks'].append({'check': 'structure (arguments, widths, no TODO)', 'ok': not problems, 'problems': problems})
if problems:
    rep['result'] = 'structure not accepted'; json.dump(rep, open(out_path, 'w'), indent=1, ensure_ascii=False); print(json.dumps(rep, indent=1, ensure_ascii=False)); sys.exit(1)
# 2. the comparison: iverilog (through `rtl`) runs the RTL, the architecture's Python runs the model
cmd = ['rtl', 'blockcheck']
for a in r['args']:
    cmd += ['--in', sigs(a['signals'])]
cmd += ['--out', sigs(r['output']['signals']), '--model', blk['python'], '--max', '12']
if r.get('active_when'): cmd += ['--when', r['active_when']]
p = subprocess.run(cmd, capture_output=True, text=True)
text = p.stdout + p.stderr
rows = []
for line in text.splitlines():
    m = re.match(r'\s*(\d+)\s*\|\s*([0-9a-fx]+)\s*\|\s*([0-9a-fx]+)\s*\|\s*([0-9a-fx-]+)\s*\|\s*(\S.*)$', line)
    if m: rows.append({'t': int(m.group(1)), 'input': m.group(2), 'rtl': m.group(3), 'model': m.group(4), 'result': m.group(5).strip()})
n_ok = sum(1 for x in rows if x['result'] == 'match'); n_bad = sum(1 for x in rows if x['result'].startswith('MISMATCH'))
rep['command'] = ' '.join(c if ' ' not in c else repr(c[:60] + '...') for c in cmd)
rep['rows'] = rows
rep['summary'] = {'compared': n_ok + n_bad, 'match': n_ok, 'mismatch': n_bad}
tool_line = [l for l in text.splitlines() if 'recorded as' in l]
rep['tool_line'] = tool_line[-1] if tool_line else ''
rep['result'] = ('not exercised (no row where the block works under active_when)' if n_ok + n_bad == 0 else 'MATCH on all compared rows' if n_bad == 0 else f'MISMATCH on {n_bad} of {n_ok + n_bad} compared rows')
rep['raw_tail'] = text[-1500:]
json.dump(rep, open(out_path, 'w'), indent=1, ensure_ascii=False)
print(json.dumps({k: rep[k] for k in ('arch_id', 'result', 'summary', 'tool_line')}, indent=1, ensure_ascii=False))
for x in rows: print(x['t'], x['input'], x['rtl'], x['model'], x['result'])
