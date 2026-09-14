from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any

from openpyxl.utils.datetime import from_excel


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def money(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    cleaned = text(value).replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        result = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Некорректная сумма: {value!r}") from exc
    if result < 0:
        raise ValueError(f"Сумма не может быть отрицательной: {value!r}")
    return result.quantize(Decimal("0.01"))


def booked_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, (int, float)):
        parsed = from_excel(value)
        return parsed if isinstance(parsed, datetime) else datetime.combine(parsed, time.min)
    candidate = text(value)
    for pattern in (
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(candidate, pattern)
        except ValueError:
            pass
    raise ValueError(f"Некорректная дата: {value!r}")


def normalize_currency(value: Any) -> str:
    candidate = text(value).upper()
    if candidate in {"643", "RUR", "РУБ", "РУБЛЬ", "РОССИЙСКИЙ РУБЛЬ"}:
        return "RUB"
    return candidate or "RUB"


def split_party_block(value: Any) -> tuple[str, str, str]:
    lines = [line.strip() for line in text(value).splitlines() if line.strip()]
    account = lines[0] if lines else ""
    inn = lines[1] if len(lines) > 1 else ""
    name = " ".join(lines[2:]) if len(lines) > 2 else ""
    return account, inn, name

