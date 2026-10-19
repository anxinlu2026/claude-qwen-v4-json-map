#!/usr/bin/env python3
"""Drive a local model (Ollama) as the HDL engineer through the Claude Code interface, for one round of the block-map flow.
One call = one turn of the session; after each turn the script checks whether the round's files are complete and, if not, asks the model to continue
(same session, --resume). It stops when the round is complete, when the time budget is used, or after N turns without progress (new or changed files, new rtl commands).
Every turn is logged (time, duration, tokens, last words) in <exchange>/hdl-session-log.jsonl: this is the data for comparing models.
usage: run_hdl_cc.py CELL_DIR ROUND PROMPT_FILE   (a non-empty <exchange>/.nudge.txt becomes the next turn's message and is then renamed .nudge.used-N.txt)
       run_hdl_cc.py CELL_DIR ROUND PROMPT_FILE [--base-url URL (11435 = the no-think proxy)] [--model NAME] [--hours H] [--idle-turns N] [--turn-minutes M]
Round 0 is complete when hdl-blk0..14-rtl-v0.json and hdl-top-rtl-v0.json exist and the form check passes; round K>=1 when the files of round K exist, the form check
passes and tool-top-regression-vK.json exists."""
import glob, json, os, subprocess, sys, time
cell, K, prompt = sys.argv[1], int(sys.argv[2]), sys.argv[3]
o = {'--base-url': 'http://localhost:11434', '--model': 'qwen3.8:27b-mxfp8-v3-ctx262144', '--hours': '3', '--idle-turns': '3', '--turn-minutes': '25'}
for i, x in enumerate(sys.argv):
    if x in o: o[x] = sys.argv[i + 1]
here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.normpath(os.path.join(here, '..'))
ex = os.path.join(cell, 'exchange'); bind = os.path.join(cell, 'hdl_bin'); cfg = os.path.join(cell, 'cc_cfg'); os.makedirs(cfg, exist_ok=True)
logp = os.path.join(ex, 'hdl-session-log.jsonl'); sidp = os.path.join(ex, f'.hdl-session-id')
env = dict(os.environ, PATH=bind + ':' + os.environ['PATH'], FLOW_ACTOR='hdl', CLAUDE_CONFIG_DIR=cfg, ANTHROPIC_BASE_URL=o['--base-url'], ANTHROPIC_AUTH_TOKEN='ollama',
           ANTHROPIC_API_KEY='', ANTHROPIC_MODEL=o['--model'], ANTHROPIC_DEFAULT_OPUS_MODEL=o['--model'], ANTHROPIC_DEFAULT_SONNET_MODEL=o['--model'],
           ANTHROPIC_DEFAULT_HAIKU_MODEL=o['--model'], CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1', BASH_DEFAULT_TIMEOUT_MS='600000', BASH_MAX_TIMEOUT_MS='900000')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_permissions
allowed = cc_permissions.allowed(cell, repo)
# --permission-mode dontAsk: whatever is not allowed above is denied (measured: ls, find, cat of a file outside, Read outside are refused). --allowedTools alone does not restrict.

def complete():
    need = [f'hdl-blk{n}-rtl-v{K}.json' for n in range(15)] + [f'hdl-top-rtl-v{K}.json']
    if any(not os.path.exists(os.path.join(ex, f)) for f in need): return False, 'files missing: ' + ', '.join(f for f in need if not os.path.exists(os.path.join(ex, f)))[:150]
    r = subprocess.run([sys.executable, os.path.join(here, 'validate_json.py'), ex] + [os.path.join(ex, f) for f in need], capture_output=True, text=True)
    if r.returncode: return False, 'form check: ' + r.stdout.strip().splitlines()[0]
    if K >= 1 and not os.path.exists(os.path.join(ex, f'tool-top-regression-v{K}.json')): return False, f'tool-top-regression-v{K}.json missing'
    return True, 'complete'

def snapshot():
    h = os.path.join(cell, 'state', 'rtlwork', 'history.jsonl')
    return (sum(1 for _ in open(h)) if os.path.exists(h) else 0, tuple(sorted((f, os.path.getmtime(os.path.join(ex, f))) for f in os.listdir(ex) if f.startswith(('hdl-', 'tool-')) and f.endswith('.json'))))

def turn(text, sid):
    cmd = ['claude', '-p', text, '--output-format', 'json', '--max-turns', '80', '--model', o['--model'], '--permission-mode', 'dontAsk', '--allowedTools'] + allowed + (['--resume', sid] if sid else [])
    t0 = time.time()
    try: p = subprocess.run(cmd, cwd=ex, env=env, capture_output=True, text=True, timeout=int(o['--turn-minutes']) * 60, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired: return None, time.time() - t0, 'turn timed out'
    try: d = json.loads(p.stdout)
    except Exception: return None, time.time() - t0, 'unparsable output: ' + (p.stdout + p.stderr)[-300:]
    return d, time.time() - t0, ''

sid = open(sidp).read().strip() if os.path.exists(sidp) else None
start = time.time(); idle = 0; n = 0
cont = '授權說明（orchestrator）：本流程需要的 rtl 指令、flow 腳本、在 exchange 資料夾內寫檔，都已經核准，不需要再向使用者確認；直接開始。PATH 與 FLOW_ACTOR 已設好，直接執行 rtl …，不要用 export。請繼續第 %d 輪的工作，直到全部完成。已完成的部分不用重做；完成後告訴我完成了什麼、哪些方塊 harness 不符、你想問架構的問題。' % K
while True:
    ok, why = complete()
    if ok: print('round complete'); break
    if time.time() - start > float(o['--hours']) * 3600: print('time budget used:', why); break
    before = snapshot(); n += 1
    nudge = os.path.join(ex, '.nudge.txt')
    if sid is not None and os.path.exists(nudge) and open(nudge).read().strip():     # a message from the orchestrator replaces the standard 'continue' text once
        text = open(nudge).read().strip() + f'\n（目前檢查：{why}）'; os.rename(nudge, os.path.join(ex, f'.nudge.used-{n + 1}.txt'))
    else:
        text = open(prompt).read() if sid is None else cont + f'\n（目前檢查：{why}）'
    d, dur, err = turn(text, sid)
    rec = {"t": time.strftime('%Y-%m-%d %H:%M:%S'), "turn": n, "seconds": round(dur), "error": err}
    if d:
        sid = d.get('session_id', sid); open(sidp, 'w').write(sid or '')
        u = d.get('usage', {}); rec.update(model_turns=d.get('num_turns'), subtype=d.get('subtype'), input_tokens=u.get('input_tokens'), cache_read=u.get('cache_read_input_tokens'),
                                          output_tokens=u.get('output_tokens'), last_words=str(d.get('result'))[-300:])
    if not d:    # the turn timed out or gave no JSON: the session id is still the name of the newest transcript; keep it so the next turn resumes instead of starting over
        tp = sorted(glob.glob(os.path.join(cfg, 'projects', '*', '*.jsonl')), key=os.path.getmtime)
        if tp and (sid is None or os.path.basename(tp[-1])[:-6] != sid):
            sid = os.path.basename(tp[-1])[:-6]; open(sidp, 'w').write(sid); rec['recovered_session_id'] = sid
    after = snapshot(); rec['progress'] = after != before
    open(logp, 'a').write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(f"turn {n}: {rec['seconds']} s, model turns {rec.get('model_turns')}, progress {rec['progress']}, {err or rec.get('subtype')}")
    idle = 0 if rec['progress'] else idle + 1
    if idle >= int(o['--idle-turns']): print(f'stopped: {idle} turns without progress ({why})'); break
