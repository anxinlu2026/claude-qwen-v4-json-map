# Review Summary：方塊對應流程（v5a）第 1 輪

範圍：原始 RTL（AES_0005），HDL 為使用者開的獨立 session「JSON map flow v2」（使用者說明是 Codex app；訊息層標示為 Claude Desktop session，orchestrator 無法從這端確認底層模型），架構為獨立 Claude session，orchestrator 為 Claude。
結果：testbench PASS（19:01，RUN #236）、官方測試（cocotb）1 passed（19:02）；架構收尾審查（v2）結論為可以結案。
資料來源：`results/v5a_round1/`（exchange 檔案、最終 RTL、diff、runlog）；統計表另見 `EVAL_flow_round1.zh.md`。以下答案來自檔案與工具記錄；歸類（誰先發現）是 orchestrator 對檔案的解讀。

## 1. 這次對齊一共跑了幾個輪迴？是到 v2？之後沒再重新對齊？
- HDL 兩輪（v0、v1）；架構三次（v0 由模型產生、v1 審查、v2 收尾審查）。沒有 HDL 的 v2。
- v2 之後沒有正式重新對齊。但被修改過的方塊在第 1 輪內都由方塊 harness 重新驗證，例如 blk3 從 2/26 到 39/39、blk10 從 0/23 到 20/20、blk12 從 0/32 到 32/32。

## 2. 有沒有發生方塊的介面往外或往內重新推？
- **沒有。** 15 個方塊的 `ports` 在 v0 到 v2 全部沒改，v1 只加了暫存器層級的 `elements`。
- 有四個方塊的介面對應有問題，架構都用「對應表或不採用」處理，沒有重切：
  - blk1：切點平移（架構給了 `register_mapping`）。
  - blk2：HDL 把它對應到整個 `expanded_key`，比對對象選錯，不採用。
  - blk8：沒有獨立訊號，harness 跑不了（間接證據）。
  - blk13：RTL 沒有三選一多工，比對不採用。

## 3. HDL 做介面定位，內部訊號可以對比，得到好處嗎？有實例嗎？
有。比較的是 RTL 自己的方塊輸入，所以上游錯也不會遮住下游。實例：
- blk3／blk7：key 的字 0 與字 2 互換，用內部訊號比對看出來（2/26 吻合，修後 39/39）。
- blk10：ShiftRows 方向，從原始列直接看出（修後 32 列全吻合）。
- blk12：用 `xtimes02` 對 `xtimes04` 的比對定位到子運算的錯（12 列只有 7 列吻合）；MixColumns 只剩 column 0 到 2 不符，因而發現「迴圈內讀到尚未賦值的元素」。
限制：blk1、2、8、13（狀態與選擇類）的比對不可用；start 沒被接受時，輸入檢查沒有資訊。

## 4. 這次修改，HDL 自己發現的比例高嗎？
11 個修改項（10 個位置）：**HDL 首次提出 11 項，架構 0 項。**
- HDL 在 v0（沒改 RTL、架構尚未回饋）就提出 8 項：載入轉置、round_ff 待機自走、key_done bit10 不會為 1、step_key 字序、金鑰位元組序、ShiftRows 方向、MixColumns 係數、round 1 多了 InvMixColumns。
- HDL 在 v1 自己找到 3 項：key 等待期間資料暫存器被覆寫、xtimes 歸約看錯級、MixColumns 的求值順序（後兩項用 blockcheck 的 xor 型態找到，架構自述沒預期到）。
- 架構的貢獻：用原始列確認（blk3／blk7 字 0／2 互換、blk10 方向）、以規格與 testbench 裁決 `model_kept`、指出「start 未被接受」是最上游的症狀。
- 注意：HDL 有規格導出的模型與 harness，且這個 HDL 比先前的 Qwen 強，不能全歸功於流程。

## 5. 除錯用的是 rtl sim，還是方塊 harness 的 stimulus 與 expected？工具與技能使用次數
HDL 期間 344 筆 `rtl` 呼叫（已排除約 6 筆 orchestrator 的）：
| 指令 | 次數 | 備註 |
|---|---|---|
| blockcheck | 213 | 約 62%；含方塊 harness 腳本自動呼叫的；第 0 輪 170、第 1 輪 43 |
| probe | 43 | |
| replace | 26 | 13 次成功、13 次被工具關卡 STOP |
| show / mark / sim / signals / status / diff / revert / ask / next / history | 19 / 11 / 9 / 6 / 5 / 5 / 3 / 2 / 1 / 1 | |
- 主要靠方塊層級比對；`rtl sim` 只有 9 次，多用於修改後確認 testbench。第一次成功修改 18:49，testbench 通過 19:01（12 分鐘後）。
- 技能與流程腳本（block_harness、validate_json、rtl_regression）的使用次數沒有被記錄：unknown；只能從輸出檔推得 `tool-blk*-check` 各 14 份（v0、v1）與 `tool-top-regression-v1` 一份。

## 6. 經過這次，需要更新 agent.md、技能、工具嗎？（建議，尚未實作，待使用者確認）
| 類別 | 建議 |
|---|---|
| orchestrator 的 `agent.md` | 加這個流程的章節：JSON 溝通、輪次 v0 到 v3、`rtl ask` 要及時答覆、不在共用容器執行 `rtl`、testbench 通過後才跑官方測試、運行記錄格式 |
| HDL 的 `agent.md` | 加「方塊對應流程」職責：填對應表、用 harness、記 `rtl_changes`、start 被接受的前提、不用 `rtl next` |
| 架構的 `agent.md` | 加輪次審查職責、`model_kept` 規則、只依規格細化、收尾審查的修改分類（規格要求、等價重寫、繞過） |
| 技能 | 新增「方塊對應對齊」技能；修正技能文件裡不存在的 `rtl assumption` |
| 工具 | ① 放寬「一次只改一處、還原次數」關卡 ② 由 diff 自動產生修改清單與計數 ③ harness 支援狀態類方塊的對應表 ④ 記錄技能與腳本的使用次數 ⑤ 自動回答 `rtl ask` 的監看程序 ⑥ 看板顯示 `rtl_changes` 與工具使用 |
建議優先：工具 ①②④（直接影響評估的可重複性）。

## 不能下的結論
- 流程與模型的影響混在一起（HDL 換成更強的模型）；要分離需要同一個 HDL 的對照（例如 Qwen 走同一個流程）。
- 只有一次運行，沒有重複。
- blk8 的證據是間接的；重置後以 `i_update_key=0` 開始時 `round_ff` 會停在 1（規格未定義，不影響 testbench 與官方測試）。
