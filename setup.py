from setuptools import setup, find_packages

setup(
    name="json-formatter",
    version="1.0.0",
    description="JSON formatter CLI tool",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "json-formatter=json_formatter.cli:main",
        ],
    },
)
