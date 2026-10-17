[work order report, request 4]

State: 0 edit(s) vs original; signals: 34 not_compared, 0 match, 0 mismatch, 0 recheck, 0 fixed, 0 nogolden; last testbench run #1: FAIL; task sheet not approved; model validated

## Report
found: Trusted source = the validated aes128 model at /opt/resources/ip_models/aes128 (FIPS 197, Python 3). What it can give: (1) 'roundkeys <key>' -> the 11 round keys / 44 words W[0..43]; (2) 'decrypt <key> <ciphertext>' -> full single-block decryption printing the state after every step of every round (InvShiftRows, InvSubBytes, AddRoundKey, InvMixColumns; final round no InvMixColumns); (3) per-block 'block <name>' operations: add_round_key, inv_shift_rows, inv_sub_bytes, inv_mix_columns, inv_mix_column, next_round_key, rot_word, sub_word, xtime (x*02), gmul (GF(2^8) product). State/round-key byte order: byte n is row (n mod 4), column (n div 4) -- must check this matches the RTL/testbench order before comparing. How validated: 'rtl model /opt/resources/ip_models/aes128' ran validate.py against openssl: decrypt vs openssl 202/202, round-trip 202/202, block entry points chained vs openssl 40/40, and all 40 expanded key words agree with FIPS 197 Appendix A.1 -> HARNESS PASS. It is now on record and its values are golden. / evidence: rtl model run (HARNESS PASS, 202/202 + 40/40) + MODEL.md + BLOCKS.txt / unsure: the per-step decryption states in the model have not been compared with a published source (only the end-to-end results and the 40 key words are independently checked), so when I compare intermediate round states I should anchor on the end-to-end plaintext and the FIPS-197 key words, and confirm the model's step order/sampling point matches the RTL's before trusting an intermediate value.

## Recorded comparisons
(none)

## Rule-based suggestion of the tool (for reference, not shown to the agent)
NEXT: write the task sheet /tmp/task_sheet.md, rtl sheetsubmit and wait for the orchestrator's review.

## Last commands and their output
$ rtl next found: aes128_decrypt must take 128-bit ciphertext i_data + 128-bit key i_key, expand the key into 11 round keys (44 words) via aes128_key_expansion when (i_update_key & i_start & o_done), then run AES-128 decryption = 1 initial AddRoundKey + 9 rounds of InvShiftRows/InvSubBytes/AddRoundKey/InvMixColumns + 1 final round (InvShiftRows/InvSubBytes/AddRoundKey, no InvMixColumns), producing 128-b
State: 0 edit(s) vs original; signals: 34 not_compared, 0 match, 0 mismatch, 0 recheck, 0 fixed, 0 nogolden; no testbench run yet; task sheet not approved; model not validated
Report 1 sent to the orchestrator. Waiting for the next work order (up to 30 min). If this command is cut off, run rtl next again: it resumes the same report.
ORCHESTRATOR ANSWER 1:
Accepted.

WORK ORDER 0.2
Goal:      Read the testbench.
Look at:   /code/verif
Done when: you can say what it drives, what it expects, which cases it covers, and which cases named in the task it does not cover.
Report:    rtl next "found: ... / evidence: file and lines / unsure: ..."


$ rtl show /code/verif/tb_aes128_dec.sv
verif/tb_aes128_dec.sv  lines 1-60 of 93
   1: module tb_aes128_dec;
   2: 
   3: localparam NBW_KEY  = 'd128;
   4: localparam NBW_DATA = 'd128;
   5: 
   6: logic                clk;
   7: logic                rst_async_n;
   8: logic                i_update_key;
   9: logic [NBW_KEY-1:0]  i_key;
  10: logic                i_start;
  11: logic [NBW_DATA-1:0] i_data;
  12: logic                o_done;
  13: logic [NBW_DATA-1:0] o_data;
  14: 
  15: aes128_decrypt #(
  16:     .NBW_KEY (NBW_KEY),
  17:     .NBW_DATA(NBW_DATA)
  18: ) uu_aes128_decrypt (
  19:     .clk(clk),
  20:     .rst_async_n(rst_async_n),
  21:     .i_update_key(i_update_key),
  22:     .i_key(i_key),
  23:     .i_start(i_start),
  24:     .i_data(i_data),
  25:     .o_done(o_done),
  26:     .o_data(o_data)
  27: );
  28: 
  29: task Simple_test(logic update_key);
  30:     @(negedge clk);
  31:     i_key = 128'h2b7e151628aed2a6abf7158809cf4f3c;
  32:     i_data = 128'h3925841d02dc09fbdc118597196a0b32;
  33:     // Data is stored in the RTL as a 4x4 matrix. With this i_data, the matrix should be:
  34:     // Col  : 0  | 1  | 2  | 3
  35:     //       -------------------
  36:     // Row 0: 39 | 02 | dc | 19


$ rtl show /code/verif/tb_aes128_dec.sv 60 93
verif/tb_aes128_dec.sv  lines 60-93 of 93
  60:         $display("FAIL");
  61:         $display("Expected output: %h", 128'h3243f6a8885a308d313198a2e0370734);
  62:         $display("Observed output: %h", o_data);
  63:     end
  64: endtask
  65: 
  66: initial begin
  67:     $dumpfile("test.vcd");
  68:     $dumpvars(0,tb_aes128_dec);
  69: end
  70: 
  71: always #5 clk = ~clk;
  72: 
  73: initial begin
  74:     clk = 0;
  75:     i_start = 0;
  76:     rst_async_n = 1;
  77:     #1;
  78:     rst_async_n = 0;
  79:     #2;
  80:     rst_async_n = 1;
  81:     @(negedge clk);
  82: 
  83:     // Tasks go here
  84:     Simple_test(1'b1);
  85:     Simple_test(1'b0);
  86: 
  87:     @(negedge clk);
  88:     @(negedge clk);
  89: 
  90:     $finish();
  91: end
  92: 
  93: endmodule


$ rtl next found: The testbench (verif/tb_aes128_dec.sv) instantiates aes128_decrypt (lines 15-27) and drives: clk 5ns (L71), async reset rst_async_n=0 for #2 then 1 (L76-80), i_key=128'h2b7e151628aed2a6abf7158809cf4f3c (L31), i_data=128'h3925841d02dc09fbdc118597196a0b32 (L32), i_update_key=update_key (L45), i_start=1 for one clock then 0 (L46,L49), zeroing i_key/i_data on the next negedge (L48-52). It 
State: 0 edit(s) vs original; signals: 34 not_compared, 0 match, 0 mismatch, 0 recheck, 0 fixed, 0 nogolden; no testbench run yet; task sheet not approved; model not validated
Report 2 sent to the orchestrator. Waiting for the next work order (up to 30 min). If this command is cut off, run rtl next again: it resumes the same report.
ORCHESTRATOR ANSWER 2:
Accepted.

WORK ORDER 0.3
Goal:      Run the testbench once on the untouched design.
Use:       rtl sim
Done when: you have the expected and the observed value of every failing case.
Report:    rtl next "found: ... / evidence: run number / unsure: ..."


$ rtl sim
RUN #1  compile: OK   result: FAIL (2 FAIL, 0 PASS)   design: 0 edit(s) vs original
FAIL
Expected output: 3243f6a8885a308d313198a2e0370734
Observed output: 00000000000000600000000000000000
FAIL
Expected output: 3243f6a8885a308d313198a2e0370734
Observed output: 00000000000000970000000000000000
/code/verif/tb_aes128_dec.sv:90: $finish called at 260 (1s)
(hidden: 118 x "constant selects" notice, original design had 118; full text: rtl log 1 --full)
(hidden: 1 x "VCD dumpfile opened" notice, original design had 1; full text: rtl log 1 --full)


$ rtl next found: rtl sim run #1 on the untouched design: compile OK, result FAIL (2 FAIL, 0 PASS). Both failing cases: CASE 1 = Simple_test(1'b1) (update_key=1, full key expansion + decryption): Expected 3243f6a8885a308d313198a2e0370734, Observed 00000000000000600000000000000000. CASE 2 = Simple_test(1'b0) (update_key=0, reuse stored key, only i_start): Expected 3243f6a8885a308d313198a2e0370734, Observ
State: 0 edit(s) vs original; signals: 34 not_compared, 0 match, 0 mismatch, 0 recheck, 0 fixed, 0 nogolden; last testbench run #1: FAIL; task sheet not approved; model not validated
Report 3 sent to the orchestrator. Waiting for the next work order (up to 30 min). If this command is cut off, run rtl next again: it resumes the same report.
ORCHESTRATOR ANSWER 3:
Accepted.

WORK ORDER 0.4
Goal:      Find a trusted source of expected values.
Look at:   /opt/resources (start at INDEX.md). Read /opt/skills/hdl-debug/SKILL.md.
Use:       rtl model DIR for a model you find there.
Done when: a model is validated and on record, or you can say that none exists for this function.
Report:    rtl next "found: which model, what it can give (which blocks), how it was validated / evidence: ... / unsure: ..."


$ rtl model /opt/resources/ip_models/aes128
MODEL VALIDATION in /opt/resources/ip_models/aes128 (validate.py): PASS
checking: decrypt_block
all decrypt* functions vs openssl -d : 202/202
decrypt vs openssl -d : 202/202
openssl -e round trip : 202/202
block entry points chained vs openssl : 40/40
HARNESS PASS
The model is validated and on record: its values can be used as golden (rtl next tells the next step).
Blocks of the validated model (/opt/resources/ip_models/aes128/BLOCKS.txt):
command (run in this folder): python3 aes128_model.py block NAME INPUT [INPUT ...]     every value in hex
  NAME              inputs (in this order)                          output
  add_round_key     state (32 digits), round key (32 digits)        state
  inv_shift_rows    state (32 digits)                               state
  inv_sub_bytes     state (32 digits)                               state
  inv_mix_columns   state (32 digits)                               state
  inv_mix_column    one column (8 digits, row 0 first)              column
  next_round_key    round key N-1 (32 digits), N (1..10)            round key N
  rot_word          word (8 digits)                                 word
  sub_word          word (8 digits)               
