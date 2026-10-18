#!/usr/bin/env python3
"""Freshness report for the orchestrator: which documents are current, which copies disagree, and where the newest run stands.
Read-only. Run it at the start of every use of the skill orchestrator-run-loop, then read the files it flags.

usage: refresh.py [--run RUN_DIR]
"""
import argparse, glob, hashlib, json, os, re, subprocess, time

M = '/Users/anxin/AI/benchmarks/multi-ai'
D = M + '/claude/cvdp_aes0005_multi_ai'
W = M + '_a34197d'


def md5(p):
    try:
        return hashlib.md5(open(p, 'rb').read()).hexdigest()[:8]
    except OSError:
        return '-'


def mt(p):
    try:
        return time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(p)))
    except OSError:
        return '-'


def sh(*a):
    return subprocess.run(list(a), capture_output=True, text=True).stdout.strip()


ap = argparse.ArgumentParser(); ap.add_argument('--run', default=None); a = ap.parse_args()
run = a.run or max(glob.glob(D + '/runs/orders-*'), key=os.path.getmtime)

print('== documents of record (newest first by mtime; copies that disagree are marked DIFF)')
docs = [
    ('orchestrator agent.md', D + '/01_plan/muti-agent-v2/orchestrator/agent.md', [M + '/doc/muti-agent-v2/orchestrator/agent.md']),
    ('hdl agent.md', D + '/01_plan/muti-agent-v2/hdl/agent.md', []),
    ('architecture agent.md', D + '/01_plan/muti-agent-v2/architecture/agent.md', [M + '/doc/muti-agent-v2/architecture/agent.md']),
    ('HDL kickoff', D + '/03_agent_kickoff/kickoff_hdl_v1.txt', []),
    ('responsibility table', D + '/01_plan/responsibility_table.md', [M + '/skills_arch/responsibility_table.md']),
    ('skill orchestrator-run-loop', D + '/04_skills/orchestrator-run-loop/SKILL.md', [M + '/.claude/skills/orchestrator-run-loop/SKILL.md']),
    ('rtl tool', D + '/02_work_order_format/rtl', [M + '/tools/rtl/rtl', W + '/tools/rtl/rtl']),
    ('a1_round.py', D + '/02_work_order_format/a1_round.py', [M + '/tools/agentic/a1_round.py']),
    ('run_orders.py', D + '/02_work_order_format/run_orders.py', [M + '/tools/agentic/run_orders.py', W + '/tools/agentic/run_orders.py']),
    ('README', D + '/README.md', []),
]
rows = []
for name, p, others in docs:
    flag = ''
    for o in others:
        if os.path.exists(o) and md5(o) != md5(p):
            flag += f' DIFF vs {o.replace(M, "")} ({md5(o)}, {mt(o)})'
    rows.append((os.path.getmtime(p) if os.path.exists(p) else 0, f'  {mt(p)}  {md5(p)}  {name}{flag}'))
for _, r in sorted(rows, reverse=True):
    print(r)

print('\n== skills: tracked copy (claude/04_skills) vs working copy (skills/) vs worktree a34197d')
diff = []
for f in sorted(glob.glob(D + '/04_skills/*/SKILL.md')):
    n = f.split('/')[-2]
    w, x = M + f'/skills/{n}/SKILL.md', W + f'/skills/{n}/SKILL.md'
    d = []
    if os.path.exists(w) and md5(w) != md5(f): d.append('skills/ differs')
    if os.path.exists(x) and md5(x) != md5(f): d.append('worktree differs')
    if d: diff.append(f'  {n}: ' + ', '.join(d))
print('\n'.join(diff) if diff else '  all copies equal')

print('\n== images and containers')
print('  ' + sh('docker', 'images', '--format', '{{.Repository}}:{{.Tag}} {{.CreatedSince}}', 'multi-ai/cvdp-qwen-agent').replace('\n', '\n  ').split('\n  0.25.0-rtl2')[0][:600])
print('  ' + sh('docker', 'ps', '--format', '{{.Names}} {{.Image}} {{.Status}}').replace('\n', '\n  ')[:900])

print('\n== newest run:', os.path.basename(run))
ctl = run + '/control'
log = open(run + '/console.log').read().splitlines() if os.path.exists(run + '/console.log') else []
print('  console.log last lines:'); [print('   ', l[:150]) for l in log[-4:]]
try:
    proto = json.load(open(run + '/protocol.json')); ses = proto['work_orders']['sessions'][-1]
    print('  last session:', {k: ses.get(k) for k in ('image', 'model', 'reasoning_effort', 'temperature')}, os.path.basename(ses.get('kickoff_file', '')))
except Exception as e:
    print('  protocol:', e)
ol = []
if os.path.exists(ctl + '/orchestrator_log.jsonl'):
    ol = [json.loads(l) for l in open(ctl + '/orchestrator_log.jsonl') if l.strip()]
rounds = [e for e in ol if e.get('action') == 'round']
fails = 0
for e in rounds:
    fails = 0 if e.get('result') == 'pass' else fails + 1
print(f'  rounds written: {len(rounds)}; consecutive non-pass now: {fails} (stop at 3)')
for e in rounds[-5:]:
    print(f'    {e.get("order")}: {e.get("result")} fails={e.get("fails")} auth={e.get("auth")} next={e.get("next")} | {e.get("text","")[:80]}')
print('  last log entries:')
for e in ol[-4:]:
    print(f'    {time.strftime("%H:%M:%S", time.localtime(e["t"]))} {e.get("action")} {e.get("order")}: {e.get("text","")[:90]}')
box = next(iter(glob.glob(run + '/work/*/harness/*/rundir/.orchestrator')), '')
if box:
    pend = [os.path.basename(f) for f in glob.glob(box + '/request_*.md') if not os.path.exists(f.replace('request_', 'answer_'))]
    print('  reports waiting for an answer:', pend or 'none')
done = sorted(int(re.search(r'conv_(\d+)', f).group(1)) for f in glob.glob(ctl + '/conv_*.done'))
cases = sorted(int(re.search(r'case_(\d+)', f).group(1)) for f in glob.glob(ctl + '/case_*.md'))
print(f'  conversations: cases {cases[-3:]} done {done[-3:]}; delivered:', sorted(os.path.basename(f) for f in glob.glob(run + '/state/deliveries/*.md')))
print('  architecture files:', sorted(os.path.basename(f) for f in glob.glob(ctl + '/architecture/*')))

print('\n== git (tracked documents)')
print('  ' + (sh('git', '-C', M, 'status', '--short', '--', 'claude').replace('\n', '\n  ')[:700] or 'clean'))
print('  last commits:', sh('git', '-C', M, 'log', '--oneline', '-3').replace('\n', ' | '))
