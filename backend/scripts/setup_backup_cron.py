#!/usr/bin/env python3
"""
Настройка автоматических backup'ов через cron для strain_collection_new

Поддерживает:
- Создание cron задач для регулярных backup'ов
- Настройка разных расписаний (ежедневно, еженедельно, ежемесячно)
- Автоматическая очистка старых backup'ов
- Мониторинг и уведомления
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


class BackupCronSetup:
    """Класс для настройки автоматических backup'ов через cron"""

    def __init__(self, project_path: str = None):
        self.project_path = Path(
            project_path or os.path.dirname(__file__)
        ).parent
        self.scripts_path = self.project_path / "scripts"
        self.backup_script = self.scripts_path / "backup_database.py"
        self.venv_path = self.project_path / "strain_venv"

    def get_current_crontab(self) -> str:
        """Получение текущего crontab"""
        try:
            result = subprocess.run(
                ["crontab", "-l"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout
            else:
                return ""
        except Exception:
            return ""

    def backup_crontab(self):
        """Создание backup'а текущего crontab"""
        current_crontab = self.get_current_crontab()
        if current_crontab:
            backup_file = self.project_path / "backups" / "crontab_backup.txt"
            backup_file.parent.mkdir(exist_ok=True)

            with open(backup_file, "w") as f:
                f.write(current_crontab)
            print(f"✅ Backup crontab создан: {backup_file}")

    def generate_cron_entries(self, schedule: str = "daily") -> list:
        """
        Генерация записей cron для backup'ов

        Args:
            schedule: 'daily', 'weekly', 'monthly' или 'custom'
        """
        python_path = self.venv_path / "bin" / "python"
        log_file = self.project_path / "backups" / "cron.log"

        entries = []

        if schedule == "daily":
            # Ежедневный полный backup в 2:00
            entries.append(
                f"0 2 * * * cd {self.project_path} && "
                f"{python_path} {self.backup_script} create --type full "
                f">> {log_file} 2>&1"
            )

            # Еженедельная очистка старых backup'ов в воскресенье в 3:00
            entries.append(
                f"0 3 * * 0 cd {self.project_path} && "
                f"{python_path} {self.backup_script} cleanup --keep-days 30 --keep-count 10 "
                f">> {log_file} 2>&1"
            )

        elif schedule == "weekly":
            # Еженедельный полный backup в понедельник в 2:00
            entries.append(
                f"0 2 * * 1 cd {self.project_path} && "
                f"{python_path} {self.backup_script} create --type full "
                f">> {log_file} 2>&1"
            )

            # Ежедневный schema backup в 23:00 (кроме понедельника)
            entries.append(
                f"0 23 * * 2-7 cd {self.project_path} && "
                f"{python_path} {self.backup_script} create --type schema "
                f">> {log_file} 2>&1"
            )

            # Ежемесячная очистка в первое воскресенье в 3:00
            entries.append(
                f"0 3 1-7 * 0 cd {self.project_path} && "
                f"{python_path} {self.backup_script} cleanup --keep-days 60 --keep-count 20 "
                f">> {log_file} 2>&1"
            )

        elif schedule == "monthly":
            # Ежемесячный полный backup в первое число в 2:00
            entries.append(
                f"0 2 1 * * cd {self.project_path} && "
                f"{python_path} {self.backup_script} create --type full "
                f">> {log_file} 2>&1"
            )

            # Еженедельный schema backup в воскресенье в 2:00
            entries.append(
                f"0 2 * * 0 cd {self.project_path} && "
                f"{python_path} {self.backup_script} create --type schema "
                f">> {log_file} 2>&1"
            )

            # Квартальная очистка
            entries.append(
                f"0 3 1 1,4,7,10 * cd {self.project_path} && "
                f"{python_path} {self.backup_script} cleanup --keep-days 90 --keep-count 30 "
                f">> {log_file} 2>&1"
            )

        return entries

    def install_cron_entries(self, entries: list):
        """Установка записей в crontab"""
        current_crontab = self.get_current_crontab()

        # Удаление существующих записей strain_collection
        lines = current_crontab.split("\n") if current_crontab else []
        filtered_lines = [
            line
            for line in lines
            if "strain_collection" not in line
            and "backup_database.py" not in line
        ]

        # Добавление заголовка
        filtered_lines.extend(
            [
                "",
                "# Автоматические backup'ы для strain_collection_new",
                f"# Создано: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}",
            ]
        )

        # Добавление новых записей
        filtered_lines.extend(entries)

        # Создание нового crontab
        new_crontab = "\n".join(filtered_lines) + "\n"

        # Установка нового crontab
        try:
            process = subprocess.Popen(
                ["crontab", "-"], stdin=subprocess.PIPE, text=True
            )
            process.communicate(input=new_crontab)

            if process.returncode == 0:
                print("✅ Cron записи успешно установлены")
                return True
            else:
                print("❌ Ошибка установки cron записей")
                return False
        except Exception as e:
            print(f"❌ Ошибка установки crontab: {e}")
            return False

    def remove_cron_entries(self):
        """Удаление записей strain_collection из crontab"""
        current_crontab = self.get_current_crontab()

        if not current_crontab:
            print("📂 Crontab пуст")
            return True

        # Фильтрация записей
        lines = current_crontab.split("\n")
        filtered_lines = []
        removing = False

        for line in lines:
            if "strain_collection" in line and line.startswith("#"):
                removing = True
                continue
            elif removing and (line.strip() == "" or not line.startswith("#")):
                if "backup_database.py" not in line:
                    removing = False
                    filtered_lines.append(line)
            elif not removing:
                filtered_lines.append(line)

        # Удаление пустых строк в конце
        while filtered_lines and filtered_lines[-1].strip() == "":
            filtered_lines.pop()

        new_crontab = "\n".join(filtered_lines)
        if new_crontab and not new_crontab.endswith("\n"):
            new_crontab += "\n"

        # Установка обновленного crontab
        try:
            process = subprocess.Popen(
                ["crontab", "-"], stdin=subprocess.PIPE, text=True
            )
            process.communicate(input=new_crontab)

            if process.returncode == 0:
                print("✅ Записи strain_collection удалены из crontab")
                return True
            else:
                print("❌ Ошибка обновления crontab")
                return False
        except Exception as e:
            print(f"❌ Ошибка обновления crontab: {e}")
            return False

    def show_current_entries(self):
        """Показ текущих записей cron для strain_collection"""
        current_crontab = self.get_current_crontab()

        if not current_crontab:
            print("📂 Crontab пуст")
            return

        lines = current_crontab.split("\n")
        strain_entries = []
        in_strain_section = False

        for line in lines:
            if "strain_collection" in line and line.startswith("#"):
                in_strain_section = True
                strain_entries.append(line)
            elif in_strain_section:
                if (
                    line.strip() == ""
                    or line.startswith("#")
                    or "backup_database.py" in line
                ):
                    strain_entries.append(line)
                else:
                    in_strain_section = False

        if strain_entries:
            print("📅 Текущие cron записи для strain_collection:")
            for entry in strain_entries:
                print(f"   {entry}")
        else:
            print("📂 Записи strain_collection в crontab не найдены")

    def test_backup_command(self):
        """Тестирование команды backup"""
        python_path = self.venv_path / "bin" / "python"

        if not python_path.exists():
            print(f"❌ Python в venv не найден: {python_path}")
            return False

        if not self.backup_script.exists():
            print(f"❌ Скрипт backup не найден: {self.backup_script}")
            return False

        try:
            # Тест создания schema backup
            cmd = [
                str(python_path),
                str(self.backup_script),
                "create",
                "--type",
                "schema",
            ]
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print("✅ Тест backup команды прошел успешно")
                return True
            else:
                print(f"❌ Ошибка тестирования backup: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Timeout при тестировании backup команды")
            return False
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Настройка автоматических backup'ов через cron"
    )
    parser.add_argument(
        "action",
        choices=["install", "remove", "show", "test"],
        help="Действие для выполнения",
    )
    parser.add_argument(
        "--schedule",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Расписание backup'ов (только для install)",
    )
    parser.add_argument("--project-path", help="Путь к проекту")

    args = parser.parse_args()

    # Создание объекта setup
    setup = BackupCronSetup(args.project_path)

    if args.action == "test":
        print("🧪 Тестирование backup команды...")
        success = setup.test_backup_command()
        sys.exit(0 if success else 1)

    elif args.action == "show":
        setup.show_current_entries()

    elif args.action == "remove":
        setup.backup_crontab()
        success = setup.remove_cron_entries()
        sys.exit(0 if success else 1)

    elif args.action == "install":
        print(f"📅 Настройка автоматических backup'ов ({args.schedule})")

        # Проверка зависимостей
        if not setup.test_backup_command():
            print("❌ Backup команда не работает, установка отменена")
            sys.exit(1)

        # Создание backup текущего crontab
        setup.backup_crontab()

        # Генерация и установка cron записей
        entries = setup.generate_cron_entries(args.schedule)

        print("\n📋 Будут установлены следующие cron записи:")
        for entry in entries:
            print(f"   {entry}")

        response = input("\nПродолжить установку? (y/N): ").strip().lower()
        if response not in ["y", "yes"]:
            print("Установка отменена")
            sys.exit(0)

        success = setup.install_cron_entries(entries)

        if success:
            print(f"\n✅ Автоматические backup'ы настроены ({args.schedule})")
            print(f"📁 Backup'ы сохраняются в: {setup.project_path}/backups/")
            print(f"📝 Логи cron: {setup.project_path}/backups/cron.log")
            print("\n💡 Для просмотра: crontab -l")
            print(f"💡 Для удаления: {sys.argv[0]} remove")

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
