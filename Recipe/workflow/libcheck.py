import importlib
import subprocess
import sys

def ensure_dependencies():
    """
    Check if 'yadg' and 'dgpost' libraries are installed.
    If not, install them via pip (yadg first, then dgpost).
    """
    for pkg in ["yadg", "dgpost"]:
        try:
            importlib.import_module(pkg)
            print(f"'{pkg}' is already installed.")
        except ImportError:
            print(f"'{pkg}' not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
            print(f"'{pkg}' installation completed.")