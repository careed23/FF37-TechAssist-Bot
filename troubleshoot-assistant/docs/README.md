# FF37-TechAssist-Bot — Developer Guide

This document covers project setup, architecture, and contribution guidelines for developers working on FF37-TechAssist-Bot.

---

## Architecture Overview

The application consists of three independent front-ends that share a common engine and logger:

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  CLI (Rich)  │  │ Desktop GUI  │  │  Web (Flask)  │
│ assistant.py │  │desktop_app.py│  │  web_app.py   │
└──────┬───────┘  └──────┬───────┘  └──────┬────────┘
       │                 │                 │
       └────────┬────────┴────────┬────────┘
                │                 │
        ┌───────▼───────┐ ┌──────▼──────┐
        │  flow_engine  │ │   logger    │
        │ decision tree │ │ CSV logging │
        └───────┬───────┘ └─────────────┘
                │
        ┌───────▼────────────┐
        │ knowledge_parser   │
        │ workflows/glossary │
        └────────────────────┘
                │
        ┌───────▼───────┐
        │  YAML data    │
        │ flows/solutions│
        │ workflow/meta │
        └───────────────┘
```

- **`flow_engine.py`** — Core engine. Loads `flows` and `solutions` from the YAML file, provides step navigation and solution lookup.
- **`knowledge_parser.py`** — Reference knowledge layer. Loads the `workflow` and `metadata` YAML sections that the flow engine ignores — glossary, procedures, escalation criteria, best practices, and ticket templates.
- **`logger.py`** — CSV-based session logger with analytics (resolution rate, common flows, average duration).
- **`assistant.py`** — Interactive CLI using the [Rich](https://github.com/Textualize/rich) library.
- **`desktop_app.py`** — Windows desktop GUI built with tkinter + ttk.
- **`web_app.py`** — Flask web application with Jinja2 templates.

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git

### Install

```bash
# Clone
git clone https://github.com/careed23/FF37-TechAssist-Bot.git
cd FF37-TechAssist-Bot/troubleshoot-assistant

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Editable install (includes all dependencies)
pip install -e .

# Or install with build tools
pip install -e ".[dev]"
```

---

## Running the Application

After installation, three entry-point commands are available:

| Command | Mode | Notes |
|---------|------|-------|
| `techassist-cli` | Interactive CLI | Requires terminal with color support |
| `techassist-gui` | Desktop GUI | Requires display (tkinter) |
| `techassist-web` | Web server | Opens at `http://127.0.0.1:5000` |

You can also run each module directly:

```bash
python -m techassist.assistant      # CLI
python -m techassist.desktop_app    # Desktop GUI
python -m techassist.web_app        # Web server
```

### Desktop GUI options

```bash
techassist-gui --flows path/to/flows.yaml --log path/to/log.csv
techassist-gui --screenshot screenshot.png  # Capture and exit
```

---

## Configuration

Application configuration lives in `config.yaml` at the project root (`troubleshoot-assistant/config.yaml`). The file is optional — built-in defaults are used if it's missing or empty.

### Supported keys

```yaml
paths:
  data_file: "data/troubleshooting_flows.yaml"   # Troubleshooting data
  log_file: "logs/troubleshooting_log.csv"        # Session log output
```

Configuration is loaded via `techassist.load_config()`:

```python
from techassist import load_config
config = load_config()
data_path = config["paths"]["data_file"]
```

---

## YAML Flow Authoring Guide

Troubleshooting data lives in `data/troubleshooting_flows.yaml`. The file has four top-level keys:

### `flows` — Decision Trees

Each flow defines a guided troubleshooting path:

```yaml
flows:
  - id: "unique-flow-id"
    name: "Human-readable name"
    description: "Brief description shown in the UI"
    steps:
      - id: "step-1"
        question: "What is the symptom?"
        options:
          - value: "No light on ONT"
            description: "The ONT power LED is off"
            next: "step-2"           # → go to another step
          - value: "Flashing light"
            description: "The ONT LED is blinking"
            solution: "sol-flash-01"  # → show a solution
```

**Rules:**
- Every option must have either `next` (step ID) or `solution` (solution ID), never both.
- Step IDs must be unique within a flow.
- Run `python -m techassist.flow_engine` from the `data/` directory to validate.

### `solutions` — Resolution Procedures

```yaml
solutions:
  - id: "sol-flash-01"
    title: "Reset ONT Power Cycle"
    steps:
      - "Unplug the ONT power adapter"
      - "Wait 30 seconds"
      - "Reconnect power and wait for solid green LED"
    reference_doc: "https://internal-docs/ont-reset"   # optional
    video: "https://training-videos/ont-reset"         # optional
    escalate_if: "ONT does not power on after 3 attempts"  # optional
```

### `workflow` — Reference Procedures (exposed via `knowledge_parser`)

Rich operational procedure documentation with glossary, decision points, step-by-step procedures, escalation criteria, and ticket templates. See existing content for the full schema.

### `metadata` — Document History

Changelog, approval, and contact information for the knowledge base.

---

## Building the Executable

The desktop GUI can be packaged as a standalone Windows `.exe`:

```bash
cd troubleshoot-assistant
pip install -e ".[build]"
python build_exe.py
```

Output: `dist/FF37-TechAssist-Bot.exe` with the YAML data bundled.

---

## Logging

Session logs are written to CSV at the configured `log_file` path (default: `logs/troubleshooting_log.csv`).

### CSV columns

| Column | Description |
|--------|-------------|
| `timestamp` | ISO 8601 timestamp |
| `flow_id` | Troubleshooting flow used |
| `flow_name` | Human-readable flow name |
| `solution_id` | Solution reached |
| `steps_taken` | JSON array of step/answer pairs |
| `num_steps` | Number of steps traversed |
| `resolved` | Whether the issue was resolved |
| `duration_seconds` | Session duration |
| `session_date` | Date (YYYY-MM-DD) |

### Analytics API

```python
from techassist.logger import TroubleshootingLogger

logger = TroubleshootingLogger("logs/troubleshooting_log.csv")
logger.get_session_count()         # int
logger.get_resolution_rate()       # float (0–100)
logger.get_most_common_flows()     # [(flow_name, count), ...]
logger.get_most_common_solutions() # [(solution_id, count), ...]
logger.get_average_duration()      # float (seconds)
```

---

## Knowledge Base

The `knowledge_parser` module exposes reference data from the YAML file:

```python
from techassist.knowledge_parser import KnowledgeBase

kb = KnowledgeBase("data/troubleshooting_flows.yaml")

kb.get_glossary()              # {"ONT": "Optical Network Terminal…", …}
kb.lookup_term("ONT")          # "Optical Network Terminal…"
kb.get_procedures()            # {"procedure_FDT": {…}, …}
kb.get_escalation_criteria()   # {"escalate_to_supervisor": …, …}
kb.get_best_practices()        # {"before_starting": […], …}
kb.get_ticket_template()       # Template string for ticket notes
kb.get_troubleshooting_tips()  # [{"issue": …, "cause": …, "solution": …}]
kb.search("ONT")               # Text search across all knowledge content
```

---

## Project Structure

```
troubleshoot-assistant/
├── config.yaml                 # Application configuration
├── logo.png                    # Quantum Fiber branding
├── pyproject.toml              # Package metadata & entry points
├── build_exe.py                # PyInstaller build script
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Build dependencies
├── data/
│   └── troubleshooting_flows.yaml   # All flow/solution/workflow data
├── docs/
│   └── README.md               # This file
├── logs/
│   └── troubleshooting_log.csv # Session logs (created at runtime)
└── src/
    └── techassist/             # Python package
        ├── __init__.py         # Package init, version, config loader
        ├── flow_engine.py      # Core decision-tree engine
        ├── knowledge_parser.py # Reference knowledge access layer
        ├── logger.py           # CSV session logger + analytics
        ├── assistant.py        # CLI entry point (Rich)
        ├── desktop_app.py      # Desktop GUI entry point (tkinter)
        └── web_app.py          # Web entry point (Flask)
```

---

## Contributing

1. **Adding flows** — Edit `data/troubleshooting_flows.yaml` following the schema above. Validate with `python -m techassist.flow_engine`.
2. **Code changes** — Use relative imports within the `techassist` package (`from .flow_engine import …`).
3. **New dependencies** — Add to both `pyproject.toml` `[project.dependencies]` and `requirements.txt`.
