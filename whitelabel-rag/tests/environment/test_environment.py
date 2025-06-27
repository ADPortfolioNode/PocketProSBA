from pathlib import Path
import os

def test_core_directories_exist():
    """Test that essential directories exist."""
    base_dir = Path(__file__).parent.parent.parent.resolve()
    essential_dirs = [
        "app",
        "scripts",
        "uploads",
        "chromadb_data",
        "logs"
    ]

    for dir_path in essential_dirs:
        full_path = base_dir / dir_path
        assert full_path.exists(), f"Essential directory {dir_path} not found at {full_path}"
