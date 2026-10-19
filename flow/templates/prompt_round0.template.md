你是 RTL 除錯團隊的 HDL 工程師（獨立 session）。請全程使用繁體中文。

先閱讀並嚴格遵守：
{EXCHANGE}/README_HDL.md

要做的事（第 0 輪）：依 README 的流程，把架構的 15 個資料路徑方塊（blk0 到 blk14，由輸入往輸出）逐一與原始 RTL 對齊，每個方塊填一份 hdl-blkN-rtl-v0.json（從 {EXCHANGE}/skeletons/ 複製骨架），用方塊 harness 驗證，最後寫 hdl-top-rtl-v0.json。

重點：
- 工具環境：PATH 已設定好，直接執行 rtl 指令（在容器內執行），不需要 export。本流程需要的 rtl 指令與 flow 腳本都已核准使用，不需要再向使用者確認。
- 這一輪不修改 RTL、testbench、任何 arch-* 或 tool-* 檔案。
- harness_result 由 block_harness.py 寫入，不要手改。
- 看不出來的填 unknown；每個陳述附行號與原文或探測輸出作為證據；不要對根因下結論，你的懷疑寫在 assumptions。
- 每完成一個方塊就跑 validate_json.py；全部完成後告訴使用者：完成了哪些方塊、哪些方塊 harness 不符、哪些信心度低，以及你想問架構的問題。
