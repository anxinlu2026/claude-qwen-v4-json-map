Accepted. Note for later: the testbench clears i_key and i_data one cycle after start, so the design must keep what it needs.

WORK ORDER 0.3
Goal:      Run the testbench once on the untouched design.
Use:       rtl sim
Done when: you have the expected and the observed value of every failing case.
Report:    rtl next "found: ... / evidence: run number / unsure: ..."
