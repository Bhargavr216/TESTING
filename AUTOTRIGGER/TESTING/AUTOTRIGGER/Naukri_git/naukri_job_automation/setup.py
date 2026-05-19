from setuptools import setup, find_packages

setup(
    name="naukri-automation",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "playwright",
        "pyyaml",
        "rich",
        "click",
        "jinja2",
        "requests",
        "fastapi",
        "uvicorn[standard]",
    ],
    entry_points={
        "console_scripts": [
            "naukri-auto=src.main:cli",
        ],
    },
)
