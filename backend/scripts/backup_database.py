#!/usr/bin/env python3
"""
Система backup базы данных для проекта strain_collection_new

Поддерживает:
- Полные backup'ы с данными
- Schema-only backup'ы
- Сжатие backup'ов
- Ротацию старых backup'ов
- Валидацию backup'ов
- Логирование операций
"""

import argparse
import datetime
import gzip
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Добавляем путь к Django проекту
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "backend"))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "strain_tracker_project.settings"
)

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.db import connection  # noqa: E402


class DatabaseBackup:
    """Класс для управления backup'ами PostgreSQL базы данных"""

    def __init__(self, backup_dir: str = None):
        self.backup_dir = Path(
            backup_dir
            or os.path.join(os.path.dirname(__file__), "..", "backups")
        )
        self.backup_dir.mkdir(exist_ok=True)

        # Настройка логирования
        self.setup_logging()

        # Получение настроек БД из Django
        self.db_config = settings.DATABASES["default"]
        self.db_name = self.db_config["NAME"]
        self.db_user = self.db_config["USER"]
        self.db_password = self.db_config["PASSWORD"]
        self.db_host = self.db_config["HOST"] or "localhost"
        self.db_port = self.db_config["PORT"] or "5432"

    def setup_logging(self):
        """Настройка логирования"""
        log_file = self.backup_dir / "backup.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def get_timestamp(self) -> str:
        """Получение timestamp для имени файла"""
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_database_stats(self) -> Dict[str, Any]:
        """Получение статистики базы данных"""
        try:
            with connection.cursor() as cursor:
                # Количество таблиц
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
                )
                tables_count = cursor.fetchone()[0]

                # Размер базы данных
                cursor.execute(
                    "SELECT pg_size_pretty(pg_database_size(%s))",
                    [self.db_name],
                )
                db_size = cursor.fetchone()[0]

                # Количество записей в основных таблицах
                stats = {}
                for table in [
                    "collection_manager_strain",
                    "collection_manager_sample",
                    "collection_manager_storage",
                ]:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        stats[table] = cursor.fetchone()[0]
                    except Exception:
                        stats[table] = 0

                return {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "database": self.db_name,
                    "tables_count": tables_count,
                    "database_size": db_size,
                    "records": stats,
                }
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики БД: {e}")
            return {}

    def create_backup(
        self, backup_type: str = "full", compress: bool = True
    ) -> Optional[Path]:
        """
        Создание backup'а базы данных

        Args:
            backup_type: 'full' - полный backup, 'schema' - только схема
            compress: сжимать ли backup
        """
        timestamp = self.get_timestamp()

        if backup_type == "full":
            filename = f"strain_collection_full_{timestamp}.sql"
        elif backup_type == "schema":
            filename = f"strain_collection_schema_{timestamp}.sql"
        else:
            raise ValueError("backup_type должен быть 'full' или 'schema'")

        backup_path = self.backup_dir / filename

        try:
            self.logger.info(f"Создание {backup_type} backup: {filename}")

            # Построение команды pg_dump
            cmd = [
                "pg_dump",
                f"--host={self.db_host}",
                f"--port={self.db_port}",
                f"--username={self.db_user}",
                "--no-password",
                "--verbose",
            ]

            if backup_type == "schema":
                cmd.append("--schema-only")

            cmd.append(self.db_name)

            # Установка переменной окружения для пароля
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password

            # Выполнение backup'а
            self.logger.info(
                f"Выполнение команды: {' '.join(cmd[:-1])} [DB_NAME]"
            )

            with open(backup_path, "w") as f:
                result = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True
                )

            if result.returncode != 0:
                self.logger.error(f"Ошибка создания backup: {result.stderr}")
                if backup_path.exists():
                    backup_path.unlink()
                return None

            # Сжатие backup'а
            if compress:
                compressed_path = backup_path.with_suffix(".sql.gz")
                self.logger.info(f"Сжатие backup: {compressed_path.name}")

                with open(backup_path, "rb") as f_in:
                    with gzip.open(compressed_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

                backup_path.unlink()  # Удаляем несжатый файл
                backup_path = compressed_path

            # Сохранение метаданных
            self.save_backup_metadata(backup_path, backup_type)

            self.logger.info(f"Backup успешно создан: {backup_path}")
            return backup_path

        except Exception as e:
            self.logger.error(f"Ошибка создания backup: {e}")
            if backup_path.exists():
                backup_path.unlink()
            return None

    def save_backup_metadata(self, backup_path: Path, backup_type: str):
        """Сохранение метаданных backup'а"""
        metadata = {
            "backup_file": backup_path.name,
            "backup_type": backup_type,
            "creation_time": datetime.datetime.now().isoformat(),
            "database_stats": self.get_database_stats(),
            "file_size": backup_path.stat().st_size,
            "compressed": backup_path.suffix == ".gz",
        }

        metadata_path = backup_path.with_suffix(".json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Метаданные сохранены: {metadata_path.name}")

    def list_backups(self) -> List[Dict[str, Any]]:
        """Получение списка всех backup'ов"""
        backups = []

        for backup_file in self.backup_dir.glob("strain_collection_*.sql*"):
            if backup_file.suffix in [".sql", ".gz"]:
                metadata_file = backup_file.with_suffix(".json")

                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        backups.append(metadata)
                    except Exception as e:
                        self.logger.warning(
                            f"Ошибка чтения метаданных {metadata_file}: {e}"
                        )
                else:
                    # Создаем базовые метаданные для файлов без них
                    stat = backup_file.stat()
                    backups.append(
                        {
                            "backup_file": backup_file.name,
                            "backup_type": "unknown",
                            "creation_time": datetime.datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                            "file_size": stat.st_size,
                            "compressed": backup_file.suffix == ".gz",
                        }
                    )

        # Сортировка по времени создания (новые первыми)
        backups.sort(key=lambda x: x["creation_time"], reverse=True)
        return backups

    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 10):
        """
        Удаление старых backup'ов

        Args:
            keep_days: количество дней для хранения
            keep_count: минимальное количество backup'ов для сохранения
        """
        backups = self.list_backups()
        cutoff_date = datetime.datetime.now() - datetime.timedelta(
            days=keep_days
        )

        removed_count = 0
        for i, backup in enumerate(backups):
            if i < keep_count:  # Всегда сохраняем минимальное количество
                continue

            backup_date = datetime.datetime.fromisoformat(
                backup["creation_time"]
                .replace("Z", "+00:00")
                .replace("+00:00", "")
            )

            if backup_date < cutoff_date:
                backup_path = self.backup_dir / backup["backup_file"]
                metadata_path = backup_path.with_suffix(".json")

                try:
                    if backup_path.exists():
                        backup_path.unlink()
                    if metadata_path.exists():
                        metadata_path.unlink()

                    self.logger.info(
                        f"Удален старый backup: {backup['backup_file']}"
                    )
                    removed_count += 1

                except Exception as e:
                    self.logger.error(
                        f"Ошибка удаления backup {backup['backup_file']}: {e}"
                    )

        self.logger.info(f"Удалено старых backup'ов: {removed_count}")

    def validate_backup(self, backup_file: str) -> bool:
        """Валидация backup файла"""
        backup_path = self.backup_dir / backup_file

        if not backup_path.exists():
            self.logger.error(f"Backup файл не найден: {backup_file}")
            return False

        try:
            # Проверка формата файла
            if backup_path.suffix == ".gz":
                # Проверка gzip файла
                with gzip.open(backup_path, "rt") as f:
                    # Читаем первые несколько строк
                    for i, line in enumerate(f):
                        if i > 10:  # Проверяем первые 10 строк
                            break
                        if not line.strip():
                            continue
                        # Ожидаем SQL комментарии или команды
                        if not (
                            line.startswith("--")
                            or line.startswith("SET")
                            or line.startswith("CREATE")
                            or line.startswith("INSERT")
                        ):
                            self.logger.warning(
                                f"Подозрительная строка в backup: {line[:50]}..."
                            )
            else:
                # Проверка обычного SQL файла
                with open(backup_path, "r") as f:
                    first_lines = [f.readline() for _ in range(10)]
                    if not any(
                        "PostgreSQL" in line or "pg_dump" in line
                        for line in first_lines
                    ):
                        self.logger.warning(
                            "Backup не содержит стандартных заголовков PostgreSQL"
                        )

            self.logger.info(f"Backup файл валиден: {backup_file}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка валидации backup {backup_file}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Система backup базы данных strain_collection"
    )
    parser.add_argument(
        "action",
        choices=["create", "list", "cleanup", "validate"],
        help="Действие для выполнения",
    )
    parser.add_argument(
        "--type",
        choices=["full", "schema"],
        default="full",
        help="Тип backup (только для create)",
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Не сжимать backup (только для create)",
    )
    parser.add_argument("--backup-dir", help="Директория для backup'ов")
    parser.add_argument(
        "--keep-days",
        type=int,
        default=30,
        help="Количество дней для хранения backup'ов (только для cleanup)",
    )
    parser.add_argument(
        "--keep-count",
        type=int,
        default=10,
        help="Минимальное количество backup'ов (только для cleanup)",
    )
    parser.add_argument(
        "--file", help="Имя файла для валидации (только для validate)"
    )

    args = parser.parse_args()

    # Создание объекта backup
    backup = DatabaseBackup(args.backup_dir)

    if args.action == "create":
        result = backup.create_backup(
            backup_type=args.type, compress=not args.no_compress
        )
        if result:
            print(f"✅ Backup создан: {result}")
            sys.exit(0)
        else:
            print("❌ Ошибка создания backup")
            sys.exit(1)

    elif args.action == "list":
        backups = backup.list_backups()
        if not backups:
            print("📂 Backup'ы не найдены")
        else:
            print("📂 Список backup'ов:")
            for i, b in enumerate(backups, 1):
                size_mb = b["file_size"] / (1024 * 1024)
                compressed = " (сжат)" if b.get("compressed") else ""
                print(f"{i:2d}. {b['backup_file']}{compressed}")
                print(f"    Дата: {b['creation_time'][:19]}")
                print(f"    Тип: {b['backup_type']}, Размер: {size_mb:.1f} MB")
                if "database_stats" in b and "records" in b["database_stats"]:
                    records = b["database_stats"]["records"]
                    print(
                        f"    Данные: штаммы={records.get('collection_manager_strain', 0)}, "
                        f"образцы={records.get('collection_manager_sample', 0)}"
                    )
                print()

    elif args.action == "cleanup":
        backup.cleanup_old_backups(args.keep_days, args.keep_count)
        print(
            f"✅ Очистка завершена (хранение: {args.keep_days} дней, минимум: {args.keep_count} файлов)"
        )

    elif args.action == "validate":
        if not args.file:
            print("❌ Укажите файл для валидации с помощью --file")
            sys.exit(1)

        if backup.validate_backup(args.file):
            print(f"✅ Backup файл валиден: {args.file}")
        else:
            print(f"❌ Backup файл не валиден: {args.file}")
            sys.exit(1)


if __name__ == "__main__":
    main()
