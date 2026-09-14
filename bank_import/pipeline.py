from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from .detect import parse_statement
from .mapping import apply_mapping, load_mapping
from .models import ProcessedOperation


JOURNAL_COLUMNS = [
    "ID операции", "Дата операции", "Дата начисления", "Тип записи", "Тип операции",
    "Поступление", "Списание", "Сумма ДДС", "Сумма учета", "Валюта", "Счёт денежных средств",
    "Статья операции", "ДДС: раздел", "ДДС: строка", "ОПиУ: строка", "Проект", "ЦФО",
    "Контрагент", "ИНН", "Назначение", "НДС", "Дт", "Кт", "Тип источника",
    "ID источника", "ID документа источника", "Номер документа", "Дата импорта",
    "Статус автоматики", "Требует уточнения", "Комментарий", "Балансовая статья",
]


@dataclass
class RunResult:
    ready: list[ProcessedOperation]
    exceptions: list[ProcessedOperation]
    duplicates: list[ProcessedOperation]
    input_count: int

    @property
    def unique(self) -> list[ProcessedOperation]:
        return [*self.ready, *self.exceptions]


def process_files(paths: Iterable[str | Path], mapping_path: str | Path) -> RunResult:
    mapping = load_mapping(mapping_path)
    ready: list[ProcessedOperation] = []
    exceptions: list[ProcessedOperation] = []
    duplicates: list[ProcessedOperation] = []
    seen: set[str] = set()
    input_count = 0
    for path in paths:
        for operation in parse_statement(path):
            input_count += 1
            if operation.operation_id in seen:
                duplicates.append(ProcessedOperation(operation, None, "Дубль", "operation_id уже встречался"))
                continue
            seen.add(operation.operation_id)
            mapped = apply_mapping(operation, mapping)
            if mapped is None:
                exceptions.append(ProcessedOperation(operation, None, "Требует разъяснения", "Не найдено правило маппинга"))
            else:
                ready.append(ProcessedOperation(operation, mapped, "Готово"))
    return RunResult(ready, exceptions, duplicates, input_count)


def _write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _amounts(rows: list[ProcessedOperation]) -> tuple[Decimal, Decimal]:
    money_in = sum((row.operation.money_in for row in rows), Decimal("0"))
    money_out = sum((row.operation.money_out for row in rows), Decimal("0"))
    return money_in, money_out


def write_outputs(result: RunResult, output_dir: str | Path) -> dict[str, Path]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    ready_path = target / "operations_ready.csv"
    exceptions_path = target / "exceptions.csv"
    duplicates_path = target / "duplicates.csv"
    raw_path = target / "raw_operations.jsonl"
    control_path = target / "control_report.json"
    _write_csv(ready_path, [row.journal_record() for row in result.ready], JOURNAL_COLUMNS)
    _write_csv(exceptions_path, [row.journal_record() for row in result.exceptions], JOURNAL_COLUMNS)
    _write_csv(duplicates_path, [row.journal_record() for row in result.duplicates], JOURNAL_COLUMNS)
    with raw_path.open("w", encoding="utf-8") as handle:
        for row in [*result.unique, *result.duplicates]:
            handle.write(json.dumps(row.raw_record(), ensure_ascii=False) + "\n")
    money_in, money_out = _amounts(result.unique)
    control = {
        "input_rows": result.input_count,
        "ready_rows": len(result.ready),
        "exception_rows": len(result.exceptions),
        "duplicate_rows": len(result.duplicates),
        "unique_rows": len(result.unique),
        "row_control_ok": result.input_count == len(result.ready) + len(result.exceptions) + len(result.duplicates),
        "unique_money_in": str(money_in.quantize(Decimal("0.01"))),
        "unique_money_out": str(money_out.quantize(Decimal("0.01"))),
    }
    control_path.write_text(json.dumps(control, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ready": ready_path,
        "exceptions": exceptions_path,
        "duplicates": duplicates_path,
        "raw": raw_path,
        "control": control_path,
    }
