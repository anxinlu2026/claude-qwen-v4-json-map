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

## 不能下的結論
- **HDL 模型不同**：先前的 Qwen 3.8 27B 流程是另一個模型，所以「流程是否更快收斂」與「HDL 模型更強」混在一起，無法只歸因於流程。要分開，需用同一個 HDL（例如 Qwen）跑同一個流程。
- **原始問題的 12 個錯誤是否都修正**：官方測試與 testbench 通過，但 blk1、blk2、blk13 的功能檢查吻合數低（3/39、0/39、2/32）卻標 aligned，blk8 仍無法執行 harness；是否只是 harness 對狀態類方塊的限制，需要架構在 v2 判斷。
- 評估只有一次運行，沒有重複。

## 建議的下一步
1. 架構做收尾審查（v2）：核對 rtl_changes 與 rtl diff、判斷 blk1/2/8/13 的 aligned 是否成立。
2. 用 Qwen 當 HDL 重跑同一流程，分離流程與模型的影響。
3. 決定是否放寬 rtl 的「一次只改一處、還原次數」關卡。
