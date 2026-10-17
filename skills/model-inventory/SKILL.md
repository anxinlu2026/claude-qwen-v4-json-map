---
name: model-inventory
description: "A2.2 (architecture engineer): list the blocks of the IP model, their inputs and outputs, byte and bit order, and the step order the model states."
version: 0.1.0-draft
---

# model-inventory — what the model offers

## Goal
Give the team an inventory of the IP model as it describes itself: its blocks, what each takes and gives, the order of bytes and bits, and the order of steps. You do not pair it with the RTL and you do not validate it.

## Source
The model folder: MODEL.md, BLOCKS.txt, VALIDATION.md, SOURCE.md, the commands the CLI lists. The shell for reading.

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. List the files with path and hash.
2. From BLOCKS.txt and the CLI listing: every block by name, with its inputs in the order the model takes them, its output, and the unit (byte, word, block).
3. From MODEL.md and the code: byte and bit order, how a block or word is laid out, how a state or array is flattened.
4. From MODEL.md: the order of steps in the function the model describes, with the file and line.
5. Note what a block is called in the model versus what it does when the two differ; note anything the model does not state.
6. Record questions that only a run can answer as open questions; do not run them.

## Output: `A2.2.md`
Sections, in this order: Files (path, hash) / Blocks (name, inputs in order, output, unit, source line) / Order rules (byte, bit, flattening, with source lines) / Step order / Not stated by the model / Open questions.

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
   Values from a run are copied character for character from the output, as the line the tool printed; do not retype, shorten or recompute them.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every block named in BLOCKS.txt or listed by the CLI has a row in Blocks with its inputs and output; the step order has a source line or is `not_done: reason`.
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- Use only what the model files state; do not infer from the RTL.
- Do not run the model validation and do not edit the model.
- A value you read is copied from the file with its line number.

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
