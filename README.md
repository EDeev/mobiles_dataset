# Mobile Devices Database

**Русский** · [English](README.en.md)

[![CI](https://github.com/EDeev/mobiles_dataset/actions/workflows/ci.yml/badge.svg)](https://github.com/EDeev/mobiles_dataset/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/EDeev/mobiles_dataset)](https://github.com/EDeev/mobiles_dataset/releases)

Курсовая по проектированию баз данных: датасет мобильных устройств 2025 года, разложенный в
нормализованную базу PostgreSQL, десктопное приложение на PyQt6 для работы с ним и измерение
выигрыша от индексов через `EXPLAIN ANALYZE`.

**Статус:** учебный проект (курсовая «Проектирование и администрирование баз данных», Московский
Политех, 2025), завершён

![Вкладка «Модели»](docs/screenshots/models.png)

**Стек:** Python 3.11 · PostgreSQL 15 · psycopg2 · PyQt6 · pandas · Docker

## Возможности

- Схема в 3НФ из пяти таблиц (компании, процессоры, модели, регионы, цены) с внешними ключами и
  каскадными операциями
- Импорт [датасета с Kaggle](https://www.kaggle.com/datasets/abdulmalik1518/mobiles-dataset-2025)
  (930 строк, после очистки 914 моделей и 4569 цен) с разнесением по справочникам
- Приложение: компании и модели с добавлением, правкой и удалением, цены по пяти регионам (Пакистан,
  Индия, Китай, ОАЭ, США) с символами валют, поиск по названию, компании и RAM, вкладка статистики цен
- Эксперимент с индексами: запросы `EXPLAIN ANALYZE` до и после, планы сохранены в `sql/explain_results/`

| Метрика | Без индексов | С индексами | Разница |
|---|---|---|---|
| Поиск | 0,234 мс | 0,089 мс | быстрее на 62 % |
| JOIN четырёх таблиц | 18,6 мс | 0,95 мс | быстрее на 95 % |
| Стоимость по планировщику | 44,76 | 12,45 | ниже на 72 % |
| Просмотренные строки | 914 | 18 | меньше на 98 % |

Измерено на этом датасете (сотни строк), поэтому абсолютные времена — доли миллисекунды.

## Быстрый старт

```bash
git clone https://github.com/EDeev/mobiles_dataset.git && cd mobiles_dataset
docker compose up -d                  # PostgreSQL 15 со схемой из sql/create_schema.sql
pip install -r requirements.txt
python scripts/import_data.py         # загрузка датасета
python main.py                        # приложение
```

Готовая сборка для Windows (`.exe`) — в [релизах](https://github.com/EDeev/mobiles_dataset/releases).

## Без Docker

1. Выполните `sql/create_schema.sql` в psql или pgAdmin под пользователем `postgres` — скрипт сам
   создаёт базу `mobile_devices_db`.
2. Задайте подключение переменными `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
   (по умолчанию `localhost:5432`, `mobile_devices_db`, `admin` / `password`).
3. `python scripts/import_data.py`, затем `python main.py`.

## Как выглядит

| Компании | Аналитика |
|---|---|
| ![Компании](docs/screenshots/companies.png) | ![Аналитика](docs/screenshots/analytics.png) |

## Структура

```
database.py               доступ к БД (синглтон, параметризованные запросы)
main_window.py, main.py   приложение на PyQt6
scripts/import_data.py    импорт и нормализация датасета
scripts/exe/              однофайловая версия приложения для сборки .exe
sql/                      схема, запросы для анализа производительности, ERD, результаты EXPLAIN
docs/report.*             отчёт по курсовой (md, docx, pdf)
```

## Лицензия

Учебный проект (Проектирование и администрирование баз данных, Московский Политех, 2025). Код открыт
для изучения, отдельной лицензии нет. Датасет — с Kaggle, на условиях его автора.

## Автор

**Деев Егор Викторович** — [GitHub](https://github.com/EDeev) · [Telegram](https://t.me/DeevEgor) · [egor@deev.space](mailto:egor@deev.space)

---

<div align="center">
  <sub>⭐ Если проект оказался полезным, поставьте звёздочку на GitHub!</sub>
  <p><sub>Сделано с ❤️ — <a href="https://deev.space">deev.space</a></sub></p>
</div>
