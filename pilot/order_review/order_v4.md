WORK ORDER D-load_block-ports - TYPE: ALIGN-IFACE
目標:把方塊 load_block 在原始 RTL 裡的端口,如實填進 /tmp/deliveries/load_block_ports.json。只記錄 RTL 實際有的東西:不比較、不判斷對錯、不追查原因、不改設計。限時 15 分鐘,一開始就動手。

做法:
  1. cp /tmp/pilot/load_block_ports.skeleton.json /tmp/deliveries/load_block_ports.json
     骨架裡每個 "arch_port" 是架構的一個端口(只給名字和它接到哪個方塊,幫你找對應的 RTL 訊號)。你只填每個 "rtl" 裡的 TODO。
  2. 讀 RTL 找出對應的訊號:rtl show rtl/aes128_decrypt.sv 1 140(行號與原文從輸出複製,不自己算);寬度、時脈、邊緣、reset 從 /tmp/pilot/rtl_structure.json 抄。
  3. 需要看時間上的行為時,最多探測兩次:rtl probe <RTL 裡的真實訊號名,空白隔開> --to <模擬結束時間> --max 40(rtl sim 的輸出有模擬結束時間)。看到什麼就記什麼。
  4. 用 /tmp/pilot/fill_port.py 填值（它保持鍵名與結構，並檢查取值；不要自己寫 Python 改 JSON，也不要重打整份檔案）：
       python3 /tmp/pilot/fill_port.py /tmp/deliveries/load_block_ports.json inputs <arch_port> signal=<名> width=<整數> kind=<…> "valid_when=<條件>" clock=<…> edge=<…> storage=<…> latency_min_cycles=<整數> latency_max_cycles=<整數> source="<依據>"
       python3 /tmp/pilot/fill_port.py /tmp/deliveries/load_block_ports.json outputs <arch_port> …（同上）
       python3 /tmp/pilot/fill_port.py /tmp/deliveries/load_block_ports.json extra signal=<名> width=<整數> kind=<…> source="<依據>"
     值寫 unknown 時，腳本會自動把該欄位加進 "unknown" 清單。完成後 grep -n TODO 必須沒有輸出，並用 python3 -m json.tool 確認是合法 JSON。
  5. rtl next "skill step used: ... / found: ... / evidence: ... / unsure: ..."

欄位怎麼填(都填 RTL 的事實):
  signal:RTL 裡實際的訊號名;多個訊號組成一個端口時用 + 連起來(寫法同 rtl probe)。RTL 裡沒有對應的訊號就寫 "none"(其餘欄位寫 "n/a")。
  width:位元數(整數)。
  kind:只能是 pulse(一個週期的脈衝)、level(位準)、held(保持)、data(資料,有效條件寫在 valid_when)。
  valid_when:data 才填,寫 RTL 裡讓它有效的條件(照 RTL 的寫法);其餘填 "n/a"。
  clock:所屬 clock 名;純組合邏輯填 "none"。edge:rising 或 falling;組合填 "n/a"。
  storage:combinational 或 register。
  latency_min_cycles、latency_max_cycles:從這個端口的輸入到它的延遲(整數週期)。組合 = 0;暫存器串接 = 級數。
  source:你的依據,例如 "rtl line 10; rtl_structure.json"。
  unknown:哪個欄位你從 RTL、testbench、探測都得不到,就把欄位名放進這個清單,該欄位值填 "unknown"。不要猜。
  "rtl_extra_ports":RTL 裡有接到這個方塊、但骨架沒有對應 arch_port 的訊號(例如控制訊號),每個一項:signal、width、kind、source。只列出,不分析它們的行為。
