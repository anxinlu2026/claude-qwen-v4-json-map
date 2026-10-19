第 1 輪（v1）。架構已審查你的第 0 輪結果，並寫了 v1 檔案。請先重新閱讀（README 有新增的「第 1 輪起」一節）：
{EXCHANGE}/README_HDL.md

然後：
1. 讀架構的 v1：{EXCHANGE}/arch-top-model-v1.json、arch-blk0..14-model-v1.json（重點在 to_hdl 與 decisions）、arch-blk1/2/8/13-harness-v1.json。
2. 執行 python3 {REPO}/flow/next_round_hdl.py {EXCHANGE} 0 （v1 檔案我已經替你複製好了，若已存在會略過），再依 README 的規則更新 hdl-blk0..14-rtl-v1.json 與 hdl-top-rtl-v1.json。
3. 你可以修改 RTL（規則見 README）。請記錄每個修改，並在每次修改後重跑方塊 harness 與 RTL 回歸。
4. 沒有變動的方塊把 no_change 設為 true。
5. 完成後告訴使用者：改了哪些、每個方塊 harness 與回歸的結果、testbench 的目前狀態、你想問架構的問題。
工具環境與路徑與第 0 輪相同（PATH 已設定好，直接執行 rtl）。
