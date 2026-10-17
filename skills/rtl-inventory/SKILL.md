---
name: rtl-inventory
description: "A2.1 (HDL engineer): list the structure of the RTL as it is written: files, module hierarchy, ports with widths, clock and reset, generate blocks, and whether it compiles."
version: 0.1.0-draft
---

# rtl-inventory — what the design is made of

## Goal
Give the team a static inventory of the design: modules and how they are instantiated, the ports of each with direction and width, the clock and reset, the generate blocks. You do not pair it with a model and you do not judge it.

## Source
The RTL directory (and the testbench directory for the top module). Commands: `rtl signals`, `rtl show`, the shell for reading and for a compile check (`iverilog`, `verilator --lint-only`).

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. List the files with path and hash (`md5sum FILE`) and the top module.
2. Use `rtl signals` for modules, signals and their widths; read the source for what the tool does not list (instances and signals inside generate blocks, parameters, clock and reset names).
3. For each module: its instances (instance name, module, line), its ports (name, direction, width), its parameters.
4. Name the clock and the reset of each module that has them, with polarity as the code states it.
5. Compile the design once with the plainest command (`iverilog -g2012 -o /dev/null FILES` or `verilator --lint-only`). Keep the command and the output.
6. Say what the tool did not list and you read from the source; label it as reading.
7. Where you give what a block does, derive it from its statements and cite the lines; a function taken only from a module name, a signal name or a comment is labelled `name only`.

## Output: `A2.1.md`
Sections, in this order: Files (path, hash, lines) / Hierarchy (module tree with instance names and source lines) / Ports (module, port, direction, width, line) / Clock and reset / Generate blocks / Compile check (command, result) / Not listed by the tool (reading only).

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
   Values from a run are copied character for character from the output, as the line the tool printed; do not retype, shorten or recompute them.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every file of the RTL directory has a row in Files, every module has a row in Hierarchy, every port of every module has a row in Ports; the compile check has its command and result, or `not_run: reason`.
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- Static work: do not run the simulation.
- Do not pair with the model and do not interpret what a block does beyond what its statements show.
- A name or a comment says what the author meant, not what the code does. State what a block, signal or statement does from its statements: which value is assigned from which, in what order, in which direction, under which condition. Copy the statements with their lines. Where a name or comment is all that supports a statement, label it `name only`. Where a name or comment and the statements disagree, write both and mark the row `unresolved`; do not take the one that sounds right.
- Do not edit any file.

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
