# RETRACE agent (self-driving-agents format)

This folder packages RETRACE as a [self-driving agent](https://github.com/vectorize-io/self-driving-agents):

- `bank-template.json`: Hindsight bank config (reflect/retain/observations missions, dispositions), **directives** (no causal claims, weak-evidence rules, people are not causes, open questions not predictions) and **mental models** (`current-beliefs`, `experiment-history`) that Hindsight keeps refreshed as memory grows.
- `*.md`: seed knowledge (persona, company background, method, experiment playbook).

## Install into OpenClaw

```bash
npx @vectorize-io/self-driving-agents install ./retrace-agent --harness openclaw
# or straight from GitHub:
npx @vectorize-io/self-driving-agents install VijayaY836/retrace/retrace-agent --harness openclaw
```

Point the Hindsight OpenClaw plugin at the same bank as the dashboard (`retrace-nova`) so chat and dashboard share one memory. See the main README.
