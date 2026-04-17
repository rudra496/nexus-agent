from setuptools import setup, find_packages

setup(
    name="nexus-agent",
    version="0.1.0",
    description="The Zero-Config, Self-Evolving Local AI Agent Framework",
    author="Nexus Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "litellm>=1.0.0",
        "requests>=2.31.0",
        "networkx>=3.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "nexus=cli:app",
        ],
    },
    python_requires=">=3.10",
)