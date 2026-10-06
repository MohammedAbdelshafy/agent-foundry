# agent-foundry

A command-line tool that scaffolds a working Python agent project in one command.
The scaffold includes a manifest, a skill description, a runnable entrypoint,
and a test suite — all using only the Python standard library.

## Install

No dependencies. Requires Python 3.9 or newer.

```sh
git clone https://github.com/MohammedAbdelshafy/agent-foundry.git
cd agent-foundry
```

Run it directly:

```sh
python3 agent_foundry.py --help
```

Or install it to get the `agent-foundry` console script:

```sh
pip install .
# or straight from GitHub:
pip install git+https://github.com/MohammedAbdelshafy/agent-foundry.git
```

After installing, replace `python3 agent_foundry.py` with `agent-foundry` in
the commands below (and `python3 -m agent_foundry` also works).

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

Name rules: lowercase letters, numbers, and hyphens only; the name must not
start or end with a hyphen. A non-empty target directory is not overwritten
unless `--force` is passed.

### Validate a project

```sh
python3 agent_foundry.py validate ./projects/my-agent
# valid agent project: /abs/path/projects/my-agent
```

Validation checks that `manifest.json` parses and contains the required keys
(`name`, `version`, `description` as strings; `entrypoint` as a string;
`skills` as a list of strings), that the entrypoint is a relative path inside
the project and the file exists, and that `SKILL.md` is present. It exits
non-zero and lists problems otherwise.

## Inputs / outputs

- `new <name> [--dir DIR] [--force]` → writes files under `<DIR>/<name>/`,
  prints the target path, exit 0. Exit 2 on invalid name, an unusable
  `--dir`/target path, or refusal to overwrite a non-empty directory without
  `--force`; exit 1 if files cannot be created or written.
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
