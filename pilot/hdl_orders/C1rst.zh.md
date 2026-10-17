WORK ORDER pilot1rst - TYPE: ALIGN-RESET
目標:描述 RTL 的 reset:類型(同步或非同步)、準位、哪些暫存器有 reset、reset 的值、哪些暫存器沒有 reset。這張工單不找錯誤。

輸入(機器上已經有):
  - /tmp/pilot/rtl_structure.json:用工具(yosys)從 RTL 抽出的結構(模組、埠、暫存器與其時脈與 reset、訊號與其依賴)。陣列已合併(例如 current_data_ff[0][0] 到 [3][3] 是一個形狀 [4,4] 的訊號)。用它找 RTL 訊號,事實(方向、寬度、時脈、reset)從這裡複製。
  - /tmp/pilot/blocks_abstract.json:架構給的方塊清單,每個方塊只有名稱和抽象的功能說明。
  - RTL(rtl show 檔案 起 迄、rtl signals)、testbench(verif/tb_aes128_dec.sv)、模擬器(rtl sim、rtl probe)。時間上的行為看不出來時,可以在模擬中觀察。

輸出:/tmp/deliveries/reset.json,合法 JSON。
**第一個動作**:建立這個骨架檔:
{
 "reset": {
  "name": "TODO",
  "type": "TODO",
  "level": "TODO",
  "evidence": "TODO"
 },
 "registers_with_reset": [
  {
   "register": "TODO",
   "value": "TODO",
   "lines": "TODO"
  }
 ],
 "registers_without_reset": [
  {
   "register": "TODO",
   "note": "TODO"
  }
 ],
 "reset_in_testbench": "TODO",
 "assumptions": []
}

說明:registers_with_reset 與 registers_without_reset 要涵蓋 rtl_structure.json 中所有模組的所有暫存器(含 key 展開模組);reset 值從 RTL 的 reset 分支複製行號;reset_in_testbench 寫 testbench 怎麼施加 reset(行號)。

假設編號從 H8 開始。
規則:
  - 你的工作是描述 RTL 實際做什麼,不是判斷它對不對。細節(位元組順序、索引、週期)只能從 RTL 陳述式的索引運算式、testbench 或探測得到,並把依據的行連同行號複製過來;不能從名稱或註解推。
  - 有疑問、看不出來、或只靠讀程式推測的地方,一律記成假設(格式 {"id":"H?","subject":"...","statement":"...","source":"rtl|testbench|probe","status":"open"}),不要把猜測寫成事實。
  - 工作規則:第一個動作是用 shell 建立輸出檔(骨架如下,複製),之後邊讀邊把整個檔案重寫,保持合法 JSON;回報前 python3 -m json.tool 要通過,grep -n TODO 要沒有輸出。
  - 不要改設計。用 rtl next 回報(格式固定):rtl next "skill step used: ... / found: ... / evidence: 檔案與指令 / unsure: ..."
