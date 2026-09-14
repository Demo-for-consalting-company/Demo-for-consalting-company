from __future__ import annotations

import argparse
from pathlib import Path

from bank_import.pipeline import process_files, write_outputs


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = ROOT / "data" / "для_загрузки_в_чат" / "основной_сценарий"
REPEAT_INPUT_DIR = ROOT / "data" / "для_загрузки_в_чат" / "дополнительно"
DEFAULT_MAPPING = ROOT / "config" / "projects" / "atlas.json"
DEFAULT_OUTPUT = ROOT / "build" / "latest"


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Разнести банковские выписки по правилам выбранного проекта."
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Пути к выпискам. Если не указаны, используются три файла основного сценария.",
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=DEFAULT_MAPPING,
        help="Файл правил проекта. По умолчанию: config/projects/atlas.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Папка результата. По умолчанию: build/latest.",
    )
    parser.add_argument(
        "--include-repeat",
        action="store_true",
        help="Добавить повтор выписки Т-Банка и показать работу защиты от дублей.",
    )
    return parser


def main() -> None:
    args = argument_parser().parse_args()
    files = list(args.files) or sorted(DEFAULT_INPUT_DIR.glob("*.xlsx"))
    if args.include_repeat:
        files.extend(sorted(REPEAT_INPUT_DIR.glob("*.xlsx")))
    if not files:
        raise SystemExit("Не найдены файлы выписок.")

    result = process_files(files, args.mapping)
    written = write_outputs(result, args.output_dir)

    print("Обработка завершена")
    print(f"  Строк во входных файлах: {result.input_count}")
    print(f"  Готово к загрузке:       {len(result.ready)}")
    print(f"  Требует решения:         {len(result.exceptions)}")
    print(f"  Повторные операции:      {len(result.duplicates)}")
    print(f"  Подробный результат:     {args.output_dir}")
    if result.exceptions:
        print(f"  Вопросы финансисту:      {written['exceptions']}")


if __name__ == "__main__":
    main()
