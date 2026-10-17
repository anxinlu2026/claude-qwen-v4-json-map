# v4 計畫:端口對齊流程(AES_0005)

## 目標
讓本地 Qwen(HDL)與架構、orchestrator 分工,從**原始 RTL**起手,先把每個資料路徑方塊的端口接口如實記錄下來,再由架構判斷差異並用假設引導後續證明與修正。最終目標仍是修好 RTL 使其通過官方 testbench,但這一輪先驗證對齊流程本身。

## 角色與邊界
| 角色 | 做什麼 | 不做什麼 |
|---|---|---|
| 架構(獨立 Claude session) | 規格、Python 模型與 `model.json`、骨架、寫給 HDL 的工單、判讀差異、決定改模型(只依規格)或寫假設並出 PROVE 工單 | 不改 RTL 與 testbench、不跑模擬器 |
| HDL(Qwen 3.8 27B 8-bit,思考關閉) | 找出每個架構埠在 RTL 的對應訊號,如實填端口 JSON;之後執行 PROVE 工單的單一觀察與指定的單處修改 | 不比較、不判斷對錯、不追查原因、不寫假設、不改 testbench |
| 腳本 | `make_port_skeleton.py` 產生骨架、`fill_port.py` 填值並檢查取值、`port_compare.py` 列出缺少/多出/不同 | 不判斷差異的意義 |
| orchestrator(Claude) | 原樣轉發架構的工單、計時、形式檢查、看板與決策日誌、預算彙總 | 不寫工單、不裁決技術問題、不引用其他 walk 的發現 |

兩條界線:模型只能依規格或標準修改,不能為了貼合 RTL 而修改;RTL 與模型不同時,在證明有錯之前都只是假設。

## 流程
1. 架構給骨架(每個方塊的埠名與連接,不含屬性值,避免 HDL 照抄模型)。
2. HDL 填 `rtl` 欄位(signal、width、kind、valid_when、clock、edge、storage、latency、source、unknown)。
3. `port_compare.py` 列出差異。
4. 架構判斷:改模型(依規格)/ 寫假設並出 PROVE 工單 / 要求重新觀察。
5. 15 個資料路徑方塊都完成後,再進入功能對齊(c3)與證明、修正、確認。
控制邏輯暫不在架構的方塊內,留到架構證明假設時澄清。

## 分級
本流程為委派分級表最後一列 LP(見 `docs/delegation_levels.zh.md`)。之後要把工作往 Qwen 移,一次移一格,用同一批故障量時間與通過率。

## 運作規則
- 一張工單最多 3 回合,orchestrator 在回合內自行決定如何收斂;3 回合解決不了才停下來與使用者討論(`roles/orchestrator/agent.md`)。
- 每次 Qwen 測試開新 cell(`scripts/make_cell.sh`),不沿用上一個。
- 工單、文件與回覆一律繁體中文。

## 目前進度
- 環境:snapshot 內容、映像 `multi-ai/cvdp-qwen-agent:0.26.0-v4-ports`(含端口工具)。
- 試點:`pilot/`(架構套件、工具、工單檢討);cell `v4a` 正在執行架構寫的第 1 張工單(`load_block` 端口填表)。
- 待做:其餘 14 個方塊、差異判讀、PROVE 工單、功能對齊。
