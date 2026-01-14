#!/usr/bin/env python3
"""
Universal script runner for ParaView skill.
Automatically sets up virtual environment and installs dependencies.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.resolve()
VENV_DIR = SKILL_DIR / ".venv"
REQUIREMENTS_FILE = SKILL_DIR / "requirements.txt"

def create_venv():
    """Create virtual environment if it doesn't exist."""
    if not VENV_DIR.exists():
        print(f"Creating virtual environment in {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)
        return True
    return False

def get_venv_python():
    """Get path to Python in virtual environment."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def get_venv_pip():
    """Get path to pip in virtual environment."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"

def install_requirements():
    """Install requirements if requirements.txt exists."""
    if REQUIREMENTS_FILE.exists():
        print("Installing requirements...")
        pip_path = get_venv_pip()
        subprocess.run([str(pip_path), "install", "-r", str(REQUIREMENTS_FILE), "-q"], check=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <script.py> [args...]")
        print("\nAvailable scripts:")
        scripts_dir = SKILL_DIR / "scripts"
        for script in scripts_dir.glob("*.py"):
            if script.name != "run.py":
                print(f"  - {script.name}")
        sys.exit(1)
    
    script_name = sys.argv[1]
    script_args = sys.argv[2:]
    
    # Find script path
    script_path = SKILL_DIR / "scripts" / script_name
    if not script_path.exists():
        script_path = Path(script_name)
    
    if not script_path.exists():
        print(f"Error: Script not found: {script_name}")
        sys.exit(1)
    
    # Setup venv
    venv_created = create_venv()
    if venv_created:
        install_requirements()
    
    # Run script with venv Python
    python_path = get_venv_python()
    cmd = [str(python_path), str(script_path)] + script_args
    
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
