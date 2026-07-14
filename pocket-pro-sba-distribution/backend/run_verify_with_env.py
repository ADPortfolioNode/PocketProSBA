#!/usr/bin/env python3
"""
Load the distribution .env file into os.environ then run verify_environment.py
"""
import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
ENV_PATH = ROOT / '.env'
VERIFY_PATH = Path(__file__).parent / 'verify_environment.py'

if ENV_PATH.exists():
    for raw in ENV_PATH.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k, v)
else:
    print(f".env not found at {ENV_PATH}")

if VERIFY_PATH.exists():
    # Ensure the distribution folder is on sys.path so imports like
    # `backend.services` resolve (we want the parent of `backend` on sys.path)
    dist_dir = str(ROOT)
    if dist_dir not in sys.path:
        sys.path.insert(0, dist_dir)
    # Set CWD to distribution folder so relative data paths work
    os.chdir(dist_dir)
    runpy.run_path(str(VERIFY_PATH), run_name='__main__')
else:
    print(f"verify_environment.py not found at {VERIFY_PATH}")
