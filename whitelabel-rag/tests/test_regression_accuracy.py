import os
import difflib
import pytest

INSTRUCTIONS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads', 'instructions.md'))

def load_instructions():
    with open(INSTRUCTIONS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
        return content[:1000]  # Return first 1000 chars as summary

import ast

def extract_docstrings_and_comments(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        parsed = ast.parse(source)
        docstrings = []
        for node in ast.walk(parsed):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    docstrings.append(docstring)
        # Extract comments (lines starting with #)
        comments = []
        for line in source.splitlines():
            line_strip = line.strip()
            if line_strip.startswith('#'):
                comments.append(line_strip.lstrip('#').strip())
        return "\n".join(docstrings + comments)
    except Exception:
        return ""

import os

def get_all_py_files(root_dir):
    py_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                py_files.append(os.path.join(dirpath, filename))
    return py_files

def get_codebase_text():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'whitelabel-rag'))
    py_files = get_all_py_files(root_dir)
    texts = []
    for file in py_files:
        texts.append(extract_docstrings_and_comments(file))
    return "\n".join(texts)

def calculate_similarity(a: str, b: str) -> float:
    seq = difflib.SequenceMatcher(None, a, b)
    return seq.ratio()

def test_regression_and_accuracy():
    instructions_text = load_instructions()
    codebase_text = get_codebase_text()

    similarity = calculate_similarity(instructions_text, codebase_text)
    regression = 1 - similarity

    print(f"Regression Percentage: {regression * 100:.2f}%")
    print(f"Accuracy Percentage: {similarity * 100:.2f}%")

    # Assert accuracy threshold (example: at least 50%)
    assert similarity >= 0.5, "Accuracy below acceptable threshold"

if __name__ == "__main__":
    pytest.main([__file__])
