WORK ORDER C-load_block-c2_from - TYPE: ALIGN-IFACE
目標:對方塊 load_block,逐訊號比較「RTL 實際從上游接進來的端口」與「架構宣告的上游端口」,寫成 /tmp/deliveries/load_block_c2_from.md。只比較端口:不找錯、不追查原因、不改設計。限時 15 分鐘,一開始就動手。

這份文件記錄的是「你看到的、讀到的」,不要求證明。看不清楚、和架構不一樣、或你只是從 RTL 推得出來的,都寫成假設;假設不一定是對的,也不需要你去確認或釐清,釐清是架構的事。

資料來源:
  架構側(只看這個方塊):
    python3 -c "import json;b=[x for x in json.load(open('/tmp/pilot/model_dp.json'))['blocks'] if x['id']=='load_block'][0];print(json.dumps({k:b[k] for k in ('upstream_blocks','ports_detail')},ensure_ascii=False,indent=1))"
  RTL 側:
    - rtl show rtl/aes128_decrypt.sv 1 140(行號與原文從輸出複製,不自己算)
    - /tmp/pilot/rtl_structure.json(寬度、時脈、邊緣、reset 從這裡抄)
    - 需要看時間上的行為時,最多探測兩次:rtl probe <這個方塊的端口訊號名,以空白隔開> --to <模擬結束時間> --max 40(訊號名要用 RTL 裡的真實名稱,不是方塊名;模擬結束時間看 rtl sim 的輸出)。探測看到什麼就記什麼。
  標成「control (RTL's own; not specified by the architecture)」的連接:列出 RTL 用來控制這個方塊的訊號(名稱、寬度、類型、clock),結果寫 not specified。只列出,不分析它們的行為。

步驟(照順序):
  1. cp /tmp/pilot/skeleton_c2_from.md /tmp/deliveries/load_block_c2_from.md
  2. 讀 /tmp/deliveries/load_block_c1_to.md 的「假設」:你的假設編號從它的最大編號 +1 開始。
  3. 取架構側資料;取 RTL 側資料。
  4. 只填 TODO 的地方,用 python 或 sed 就地取代;標題(以 ## 開頭的行)和表格欄位一個字都不要動,也不要把整份檔案重打。完成後 grep -n TODO 必須沒有輸出。
  5. rtl next "skill step used: ... / found: ... / evidence: ... / unsure: ..."

判斷規則:
  - 結果欄:same = 每個屬性都一致(寬度、類型含有效條件、clock、邊緣、組合或暫存、延遲);different = 任一屬性不同;no rtl signal = RTL 找不到對應訊號;not specified = RTL 自己的控制;unknown = 你取不到資料或看不清楚(原因寫在「歧義」)。
  - different、unknown、或你順便看到與架構說明不同的地方:各寫一條假設(編號、對象、內容、原因),並註明來源是「讀 RTL」「testbench」或「探測」。不要把猜測寫成事實,也不要追查它為什麼不同。
  - RTL 側的屬性只能從 rtl_structure.json、RTL 陳述式、testbench 或探測得到,不能從名稱或註解推。延遲:組合 = 0;暫存器串接 = 級數。
  - 探測沒有看到你預期的行為時,照實寫「探測看到:…」,寫一條假設,然後繼續,不要再花時間查。
