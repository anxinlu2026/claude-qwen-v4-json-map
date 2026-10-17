---
name: closing
description: "Work orders of type CLOSING: the cases the testbench lacks, and the report."
version: 1.0.0-container-draft
---

# closing — for work orders of type CLOSING

1. **Check the cases the task names but the testbench does not exercise**, with a test of your own
   (`rtl sim --tb FILE`, `rtl probe --tb FILE`); expected values come from the validated model.
2. **Write the report.** For each fault: what was wrong (file, lines), what was changed, and how it was
   confirmed (which comparison, on which input). Mark every statement "confirmed by comparison" or "not confirmed".
   Never report "fixed" without a passing `rtl sim`.
