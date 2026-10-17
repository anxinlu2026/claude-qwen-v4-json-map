WORK ORDER C-load_block-c2_from - TYPE: ALIGN-IFACE
目標:對方塊 load_block,比較「RTL 實際從上游接進來的端口」與「架構宣告的上游端口」,逐訊號,寫成 /tmp/deliveries/load_block_c2_from.md。不找功能錯誤,不改設計。限時 15 分鐘:一開始就動手,不要先長篇推理。

資料來源:
  架構側(只看這個方塊,不要 cat 整個 model_dp.json,它很大):
    python3 -c "import json;b=[x for x in json.load(open('/tmp/pilot/model_dp.json'))['blocks'] if x['id']=='load_block'][0];print(json.dumps({k:b[k] for k in ('upstream_blocks','ports_detail')},ensure_ascii=False,indent=1))"
  RTL 側:rtl show rtl/aes128_decrypt.sv 1 140(行號與原文從輸出複製,不自己算;沒有「rtl show 方塊名」這種用法)、/tmp/pilot/rtl_structure.json(寬度、時脈、邊緣、reset 從這裡抄)、rtl probe 的參數是訊號名,不是方塊名,例如:rtl probe i_start o_done round_ff --to 260 --max 40(模擬到 260 結束)。
  標成「control (RTL's own; not specified by the architecture)」的連接:列出 RTL 實際用來控制這個方塊的訊號(名稱、寬度、類型、clock),結果寫 not specified。

步驟(照順序):
  1. cp /tmp/pilot/skeleton_c2_from.md /tmp/deliveries/load_block_c2_from.md(不要自己重打骨架;標題與欄位一個字都不改)
  2. 讀 /tmp/deliveries/load_block_c1_to.md 的「假設」:你的假設編號從它的最大編號 +1 開始。
  3. 取架構側資料;用 rtl show、rtl_structure.json、rtl probe 取 RTL 側資料。
  4. 把整份檔案一次寫完(不要邊讀邊重寫整檔);grep -n TODO 必須沒有輸出。
  5. rtl next "skill step used: ... / found: ... / evidence: ... / unsure: ..."

判斷規則:
  - 結果欄:same = 每個屬性都一致(寬度、類型含有效條件、clock、邊緣、組合或暫存、延遲);different = 任一屬性不同(有效條件不同也算);no rtl signal = RTL 找不到對應訊號;not specified = RTL 自己的控制;unknown = 兩側的資料你取得不了或看不清楚,無法判斷(原因寫在「歧義」);兩側都看到了而且不同,一律 different,不要用 unknown。
  - different、unknown、或順便看到的功能差異(例如位元組順序與架構不同):各寫一條假設(編號、對象、內容、原因);功能差異註明「交給 c3」。不要把猜測寫成事實。
  - RTL 側的屬性只能從 rtl_structure.json、RTL 陳述式、testbench 或探測得到,不能從名稱或註解推。延遲:組合 = 0;暫存器串接 = 級數。
  - 探測要選「這個方塊真的在工作」的那一列(例如 load 條件為真)。找不到時先把 --to 加到 260 再找一次;還是找不到,就在「依據」寫「探測不到該方塊工作」並說明看了哪些列,不要拿別的列當證據;並把它寫成假設。第一次 start 之前的控制訊號值若與預期不同,也寫成假設。
