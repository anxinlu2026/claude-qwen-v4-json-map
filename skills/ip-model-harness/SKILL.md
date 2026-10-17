---
name: ip-model-harness
description: "A1.2 (architecture engineer): state what the IP model's own verification compares, against which independent source, and where it stops."
version: 0.1.0-draft
---

# ip-model-harness — what the model's own verification proves

## Goal
Say how far the model's values can be used as golden: what its verification compares, against what independent source, with how many vectors, and what it does not cover.

## Source
The model folder: MODEL.md, VALIDATION.md, SOURCE.md, BLOCKS.txt, validate.py and the code it calls.

## Importance
- Don't forget to assert rtl next to close the current worker order.

## Method
1. Read the documents of the model; note what each says it has verified.
2. Read validate.py (reading only): what it computes, what it compares with, where the reference value comes from (an independent tool, a table of the standard, a testbench value, or the model itself), how many vectors and how they were chosen.
3. Classify every kind of value the model gives — end-to-end result, intermediate values, block functions — as: independent source / indirect only / none.
4. Write down the byte/bit order and the step order the model states.
5. List what the verification does not cover and the questions that only a run can answer.

## Output: `A1.2.md`
Sections, in this order: Model (name, version or hash, language, commands) / What validate compares (table: kind of value, reference source, independent or not, vectors) / Not validated / Layout and order as the model states them / Open questions for a run (each as a command to run, for A1.4).

## Working rule (the file first)
1. First action: create the output file, with the section headings of "Output" above, each followed by `TODO`.
2. After each source you read, fill in the section(s) it answers in the file at once. Do not keep results for later.
   Every field gets its value from a command you ran or a file you read; where the output format does not name the command, use the plainest one (`md5sum FILE` for a hash, `cat -n FILE` for lines, `wc -l FILE` for a size).
   A source line number is copied from a numbered listing (`rtl show FILE FIRST LAST`, or `cat -n FILE`), never counted by yourself; a path is copied from the listing or the file that names it, not inferred.
   Change the file by rewriting it whole with `write_file` (it is short). If you use `edit` and it fails once, `read_file` the file first and take the text to replace from what you read; never repeat the same call.
   Values from a run are copied character for character from the output, as the line the tool printed; do not retype, shorten or recompute them.
3. Done = no `TODO` is left (a section that does not apply says `N/A: reason`; one you could not fill says `not_done: reason`; a field the tools do not give you, such as a tool version, is `not_done: <the reason in words, e.g. "the tool does not print a version">` at once, not looked for) and the condition of this skill holds: every kind of value the model gives (end-to-end result, intermediate values, block functions) is a row in the table with its classification.
4. Before you report, count what is left: run `grep -n TODO <your output file>` with the shell; it must print nothing. Each line it prints is a place still open: fill exactly that place, or write `not_done: <reason>` there; then run it again.
   Then report by running `rtl next "..."` with the shell tool. Text in your reply is not a command and is not a report; a final message without the command has delivered nothing.
   Do not check again what is written.
5. Time: when 60% of the time of the work order is used, mark the sections still open `not_done: reason` and send.

## Rules
- Reading only. Do not run validate; running is A1.4. Do not judge the RTL.
- Mark what a document says and what you read in the script as different things.
- A value whose only reference is the model itself is "none".

## Stop
Done is a state of the file, not a feeling: see the working rule. Report with `rtl next` and name the output file.
