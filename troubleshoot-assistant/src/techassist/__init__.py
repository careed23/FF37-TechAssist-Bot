"""
FF37-TechAssist-Bot — Interactive Troubleshooting Assistant

A guided troubleshooting tool for Forged Fiber 37 (Quantum Fiber) field
technicians and service desk analysts.
"""

__version__ = "1.0.0"

import yaml
from pathlib import Path
from typing import Dict, Any


_DEFAULT_CONFIG: Dict[str, Any] = {
    "paths": {
        "data_file": "data",
        "log_file": "logs/troubleshooting_log.csv",
    },
}


def _resolve_config_path(config_path: str | Path | None) -> Path:
    """Return the resolved config file path."""
    if config_path is not None:
        return Path(config_path)
    project_root = Path(__file__).resolve().parent.parent.parent
    return project_root / "config.yaml"


def _merge_config(base: Dict[str, Any], overrides: Dict[str, Any]) -> None:
    """Shallow-merge *overrides* into *base* in place."""
    for section, values in overrides.items():
        if isinstance(values, dict) and section in base:
            base[section] = {**base[section], **values}
        else:
            base[section] = values


def _read_yaml_config(path: Path) -> Dict[str, Any] | None:
    """Read a YAML file and return its contents, or ``None`` on failure."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def load_config(config_path: str | Path | None = None) -> Dict[str, Any]:
    """Load application configuration from a YAML file.

    Looks for ``config.yaml`` relative to the project root
    (``troubleshoot-assistant/``) unless *config_path* is given explicitly.
    Falls back to built-in defaults when the file is missing or empty.

    Returns:
        Merged configuration dictionary.
    """
    resolved = _resolve_config_path(config_path)
    config: Dict[str, Any] = dict(_DEFAULT_CONFIG)

    file_config = _read_yaml_config(resolved)
    if file_config is not None:
        _merge_config(config, file_config)

    return config
