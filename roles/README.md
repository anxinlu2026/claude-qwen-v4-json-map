# Claude Orchestrator 流程設計草案

版本：v1.4。日期：2026-10-13。狀態：供審閱，尚未接入執行器。

Claude 擔任 orchestrator，主導 AES 005 的工單與流程；本地 Qwen 擔任 architecture／HDL worker。沿用既有容器架構，session 資料保存於容器外並掛載回容器。每張工單完成後停點，由使用者確認再派下一張。

Python 先限縮為必要執行與保存。預算累計由 Claude 在停點彙總。AES 005 走完後，再依實際操作定義正式 runner 與 schema。

## 文件

| 文件 | 用途 | 讀者 |
|---|---|---|
| [orchestrator/agent.md](orchestrator/agent.md) | Claude 的職責、停點、審查與 session 決策 | Claude |
| [orchestrator/contracts.md](orchestrator/contracts.md) | 工單、交付與決策日誌的內容 | Claude |
| [orchestrator/context-budget.md](orchestrator/context-budget.md) | 容器外保存、new／resume、context 水位、budget 判定 | Claude |
| [architecture/agent.md](architecture/agent.md) | Qwen architecture 的角色、證據規則、比較契約欄位 | worker |
| [trial-plan.md](trial-plan.md) | AES 005 試走範圍、上限、結束條件與案例 | Claude、使用者；不給 worker |
| [trial-summary.md](trial-summary.md) | v2a1 試走總結：結果、發現、固化候選、校正與待決定 | Claude、使用者 |

這些是流程草案，沒有變更程式、skills 或測試設定。本次更新不啟動 AES 005。

## 分工

- Claude：工作分解、工單順序與指派、new／resume 決策、交付審查、停點報告。
- Architecture worker：技術假設、比較契約、技術裁決。
- HDL worker：觀測、模擬、授權的 RTL 實作。
- Python：送單、按 run 恢復、既定 timeout、保存請求回答與產物。不做技術或流程裁決，不累計預算。
- 使用者：授權範圍與預算；每張工單後的繼續、調整或終止。

## Session 與容器

Image 是環境範本，container 是執行環境，session 是模型對話。新開 session 不需重建 image；同一 container 可跑多個 session。

Session 資料、交付與證據存在容器外，沿用現有掛載。掛載只讓檔案可用，不會恢復對話。現有工具的 `--resume` 恢復的是 run（container 與 state），不是模型對話；每個 conversation 從案例檔新開。Qwen Code 本身支援 `--resume <session ID>`，已驗證可行，尚未接入工具。

## 試走方式

Claude 依前一張成果派下一張，每張後停點。範圍、上限與結束條件見 [trial-plan.md](trial-plan.md)。試走結束後整理哪些工作固化到 Python、哪些仍需 Claude 判斷，再定義 runner。

## 現有工具

repo 已有 `tools/agentic/run_orders.py`（按案例檔跑 conversation，寫 `conv_N.done`、`console.log`、`finished.json`；其「ledger」是 rtl 工具的假設／事實登錄，不是預算）與 `a1_round.py`（一次跑完 A1 五張，不含停點）。試走用 `run_orders.py --resume` 加 Claude 逐張手寫案例；`a1_round.py` 只作案例檔與形式檢查的參考。

## 設計參考

- [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)：支持最小高信號 context、按需載入、外部筆記、worker 回傳濃縮摘要。
- [Anthropic multi-agent research](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Qwen thinking](https://docs.qwencloud.com/developer-guides/text-generation/thinking)、[Ollama thinking](https://docs.ollama.com/capabilities/thinking)

文章只支持原則；context 水位、session 政策與 Python 範圍是本專案的選擇。
