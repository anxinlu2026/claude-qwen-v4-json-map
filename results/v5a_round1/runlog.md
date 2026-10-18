# 運行記錄（orchestrator）：方塊對應流程評估，cell v5a

目的：評估「架構骨架 + 方塊 harness + HDL 對應表（JSON 溝通）」能不能快速收斂並修好 bug。HDL 由獨立的 Codex session 擔任（使用者在 Codex app 開 session），架構是獨立的 Claude session。
規則：問題與動態修正當下就記一筆；每輪結束寫摘要；收斂指標＝每輪的 RTL 回歸（testbench 失敗程度）與各方塊 harness 吻合數。

## 問題與修正追蹤
| 時間 | 問題 | 原因 | 修正 | 狀態 |
|---|---|---|---|---|
| 10-18 | 先前流程中 `rtl next` 等待回覆被 120 秒逾時打斷 | Qwen Code 的 shell 逾時，orchestrator 未即時回覆 | 本流程不用 `rtl next`，以 JSON 檔溝通 | 已避開 |
| 10-18 | 工單曾要求不存在的 `rtl assumption` | 技能文件與這版 rtl 不一致 | 假設改寫在 JSON 的 `assumptions` | 已避開 |
| 10-18 | 以 Python 腳本放在 /tmp/pilot 被 rtl 的「程式檔在模型資料夾外」規則擋住 | 該規則把任何 .py 當 HDL 自己寫的程式 | 流程腳本放在 repo 的 flow/，不放進容器的 /tmp | 已避開 |
| 10-18 | 方塊 harness 的正確性無法證明 | 沒有參考 | 在參考解 RTL 上跑同一張對應表：功能 18/18 吻合、輸入 9/9；原始 RTL 上全部不符 | 已驗證（inv_mix_columns） |

## 事件
- 10-18 建立 cell v5a：原始 RTL，容器 orders_v5a，架構套件 v0（31 個檔案）由 flow/make_arch_package.py 從架構模型產生，產生時已驗證模型串能還原 testbench 的明文；格式檢查 0 問題。
- 10-18 工具驗證：block_harness.py（參考解 vs 原始 RTL）、validate_json.py、rtl_regression.py（參考解 PASS、原始 RTL FAIL）、official_test.sh（原始 RTL FAIL）。
- 10-18 17:20 Codex 獨立 HDL session（使用者命名「JSON map flow v3」）開始第 0 輪：從 rtl 歷史看到它依序執行 `rtl sim`、`rtl signals key_exp`、`rtl signals current_data_ff`、`rtl blockcheck --help`、`rtl probe`、`rtl signals`。尚無 hdl-*.json 產出（17:21 時）。
- 10-18 17:24 看板加入「Block map flow」區塊（由 exchange/ 檔案自動推得：每個方塊的 hdl 版本、TODO 數、harness 吻合數、信心度/難度/控制、問題與假設數、回歸結果、runlog）；網址 http://127.0.0.1:8767/?run=orders-cvdp_agentic_AES_encryption_decryption_0005-qwen8-qc-v5a-20261018
- 10-18 17:40 第 0 輪 HDL（Codex）完成：hdl-blk0..14-rtl-v0.json 與 hdl-top-rtl-v0.json 共 16 份，約 20 分鐘；無 TODO。orchestrator 檢查：格式 0 問題；RTL 4 個檔案與原始相同（0 edit）；arch-* 31 個檔案未被改（重新產生比對）；harness_result 與 tool-blk*-check 一致；缺口：blk8 沒有 tool 檢查檔（Codex 沒跑成或沒跑，原因待查，不由 orchestrator 判斷）。已交給架構審查，要求產出 v1。
- 10-18 17:45 架構完成 v1：arch-top-model-v1、arch-blk0..14-model-v1、arch-blk1/2/8/13-harness-v1（20 份）；orchestrator 檢查：格式 0 問題、v0 未被改、RTL 未被改、模型回歸我重跑 harness_check ALL PASS。耗時約 5.5 分鐘。
- 10-18 17:50 架構對流程的觀察與動態修正：
  | 問題 | 修正 | 狀態 |
  |---|---|---|
  | 沒有 model_cli 的狀態類方塊（blk1、2、8、13）無法做功能檢查 | block_harness.py 加「依值對應」後備模式：RTL 列的輸入以值對應 harness 步驟，輸出比對；結果標 function_check_mode（修正後 JSON 與畫面一致，並在參考解上重驗 inv_mix_columns 仍 18/18） | 已修 |
  | tool-check 的 raw 欄太長 | 加 mismatch_rows_compact（只列不符的列，最多 8 列） | 已修 |
  | start 未被接受時，input check 全部 0 吻合，沒有資訊 | README_HDL 加「前提」：HDL 先想辦法讓一次被接受的 start 出現，並在方塊檔註明輸入是否來自被接受的 start | 已寫入說明；效果待第 1 輪觀察 |
  | harness 步驟與 RTL 拍數不同時不能依順序對應 | 後備模式已改為依值對應；依順序的 input check 仍保留 | 部分 |
  | blk8 沒有獨立訊號，Codex 沒有跑出工具檢查檔 | 未修；交架構與 HDL 在 v1 處理（架構已在 to_hdl 提問） | 待觀察 |
- 10-18 17:55 已準備第 1 輪 HDL：hdl-*-rtl-v1.json 16 份由 v0 複製（flow/next_round_hdl.py）、README_HDL 加「第 1 輪起」一節（允許修改 RTL，附護欄）、flow/codex_prompt_round1.md。等使用者把提示貼進 Codex session。
- 10-18 18:05 發現並修正：README_HDL 的「第 1 輪起」一節與 codex_prompt_round1.md 中的腳本路徑因變數未展開而錯成 /flow/…（orchestrator 的疏失；已修正，送出前發現）。
- 10-18 18:10 第 1 輪提示已用 SendMessage 送到 session「JSON map flow v2」（使用者說它就是 Codex app 的 HDL session；訊息層把它標成 Claude Desktop session，orchestrator 無法從這端確認底層模型，已請使用者確認）。訂閱閒置通知。
- 10-18 18:55 HDL session 第 1 輪第一個回合結束（停在「Next: blk12」，未完成）。orchestrator 檢查：RTL 相對原始 6 處修改（aes128_decrypt.sv、aes128_key_expansion.sv；rtl 檢查點 c2–c9）；arch-v0/v1 檔案未被動；hdl-*-v1 無 TODO；多數方塊已有 applied 的 rtl_changes，blk10/12/1 為 proposed；testbench 最近一次 FAIL(2F/0P)；沒有 tool-top-regression-v1.json（HDL 用 rtl sim，未用回歸腳本）。已請它繼續做完並跑回歸腳本；不由 orchestrator 判斷修改是否正確。
- 10-18 18:58 摩擦點：rtl 工具的升級規則（同一驅動改 5 次都還原 → STOP，要求 rtl ask）擋住 HDL 的所有 rtl 指令（probe、sim、replace）；次數有一部分來自第 0 輪被「一次只改一處」規則攔下的嘗試。HDL 已用 rtl ask 說明比較與需求（request_1.md）。orchestrator 答覆授權（answer_1.md）：可編輯 decypher_logic 126–175 行，限 blk10/blk12，條件為每次修改後跑方塊 harness 與 RTL 回歸並記錄。答覆讓工具重設嘗試次數。
  候選的流程修正（需使用者同意，因為是工具/規則變更）：在本流程放寬「一次只改一處、還原次數」關卡，因為方塊 harness 與回歸已經守護每次修改。
- 10-18 18:58 注意：orchestrator 在 HDL 工作期間自己跑 rtl sim/status/diff 會進入共用的歷史與狀態，並可能干擾；之後改用唯讀方式（讀 history.jsonl、state.json、主機上的 RTL 檔）檢查，不在共用容器執行 rtl 指令。
- 10-18 19:01 **目標達成**：HDL 第 1 輪，testbench PASS（RUN #236，0 FAIL / 2 PASS，13 處修改），19:02 orchestrator 以獨立容器跑官方測試（cocotb）：1 passed。最終 RTL 存於 final_rtl_round1/，與原始的 diff 存於 final_rtl_round1.diff。
- 10-18 19:03 一致性檢查：hdl-*-v1 16 份格式 0 問題；arch-v0/v1 未被動；rtl_changes 共 12 筆，工具記 13 處修改（交架構核對）；blk1（3/39）、blk2（0/39）、blk13（2/32）標 aligned 但功能檢查吻合數低（由架構判斷，可能是「依值對應」模式對狀態類方塊的限制）；blk8 仍無法執行 harness；blk4–6 no_change 但狀態仍 open。
