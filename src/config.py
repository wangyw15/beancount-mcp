import os
from typing import TypedDict

from dotenv import load_dotenv


class Configuration(TypedDict):
    entry_file: str
    write_file: str
    read_only: bool


def load_config() -> Configuration:
    load_dotenv()
    return {
        "entry_file": os.environ["BEANCOUNT_MCP_ENTRY_FILE"],
        "write_file": os.environ.get("BEANCOUNT_MCP_WRITE_FILE", ""),
        "read_only": os.environ.get("BEANCOUNT_MCP_READ_ONLY", "y").lower()
        in ["y", "yes", "true"],
    }
