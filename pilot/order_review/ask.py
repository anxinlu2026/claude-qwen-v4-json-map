#!/usr/bin/env python3
"""Chat with local Qwen (thinking off) about a work order, without executing it. usage: ask.py ORDER.md OUT.md"""
import json, sys, urllib.request, time
order = open(sys.argv[1]).read()
q = ("下面是一張交給你的工單。現在【不要執行】,不要呼叫任何工具。請只回答下列問題,每題用一到三句話,用你自己的話,不要照抄工單:\n"
     "1. 這張工單要你交出什麼(檔案、內容)?\n2. 你的第一個動作是什麼?\n3. 你會從哪裡取得「架構那一側」的資料,從哪裡取得「RTL 那一側」的資料?\n"
     "4. 逐訊號表裡每一欄的值,各自從哪裡來?\n5. 「結果」欄 same / different / unknown / not specified / no rtl signal 各在什麼情況下用?\n"
     "6. 什麼情況下要寫假設?假設編號怎麼取?\n7. 做到什麼程度才算完成、怎麼回報?\n"
     "8. 工單裡哪些地方你讀了不確定、前後矛盾、或不知道怎麼做?逐點列出,說明原因。\n9. 如果你要把這張工單縮短一半,你會刪哪些、保留哪些?\n\n=== 工單開始 ===\n" + order + "\n=== 工單結束 ===")
body = json.dumps({"model": "qwen3.8:27b-mxfp8", "stream": False, "think": False,
                   "options": {"temperature": 0.6, "num_ctx": 16384}, "messages": [{"role": "user", "content": q}]}).encode()
t = time.time()
r = json.load(urllib.request.urlopen(urllib.request.Request("http://localhost:11434/api/chat", body, {"Content-Type": "application/json"}), timeout=1500))
open(sys.argv[2], "w").write(r["message"]["content"])
print(f'{time.time()-t:.0f}s, {r.get("eval_count")} tokens'); print(r["message"]["content"])
