# FF37 TechAssist Bot

Interactive CLI troubleshooting assistant for Forged Fiber 37 field technician support.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python src/assistant.py
```

### Web Interface
Run the web UI from the `troubleshoot-assistant` directory:
```bash
export TECHASSIST_SECRET_KEY="change-me-for-production"
python src/web_app.py
```
Then open http://localhost:5000 to select an issue and step through the flow.

## Features

- 5 troubleshooting workflows covering common issues
- 75+ solution procedures with step-by-step instructions
- Automatic session logging and analytics
- Reference links to documentation and videos

## Troubleshooting Flows

1. **ONT Not Provisioning** - ONT installation and provisioning issues
2. **Authentication Failures** - Customer connection and credential problems
3. **No Light / Fiber Issues** - Physical fiber signal problems
4. **Speed Issues** - Performance and bandwidth problems
5. **New Build Not Ready** - Facility availability and construction issues

## Analytics

View troubleshooting statistics:
```bash
# TODO: Create analytics viewer
```

## Project Structure
```
troubleshoot-assistant/
├── data/                    # Troubleshooting flows (YAML)
├── src/                     # Python source code
├── logs/                    # Session logs
└── requirements.txt         # Dependencies
```

## Built With

- Python 3.9+
- Rich (CLI interface)
- PyYAML (configuration)
- Pandas (analytics)
