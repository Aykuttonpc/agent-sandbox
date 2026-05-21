import re
from setuptools import setup, find_packages

version = re.search(
    r'__version__ = ["\'](.+)["\']',
    open("src/json_formatter/__init__.py").read()
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
)
