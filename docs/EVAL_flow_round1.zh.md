# 流程評估：方塊對應流程（v5a）第 1 輪結果

HDL：使用者開的獨立 session「JSON map flow v2」（使用者說明是 Codex app；訊息層標示為 Claude Desktop session，orchestrator 無法從這端確認底層模型）。架構：獨立 Claude session。orchestrator：Claude（本 session）。設計：原始 RTL（AES_0005，12 個錯誤）。

## 時間線（2026-10-18）
| 時間 | 事件 |
|---|---|
| 17:14 | 建立 cell v5a；架構套件 v0（31 份）由模型產生，已驗證模型串能還原 testbench 明文 |
| 17:20 | HDL 開始第 0 輪 |
| 17:40 | 第 0 輪完成：15 個方塊加 top 共 16 份對應表（約 20 分鐘）；RTL 未修改 |
| 17:41–17:47 | 架構審查，產出 v1（20 份，約 5.5 分鐘）；模型回歸 ALL PASS |
| 約 18:08 | 第 1 輪提示送給 HDL（允許修改 RTL，有護欄） |
| 18:50 | rtl 的升級規則（同一驅動改 5 次還原）擋住所有 rtl 指令；HDL 用 rtl ask 報告 |
| 約 18:58 | orchestrator 答覆授權（限 blk10/blk12 自己的行） |
| 19:01 | **testbench PASS**（RUN #236，13 處修改）；19:02 官方測試 **1 passed** |
總計：從 HDL 開始（17:20）到通過 1 小時 41 分鐘，其中第 0 輪 20 分鐘、架構審查 5.5 分鐘、第 1 輪約 55 分鐘（含被關卡擋住約 8 分鐘）；解除阻擋後 3 分鐘通過。

## 結果
- 收斂輪數：v0 對齊、v1 修正，共 2 個 HDL 輪次、1 次架構審查。
- 最終 RTL：`results/v5a_round1/final_rtl_round1/`，與原始的差異：`final_rtl_round1.diff`（6 個片段）。
- HDL 的 `rtl_changes` 12 筆，工具記 13 處修改。
- orchestrator 介入：回答 1 次 rtl ask、2 次請它繼續、1 次格式與路徑修正。

## 流程帶來的好處（有證據的）
1. 第 0 輪就把問題縮小：方塊 harness 把「功能不符」與「輸入不符」分開，並由架構判讀出最大的症狀是控制（start 未被接受）和 4 組資料路徑問題（載入順序、金鑰位元組順序、ShiftRows 方向、MixColumns）。
2. 架構的判讀有依據可查（tool-check 的原始列、規格章節），沒有越權改模型：所有「改模型」要求都以規格拒絕。
3. JSON 溝通可檢查：格式檢查腳本、信封、訊息 id 讓每一輪的狀態可機械檢查。

## 問題與動態修正（詳見 runlog.md）
| 問題 | 修正 |
|---|---|
| 沒有 model_cli 的狀態類方塊無法做功能檢查 | block_harness 加依值對應的後備模式（結果欄位標明模式） |
| 起始 start 未被接受時 input check 沒有資訊 | README 加前提；HDL 自行想辦法讓 start 被接受 |
| rtl 的「同一驅動改 5 次還原」關卡擋住所有指令，次數部分來自第 0 輪被「一次只改一處」規則攔下的嘗試 | 用 rtl ask 取得授權；候選修正：在本流程放寬這兩個關卡（需使用者同意） |
| orchestrator 在共用容器上跑 rtl 指令，進入 HDL 的歷史、可能干擾 | 之後改用唯讀檢查 |
| 提示與 README 的腳本路徑變數未展開 | 送出前發現並修正 |
| HDL 把 rtl next 誤用（會等待 orchestrator） | 已記錄；本流程不使用 rtl next |

## 架構的收尾審查（v2，約 3 分鐘；以下是架構的結論，不是 orchestrator 的）
- 逐筆核對 diff：12 筆 `rtl_changes`＝10 個不同修改＋2 筆重複記錄（blk3／blk7 同一修改、blk8／blk9 同一修改）；6 個 diff 片段涵蓋全部 10 個修改，沒有「記錄找不到 diff」或「diff 片段沒被記錄」。HDL 說的「9 處」是 hdl-top 摘要把兩項合併；工具的「13 處」多出的 3 處是被還原再重做的嘗試。orchestrator 的機械核對（筆數、不同位置、diff 片段數）與此相符。
- 10 個修改都有規格或 testbench 依據；diff 中沒有針對測試向量的常數（只有 8'h1B 與 round_ff 的 0/1/11）；sbox、inv_sbox、Rcon 表靜態核對等於標準。
- blk1、blk2、blk13 標 aligned 成立（blk2 與 blk13 的低吻合數是比對對象選錯，不採用）；blk8 aligned 但為間接證據。
- 結論：可以結案。仍有疑慮（不阻擋）：重置後以 i_update_key=0 開始時 round_ff 會停在 1（規格未定義）；金鑰展開只重跑 steps[2]；blk8 證據為間接。
- 對流程的觀察：結果不能歸功於 JSON 流程（HDL 換成更強的模型）；需要同一個 HDL 的對照才能分離。架構的貢獻：以規格與 testbench 裁決 model_kept、指出 start 未被接受是最上游症狀、裁定切點平移不是缺陷；xtimes 歸約與 MixColumns 求值順序兩項是 HDL 用 blockcheck 找到的。

## 不能下的結論
- **HDL 模型不同**：先前的 Qwen 3.8 27B 流程是另一個模型，所以「流程是否更快收斂」與「HDL 模型更強」混在一起，無法只歸因於流程。要分開，需用同一個 HDL（例如 Qwen）跑同一個流程。
- **原始問題的 12 個錯誤是否都修正**：官方測試與 testbench 通過，但 blk1、blk2、blk13 的功能檢查吻合數低（3/39、0/39、2/32）卻標 aligned，blk8 仍無法執行 harness；是否只是 harness 對狀態類方塊的限制，需要架構在 v2 判斷。
- 評估只有一次運行，沒有重複。

## 建議的下一步
1. 架構做收尾審查（v2）：核對 rtl_changes 與 rtl diff、判斷 blk1/2/8/13 的 aligned 是否成立。
2. 用 Qwen 當 HDL 重跑同一流程，分離流程與模型的影響。
3. 決定是否放寬 rtl 的「一次只改一處、還原次數」關卡。

## 追問統計（orchestrator 從檔案與工具記錄整理；分類是 orchestrator 對檔案的解讀）
### 輪次與介面
- HDL 兩輪（v0、v1）；架構三次（v0 由模型產生、v1 審查、v2 收尾審查）。沒有 HDL 的 v2；v2 之後沒有正式重新對齊。編輯過的方塊在第 1 輪內由方塊 harness 重新驗證（例：blk3 2/26→39/39、blk10 0/23→20/20、blk12 0/32→32/32）。
- 15 個方塊的 ports 在 v0→v1→v2 全部沒有改（沒有把介面往外或往內重新切）；v1 只加 elements（暫存器層級）。有切點或對應問題的四個方塊（blk1 切點平移、blk2 對應到整個 expanded_key、blk8 無獨立訊號、blk13 無三選一多工）採「對應表或不採用」處理，沒有重切。
### 誰先發現（11 個修改項、10 個位置）
- HDL 在 v0（未改 RTL、架構尚未回饋）就提出 8 項：載入轉置、round_ff 待機自走、key_done bit10 不會為 1、step_key 字序、金鑰位元組序、ShiftRows 方向、MixColumns 係數、round 1 多了 InvMixColumns。
- HDL 在 v1 自己找到 3 項：key 等待期間資料暫存器被覆寫、xtimes 歸約看錯級、MixColumns 在迴圈內讀到尚未賦值的元素（後兩項用 blockcheck 的 xor 型態找到，架構自述沒預期到）。
- 架構首次提出：0 項。架構的貢獻：以原始列確認（blk3/7 字 0/2 互換、blk10 方向）、以規格與 testbench 裁決 model_kept、指出 start 未被接受是最上游症狀。
### 工具使用（HDL 期間 344 筆 rtl 呼叫；已排除約 6 筆 orchestrator 的呼叫）
| 指令 | 次數 | 備註 |
|---|---|---|
| blockcheck | 213 | 含方塊 harness 腳本自動呼叫的；第 0 輪 170、第 1 輪 43 |
| probe | 43 | |
| replace | 26 | 13 次成功、13 次被工具關卡 STOP |
| show / mark / sim / signals / status / diff / revert / ask / next / history | 19 / 11 / 9 / 6 / 5 / 5 / 3 / 2 / 1 / 1 | |
- 除錯主要靠方塊層級比對（blockcheck 約占 62%）；rtl sim 只有 9 次，多用於修改後確認 testbench；第一次成功修改 18:49，testbench 通過 19:01（12 分鐘後）。
- 技能與流程腳本（block_harness、validate_json、rtl_regression）的使用次數沒有被記錄，unknown；只能從輸出檔推得 tool-blk*-check 各 14 份（v0、v1）與 tool-top-regression-v1 一份。
