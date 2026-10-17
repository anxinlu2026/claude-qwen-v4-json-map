# The `rtl` command

Use `rtl` for every simulator and file operation. Do not call iverilog/vvp yourself.
It finds the design (`/code/rtl`), the testbench (`/code/verif`) and the top module by itself.

```
rtl sim                       compile + run the testbench; first line says PASS/FAIL and whether the output changed
rtl signals [WORD]            list signal names and widths (WORD = part of a signal, module or instance name)
rtl probe SIG [SIG ...]       print the listed signals, one row per clock edge
                              options: --from T --to T --when "cond" --max N --clk SIGNAL --tb FILE
rtl show FILE [A B]           show lines A..B with line numbers
rtl replace FILE A B          replace lines A..B with the text given on stdin (a checkpoint is saved first)
rtl insert FILE N             insert the text given on stdin after line N
rtl checkpoint [NOTE]         save the current design files
rtl revert CHECKPOINT         restore a checkpoint ("original" = the untouched files, "last" = as rtl last left them)
rtl diff [CHECKPOINT]         what has changed vs the original (or vs a checkpoint)
rtl status                    summary of edits, runs and time used
rtl log N [--full]            output of run N (--full = unfiltered)
rtl sheetsubmit               submit the task sheet to the orchestrator for review and wait
rtl model DIR                 run the validation of a golden model (DIR/validate.py) and record it; comparing
                              and editing need a validated model
rtl blockcheck --in SIG [SIG ...] --out SIG --model "COMMAND"
                              probe the inputs and the output of a block, run COMMAND (in the model folder)
                              with the probed input values appended in hex, compare what it prints with the
                              probed output, and record match / mismatch / fixed for the output signal
                              options: --when "cond" --from T --to T --max N
rtl next "found: .. / evidence: .. / unsure: .."
                              report on the current work order; the orchestrator answers with the next
                              work order (the command waits for it)
rtl mark SIGNAL STATUS "kind=control golden=REQUIRED observed=SEEN source=WHERE"
                              control signals only (state machines, counters, flags): record a sequence
                              comparison: match | mismatch | fixed. Data values are recorded by rtl blockcheck.
rtl history [N] [WORD]        earlier commands and their results, also from earlier conversations; the way to
                              find a comparison again (run logs hold simulator output, not commands)
rtl ask "MESSAGE"             notify the orchestrator and wait for the answer (say what you compared,
                              what you found, and what you need)
```

## Examples

```bash
rtl sim
rtl signals done                         # which signals have "done" in the name, and where
rtl probe i_start round_ff o_done key_done --to 200
rtl probe key_expansion.i_start "expanded_key_ff[127:0]" --when "o_done==1"
rtl show aes128_decrypt.sv 60 75
rtl replace aes128_decrypt.sv 67 67 <<'EOF'
        end else if (state_ff == 2'd0) begin
EOF
rtl revert c3
rtl blockcheck --in col_in --out col_out --model "python3 aes128_model.py block inv_mix_column" --when "round_ff==3"
rtl blockcheck --in "key_ff[127:0]" =1 --out "next_key" --model "python3 aes128_model.py block next_round_key"
#   a value held in several signals is written with +, first part highest:
#     rtl blockcheck --in "a[0]+a[1]+a[2]+a[3]" --out "y[0]+y[1]+y[2]+y[3]" --model "..."
#   the probed values of --in are appended to the model command in order; =1 passes the constant 1;
#   the blocks of a model and what each takes are listed in BLOCKS.txt in its folder
```

## Notes

- Signal names need no hierarchy path. If a name exists in several modules, write `module.signal`
  or `instance.signal`.
- Rows show the values just before each rising clock edge (what the flip-flops sample at that edge).
- Put related signals in ONE probe call so they appear on the same row.
- Line numbers change after an edit: run `rtl show` again before the next `rtl replace`.
- Signals declared inside a `generate` loop must be given with their full path, starting at the
  testbench top and including the block label and index, e.g.
  `rtl probe "tb_top.u_dut.u_sub.steps[0].RotWord"`; `rtl signals` marks such signals.
- To examine one block on its own, write a small test that drives only that block (clock, reset, one
  stimulus) and probe with it: `rtl probe SIG ... --tb /tmp/my_tb.sv`. The design files are not changed.
- `rtl replace` works only after a comparison has located a driver (`rtl mark SIGNAL mismatch`). Design
  files changed in any other way are detected; undo with `rtl revert last`.
- When the method has not got there, the tool stops and requires `rtl ask`: a signal marked nogolden; a
  driver edited and reverted twice; every signal
  compared and the testbench still failing. After an edit, the next edit waits until the first is settled
  (`rtl mark ... fixed` or `rtl revert`). After a revert the signal is "recheck": compare one level upstream.
- After three probe runs without a recorded comparison, `rtl probe` stops until one is recorded
  (`rtl blockcheck` for data, `rtl mark ... kind=control` for a control sequence) or you `rtl ask`.
- Order of work is enforced. Before the task sheet: reading (`rtl show`, `rtl signals`), one `rtl sim`, and
  validating a model of the library (`rtl model /opt/resources/ip_models/NAME`). Then the task sheet
  (`rtl sheetsubmit`); a model you build, probing and editing come after its approval.
- Which commands a work order allows depends on its type: FIND ASSUMPTION: probe, blockcheck, sim (probe and blockcheck are observations; there is no limit on their number, only the time of the work order and the rule that three probe runs without a recorded comparison stop `rtl probe`); PROVE ASSUMPTION: probe, blockcheck, mark; FIX: replace, insert, sim, revert,
  checkpoint; CONFIRM FIX: probe, blockcheck, mark, sim, revert. `rtl show/history/status/log/signals/diff/next/ask` are always open.
- Your assumptions are kept by the tool: `rtl assumption add "OBJECT: claim"`, `rtl assumption set A3 proven|struck-out|open "evidence"`,
  `rtl assumption list`; a measured fact that you will need again: `rtl assumption add --fact "FACT" "evidence"` (status established or retracted). They are shown again at the start of each conversation and after each answer of the orchestrator.
- The task sheet needs a "model map" item (design block <- inputs | model block | instant | layout) at `rtl sheetsubmit`.
- A model lives in the library (`/opt/resources/ip_models/NAME`) or, if you build or change one, in
  `/tmp/ip_work/NAME`. Its `validate.py` compares its outputs with an independent trusted source and ends
  with `HARNESS PASS` or `HARNESS FAIL`. A model built in the session is also reviewed by the orchestrator.
  Program files anywhere else stop the tool: every program you write (a model, a comparison or conversion script) goes in /tmp/ip_work.
- `rtl sheetsubmit`, `rtl model` and `rtl ask` wait for the orchestrator. If the wait is cut off, run the
  same command again: it resumes the same request.
- A testbench that waits for something that never happens does not block you: the simulation is stopped at a
  time limit (ten times what the untouched design needed) and reported as NOT FINISHED. You choose the time
  yourself with `rtl probe ... --to T` (stops at T) or `rtl sim --until T`. The testbench file is not changed.
- Two kinds of harmless notices are folded into a one-line count; every other warning or error is
  shown. Anything that was not in the first run of the untouched design is always shown.
- Only files under `/code/rtl` can be edited with `rtl replace`. The testbench is the judge and
  stays untouched. To run an extra test of your own: `rtl sim --tb /tmp/my_tb.sv`.
