WORK ORDER pilot1clk - TYPE: ALIGN-CLOCK
目標:描述 RTL 的時脈:有幾個時脈、哪些暫存器用哪個時脈與哪個邊緣、有沒有其他時序來源(例如閂鎖、非同步路徑)。這張工單不找錯誤。

輸入(機器上已經有):
  - /tmp/pilot/rtl_structure.json:用工具(yosys)從 RTL 抽出的結構(模組、埠、暫存器與其時脈與 reset、訊號與其依賴)。陣列已合併(例如 current_data_ff[0][0] 到 [3][3] 是一個形狀 [4,4] 的訊號)。用它找 RTL 訊號,事實(方向、寬度、時脈、reset)從這裡複製。
  - /tmp/pilot/blocks_abstract.json:架構給的方塊清單,每個方塊只有名稱和抽象的功能說明。
  - RTL(rtl show 檔案 起 迄、rtl signals)、testbench(verif/tb_aes128_dec.sv)、模擬器(rtl sim、rtl probe)。時間上的行為看不出來時,可以在模擬中觀察。

輸出:/tmp/deliveries/clock.json,合法 JSON。
**第一個動作**:建立這個骨架檔:
{
 "clocks": [
  {
   "name": "TODO",
   "edge": "TODO",
   "period_in_testbench": "TODO",
   "registers": [
    "TODO"
   ],
   "evidence": "TODO"
  }
 ],
 "other_timing_sources": "TODO",
 "assumptions": []
}

說明:registers 列出用這個時脈的暫存器名稱(從 rtl_structure.json 的 registers 複製,陣列用合併後的名稱);period_in_testbench 從 testbench 取得;other_timing_sources 寫有沒有不是用時脈邊緣的記憶或延遲(沒有就寫 none 並說明依據)。

假設編號從 H6 開始。
規則:
  - 你的工作是描述 RTL 實際做什麼,不是判斷它對不對。細節(位元組順序、索引、週期)只能從 RTL 陳述式的索引運算式、testbench 或探測得到,並把依據的行連同行號複製過來;不能從名稱或註解推。
  - 有疑問、看不出來、或只靠讀程式推測的地方,一律記成假設(格式 {"id":"H?","subject":"...","statement":"...","source":"rtl|testbench|probe","status":"open"}),不要把猜測寫成事實。
  - 工作規則:第一個動作是用 shell 建立輸出檔(骨架如下,複製),之後邊讀邊把整個檔案重寫,保持合法 JSON;回報前 python3 -m json.tool 要通過,grep -n TODO 要沒有輸出。
  - 不要改設計。用 rtl next 回報(格式固定):rtl next "skill step used: ... / found: ... / evidence: 檔案與指令 / unsure: ..."
