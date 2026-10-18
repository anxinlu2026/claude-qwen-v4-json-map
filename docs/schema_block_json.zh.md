# JSON 格式（schema）草案：架構與 HDL 以 JSON 溝通

狀態：草案，待使用者確認後再做驗證腳本。規劃見 `PLAN_block_map.zh.md`。

## 0. 共通規則
- 檔名：`arch-top-model-v<K>.json`、`arch-blk<N>-model-v<K>.json`、`arch-blk<N>-harness-v<K>.json`、`hdl-blk<N>-rtl-v<K>.json`；待決定：`hdl-top-rtl-v<K>.json`、腳本產生的 `tool-top-regression-v<K>.json`。
- `<K>` 是輪次（0、1、2、3），全部方塊同步；每輪每個方塊都有檔案，沒有變動的標 `"no_change": true`。舊版不覆蓋。
- **信封（每份檔案的最前面，四欄）**：`from`（`arch`、`hdl`、`tool`）、`to`、`round`（整數，等於檔名的 K）、`block`（`blk0`…，top 用 `top`）。驗證腳本檢查信封與檔名一致。
- 值看不出來就寫 `"unknown"` 並列入該物件的 `unknown` 清單，不猜。
- 凡是陳述都附證據：行號、探測原文、規格章節，或對方的訊息 id。
- 訊息 id：架構 `a1, a2…`，HDL 問題 `q1…`、假設 `h1…`、修改 `c1…`；在同一方塊內唯一，跨輪次不重用。回覆用 `replies_to` 指向對方 id。
- 架構的訊息**不放執行指令**，只放假設、懷疑、問題、規格依據；HDL 自己決定怎麼觀察與修改。

## 1. `arch-top-model-v<K>.json`
```json
{
  "from": "arch", "to": "hdl", "round": 0, "block": "top",
  "design": {"name": "<module 名>", "spec_ref": "<規格檔與章節>"},
  "design_ports": [
    {"name": "<埠名>", "dir": "in|out", "width": 128, "kind": "pulse|level|held|data", "valid_when": "<條件或 n/a>", "clock": "<名或 none>", "edge": "rising|falling|n/a", "spec_ref": "<章節>"}
  ],
  "blocks": [
    {"id": "blk0", "name": "<方塊名>", "order": 0, "file": "arch-blk0-model-v0.json", "harness": "arch-blk0-harness-v0.json"}
  ],
  "connections": [
    {"from": "design.<埠>", "to": "blk0.<埠>", "when": "<條件或 always>"},
    {"from": "blk0.<埠>", "to": "blk1.<埠>", "when": "always"}
  ],
  "order_note": "blocks 依 order 由輸入往輸出;HDL 照此順序對齊",
  "harness": {"model_chain_result": "ALL PASS", "testbench_stimulus_ref": "<檔案與行號>", "expected_output_ref": "<檔案與行號>"},
  "status": "open"
}
```

## 2. `arch-blk<N>-model-v<K>.json`
v0：規格層級；v1 起：`elements` 細到暫存器層級（仍只依規格）。
```json
{
  "from": "arch", "to": "hdl", "round": 0, "block": "blk0",
  "name": "<方塊名>", "order": 0, "function_text": "<依規格的功能描述>", "spec_ref": "<章節>",
  "ports": {
    "inputs":  [{"name": "<埠>", "width": 128, "kind": "data", "valid_when": "<條件>", "clock": "none", "edge": "n/a", "storage": "combinational", "latency_min_cycles": 0, "latency_max_cycles": 0, "connected_to": "design.<埠>"}],
    "outputs": [{"name": "<埠>", "width": 128, "kind": "data", "valid_when": "<條件>", "clock": "none", "edge": "n/a", "storage": "combinational", "latency_min_cycles": 0, "latency_max_cycles": 0, "connected_to": "blk1.<埠>"}]
  },
  "elements": [
    {"name": "<狀態元件>", "type": "register|combinational", "width": 8, "reset_value": "<值或 n/a>", "updates_when": "<條件>", "next_value": "<規格層級的描述>", "spec_ref": "<章節>"}
  ],
  "python": {"module": "model.py", "function": "<函式名>"},
  "to_hdl": [
    {"id": "a1", "type": "answer|suggestion|hypothesis|doubt", "replies_to": "q1", "text": "<內容>", "basis": "spec|testbench|hdl_report", "refs": ["<規格章節>", "hdl-blk0-rtl-v0.json#q1"]}
  ],
  "decisions": [
    {"id": "d1", "about": "q2", "decision": "model_changed|model_kept", "reason": "<為什麼>", "basis": "spec|testbench", "refs": ["<章節或檔案行號>"]}
  ],
  "status": "open|aligned|suspect",
  "no_change": false
}
```
- `decisions`：架構對 HDL 要求改模型的回應；因規格或 testbench 拒絕時寫 `model_kept` 與依據。
- v0 的 `elements` 可為空陣列；`to_hdl` 在 v0 通常為空。

## 3. `arch-blk<N>-harness-v<K>.json`
由 top testbench 的激勵送進模型串傾印；expected 來自模型，不來自 RTL。
```json
{
  "from": "arch", "to": "hdl", "round": 0, "block": "blk0",
  "source": "top testbench stimulus -> python model chain dump",
  "end_to_end_check": "模型串的最終輸出等於 testbench 期望值",
  "steps": [
    {"step": 0, "model_condition": "<此步驟在模型時程中的條件,用模型的名詞>", "inputs": {"<埠>": "<hex>"}, "outputs": {"<埠>": "<hex>"}}
  ],
  "expected_activity": [{"step": 0, "active": true, "condition_text": "<模型時程裡何時有效>"}],
  "register_expected": []
}
```
- `register_expected`：v1 起，暫存器層級的預期值（每步驟、每個 `elements` 的值）。

## 4. `hdl-blk<N>-rtl-v<K>.json`
```json
{
  "from": "hdl", "to": "arch", "round": 0, "block": "blk0",
  "active_when": "<這個方塊有作用時成立的 RTL 條件,給 rtl blockcheck 的 --when>",
  "rtl_map": [
    {"file": "<檔名>", "lines": "83-101", "kind": "always_comb|always_ff|assign|instance", "drives": ["<訊號>"], "source": "<rtl show 的輸出行號>"}
  ],
  "ports": {
    "inputs":  [{"arch_port": "<架構埠>", "upstream": "<RTL 訊號來源>", "rtl": {"signal": "<名>", "width": 128, "kind": "data", "valid_when": "<RTL 的條件>", "clock": "none", "edge": "n/a", "storage": "combinational", "latency_min_cycles": 0, "latency_max_cycles": 0, "source": "<行號>: <原文>", "unknown": []}}],
    "outputs": [{"arch_port": "<架構埠>", "downstream": "<RTL 訊號去向>", "rtl": {"signal": "<名>", "width": 128, "kind": "data", "valid_when": "<條件>", "clock": "none", "edge": "n/a", "storage": "combinational", "latency_min_cycles": 0, "latency_max_cycles": 0, "source": "<行號>: <原文>", "unknown": []}}]
  },
  "extra_ports": [{"signal": "<名>", "width": 1, "kind": "level", "source": "<行號>: <原文>"}],
  "harness_result": {
    "function_check": {"rows": 0, "match": 0, "mismatch": 0, "raw": "<探測原文或檔案路徑>"},
    "input_check": {"rows": 0, "match": 0, "mismatch": 0, "raw": "<探測原文或檔案路徑>"}
  },
  "confidence": {"level": "high|medium|low", "reason": "<一句>"},
  "difficulty": {"level": "easy|medium|hard", "reason": "<一句>"},
  "control": {
    "assessment": "consistent|suspect|unknown",
    "items": [{"item": "<例:有效條件/時序/延遲>", "expected": "<引用架構的預期活動表>", "observed": "<探測原文>", "verdict": "consistent|suspect|unknown", "evidence": "<行號或探測>"}]
  },
  "questions": [{"id": "q1", "text": "<問題>", "refs": ["<行號>", "arch-blk0-model-v0.json#ports"]}],
  "assumptions": [{"id": "h1", "claim": "<可被推翻的說法>", "evidence": "<行號或探測原文>", "status": "open|supported|refuted|unknown"}],
  "replies": [{"replies_to": "a1", "text": "<回覆>"}],
  "rtl_changes": [
    {"id": "c1", "based_on": "a1", "file": "<檔名>", "lines": "<範圍>", "before": "<原文>", "after": "<新文>", "reason": "<為什麼>", "harness_after": {"function_check": {"match": 0, "mismatch": 0}, "input_check": {"match": 0, "mismatch": 0}}, "status": "applied|proposed|reverted"}
  ],
  "status": "aligned|open|stuck",
  "unknown": [],
  "no_change": false
}
```
- v0：`rtl_changes` 為空；HDL 只對齊與評估，不修改。
- v1 起：HDL 依架構的 `to_hdl` 自己判斷如何修正，只改該方塊自己的 RTL 行，每次修改用 `rtl replace`、立刻用方塊 harness 重驗，結果寫進 `harness_after`。

## 5. 待決定：`hdl-top-rtl-v<K>.json`
HDL 記錄「整個設計」的 RTL 事實，與 `arch-top-model` 對應。
```json
{
  "from": "hdl", "to": "arch", "round": 0, "block": "top",
  "module": "<top 模組名>",
  "ports": [{"name": "<埠>", "dir": "in|out", "width": 1, "kind": "pulse|level|held|data", "clock": "<名或 none>", "edge": "rising|falling|n/a", "reset": "<async/sync,active level>", "source": "<行號>: <原文>"}],
  "hierarchy": [{"instance": "<名>", "module": "<模組>", "source": "<行號>"}],
  "control_registers": [{"name": "<暫存器>", "width": 4, "reset_value": "<值>", "source": "<行號>: <原文>"}],
  "testbench_timeline": {"raw": "<rtl probe 原文:start 到 done 的取樣列>", "source": "<testbench 行號>"},
  "unknown": []
}
```

## 6. 腳本產生：`tool-top-regression-v<K>.json`
每輪 HDL 修改後，由腳本（orchestrator 啟動）跑 top testbench（`rtl sim`）與官方 harness，產出給架構讀的結果；架構判讀並決定是否繼續。
```json
{
  "from": "tool", "to": "arch", "round": 1, "block": "top",
  "testbench": {"result": "PASS|FAIL", "pass": 0, "fail": 2, "expected": "<hex>", "observed": "<hex>"},
  "official_harness": {"result": "pass|fail|not_run", "detail": "<原文>"},
  "design_changes_since_previous": [{"block": "blk0", "change_ids": ["c1"]}]
}
```

## 7. 形式檢查（orchestrator 的腳本，不做技術判斷）
信封四欄與檔名一致、JSON 合法、必填欄位齊全、無 `TODO`、訊息 id 唯一、`replies_to` 指向存在的 id、每個陳述附證據欄位、`kind`、`edge`、`storage`、`level` 等的取值在允許清單內。

## 8. 已決定事項（2026-10-18）
- 信封四欄：`from`、`to`、`round`、`block`。
- 模型回歸由架構負責（模型串仍通過 testbench harness，才能發新版模型）；RTL 回歸由 HDL 跑（重跑 top testbench，`flow/rtl_regression.py`）；只有 testbench 通過才跑官方測試（orchestrator，`flow/official_test.sh`）。
- `hdl-top-rtl-v<K>.json` 納入流程。
- HDL 決定怎麼修 RTL；架構依規格與 testbench 決定是否改模型，可以拒絕（`decisions` 的 `model_kept`）。架構只提出假設與懷疑，不給執行指令。
- 輪數上限 v0 到 v3；評估階段由 Codex 獨立 session 擔任 HDL，快速幾輪看流程是否帶來好處。
