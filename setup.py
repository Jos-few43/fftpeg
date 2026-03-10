#!/usr/bin/env python3
"""Setup script for fftpeg - Terminal FFmpeg TUI."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="fftpeg",
    version="0.1.0",
    author="Jos-few43",
    author_email="",
    description="A modern Terminal User Interface (TUI) for ffmpeg operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Jos-few43/fftpeg",
    packages=find_packages(where="."),
    package_dir={"": "."},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Multimedia :: Video :: Conversion",
        "Topic :: Utilities",
        "Environment :: Console :: Curses",
    ],
    python_requires=">=3.9",
    install_requires=[
        "textual>=6.0.0",
        "rich>=14.0.0",
        "ffmpeg-python>=0.2.0",
        "pymediainfo>=7.0.0",
    ],
    entry_points={
        "console_scripts": [
            "fftpeg=src.main:main",
        ],
    },
    keywords="ffmpeg tui terminal video conversion multimedia",
    project_urls={
        "Bug Reports": "https://github.com/Jos-few43/fftpeg/issues",
        "Source": "https://github.com/Jos-few43/fftpeg",
    },
)
