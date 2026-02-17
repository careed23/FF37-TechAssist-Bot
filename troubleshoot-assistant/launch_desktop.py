"""PyInstaller / direct-run entry point for the desktop GUI.

This thin wrapper exists so PyInstaller analyses the ``techassist``
package via a normal ``from techassist…`` import rather than trying
to run ``desktop_app.py`` as ``__main__`` outside its package.
"""

import sys
from pathlib import Path

# Ensure the src/ directory is on sys.path so the techassist package
# is importable regardless of the current working directory.
_src_dir = str(Path(__file__).resolve().parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from techassist.desktop_app import main  # noqa: E402

if __name__ == "__main__":
    main()
