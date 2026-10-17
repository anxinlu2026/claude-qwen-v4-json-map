---
name: model-vector-run
description: "A1.4 (HDL engineer): run the IP model on the vectors the standard prints and on its own validation; record outputs and whether they match."
version: 0.1.0-draft
---

# model-vector-run — run the model on the standard's vectors

## Goal
A recorded answer to: does the model give the values the standard prints, and does its own validation pass, as run now.

## Source
The model folder (commands from MODEL.md and BLOCKS.txt), the vectors V1… of `A1.3.md`, the open questions of `A1.2.md` (each is a command).

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. Take the vectors of A1.3 and the commands of A1.2's open questions as the list. Do not add vectors.
2. For each vector: run the model command with the input exactly as the standard prints it. Keep the command, the directory and the output.
3. Compare with the expected value of the standard in one representation. Write the representation (byte or bit order) used for both strings before you compare.
4. Run the model's own validation once as its documents say; keep the result line and the count.
5. Verdict per vector: `match`, `mismatch` (both values kept, nothing fixed), `inconclusive` (the representation cannot be settled; both strings kept), `not_run` (reason).

## Output: `A1.4.md`
One table: V# / command / input / expected (clause) / observed / representation / verdict. Under it: the validation result line, and the raw log paths.

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
   Values from a run are copied character for character from the output, as the line the tool printed; do not retype, shorten or recompute them.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every vector of A1.3 and every open question of A1.2 has a row with a verdict; the validation result line is recorded.
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- Do not edit the model or the vectors. Do not take expected values from memory.
- Do not look at the RTL.
- A mismatch is a record, not a repair. If the model has no command for a vector, the verdict is `not_run`.

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
