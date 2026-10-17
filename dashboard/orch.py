#!/usr/bin/env python3
"""Orchestrator log: one line per action or decision, shown on the board (section "Orchestrator log").

usage: orch.py ACTION ORDER "text" [--run RUN_DIR] [--role orchestrator|architecture|hdl]
       orch.py round ORDER "reason" --result pass|fail --fails N --auth keep|narrow [--next ORDER]   (one line per round, written before the next round starts)
ACTION is free text; the board colours: issue, answer, close, decide, note, handoff, stop.
RUN_DIR defaults to the newest directory under ../runs.
"""
import argparse, glob, json, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('action'); ap.add_argument('order'); ap.add_argument('text')
ap.add_argument('--run', default=None); ap.add_argument('--role', default='orchestrator')
ap.add_argument('--result', default=None, help='round: pass | fail'); ap.add_argument('--fails', type=int, default=None, help='round: consecutive non-passing orders so far')
ap.add_argument('--auth', default=None, help='round: keep | narrow (work authorization for the next order)'); ap.add_argument('--next', default=None, dest='nxt', help='round: next order id')
a = ap.parse_args()
run = a.run or max(glob.glob(os.path.join(HERE, '..', 'runs', 'orders-*')), key=os.path.getmtime)
os.makedirs(os.path.join(run, 'control'), exist_ok=True)
with open(os.path.join(run, 'control', 'orchestrator_log.jsonl'), 'a') as f:
    e = {'t': time.time(), 'role': a.role, 'action': a.action, 'order': a.order, 'text': a.text}
    for k, v in (('result', a.result), ('fails', a.fails), ('auth', a.auth), ('next', a.nxt)):
        if v is not None:
            e[k] = v
    f.write(json.dumps(e, ensure_ascii=False) + '\n')
print('logged')
