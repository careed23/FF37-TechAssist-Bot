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

### Desktop GUI (Windows 11)
Run the native desktop interface from the `troubleshoot-assistant` directory:
```bash
python src/desktop_app.py
```
The Windows 11 Python installer bundles Tkinter, so no additional setup is required. The
desktop UI uses the native Windows theme with Segoe UI styling for a Windows 11 look.

### Build Windows executable
From the `troubleshoot-assistant` directory on Windows:
```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python build_exe.py
```
The executable is created at `troubleshoot-assistant/dist/FF37-TechAssist-Bot.exe`.
Logs for the packaged app are written to `%APPDATA%\FF37-TechAssist-Bot\logs`.

### Web Interface
Run the web UI from the `troubleshoot-assistant` directory:
```bash
export TECHASSIST_SECRET_KEY="$(python -c \"import os; print(os.urandom(32).hex())\")"
python src/web_app.py
```
Then open http://localhost:5000 to select an issue and step through the flow. If the
secret key environment variable is not set, the app creates a local key in
`troubleshoot-assistant/logs/.secret_key` for development use. Use a production WSGI
server (for example Gunicorn) and set `TECHASSIST_SECRET_KEY` in production.

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
