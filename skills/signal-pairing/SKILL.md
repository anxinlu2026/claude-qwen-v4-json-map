---
name: signal-pairing
description: "A2.4 (architecture engineer): for each paired block, pair the signals of the RTL with the values of the model: width, encoding, meaning."
version: 0.1.0-draft
---

# signal-pairing — which signal carries which value

## Goal
For every pair of blocks, say which RTL signals carry the model block's inputs and outputs, with width, encoding and meaning, and mark what is only read from the code.

## Source
The block pairing delivery, the RTL source, the model inventory. The shell for reading, `rtl show`, `rtl signals`.

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. Record the versions (hash) of the deliveries you work from.
2. For each pair: each model input and output, the RTL signal that carries it (full name as the code gives it), its width, how it is encoded (bit order, byte order, how an array is flattened), and what it means.
3. Copy declarations and assignments with line numbers; do not restate them from memory.
4. Derive bit order, byte order, index order and direction from the index expressions and assignments (which index feeds which); do not take them from a name or a comment.
5. Where the declaration and the use differ, or two readings are possible, write both and mark the row unresolved.
6. Label each row `reading` (from the statements), `name only`, or `evidence`.

## Output: `A2.4.md`
Sections, in this order: Inputs (path, hash) / Signal pairs (block pair, model value, RTL signal, width, encoding, meaning, line, reading or evidence) / Encoding notes / Unresolved.

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
   Values from a run are copied character for character from the output, as the line the tool printed; do not retype, shorten or recompute them.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every pair of the block pairing delivery has rows for all its model inputs and outputs, or `unresolved: reason`.
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- Do not write sampling instants or timing; that belongs to the alignment contract.
- Do not choose an order or a reversal to make two values look alike.
- A name or a comment says what the author meant, not what the code does. State what a block, signal or statement does from its statements: which value is assigned from which, in what order, in which direction, under which condition. Copy the statements with their lines. Where a name or comment is all that supports a statement, label it `name only`. Where a name or comment and the statements disagree, write both and mark the row `unresolved`; do not take the one that sounds right.
- Do not edit the RTL or the model.

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
