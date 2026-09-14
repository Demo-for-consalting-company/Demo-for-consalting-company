# Запуск импорта

## Локальная обработка

```bash
python -m bank_import путь/к/выписке.xlsx \
  --mapping config/projects/training_consulting.json \
  --output-dir build/import
```

Можно передать несколько файлов разных банков за один запуск. Результат:

- `operations_ready.csv` — готовые уникальные операции;
- `exceptions.csv` — строки без надёжного маппинга;
- `duplicates.csv` — повторные `operation_id`;
- `raw_operations.jsonl` — исходные поля и технические идентификаторы;
- `control_report.json` — контроль количества и оборотов.

## Загрузка в Google Sheets

Установите опциональные зависимости и передайте сервисный аккаунт, которому выдан доступ к таблице:

```bash
pip install -e '.[google]'
python -m bank_import путь/к/выписке.xlsx \
  --mapping config/projects/training_consulting.json \
  --output-dir build/import \
  --spreadsheet-id SPREADSHEET_ID \
  --credentials data/private/service-account.json
```

Загрузчик читает фактическую строку заголовков `ЖурналОпераций` и раскладывает поля по ней, поэтому скрытые технические колонки могут оставаться в таблице. Правила импорта и учёта в Google Sheets не хранятся: источником истины служит проектный JSON в репозитории.

## Тесты

```bash
python -m unittest discover -s tests -v
```

Тесты создают миниатюрные книги Т‑Банка, Альфы и Сбера во временном каталоге и не используют реальные реквизиты.
