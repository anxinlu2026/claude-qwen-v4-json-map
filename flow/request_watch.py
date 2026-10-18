#!/usr/bin/env python3
"""Request watcher: a worker that is blocked asks the orchestrator (rtl ask / rtl next write request files and wait). This watcher
notices new unanswered requests, writes exchange/pending-requests.json (for the board), notifies the desktop, re-notifies while a request stays
unanswered, and with --ack-next answers a plain report at once (so the worker's wait does not run into its own timeout). It never answers a request that needs a decision.
usage: request_watch.py RUN_DIR [--ack-next] [--interval 5] [--remind 300] [--once]"""
import glob, json, os, subprocess, sys, time
a = sys.argv[1:]; run = a[0]; o = {'--interval': '5', '--remind': '300'}
for i, x in enumerate(a):
    if x in ('--interval', '--remind'): o[x] = a[i + 1]
ack = '--ack-next' in a; once = '--once' in a
box = (glob.glob(os.path.join(run, 'work', '*', 'harness', '*', 'rundir', '.orchestrator')) or [''])[0]
ex = os.path.join(run, 'exchange'); os.makedirs(ex, exist_ok=True)
notified = {}
def notify(title, msg):
    print(time.strftime('%H:%M:%S'), title, '-', msg, flush=True)
    try: subprocess.run(['osascript', '-e', f'display notification {json.dumps(msg[:180])} with title {json.dumps(title)}'], capture_output=True, timeout=5)
    except Exception: pass
while True:
    pend = []
    for f in sorted(glob.glob(os.path.join(box, 'request_*.md'))):
        b = os.path.basename(f); kind = 'report' if b.startswith('request_next_') else 'ask'
        ans = f.replace('request_', 'answer_')
        if os.path.exists(ans): continue
        if kind == 'report' and ack:
            open(ans, 'w').write('CONVERSATION COMPLETE\nReport received. The architecture session judges the delivery.\n'); notify('request watcher', f'{b}: report acknowledged'); continue
        txt = open(f).read().strip().replace('\n', ' ')[:300]; age = int(time.time() - os.path.getmtime(f))
        pend.append({"file": b, "kind": kind, "age_s": age, "text": txt})
        last = notified.get(b)
        if last is None or time.time() - last >= int(o['--remind']):
            notify('request waiting for an answer' if last is None else 'request STILL waiting', f'{b} ({kind}, {age} s): {txt[:120]}'); notified[b] = time.time()
    json.dump({"time": time.strftime('%Y-%m-%d %H:%M:%S'), "pending": pend}, open(os.path.join(ex, 'pending-requests.json'), 'w'), ensure_ascii=False, indent=1)
    if once: print(f'{len(pend)} pending request(s)'); break
    time.sleep(int(o['--interval']))
