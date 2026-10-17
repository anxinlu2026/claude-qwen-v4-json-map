---
name: map-review
description: "A2.6 (architecture engineer): review the pairing and the signal checks and write the final map, marking what is only read from the code or unresolved."
version: 0.1.0-draft
---

# map-review — the final map and what it does not settle

## Goal
One final map of RTL to model, block level and signal level, with the status of each entry and the list of what is unresolved and what that costs later.

## Source
The deliveries of the block pairing, the signal pairing and the existence check; the RTL for any line you cite. The shell for reading.

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. Record the versions (hash) of the deliveries you work from.
2. Write the final map: each pair, each signal pair, with status `evidence` (read in the simulation), `reading` (code only), or `unresolved`.
3. Where the deliveries disagree (a signal paired in one and not readable in another), list both and say which entry stands and why, or leave it unresolved.
4. List items that are only read from the code and could not be read in the simulation, and items whose support is a name or a comment only (`name only`); the latter are not final until a delivery shows the behaviour.
5. For each unresolved item, state what it blocks (which later comparison cannot be defined without it).

## Output: `A2.6.md`
Sections, in this order: Inputs (path, hash) / Final map (block pair, signal pair, status, source) / Read-only items / Unpaired / Unresolved and what it blocks.

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
   Values from a run are copied character for character from the output, as the line the tool printed; do not retype, shorten or recompute them.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every pair of the block pairing and every signal pair is in Final map, Read-only items, Unpaired or Unresolved.
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- No new experiments and no new pairs: only what the deliveries support.
- Do not rewrite the earlier deliveries; cite them.
- A name or a comment says what the author meant, not what the code does. State what a block, signal or statement does from its statements: which value is assigned from which, in what order, in which direction, under which condition. Copy the statements with their lines. Where a name or comment is all that supports a statement, label it `name only`. Where a name or comment and the statements disagree, write both and mark the row `unresolved`; do not take the one that sounds right.
- Do not rate the design.

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
