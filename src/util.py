from datetime import date, datetime


def parse_date(_date: str) -> date:
    return datetime.strptime(_date, "%Y-%m-%d").date()
