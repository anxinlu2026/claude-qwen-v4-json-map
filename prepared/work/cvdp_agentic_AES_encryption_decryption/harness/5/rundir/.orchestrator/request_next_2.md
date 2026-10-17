[work order report, request 2]

State: 0 edit(s) vs original; signals: 34 not_compared, 0 match, 0 mismatch, 0 recheck, 0 fixed, 0 nogolden; no testbench run yet; task sheet not approved; model not validated

## Report
found: The testbench (verif/tb_aes128_dec.sv) instantiates aes128_decrypt (lines 15-27) and drives: clk 5ns (L71), async reset rst_async_n=0 for #2 then 1 (L76-80), i_key=128'h2b7e151628aed2a6abf7158809cf4f3c (L31), i_data=128'h3925841d02dc09fbdc118597196a0b32 (L32), i_update_key=update_key (L45), i_start=1 for one clock then 0 (L46,L49), zeroing i_key/i_data on the next negedge (L48-52). It waits for posedge o_done (L54) then samples o_data and expects o_data==128'h3243f6a8885a308d313198a2e0370734 (L57-63), printing PASS/FAIL. It covers TWO cases via Simple_test: (1) Simple_test(1'b1) L84 = update_key=1, full key expansion + decryption; (2) Simple_test(1'b0) L85 = update_key=0, reuse the stored expanded key with only i_start asserted. Both use the same single FIPS-197 vector and expect the same plaintext. / evidence: verif/tb_aes128_dec.sv L1-93 (esp. L31-32, L45-55, L57, L84-85) / unsure: the testbench does NOT cover any of the task's named sub-behaviours in isolation: it never checks the expanded key / 44 words / 11 round keys (o_expanded_key), never tests key expansion (RotWord/SubWord/Rcon/XOR W[i-4]) alone, never tests InvMixColumns/InvShiftRows/InvSubBytes stages separately, never tests the final round (round 10, no InvMixColumns) as its own case, and uses only ONE key+ciphertext (no other FIPS vectors or random data). It also does not explicitly check o_done/key_done timing or the serial key-expansion-before-decryption ordering, only the end result.

## Recorded comparisons
(none)

## Rule-based suggestion of the tool (for reference, not shown to the agent)
NEXT: rtl sim   (run the testbench once on the untouched design and note what fails)

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

