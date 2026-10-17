# Session 保存與 Context 預算規則草案

沿用容器外掛載架構。Claude 為每張工單選 new 或 resume；Python 按指示啟動與保存。預算帳由 Claude 在停點彙總。

## 容器外保存

Session 的聊天與恢復所需資料保存在本 run 的容器外目錄，掛載到容器內既有位置。交付、原始證據、執行紀錄、決策日誌與 budget 帳同樣持久保存。實際路徑、Qwen Code 版本與恢復命令依既有架構核對，不靠資料夾名稱判斷。

Image、container、session 分開記錄。沿用或重啟 container 不等於續用對話；掛載聊天檔也不自動恢復。Resume 需要可驗證的 session ID 與相符的資料目錄。

## 新開或續用

「續用」有兩層，現況不同：

| 層 | 現況 |
|---|---|
| Run 層：container、state 目錄、設計檔 | 已有。`run_orders.py --resume RUN` 恢復，沿用 state 與 `digest_block` |
| 模型對話層：恢復上一段 Qwen Code 聊天 | Qwen Code 0.25.0 支援，已驗證（見下）；`run_orders.py` 尚未接入，目前每個 conversation 從 `case_N.md` 新啟動 |

試走預設：**每張工單新開 conversation**，延續性靠 state、digest 與交接檔。

### 已驗證的 session 恢復（2026-10-13）

- 指令：`qwen --resume <session ID>`；另有 `--continue`、`--session-id`、`--fork-session`。需 chat recording 開啟（現行設定已有紀錄）。
- ID：每個 conversation 的 stream-json 輸出帶 `session_id`。
- 紀錄：`<state>/qwen-home/.qwen/projects/-code/chats/<ID>.jsonl`，在掛載到容器 `/tmp` 的 state 目錄內，容器重建後仍在。
- 測試：複製 a1r1 的 A1.2 session，在臨時容器恢復並詢問先前工單內容，回答正確，session ID 不變，聊天檔在副本中追加；原 run 目錄未改。
- 條件：需設定 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 環境變數（`run_orders.py` 已設），只傳命令列旗標會報 no auth type。
- 成本：恢復時重送整段歷史，快取冷啟動時全量重算（A1.2 約 36k tokens，47 秒）。
- 尚未做：`run_orders.py` 傳 `--resume ID` 的選項；接入需程式改動與使用者同意。接入前下表不適用：

| 情況 | 接入後的預設 | 記錄 |
|---|---|---|
| 同角色、同一工作、補查證據、context 未超標 | resume | 原 ID、延續範圍 |
| context 超過水位但歷史主要是舊 tool 結果 | 先清舊 tool 結果再 resume | 清除前後用量 |
| 換角色或獨立技術審查 | new | 交接與證據 |
| 不同工作、資料版本已改、context 超標且清理無效 | new | 必要成果與當前版本 |
| 恢復失敗或資料缺漏 | 回報使用者 | 原始錯誤 |

新開不代表檔案或自動記憶已隔離。

## Context 水位

暫定：worker 用量超過有效 context（65,536）的 60% 時，不再延續同一對話。

用量來源：`<state>/qwen-home/.qwen/usage/token-usage-YYYY-MM.jsonl`，每次請求一筆，含 `sessionId`、`inputTokens`、`outputTokens`、`cachedTokens`、`thoughtsTokens`、`apiDurationMs`。某 session 最後一筆的 `inputTokens` 即其當前 context 大小。`usage_record.jsonl` 是每 session 的彙總（請求數、工具呼叫數、耗時）。stream-json 的 `result.usage` 是整個 session 的累計，不是 context 大小，不可用於水位。

校正依據：a1r1 五個 conversation 結束時的 context 為 35,551／53,107／60,774／60,476／79,982（占 54%／81%／93%／92%／122%），多數已超過 60%。因此 60% 作為門檻時，多數工單結束後都不再延續；這個值是試走起點，是否調高或改用「剩餘餘量」判斷，由使用者在停點決定。

## 交接與 context 內容

新 session 只載入本張工單、角色規則、對應 skill、指定來源與交接檔，不注入完整前段聊天或 reasoning。Resume 保留既有對話，再加新工單，並如實記錄保留歷史的影響。

資料只作參考，不增加授權。假設與實測事實分開標記。每個 run 的聊天、記憶與輸出分開保存；核對自動記憶與檢索設定，避免跨 run 讀到其他答案。隱藏測試、golden RTL 與助手修法不提供給受測模型。

大量 log 保存原文，提供當前判斷所需片段與索引；錯誤原文、expected／observed、刺激、時間、命令與版本保持可追溯。

發生 auto-compaction、截斷或 context shift 時，記錄事件與可取得的前後用量，由 Claude 判斷能否繼續。關閉壓縮不保證不溢位。

## Budget

| 類別 | 責任 |
|---|---|
| 授權範圍、總時間、呼叫、修繕輪次 | 使用者指定；Claude 在範圍內管理 |
| 本張時間與交付餘量 | Claude 分配；Python 執行 timeout |
| Thinking、生成上限、有效 context | 依實際 client／adapter／後端；保存生效值 |
| 用量與停止原因 | Python 保存；未知標 unknown |
| Budget 帳 | Claude 在停點彙總；來源 `conv_N.done`、`finished.json`、`usage_record.jsonl`、`token-usage-*.jsonl` |

Effort、thinking tokens、輸出上限與 timeout 分開記錄；傳出的參數不假定已生效。本地 context 沿用 65,536。共用本機模型時，避免其他生成干擾計時。

### Budget 帳

名稱與 rtl 工具的假設／事實登錄（assumption ledger）區分，後者不是預算。

目前工具沒有預算累計。試走中由 Claude 在每個停點彙總一筆，寫入決策日誌：累計時間、worker conversation 次數、修繕輪次、剩餘。來源是 `conv_N.done` 的秒數與結束原因、`finished.json`、`usage_record.jsonl` 與 `token-usage-*.jsonl`。取不到的欄位標 unknown。派工前讀最新一筆，停點報告引用。

## Budget 不足的判定

Timeout、token 上限與 worker 要求更多時間都只是線索。先核對停在哪、部分產物、資源耗用與最近操作是否增加證據。

| 觀察 | 判斷 | 處理 |
|---|---|---|
| 持續有效產出，到上限時剩明確步驟 | 可能額度不足 | 估計剩餘；停點時向使用者建議續接 |
| 反覆推翻推測、重讀同內容、無新證據 | 推理停滯 | 縮小問題或重定義完成條件 |
| 工具卡住、API 或環境錯誤 | 執行障礙 | 保存輸入與錯誤，處理環境 |
| 缺規格、訊號、比較來源或取樣契約 | 前置不足 | 先補資料 |
| Context 太大、壓縮、反覆重讀 | context 配置 | 清理或 new 並交接 |
| 含多個可分別驗收的成果 | 粒度太大 | 按成果拆解 |
| 完整產物已保存，只差報告 | 回報中止 | 先審查，可能直接接受 |

無法核對時標原因未明，不直接加 budget。同時記錄時間、生成、context 與呼叫各項限制，不全稱為 budget 不足。Thinking token 多不等於有進展。

## 拆解與續接

- 拆解需有可保存、可驗收且能支援下一張的成果邊界；子工單寫明輸入、輸出、完成條件、依賴。已接受成果只引用。
- 工作只差一個清楚步驟時考慮補件續接；跨多個責任或可獨立驗收的成果時考慮拆解；前置缺漏先補前置。
- Resume 前核對：同角色同工作、步驟明確、輸入版本仍適用、context 可用、ID 與目錄可恢復、剩餘授權足夠。
- 只知 timeout 不知進展時，先讀部分交付與 log。
- 以上都不重置總額與輪次；續接、拆解與重試由停點決定，不自動執行。

## 試走觀察項目

每張記錄：new 或 resume 的理由、資料目錄、context 用量與壓縮事件、恢復是否成功、交接缺漏、重複讀檔、timeout、交付完整性、停點時使用者的決定。標明哪些處理需要判斷、哪些只是固定操作。試走後再決定警戒、水位、隔離檢查與計量是否固化。
