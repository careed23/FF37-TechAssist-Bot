from pathlib import Path
import os
import subprocess
import sys

APP_NAME = "FF37-TechAssist-Bot"
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "troubleshooting_flows.yaml"
ENTRYPOINT = BASE_DIR / "src" / "desktop_app.py"


def build_executable() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Flows file not found at {DATA_FILE}")

    add_data = [f"{DATA_FILE}{os.pathsep}data"]

    command = [
        sys.executable,
        "-m",
        "pyinstaller",
        "--name",
        APP_NAME,
        "--onefile",
        "--windowed",
        "--noconfirm",
    ]
    for payload in add_data:
        command.extend(["--add-data", payload])
    command.append(str(ENTRYPOINT))

    subprocess.run(command, check=True, cwd=BASE_DIR)


if __name__ == "__main__":
    build_executable()
