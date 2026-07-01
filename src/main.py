from datetime import datetime

from mcp.server.fastmcp import FastMCP

from _beancount import Beancount as BeancountUtil
from config import load_config

config = load_config()

mcp = FastMCP("beancount")
bc = BeancountUtil(config["entry_file"], config["write_file"])


@mcp.tool()
def reload_entries() -> str:
    """Reload Beancount ledger"""
    bc.load()
    return "Reload successful"


@mcp.tool()
def get_accounts() -> str:
    """Get all accounts of the Beancount ledger"""
    return "\n".join(bc.accounts)


@mcp.tool()
def get_balance(account: str, from_date: str = "", to_date: str = "") -> str:
    """Get balance for the given account. If from_date and to_date provided, the result will be the balance between the date range.
    Usage:
    Leave from_date and to_date empty to calculate all entries for balance.
    If the user asks for the balance of the given date for with account Asset, Liabilities, and Equity, leave from_date empty and fill to_date, this will provide balance of the given date.
    If the user asks for the balance of the given date range for with account Income and Expenses, leave from_date empty and fill to_date, this will provide total expenses or income within the date range.
    For other use cases, please confirm with the user.

    Args:
        account: The account to be calculated. Please use the name from get_accounts tool.
        from_date: Optional. The beginning of the date range. Format: YYYY-MM-DD (for example, 2026-07-01). Default: empty stands for timestamp 0
        to_date: Optional. The end of the date range. Format: YYYY-MM-DD (for example, 2026-07-01). Default: empty stands for today
    """
    _from = (
        datetime.strptime(from_date, "%Y-%m-%d").date()
        if from_date
        else datetime.fromtimestamp(0).date()
    )
    _to = (
        datetime.strptime(to_date, "%Y-%m-%d").date()
        if to_date
        else datetime.now().date()
    )

    return bc.get_balance(account, _from, _to).to_string()


@mcp.tool()
def add_transactions(transactions: str) -> str:
    """Add transaction to the Beancount ledger. If there's syntax error with the transction, the tool will report the errors and stops writing.

    Args:
        transacionts: Transctions in Beancount format string.
    """
    if config["read_only"]:
        return "User has configured the MCP as read only, unable to write transactions"

    errors = bc.add_transactions(transactions)
    if len(errors) == 0:
        return "Transactions added successfully"

    return str(errors)


def main():
    reload_entries()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
