#!/usr/bin/env python3
"""Usage report: how often each tool and skill was used, by actor, from the records the tools keep.
Sources: the rtl tool's history (state/rtlwork/history.jsonl: every rtl command with its time), the flow tools' usage log (exchange/usage-log.jsonl),
and the optional self-reported "skills_used" list in the exchange files (marked as self-reported: no tool can see a skill being read).
usage: usage_report.py RUN_DIR [--since "YYYY-MM-DD HH:MM"] [--until "YYYY-MM-DD HH:MM"] [--json FILE]"""
import collections, glob, json, os, sys, time
a = sys.argv[1:]; run = a[0]; o = {}
for i, x in enumerate(a):
    if x in ('--since', '--until', '--json'): o[x] = a[i + 1]
tm = lambda s: time.mktime(time.strptime(s, '%Y-%m-%d %H:%M')) if s else None
lo, hi = tm(o.get('--since')), tm(o.get('--until'))
inw = lambda t: (lo is None or t >= lo) and (hi is None or t <= hi)
rtl = collections.Counter(); stops = collections.Counter()
hp = os.path.join(run, 'state', 'rtlwork', 'history.jsonl')
if os.path.exists(hp):
    for l in open(hp):
        h = json.loads(l)
        if 't' in h and inw(h['t']) and h.get('cmd'):
            c = h['cmd'].split(' ')[0]; rtl[c] += 1
            if (h.get('out') or '').startswith('STOP'): stops[c] += 1
flow = collections.Counter(); by_actor = collections.Counter()
lp = os.path.join(run, 'exchange', 'usage-log.jsonl')
if os.path.exists(lp):
    for l in open(lp):
        r = json.loads(l)
        if inw(time.mktime(time.strptime(r['t'], '%Y-%m-%d %H:%M:%S'))): flow[r['tool']] += 1; by_actor[(r['actor'], r['tool'])] += 1
skills = collections.Counter()
for p in glob.glob(os.path.join(run, 'exchange', '*-v*.json')):
    try: d = json.load(open(p))
    except Exception: continue
    for s in d.get('skills_used', []) or []: skills[(d.get('from'), s)] += 1
out = {"rtl_commands": dict(rtl.most_common()), "rtl_commands_stopped_by_a_gate": dict(stops), "flow_tools": dict(flow.most_common()),
       "flow_tools_by_actor": {f'{k[0]}:{k[1]}': v for k, v in by_actor.most_common()}, "skills_self_reported": {f'{k[0]}:{k[1]}': v for k, v in skills.most_common()}}
if '--json' in o: json.dump(out, open(o['--json'], 'w'), ensure_ascii=False, indent=1)
print('rtl commands (%d): %s' % (sum(rtl.values()), dict(rtl.most_common())))
print('  stopped by a gate: %s' % dict(stops))
print('flow tools (%d): %s' % (sum(flow.values()), dict(flow.most_common())))
if by_actor: print('  by actor: %s' % {f'{k[0]}:{k[1]}': v for k, v in by_actor.most_common()})
print('skills (self-reported in the exchange files): %s' % (out['skills_self_reported'] or 'none reported'))
