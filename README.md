<div align="center">

# FF37 TechAssist Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-00ADD8?logo=python&logoColor=white)](https://github.com/TomSchimansky/CustomTkinter)
[![Release](https://img.shields.io/badge/Release-v1.0-blue)](https://github.com/careed23/FF37-TechAssist-Bot/releases)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/careed23/FF37-TechAssist-Bot/pulls)

**Professional troubleshooting assistant for Forged Fiber 37 field technician support**

A Windows desktop application that provides step-by-step troubleshooting guidance for common fiber optic installation and service issues. Built to streamline technical support workflows and reduce resolution time in the field.

</div>

---

## 💡 Why This Tool Exists

### The Problem
Field tech support at scale presents real challenges:
- **Training Overhead** - Weeks of training required for new service desk analysts to learn troubleshooting procedures across multiple systems
- **Ticket Inefficiency** - Unnecessary escalations created when analysts don't know the exact resolution steps, clogging the queue
- **Knowledge Gaps** - Critical troubleshooting steps forgotten or skipped, leading to callbacks and repeat tickets
- **First Call Resolution** - Inconsistent outcomes when analysts rely on memory rather than standardized procedures

### The Solution
This tool was built as a **proof of concept** to address these operational pain points:

✅ **Reduces Training Time** - New hires can start resolving tickets immediately with guided workflows instead of memorizing hundreds of procedures  
✅ **Improves First Call Resolution** - Step-by-step guidance ensures nothing is missed, fixing issues on the first attempt  
✅ **Eliminates Unnecessary Tickets** - Prevents premature escalations by walking analysts through complete diagnostic processes  
✅ **Serves as Training Wheels** - Acts as a knowledge companion until procedures become second nature  
✅ **Standardizes Support Quality** - Everyone follows the same proven troubleshooting paths regardless of experience level  

**Real Impact:** Field techs and service desk analysts can confidently handle complex fiber optic issues without constantly referencing documentation or escalating to senior staff.

---

## 🚀 Quick Start

### Download & Run
1. Download the latest release: [FF37-TechAssist-Bot.exe](https://github.com/careed23/FF37-TechAssist-Bot/releases)
2. Double-click `FF37-TechAssist-Bot.exe` to launch
3. **No installation required** - runs as a standalone executable

> **Note:** Windows may show a SmartScreen warning for unsigned executables. Click "More info" → "Run anyway" to proceed.

---

## ✨ Features

### 5 Comprehensive Troubleshooting Flows
- **ONT Not Provisioning** - Installation and provisioning issues
- **Authentication Failures** - Customer connection and credential problems  
- **No Light / Fiber Issues** - Physical fiber signal diagnostics
- **Speed Issues** - Performance and bandwidth troubleshooting
- **New Build Not Ready** - Facility availability and construction status

### Built for Efficiency
- **75+ Solution Procedures** - Step-by-step resolution guides
- **Automatic Session Logging** - Track troubleshooting history and analytics
- **Reference Documentation** - Links to internal docs and video tutorials
- **Escalation Guidance** - Clear indicators for when to escalate issues

---

## 🖥️ System Requirements

- **OS:** Windows 10 or Windows 11
- **RAM:** 4GB minimum
- **Disk Space:** ~50MB
- **Display:** 1100x800 minimum resolution

---

## 📊 How It Works

1. **Select Troubleshooting Flow** - Choose the issue category from the main menu
2. **Answer Diagnostic Questions** - Follow the guided step-by-step process
3. **Get Resolution Procedure** - Receive detailed instructions for fixing the issue
4. **Log Session Results** - Track whether the issue was resolved for analytics

### Example Workflow
```
Customer reports no internet → Select "Authentication Failures" flow
↓
System walks through ONT status → Credentials check → Network config
↓
Solution: "Update Improv Credentials Using QMate" (step-by-step guide)
↓
Mark resolved or escalate → Session logged automatically
```

---

## 📁 Application Structure

```
FF37-TechAssist-Bot.exe         # Standalone Windows executable
└── Embedded Resources:
    ├── Quantum Fiber branding
    ├── Troubleshooting flow data
    └── Solution procedures
```

**Session Logs Location:**  
`%APPDATA%\FF37-TechAssist-Bot\logs\troubleshooting_log.csv`

---

## 🛠️ For Developers

### Building from Source

**Prerequisites:**
- Python 3.9 or higher
- Git

**Setup & Build:**
```bash
# Clone repository
git clone https://github.com/careed23/FF37-TechAssist-Bot.git
cd FF37-TechAssist-Bot/troubleshoot-assistant

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Build executable
python build_exe.py
```

The compiled executable will be in `troubleshoot-assistant/dist/FF37-TechAssist-Bot.exe`

### Tech Stack
- **Framework:** CustomTkinter (modern UI)
- **Engine:** PyYAML-based flow processor
- **Packaging:** PyInstaller (single-file executable)
- **Logging:** CSV-based session tracking

### Project Structure
```
troubleshoot-assistant/
├── data/                       # Troubleshooting flows (YAML)
│   ├── logo.png               # Quantum Fiber branding
│   └── troubleshooting_flows.yaml
├── src/                        # Python source code
│   ├── desktop_app.py         # Main GUI application
│   ├── flow_engine.py         # Troubleshooting logic
│   └── logger.py              # Session tracking
├── build_exe.py               # PyInstaller build script
└── requirements.txt           # Python dependencies
```

---

## 📝 Troubleshooting Flows Overview

### 1. ONT Not Provisioning
Diagnoses why ONT devices aren't coming online in Calix/Adtran systems.

**Key Decision Points:**
- ONT state (O1, O5, not visible)
- Fiber signal levels (RX power)
- Serial number verification
- Service profile assignment

### 2. Authentication Failures  
Resolves customer connection issues related to credentials and network authentication.

**Key Decision Points:**
- ONT provisioning status
- Optius programming completion
- Improv credential verification
- VLAN configuration

### 3. No Light / Fiber Issues
Addresses physical fiber signal problems and hardware connectivity.

**Key Decision Points:**
- Fiber signal measurements (dBm)
- Connector cleaning status
- Splitter ratio analysis
- FDH connectivity

### 4. Speed Issues
Diagnoses bandwidth and performance problems.

**Key Decision Points:**
- Speed test results vs provisioned speed
- Bandwidth profile verification
- WiFi vs wired performance
- OLT congestion indicators

### 5. New Build Not Ready
Handles situations where customer installations are scheduled but facilities aren't available.

**Key Decision Points:**
- Address existence in Optius/ODiN
- Fiber construction status
- OLT commissioning
- TA Path availability

---

## 📊 Session Analytics

The application automatically logs all troubleshooting sessions to:  
`%APPDATA%\FF37-TechAssist-Bot\logs\troubleshooting_log.csv`

**Tracked Metrics:**
- Flow usage frequency
- Resolution rates
- Average session duration
- Most common solutions
- Timestamp data for trend analysis

Use this data to identify training needs, optimize procedures, and track team performance.

---

## 🔒 Security & Privacy

- **No Internet Connection Required** - Runs completely offline
- **Local Data Only** - Session logs stored locally on the machine
- **No PII Collection** - Logs contain flow data, not customer information
- **Read-Only Operations** - Application doesn't modify system files or registry

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Colten A. Reed**  
IT Support Specialist | Qualfon  
Milan, Tennessee

*Built from firsthand observation of support operations - watching new hires struggle through training, seeing tickets pile up from avoidable escalations, and recognizing the need for a tool that reduces both training time and ticket overhead while improving first call resolution rates.*

---

## 🤝 Contributing

This is an internal tool for Forged Fiber 37 operations. For questions, issues, or enhancement requests, please contact the IT Support team.

---

## 📚 Additional Resources

For detailed solution procedures and reference documentation, consult the internal Quantum Fiber knowledge base and training materials referenced within the application.
