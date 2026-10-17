# Local IP model library

Reference models (executable, step-by-step) of standard functions, used as the trusted source of
expected values when designing, verifying or debugging RTL.
In the agent container it is at `/opt/resources/ip_models`.

## How to use it (for the agent)

1. Read `INDEX.md`. Look for the function your design implements (by name, standard, or keywords).
2. If an entry exists, read its `MODEL.md`, run its validation (`rtl model <folder>`) and use the model
   as described there. Do not write another model of the same function.
3. If an entry lacks a value you need, copy the folder to `/tmp/ip_work/NAME`, change only what is
   needed, and validate the copy (`rtl model /tmp/ip_work/NAME`).
4. If no entry exists, build the model in `/tmp/ip_work/NAME`: read the standard that defines the
   function (`/opt/resources/standards`) and write it step by step from it, not from memory. Add a
   `validate.py` that compares its outputs with the testbench's values or a reliable established
   implementation (`/opt/resources/reference_tools`) and ends with `HARNESS PASS` or `HARNESS FAIL`.

## What every entry contains

```
ip_models/<name>/
  MODEL.md      what it models, which standard and which clause, how to run it, what intermediate
                values it can print, known limits
  SOURCE.md     where the code came from (URL, author, version or commit, licence), or — for a model
                written here — which standard document and clauses it was written from
  VALIDATION.md how it was checked: which independent source, which vectors, how many, date, by whom
  <code files>
```

An entry may be listed in `INDEX.md` as `validated` only when VALIDATION.md records a check against
a source that is independent of the model itself (for example a different trusted tool, or the
worked examples published with the standard).

## Adding an entry (for maintainers)

- Prefer established open-source code with a clear licence, or code published with the standard.
- Record the source and licence before using the code.
- Validate, then set the status in `INDEX.md`.
- For a model that had to be written here, SOURCE.md names the standard and the clauses it follows.
