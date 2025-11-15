#!/usr/bin/env python3
"""
Setup script for Tules - Background agent runner for Claude Code and Gemini CLI

Note: This is a simple setup.py for pip installation support.
For most users, the install.sh script is the recommended installation method.
"""

from setuptools import setup
from pathlib import Path

# Read the README for long description
this_directory = Path(__file__).parent
try:
    long_description = (this_directory / "README.md").read_text(encoding='utf-8')
except FileNotFoundError:
    long_description = "Background agent runner for Claude Code and Gemini CLI"

setup(
    name="tules",
    version="1.0.0",
    author="Tules Contributors",
    description="Background agent runner for Claude Code and Gemini CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Tules",  # Update with actual repo URL

    # Include Python modules
    py_modules=["ai_provider"],

    # Include the main scripts
    scripts=[
        "Tules.py",
        "Tules-sessions.py",
        "!",
    ],

    python_requires=">=3.8",

    install_requires=[
        "rich>=13.0.0",
        "click>=8.0.0",
        "schedule>=1.1.0",
    ],

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Environment :: Console",
    ],

    keywords="claude gemini ai cli automation docker background agents",

    project_urls={
        "Bug Reports": "https://github.com/yourusername/Tules/issues",  # Update
        "Source": "https://github.com/yourusername/Tules",  # Update
    },
)
