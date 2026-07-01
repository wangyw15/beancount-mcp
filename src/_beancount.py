from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

from beancount import Inventory, RealAccount, loader
from beancount.core import realization
from beancount.core.data import (
    BeancountError,
    Close,
    Directives,
    Open,
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
            if entry.date >= _from and entry.date <= _to:
                _entries.append(entry)

        real = realization.realize(_entries)
        print(real.items())
        _account: RealAccount = cast(RealAccount, realization.get(real, account))
        return _account.balance

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
            for item in directives:
                printer.print_entry(item, file=f)

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
