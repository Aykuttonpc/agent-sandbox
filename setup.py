import re
import pathlib
from setuptools import setup, find_packages

version = re.search(
    r'^__version__\s*=\s*[\'"]([\'"]^]+)[\'"]
',
    pathlib.Path("src/json_formatter/__init__.py").read_text(),
    re.MULTILINE
).group(1)

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
