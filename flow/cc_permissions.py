"""Permission rules for the HDL model run through the Claude Code interface (used with --permission-mode dontAsk: whatever is not allowed here is denied).
Measured: ls, find, cat of a file outside, Read outside are refused; --allowedTools alone does not restrict. // = absolute path in the rule syntax."""
import os
def allowed(cell, repo):
    cellp = os.path.abspath(cell); P = lambda x: '//' + x.lstrip('/')     # permission-rule syntax: // = absolute path
    allowed = [f'Read({P(cellp)}/exchange/**)', f'Read({P(cellp)}/work/**)', f'Read({P(cellp)}/hdl_bin/**)', f'Read({P(cellp)}/state/ip_work/**)',
               f'Read({P(repo)}/flow/*.py)', f'Read({P(repo)}/docs/schema_block_json.zh.md)', f'Write({P(cellp)}/exchange/**)', f'Edit({P(cellp)}/exchange/**)',
               'Bash(export *)', 'Bash(rtl *)', 'Bash(rtl)', f'Bash(python3 {repo}/flow/*)', f'Bash(cp {cellp}/exchange/* {cellp}/exchange/*)'] + \
              [f'Bash({t} {cellp}/*)' for t in ('cat', 'ls', 'head', 'tail', 'wc', 'diff')] + [f'Bash({t} -* {cellp}/*)' for t in ('cat', 'ls', 'head', 'tail', 'wc', 'diff')]
    return allowed
