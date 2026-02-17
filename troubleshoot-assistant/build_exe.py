from pathlib import Path
import os
import subprocess
from shutil import copy2
import sys

APP_NAME = "FF37-TechAssist-Bot"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGO_FILE = BASE_DIR / "logo.png"
ENTRYPOINT = BASE_DIR / "launch_desktop.py"
PACKAGE_DIR = BASE_DIR / "src"


def build_executable() -> None:
    yaml_files = list(DATA_DIR.glob("*.yaml")) + list(DATA_DIR.glob("*.yml"))
    if not yaml_files:
        raise FileNotFoundError(f"No YAML files found in {DATA_DIR}")

    if not LOGO_FILE.exists():
        raise FileNotFoundError(f"Logo file not found at {LOGO_FILE}")

    add_data = [
        f"{LOGO_FILE}{os.pathsep}.",
    ]
    for yaml_file in yaml_files:
        add_data.append(f"{yaml_file}{os.pathsep}data")

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
        "--hidden-import",
        "techassist",
        "--hidden-import",
        "techassist.flow_engine",
        "--hidden-import",
        "techassist.logger",
        "--hidden-import",
        "techassist.desktop_app",
    ]
    for payload in add_data:
        command.extend(["--add-data", payload])
    command.append(str(ENTRYPOINT))

    subprocess.run(command, check=True, cwd=BASE_DIR)

    dist_dir = BASE_DIR / "dist"
    data_dir = dist_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for yaml_file in yaml_files:
        copy2(yaml_file, data_dir / yaml_file.name)


if __name__ == "__main__":
    build_executable()
