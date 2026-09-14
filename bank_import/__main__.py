from __future__ import annotations

import argparse
import json

from .google_sheets import append_journal
from .pipeline import process_files, write_outputs


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Обработка выписок Т-Банка, Альфа-Банка и СберБизнес")
    result.add_argument("inputs", nargs="+", help="CSV/XLSX-файлы выписок")
    result.add_argument("--mapping", required=True, help="JSON-маппинг конкретного проекта")
    result.add_argument("--output-dir", default="build/import", help="Каталог контрольных результатов")
    result.add_argument("--spreadsheet-id", help="ID Google Sheets для опциональной загрузки")
    result.add_argument("--credentials", help="Путь к JSON сервисного аккаунта; файл не коммитить")
    result.add_argument("--sheet-name", default="ЖурналОпераций")
    return result


def main() -> None:
    args = parser().parse_args()
    if bool(args.spreadsheet_id) != bool(args.credentials):
        raise SystemExit("--spreadsheet-id и --credentials передаются только вместе")
    run = process_files(args.inputs, args.mapping)
    files = write_outputs(run, args.output_dir)
    uploaded = 0
    if args.spreadsheet_id:
        uploaded = append_journal(args.spreadsheet_id, run.ready, args.credentials, args.sheet_name)
    print(json.dumps({
        "input": run.input_count,
        "ready": len(run.ready),
        "exceptions": len(run.exceptions),
        "duplicates": len(run.duplicates),
        "uploaded": uploaded,
        "files": {name: str(path) for name, path in files.items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
