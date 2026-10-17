# AES 005 試走計畫

版本：v0.1。日期：2026-10-13。狀態：已執行（2026-10-13，run v2a1），總結見 [trial-summary.md](trial-summary.md)。只給 Claude 與使用者，不載入 worker。

## 範圍

| 項目 | 內容 |
|---|---|
| 題目與階段 | AES 005，只走 A1 基線：A1.1–A1.5；原 A1.6 機械閘門改為 Claude 審查 |
| 不在範圍 | 修繕輪次、A2 以後階段、修改 RTL／TB／golden |
| 模型與環境 | 沿用 a1r1：`qwen3.8:27b-nvfp4`、image `multi-ai/cvdp-qwen-agent:0.25.0-rtl25`、context 65,536；不換模型 |
| 單張上限 | 900 秒 |
| 總上限 | 最多 7 次 worker conversation，合計不超過 6,300 秒；多出的 2 次只用於補件或 A1.1 重做 |
| 修繕輪次 | 0 |
| 停點 | 每張工單完成後停，等使用者確認 |
| 結束條件 | A1.1–A1.5 經 Claude 審查接受；或在某停點由使用者終止 |
| 對照基準 | a1r1 的五份交付與用時（A1.1 於 904 秒 timeout，其餘 195–516 秒完成）|

## 做法

- 以 `run_orders.py` 建立 run，之後每張工單由 Claude 寫 `control/case_N.md`，用 `--resume` 啟動；每張後停點。
- 預設每張新開 conversation。Qwen Code 的 session 恢復已驗證可行，但 `run_orders.py` 未接入，不在本次範圍，除非使用者在停點同意接入。
- Budget 帳由 Claude 在停點彙總，來源 `conv_N.done`、`finished.json`、`usage_record.jsonl`、`token-usage-*.jsonl`。
- 形式檢查沿用原閘門三項：輸出檔存在、段落齊全、無 TODO。

## 觀察項目

見 [orchestrator/context-budget.md](orchestrator/context-budget.md)「試走觀察項目」，並加記每個停點使用者的決定，以及每張結束時的 context 用量（`token-usage-*.jsonl` 該 session 最後一筆 `inputTokens`）。

## 試走後產出

- 哪些操作是固定的，可固化到 Python。
- 哪些仍需 Claude 判斷。
- Budget 帳、60% 水位、交接檔是否足用；Qwen Code session 恢復是否值得接入。
- 正式 runner 與 schema 的需求清單。

## 後續階段的案例（暫存）

A1 之後若進入定位階段，可用「C1 更新金鑰後，解密所用展開金鑰是否對應 FIPS 197 App A.1」作為比較契約的第一個案例。這僅是候選觀測，不表示 key expansion 已被認定出錯。

保存來源：`records/a1_round_a1r1/` 的 A1.1、A1.3、A1.4。重用前核對輸入版本。

| 項目 | 內容 |
|---|---|
| 輸入 | C1：key `2b7e151628aed2a6abf7158809cf4f3c`；ciphertext `3925841d02dc09fbdc118597196a0b32`；控制與 start 序列沿用指定 TB 版本 |
| 參考 | FIPS 197 App A.1；既有模型 roundkeys 與標準 44/44 words match，只適用該算例 |
| 注意 | 該模型與驗證由受測 Qwen 在 A1.4 自行產生，不能當獨立 golden，需另行獨立驗證 |
| Word 表示 | W[i] 的 byte 0 在最左；round key r = W[4r..4r+3] 串接 |
| RTL 訊號、事件、轉換 | 由 architecture 從當前 RTL 與事件證據填入，不猜階層名稱或 cycle |
| match | 該算例、該事件的金鑰值吻合；不證明 C2 或整體解密正確 |
| mismatch | 契約成立時顯示該邊界偏離；仍需區分生成、保存、選取或消費時序 |
| inconclusive | 資料未有效、X／Z、無法讀取、事件不明、表示法未定或版本不符 |

## 判斷範例（假設情境，10 分鐘為示例上限，非授權）

| 到上限時的成果或障礙 | 流程建議（停點時向使用者提出） | Session |
|---|---|---|
| 已選邊界並定義表示法，只差訊號全名 | 補完指定缺項 | 新開並附交接檔（resume 接入前）；先核對版本 |
| RTL 結構與模型介面都未整理完 | 拆成兩份交付，再做配對 | 換角色 new |
| 一直猜哪個階段錯，沒有比較契約 | 縮小為一個可觀測邊界 | context 污染則 new |
| 工具讀不到指定訊號 | 先處理可觀測性 | 保存原錯誤 |
| 計畫已完整保存但回報前 timeout | 審查文件，滿足條件即接受 | 不重跑 |
| 持續進展但剩餘總額不足 | 保存部分成果，報告缺口 | 停止，等授權調整 |
