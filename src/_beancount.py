from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

from beancount import Inventory, RealAccount, loader
from beancount.core import realization
from beancount.core.data import (
    Balance,
    BeancountError,
    Close,
    Directives,
    Document,
    Note,
    Open,
    Pad,
    Transaction,
)
from beancount.parser import parser, printer
from dotenv import load_dotenv

load_dotenv()


class Beancount:
    def __init__(self, entry_file: str, write_file: str = "") -> None:
        self._entry_file = Path(entry_file)
        self._write_file = Path(write_file or self._entry_file)

        self._entries: Directives = []
        self._errors: list[BeancountError] = []
        self._options: Any = None

        self.printer = printer.EntryPrinter()

    def load(self):
        if not (self._entry_file.exists and self._entry_file.is_file()):
            raise ValueError(f"{self._entry_file} not found!")
        self._entries, self._errors, self._options = loader.load_file(self._entry_file)

    def get_balance(
        self, account: str, from_date: date | None = None, to_date: date | None = None
    ) -> Inventory:
        _from = from_date or datetime.fromtimestamp(0).date()
        _to = to_date or datetime.now().date()
        _entries: Directives = []
        for entry in self._entries:
            if isinstance(entry, (Open, Close)):
                _entries.append(entry)
            if _from <= entry.date and entry.date <= _to:
                _entries.append(entry)

        real = realization.realize(_entries)
        print(real.items())
        _account: RealAccount = cast(RealAccount, realization.get(real, account))
        return _account.balance

    def filter_entries(
        self,
        account: str = "",
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        _from = from_date or datetime.fromtimestamp(0).date()
        _to = to_date or datetime.now().date()

        entries: Directives = []
        for entry in self._entries:
            if not (_from <= entry.date and entry.date <= _to):
                continue

            keep_entry = True
            if account:
                if isinstance(entry, Transaction):
                    account_match = False
                    for posting in entry.postings:
                        if posting.account == account:
                            account_match = True
                            break
                    keep_entry = account_match
                elif isinstance(entry, (Open, Close, Pad, Balance, Note, Document)):
                    if entry.account != account:
                        keep_entry = False

            if keep_entry:
                entries.append(entry)

        return entries

    def validate(self, transactions: str) -> bool:
        _, errors, _ = parser.parse_string(transactions)
        return len(errors) == 0

    def add_transactions(self, transactions: str) -> list[BeancountError]:
        directives, errors, _ = parser.parse_string(transactions)
        if len(errors) > 0:
            return errors

        with self._write_file.open(
            "a" if self._write_file.exists() else "w", encoding="utf-8"
        ) as f:
            f.write("\n".join([self.printer(directive) for directive in directives]))

        f.close()
        return []

    @property
    def accounts(self) -> list[str]:
        real = realization.realize(self._entries)
        accounts: list[str] = []

        def _get_accounts(prefix: str, node: RealAccount):
            if not node:
                accounts.append(prefix)
                return

            for k, v in node.items():
                _get_accounts(f"{prefix}:{k}", v)

        _get_accounts("", real)
        return [acc[1:] for acc in accounts]  # remove leading colon

    @property
    def entries(self) -> Directives:
        return self._entries

    @property
    def errors(self) -> list[BeancountError]:
        return self._errors

    @property
    def options(self) -> Any:
        return self._options
