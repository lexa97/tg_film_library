#!/bin/sh
set -e
# При первом запуске: миграции создают таблицы; если миграций нет — создаст init_db() в main.py
alembic upgrade head || true
exec python main.py
