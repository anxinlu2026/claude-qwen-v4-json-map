module aes128_key_expansion #(
    parameter NBW_KEY = 'd128,
    parameter NBW_OUT = 'd1408
) (
    input  logic               clk,
    input  logic               rst_async_n,
    input  logic               i_start,
    input  logic [NBW_KEY-1:0] i_key,
    output logic               o_done,
    output logic [NBW_OUT-1:0] o_expanded_key
);

// ----------------------------------------
// - Parameters
// ----------------------------------------
localparam NBW_BYTE = 'd8;
localparam NBW_WORD = 'd32;
localparam STEPS    = 'd10;

// ----------------------------------------
// - Wires/registers creation
// ----------------------------------------
logic [NBW_BYTE-1:0] Rcon   [STEPS];
logic [NBW_OUT-1:0]  expanded_key_nx;
logic [NBW_OUT-1:0]  expanded_key_ff;
logic [NBW_KEY-1:0]  step_key[STEPS];
logic [NBW_KEY-1:0]  valid_key;
logic [STEPS:0]      key_exp_steps_ff;

// ----------------------------------------
// - Output assignment
// ----------------------------------------
assign o_expanded_key = expanded_key_ff;
assign o_done = key_exp_steps_ff[STEPS];

// ----------------------------------------
// - Registers
// ----------------------------------------
always_ff @(posedge clk or negedge rst_async_n) begin : reset_regs
    if(~rst_async_n) begin
        expanded_key_ff  <= {NBW_OUT{1'b0}};
        key_exp_steps_ff <= 0;
    end else begin
        expanded_key_ff <= expanded_key_nx;

        if(i_start) begin
            key_exp_steps_ff <= {{(STEPS-2){1'b0}}, 1'b1};
        end else begin
            if(key_exp_steps_ff[STEPS-1]) begin
                key_exp_steps_ff <= 0;
            end else begin
                key_exp_steps_ff <= key_exp_steps_ff << 1;
            end
        end
    end
end


// ----------------------------------------
// - Operation logic
// ----------------------------------------
assign Rcon[0] = 8'h01;
assign Rcon[1] = 8'h02;
assign Rcon[2] = 8'h04;
assign Rcon[3] = 8'h08;
assign Rcon[4] = 8'h10;
assign Rcon[5] = 8'h20;
assign Rcon[6] = 8'h40;
assign Rcon[7] = 8'h80;
assign Rcon[8] = 8'h1b;
assign Rcon[9] = 8'h36;

generate
    for(genvar i = 0; i < STEPS; i++) begin : steps
        logic [NBW_WORD-1:0] RotWord;
        logic [NBW_WORD-1:0] SubWord;
        logic [NBW_WORD-1:0] RconXor;

        sbox uu_sbox0 (
            .i_data(RotWord[NBW_WORD-1-:NBW_BYTE]),
            .o_data(SubWord[NBW_WORD-1-:NBW_BYTE])
        );

        sbox uu_sbox1 (
            .i_data(RotWord[NBW_WORD-NBW_BYTE-1-:NBW_BYTE]),
            .o_data(SubWord[NBW_WORD-NBW_BYTE-1-:NBW_BYTE])
        );

        sbox uu_sbox2 (
            .i_data(RotWord[NBW_WORD-2*NBW_BYTE-1-:NBW_BYTE]),
            .o_data(SubWord[NBW_WORD-2*NBW_BYTE-1-:NBW_BYTE])
        );

        sbox uu_sbox3 (
            .i_data(RotWord[NBW_WORD-3*NBW_BYTE-1-:NBW_BYTE]),
            .o_data(SubWord[NBW_WORD-3*NBW_BYTE-1-:NBW_BYTE])
        );

        always_comb begin : main_operation
            RotWord = {expanded_key_ff[NBW_OUT-(i+1)*NBW_KEY+NBW_WORD-NBW_BYTE-1-:(NBW_WORD-NBW_BYTE)], expanded_key_ff[NBW_OUT-(i+1)*NBW_KEY+NBW_WORD-1-:NBW_BYTE]};
            RconXor = {SubWord[NBW_WORD-1-:NBW_BYTE]^Rcon[i], SubWord[NBW_WORD-NBW_BYTE-1-:(NBW_WORD-NBW_BYTE)]};

            step_key[i][NBW_KEY-1-:NBW_WORD]            = expanded_key_ff[NBW_OUT-(4*i+3)*NBW_WORD-1-:NBW_WORD] ^ RconXor;
            step_key[i][NBW_KEY-NBW_WORD-1-:NBW_WORD]   = expanded_key_ff[NBW_OUT-(4*i+2)*NBW_WORD-1-:NBW_WORD] ^ step_key[i][NBW_KEY-1-:NBW_WORD];
            step_key[i][NBW_KEY-2*NBW_WORD-1-:NBW_WORD] = expanded_key_ff[NBW_OUT-(4*i+1)*NBW_WORD-1-:NBW_WORD] ^ step_key[i][NBW_KEY-NBW_WORD-1-:NBW_WORD];
            step_key[i][NBW_KEY-3*NBW_WORD-1-:NBW_WORD] = expanded_key_ff[NBW_OUT-(4*i  )*NBW_WORD-1-:NBW_WORD] ^ step_key[i][NBW_KEY-2*NBW_WORD-1-:NBW_WORD];
        end
    end
endgenerate

assign expanded_key_nx = {valid_key  , step_key[0], step_key[1], step_key[2],
                          step_key[3], step_key[4], step_key[5], step_key[6],
                          step_key[7], step_key[8], step_key[9]};

always_comb begin : input_data
    if (i_start) begin
        valid_key = i_key;
    end else begin
        valid_key = expanded_key_ff[NBW_OUT-1-:NBW_KEY];
    end
end

endmodule : aes128_key_expansion