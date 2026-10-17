#!/usr/bin/env python3
"""Multi-turn chat with local Qwen about a work order. usage: chat.py ORDER.md OUT.md  (questions from questions_*.txt via QFILE env, blank-line separated; first turn includes the order)"""
import json, os, sys, urllib.request, time
order = open(sys.argv[1]).read(); qs = [q.strip() for q in open(os.environ['QFILE']).read().split('\n\n') if q.strip()]
msgs = []; out = []
for i, q in enumerate(qs):
    msgs.append({"role": "user", "content": (("下面是一張交給你的工單。現在【不要執行】,不要呼叫任何工具,只回答問題,每題一到三句話,用你自己的話。\n\n=== 工單開始 ===\n" + order + "\n=== 工單結束 ===\n\n") if i == 0 else "") + q})
    body = json.dumps({"model": "qwen3.8:27b-mxfp8", "stream": False, "think": False, "options": {"temperature": 0.6, "num_ctx": 16384}, "messages": msgs}).encode()
    t = time.time(); r = json.load(urllib.request.urlopen(urllib.request.Request("http://localhost:11434/api/chat", body, {"Content-Type": "application/json"}), timeout=1500))
    a = r["message"]["content"]; msgs.append({"role": "assistant", "content": a}); out.append(f"## 問 {i+1}\n{q}\n\n## 答 {i+1}({time.time()-t:.0f}s)\n{a}\n")
open(sys.argv[2], "w").write('\n'.join(out)); print('\n'.join(out))
