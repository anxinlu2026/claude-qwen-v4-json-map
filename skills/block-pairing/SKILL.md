---
name: block-pairing
description: "A2.3 (architecture engineer): pair the blocks of the RTL with the blocks of the IP model and list what has no pair on either side."
version: 0.1.0-draft
---

# block-pairing — which RTL block is which model block

## Goal
A table that says which RTL block does the work of which model block, on what basis, and a list of what is left without a pair on each side.

## Source
The deliveries of the RTL inventory and the model inventory, and the RTL for any line you cite. The shell for reading, `rtl show`, `rtl signals`.

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. Record the versions (hash) of the two inventories you work from.
2. Take each model block and look for the RTL module, instance, or group of statements that does that work. Write the basis from what the statements do: the operation, what it takes and gives, its place in the sequence. Read the statements; a matching name is not a basis by itself.
3. Take each RTL block that no model block was paired to and say why it has none (control, storage, interface, or unknown).
4. Label each pair `reading` (from the statements), `name only` (the only support is a name or a comment), or `evidence` (a delivery or log that shows it).
5. For each pair, say in one line what the RTL statements do (operation, direction or order where it matters) and compare that line with what the model block does; if they differ, say so in the row.
6. Where one RTL block covers several model blocks, or the reverse, say so in the row.

## Output: `A2.3.md`
Sections, in this order: Inputs (path, hash) / Pairs (model block, RTL block with line, what the RTL statements do, basis, reading or name only or evidence) / Unpaired RTL (block, reason) / Unpaired model (block, reason) / Basis notes.

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
   Values from a run are copied character for character from the output, as the line the tool printed; do not retype, shorten or recompute them.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every block of the RTL inventory and every block of the model inventory appears in Pairs or in one of the two unpaired lists.
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- No signal-level detail here; that is the next order.
- Do not guess a pair: a block without a basis is unpaired, with the reason.
- A name or a comment says what the author meant, not what the code does. State what a block, signal or statement does from its statements: which value is assigned from which, in what order, in which direction, under which condition. Copy the statements with their lines. Where a name or comment is all that supports a statement, label it `name only`. Where a name or comment and the statements disagree, write both and mark the row `unresolved`; do not take the one that sounds right.
- Do not edit the RTL or the model.

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
