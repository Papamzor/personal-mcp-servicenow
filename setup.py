from setuptools import setup, find_packages

setup(
    name="personal-mcp-servicenow",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "orjson",
        "mcp-server"
    ],
    python_requires=">=3.8",
    author="Your Name",
    description="MCP ServiceNow integration tools",
    entry_points={
        "console_scripts": [
            "mcp-snow=personal_mcp_servicenow_main:main",
        ],
    }
)