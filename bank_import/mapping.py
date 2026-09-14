from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import BankOperation, MappingResult


def load_mapping(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if not config.get("project_id") or not isinstance(config.get("rules"), list):
        raise ValueError("В JSON-маппинге обязательны project_id и список rules")
    return config


def _matches(operation: BankOperation, when: dict[str, Any]) -> bool:
    haystack = " ".join(
        [operation.description, operation.purpose, operation.counterparty_name, operation.counterparty_inn]
    ).casefold()
    direction = when.get("direction")
    if direction and direction != operation.direction:
        return False
    counterparty = str(when.get("counterparty_contains", "")).casefold()
    if counterparty and counterparty not in operation.counterparty_name.casefold():
        return False
    contains_all = [str(value).casefold() for value in when.get("contains_all", [])]
    if any(value not in haystack for value in contains_all):
        return False
    contains_any = [str(value).casefold() for value in when.get("contains_any", [])]
    if contains_any and not any(value in haystack for value in contains_any):
        return False
    not_contains = [str(value).casefold() for value in when.get("not_contains", [])]
    if any(value in haystack for value in not_contains):
        return False
    return bool(direction or counterparty or contains_all or contains_any)


def apply_mapping(operation: BankOperation, config: dict[str, Any]) -> MappingResult | None:
    for rule in config["rules"]:
        if not _matches(operation, rule.get("when", {})):
            continue
        target = rule.get("set", {})
        return MappingResult(
            rule=str(rule.get("name", "без названия")),
            article=str(target.get("article", "")),
            project=str(target.get("project", config.get("default_operation_project", "Общий"))),
            cash_flow_section=str(target.get("cash_flow_section", "")),
            cash_flow_line=str(target.get("cash_flow_line", "")),
            pnl_line=str(target.get("pnl_line", "")),
            balance_account=str(target.get("balance_account", "")),
            include_cash_flow=bool(target.get("include_cash_flow", True)),
            include_pnl=bool(target.get("include_pnl", True)),
        )
    return None

