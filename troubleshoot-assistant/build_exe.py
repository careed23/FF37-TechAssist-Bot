from pathlib import Path
import os
import subprocess
from shutil import copy2
import sys

APP_NAME = "FF37-TechAssist-Bot"
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "troubleshooting_flows.yaml"
LOGO_FILE = BASE_DIR / "logo.png"
ENTRYPOINT = BASE_DIR / "src" / "techassist" / "desktop_app.py"
PACKAGE_DIR = BASE_DIR / "src"


def build_executable() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Flows file not found at {DATA_FILE}")

    if not LOGO_FILE.exists():
        raise FileNotFoundError(f"Logo file not found at {LOGO_FILE}")

    add_data = [
        f"{DATA_FILE}{os.pathsep}data",
        f"{LOGO_FILE}{os.pathsep}.",
    ]

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        APP_NAME,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--paths",
        str(PACKAGE_DIR),
    ]
    for payload in add_data:
        command.extend(["--add-data", payload])
    command.append(str(ENTRYPOINT))

    subprocess.run(command, check=True, cwd=BASE_DIR)

    dist_dir = BASE_DIR / "dist"
    data_dir = dist_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    copy2(DATA_FILE, data_dir / DATA_FILE.name)


if __name__ == "__main__":
    build_executable()
