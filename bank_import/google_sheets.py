from __future__ import annotations

from pathlib import Path

from .models import ProcessedOperation


def append_journal(
    spreadsheet_id: str,
    rows: list[ProcessedOperation],
    credentials_path: str | Path,
    sheet_name: str = "ЖурналОпераций",
) -> int:
    """Добавляет уникальные строки в существующий журнал, используя его фактические заголовки."""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("Для загрузки установите пакет: pip install -e '.[google]'") from exc
    credentials = Credentials.from_service_account_file(
        str(credentials_path), scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    header_response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!1:1",
    ).execute()
    headers = header_response.get("values", [[]])[0]
    if not headers:
        raise ValueError(f"На листе {sheet_name!r} нет строки заголовков")
    records = [row.journal_record() for row in rows]
    values = [[record.get(str(header), "") for header in headers] for record in records]
    if not values:
        return 0
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!A:A",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    ).execute()
    return len(values)

