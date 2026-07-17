#!/usr/bin/env python3
"""Runner for verify_environment.py that bootstraps the environment.
Load the distribution .env file into os.environ then run verify_environment.py
"""
import os
import runpy
import sys
from pathlib import Path

def main():
    """
    Set up the environment and run the verification script.
    """
    # Project root is the parent of the 'backend' directory where this script lives
    root = Path(__file__).parent.parent
    env_path = root / '.env'
    verify_path = root / 'backend' / 'verify_environment.py'

    if env_path.exists():
        print(f"Loading environment variables from: {env_path}")
        for raw in env_path.read_text(encoding='utf-8').splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k, v.strip())
    else:
        print(f"[WARNING] .env file not found at {env_path}")

    if verify_path.exists():
        # Ensure the project root is on sys.path so imports like `backend.services` resolve
        project_dir = str(root)
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)
        # Set CWD to project root so relative data paths work
        os.chdir(project_dir)
        print(f"Running verification script: {verify_path}")
        runpy.run_path(str(verify_path), run_name='__main__')
    else:
        print(f"[ERROR] verify_environment.py not found at {verify_path}")

if __name__ == "__main__":
    main()
