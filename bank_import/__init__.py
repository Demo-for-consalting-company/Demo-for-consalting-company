"""Учебный конвейер импорта банковских выписок."""

from .detect import detect_bank, parse_statement
from .pipeline import process_files, write_outputs

__all__ = ["detect_bank", "parse_statement", "process_files", "write_outputs"]

