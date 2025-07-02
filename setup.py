"""
Setup script for PocketPro SBA Edition
This provides a fallback setup method for environments that might have issues with pyproject.toml
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "PocketPro SBA Edition - RAG-powered business assistant"

# Read requirements
def read_requirements():
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Filter out comments and empty lines
        requirements = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove version comments
                if ' #' in line:
                    line = line.split(' #')[0].strip()
                requirements.append(line)
        return requirements
    except FileNotFoundError:
        return []

setup(
    name="pocketpro-sba",
    version="1.0.0",
    description="PocketPro SBA Edition - RAG-powered business assistant",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="StainlessDeoism.biz",
    author_email="support@stainlessdeoism.biz",
    url="https://github.com/yourusername/pocketpro-sba",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=read_requirements(),
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    keywords=["rag", "sba", "business", "ai", "assistant"],
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.json", "*.yaml", "*.yml", "*.html"],
    },
)
