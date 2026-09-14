from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any


def _digest(parts: list[str], length: int = 24) -> str:
    payload = "|".join(part.strip().casefold() for part in parts)
    return sha256(payload.encode("utf-8")).hexdigest()[:length].upper()


@dataclass(frozen=True)
class BankOperation:
    bank: str
    source_path: str
    source_sheet: str
    source_row: int
    account: str
    booked_at: datetime
    document_number: str
    direction: str
    amount: Decimal
    currency: str
    description: str = ""
    purpose: str = ""
    counterparty_name: str = ""
    counterparty_inn: str = ""
    counterparty_account: str = ""
    raw: dict[str, str] = field(default_factory=dict)

    @property
    def source_row_id(self) -> str:
        file_key = _digest([Path(self.source_path).name], 10)
        return f"{self.bank.upper()}-{file_key}-R{self.source_row:06d}"

    @property
    def source_id(self) -> str:
        return f"{self.bank.upper()}-{_digest([Path(self.source_path).name], 10)}"

    @property
    def operation_id(self) -> str:
        amount = format(self.amount.quantize(Decimal("0.01")), "f")
        return _digest(
            [
                self.bank,
                self.account,
                self.booked_at.isoformat(timespec="minutes"),
                self.document_number,
                self.direction,
                amount,
                self.counterparty_account,
            ]
        )

    @property
    def money_in(self) -> Decimal:
        return self.amount if self.direction == "credit" else Decimal("0")

    @property
    def money_out(self) -> Decimal:
        return self.amount if self.direction == "debit" else Decimal("0")


@dataclass(frozen=True)
class MappingResult:
    rule: str
    article: str
    project: str
    cash_flow_section: str
    cash_flow_line: str
    pnl_line: str
    balance_account: str
    include_cash_flow: bool
    include_pnl: bool


@dataclass
class ProcessedOperation:
    operation: BankOperation
    mapping: MappingResult | None
    status: str
    reason: str = ""

    def journal_record(self) -> dict[str, Any]:
        op = self.operation
        mapped = self.mapping
        money_account = "Денежные средства / Основной счёт"
        balance = mapped.balance_account if mapped else ""
        debit_account = money_account if op.direction == "credit" else balance
        credit_account = balance if op.direction == "credit" else money_account
        return {
            "ID операции": op.operation_id,
            "Дата операции": op.booked_at.strftime("%d.%m.%Y"),
            "Дата начисления": op.booked_at.strftime("%d.%m.%Y"),
            "Тип записи": "Денежная операция",
            "Тип операции": "Поступление" if op.direction == "credit" else "Списание",
            "Поступление": str(op.money_in),
            "Списание": str(op.money_out),
            "Сумма ДДС": str(op.money_in - op.money_out),
            "Сумма учета": str(op.amount),
            "Валюта": op.currency,
            "Денежный счет": money_account,
            "Статья операции": mapped.article if mapped else "",
            "ДДС: раздел": mapped.cash_flow_section if mapped and mapped.include_cash_flow else "",
            "ДДС: строка": mapped.cash_flow_line if mapped and mapped.include_cash_flow else "",
            "ОПиУ: строка": mapped.pnl_line if mapped and mapped.include_pnl else "",
            "Проект": mapped.project if mapped else "",
            "ЦФО": "Учебный ЦФО",
            "Контрагент": op.counterparty_name,
            "ИНН": op.counterparty_inn,
            "Назначение": op.purpose,
            "НДС": "0%",
            "Дт": debit_account,
            "Кт": credit_account,
            "Тип источника": f"{op.bank.upper()}_{Path(op.source_path).suffix.lstrip('.').upper()}",
            "ID источника": op.source_id,
            "ID документа источника": op.source_row_id,
            "Номер документа": op.document_number,
            "Дата импорта": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "Статус автоматики": self.status,
            "Требует уточнения": "Да" if self.status != "Готово" else "Нет",
            "Комментарий": self.reason,
        }

    def raw_record(self) -> dict[str, Any]:
        record = asdict(self.operation)
        record["booked_at"] = self.operation.booked_at.isoformat()
        record["amount"] = str(self.operation.amount)
        record["source_row_id"] = self.operation.source_row_id
        record["source_id"] = self.operation.source_id
        record["operation_id"] = self.operation.operation_id
        return record
