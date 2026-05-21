import re
import os
from setuptools import setup, find_packages

def _get_version():
    with open(os.path.join(os.path.dirname(__file__), "src/json_formatter/__init__.py")) as f:
        match = re.search(r'__version__ = "([^"]+)"', f.read())
        if not match:
            raise RuntimeError("__version__ not found in __init__.py")
        return match.group(1)

version = _get_version()

setup(
    name="json-formatter",
    version=version,
    description="JSON formatter CLI tool",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "json-formatter=json_formatter.cli:main",
        ],
    },
    tests_require=['pytest'],
)
