---
name: use-ip-model
description: "How to use a validated model from the IP library to judge a block of the design: find it, pair its blocks with the design's, compare on the design's own inputs."
version: 1.0.0-container-draft
---

# use-ip-model — comparing the design with a validated model

A model of the library is the golden source. It judges a block only when the pairing is written down
and the comparison is made on the inputs and layout the design really has.

## 1. Find it
`/opt/resources/ip_models/INDEX.md` -> the entry of the function -> its folder:
`MODEL.md` (what it models, byte/bit layout, step order, known limits), `BLOCKS.txt` (block names, inputs in
order, output). If the task sheet has a "model map" item, start from it; if it has none, write the pairing you use into your report.

## 2. Pair
For each block of the design that you want to judge, write one line (this is the "model map" of the task sheet):

    design block (signals out) <- design signals in | model block | instant the inputs are complete | layout

- *Instant:* the clock at which the inputs of the block are final. A value read while it is still being
  produced is not the value the block uses. Check it with one probe over the window before you trust a row.
- *Layout:* how the model orders bytes/bits (MODEL.md) and how the signals are joined in the probe (`+`).
  A mismatch that disappears when the layout is aligned is not a fault.
- If the design performs the steps in another order than the model, or registers its state at another point,
  compare one block at a time; do not compare whole-round states.

## 3. Compare
- Take the inputs from the design (`rtl probe`), feed them to the model block, compare the model's output
  with the design's output: `rtl blockcheck --in ... --out ... --model "..."`.
- A model block may also be run directly in the model folder (`python3 NAME.py block ...`, or the model's
  commands for whole results) to obtain a reference value. The comparison with a probed value is yours to
  make, and it counts only when instant and layout are as in the pairing.
- Work from the output of the failing block towards its inputs. The first block whose inputs are right and
  whose output is wrong holds the fault; a block whose inputs are already wrong is not judged yet.
- A match on inputs that could not have shown the fault proves nothing.

## Where your own programs go
Any program you write (a model, a comparison script, a conversion script) goes in `/tmp/ip_work/` (create it if it
does not exist). A program anywhere else makes the tool stop. To compare values you already hold, prefer
`rtl blockcheck` or a short command in the model's folder; a script is for what those cannot do.

## 4. When the model has no such block or value
Copy the folder to `/tmp/ip_work/NAME`, add only what is needed, validate the copy (`rtl model`). Or `rtl ask`.

## 5. How far the model is trusted
Take from VALIDATION.md which values have an independent source (end-to-end results, standard tables) and
which have not (for example intermediate states). A conclusion that rests only on a value without an
independent source is reported as such under "unsure".
