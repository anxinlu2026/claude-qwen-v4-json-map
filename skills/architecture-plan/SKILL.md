---
name: architecture-plan
description: "Work orders of type ARCH-PLAN: from the ledger and the latest evidence, decide the next experiment and write the HDL work order."
version: 0.1.0-draft
---

# architecture-plan — for work orders of type ARCH-PLAN

One decision: which experiment next, and the work order that runs it.

1. **Read the ledger** (`rtl assumption list`): facts are used, not measured again; struck-out assumptions are not proposed again;
   open ones are the candidates. Read the latest HDL report only for what changed.
2. **State where you stand**: the symptom at the highest measured level, and the nearest upstream point where design and model agree
   (a fact). The fault is between that point and the symptom.
3. **List at most two candidate assumptions**, each as `OBJECT: claim`. For each: why (evidence, or "reading only"), what you
   would see if it is true, what if it is false. Register each: `rtl assumption add "OBJECT: claim"`.
4. **Choose the experiment that separates them.** If no observation separates them, say so and propose the one that narrows the interval.
   Prefer a block the model has a block for, judged on the inputs the design really has; do not compare states that are not at matching points.
5. **Check comparability** before you write the order: inputs and their source, instant, layout, conversion. Reuse the facts that already
   hold them; write down only what is new.
6. **Write the HDL work order** in the template (`skills_arch/work_orders.md`): observe, compare with, layout, meaning of each result, do not edit, stop.
7. **If the last two orders ended without a verdict, change the question** one level up (the symptom, or the matching point), and say so.
8. **Do not decide on reading alone.** What you read in the source is an assumption; the order you write is how it becomes a fact.

## The report (`plan.md`, one page)

    where we stand: <symptom> / <nearest matching point, fact number>
    assumptions: A#: object - why - if true - if false   (at most two)
    experiment: <what separates them>
    comparability: <inputs, instant, layout, conversion; fact numbers>
    HDL work order: <the text, in the template>
    unsure: <what you could not settle and what would settle it>
