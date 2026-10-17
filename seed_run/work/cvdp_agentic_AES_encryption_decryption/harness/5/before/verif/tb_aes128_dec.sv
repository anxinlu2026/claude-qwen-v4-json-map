module tb_aes128_dec;

localparam NBW_KEY  = 'd128;
localparam NBW_DATA = 'd128;

logic                clk;
logic                rst_async_n;
logic                i_update_key;
logic [NBW_KEY-1:0]  i_key;
logic                i_start;
logic [NBW_DATA-1:0] i_data;
logic                o_done;
logic [NBW_DATA-1:0] o_data;

aes128_decrypt #(
    .NBW_KEY (NBW_KEY),
    .NBW_DATA(NBW_DATA)
) uu_aes128_decrypt (
    .clk(clk),
    .rst_async_n(rst_async_n),
    .i_update_key(i_update_key),
    .i_key(i_key),
    .i_start(i_start),
    .i_data(i_data),
    .o_done(o_done),
    .o_data(o_data)
);

task Simple_test(logic update_key);
    @(negedge clk);
    i_key = 128'h2b7e151628aed2a6abf7158809cf4f3c;
    i_data = 128'h3925841d02dc09fbdc118597196a0b32;
    // Data is stored in the RTL as a 4x4 matrix. With this i_data, the matrix should be:
    // Col  : 0  | 1  | 2  | 3
    //       -------------------
    // Row 0: 39 | 02 | dc | 19
    //       -------------------
    // Row 1: 25 | dc | 11 | 6a
    //       -------------------
    // Row 2: 84 | 09 | 85 | 0b
    //       -------------------
    // Row 3: 1d | fb | 97 | 32
    //       -------------------

    i_update_key = update_key;
    i_start = 1;

    @(negedge clk);
    i_start = 0;
    i_update_key = 0;
    i_key = 0;
    i_data = 0;

    @(posedge o_done);
    @(negedge clk);

    if(o_data == 128'h3243f6a8885a308d313198a2e0370734) begin
        $display("PASS");
    end else begin
        $display("FAIL");
        $display("Expected output: %h", 128'h3243f6a8885a308d313198a2e0370734);
        $display("Observed output: %h", o_data);
    end
endtask

initial begin
    $dumpfile("test.vcd");
    $dumpvars(0,tb_aes128_dec);
end

always #5 clk = ~clk;

initial begin
    clk = 0;
    i_start = 0;
    rst_async_n = 1;
    #1;
    rst_async_n = 0;
    #2;
    rst_async_n = 1;
    @(negedge clk);

    // Tasks go here
    Simple_test(1'b1);
    Simple_test(1'b0);

    @(negedge clk);
    @(negedge clk);

    $finish();
end

endmodule