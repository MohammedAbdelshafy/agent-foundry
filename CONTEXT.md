---
type: repository
status: active
owner_repo: MohammedAbdelshafy/agent-foundry
product_name: Agent Foundry
source_of_truth: https://github.com/MohammedAbdelshafy/agent-foundry
---

# Agent Foundry CONTEXT

One job: create a consistent starter project and check whether its required files and configuration are present.

## Inputs
- Commands and scope: [README](README.md)
- Implementation: [agent_foundry.py](agent_foundry.py)
- Tests: [tests](tests/)

## Process
1. Create a named project in a new or explicitly approved target directory.
2. Generate the manifest, instructions, entrypoint and test starter.
3. Validate the required manifest fields and project paths.
4. Refuse unsafe overwrites unless the user explicitly passes the supported force option.
5. Run the generated project's tests.

## Output
A starter Python project and a validation result.

## Check
Run the repository's test suite. Verify that invalid names, path traversal, missing files and non-empty target directories are handled as documented.
