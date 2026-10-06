# agent-foundry

A command-line tool that scaffolds a working Python agent project in one command.
The scaffold includes a manifest, a skill description, a runnable entrypoint,
and a test suite — all using only the Python standard library.

## Install

No dependencies. Requires Python 3.8 or newer.

```sh
git clone https://github.com/MohammedAbdelshafy/agent-foundry.git
cd agent-foundry
```

Run it directly:

```sh
python3 agent_foundry.py --help
```

## Usage

### Scaffold a new agent

```sh
python3 agent_foundry.py new my-agent --dir ./projects
```

This creates `./projects/my-agent/` containing:

- `manifest.json` — agent manifest: name, version, description, entrypoint,
  skills list, capabilities, and security fields
- `SKILL.md` — skill description in the standard `name`/`description`
  frontmatter + Workflow/Output format, customized to the agent name
- `agent.py` — runnable entrypoint; reads its own `manifest.json`
- `tests/test_agent.py` — unit tests for the scaffolded agent
- `README.md` — usage notes for the scaffolded project

Run the scaffolded agent:

```sh
python3 projects/my-agent/agent.py --task "hello"
# hello from my-agent: manifest wiring OK
```

Test the scaffolded agent:

```sh
cd projects/my-agent && python3 -m unittest discover -s tests
```

Name rules: lowercase letters, numbers, and hyphens only. A non-empty target
directory is not overwritten unless `--force` is passed.

### Validate a project

```sh
python3 agent_foundry.py validate ./projects/my-agent
# valid agent project: /abs/path/projects/my-agent
```

Validation checks that `manifest.json` parses and contains the required keys
(`name`, `version`, `description`, `entrypoint`, `skills` as a list), that the
entrypoint file exists, and that `SKILL.md` is present. It exits non-zero and
lists problems otherwise.

## Inputs / outputs

- `new <name> [--dir DIR] [--force]` → writes files under `<DIR>/<name>/`,
  prints the target path, exit 0. Exit 2 on invalid name or refusal to
  overwrite a non-empty directory without `--force`.
- `validate <project-dir>` → prints `valid agent project: ...` (exit 0) or a
  list of problems (exit 1).

## Limits

- Scaffolded agents are templates: the default entrypoint only answers a task
  string and proves manifest wiring. Real tools, credentials, and integrations
  are left for the developer to add.
- The generator and scaffolded projects use only the Python standard library;
  no packaging, no network calls.
- `validate` checks structure, not behavior — it does not run the agent's tests.

## Tests

```sh
python3 -m unittest discover -s tests
```

## License

MIT — see [LICENSE](LICENSE).
