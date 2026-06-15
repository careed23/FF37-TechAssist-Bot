# Contributing to FF37 TechAssist Bot

Thanks for your interest in contributing to the FF37 TechAssist Bot project. This repository is a proof-of-concept troubleshooting assistant for field technicians, with a Python-based core engine, a Windows desktop UI, a Flask web app, and a React frontend.

## What this project needs

Contributions are most welcome in these areas:

- Adding or improving troubleshooting flows in YAML
- Enhancing the core flow engine or app integration
- Improving docs and developer guidance
- Fixing bugs or improving stability
- Updating the React web UI or Flask backend
- Adding or extending automated tests

## Getting started

### 1. Fork and branch

- Fork the repository and create a feature branch from `main`
- Use a descriptive branch name like `feature/add-flow`, `fix/logging`, or `docs/contributing`

### 2. Local setup

```bash
git clone https://github.com/<your-username>/FF37-TechAssist-Bot.git
cd FF37-TechAssist-Bot/troubleshoot-assistant
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

To install development dependencies:

```bash
pip install -e ".[dev]"
```

For the web frontend:

```bash
cd ../web-frontend
npm install
```

## Contribution workflow

### Reporting issues

- Open issues for bugs, feature requests, missing flows, or documentation improvements
- Provide clear reproduction steps, expected behavior, and any relevant logs
- If you are proposing a new troubleshooting flow, describe the scenario and expected decision path

### Making code changes

This repository has two main code areas:

- `troubleshoot-assistant/` — Python engine, CLI, desktop GUI, Flask backend, YAML flow data, and docs
- `web-frontend/` — React + Vite frontend

Common contribution types:

- Add or update troubleshooting flows in `troubleshoot-assistant/data/troubleshooting_flows.yaml`
- Add solution procedures and reference workflows in YAML
- Improve the flow engine in `troubleshoot-assistant/src/techassist/flow_engine.py`
- Update the desktop or web UI in `troubleshoot-assistant/src/techassist/desktop_app.py` and `web_app.py`
- Maintain logging and analytics in `troubleshoot-assistant/src/techassist/logger.py`
- Add tests in `troubleshoot-assistant/tests/`

### YAML authoring

The application uses YAML data for flow definitions and solutions.

- Keep step IDs unique within a flow
- Each option should point to either a `next` step or a `solution`, not both
- Add descriptive titles and user-facing text for questions and solution steps
- Validate syntax carefully before submitting

## Testing and validation

### Python app

From `troubleshoot-assistant/`:

```bash
pytest
```

Also test the app manually using one of the entry points:

```bash
techassist-cli
techassist-gui
techassist-web
```

### React frontend

From `web-frontend/`:

```bash
npm run dev
```

Then open the Vite-hosted app in the browser.

## Packaging

To build the Windows executable from `troubleshoot-assistant/`:

```bash
python build_exe.py
```

## Pull request expectations

When you open a pull request, please include:

- A summary of what changed and why
- Issues addressed or linked
- Testing steps you followed
- Any required manual verification
- Updated documentation if behavior or usage changed

Good PRs should be:

- Small and focused
- Well-tested
- Clear about the problem being fixed or feature being added
- Aligned with the repo’s existing structure

## Style and quality

- Prefer clear, readable Python code
- Keep YAML data structured and easy to follow
- Update docs when behavior changes
- If you add new flows, make sure they are realistic and consistent with the existing proof-of-concept model

## Documentation contributions

This repo already includes developer docs in `troubleshoot-assistant/docs/README.md` and the root `README.md`.

If you add or change flow behavior, please update documentation accordingly.

## Contact and support

If you need clarification before contributing, open an issue or leave a comment on an existing issue. This project is maintained as a proof-of-concept, so contributions that improve coverage, reliability, and workflow clarity are especially valuable.

## License

By contributing, you agree that your contributions will be licensed under the project’s MIT license.
