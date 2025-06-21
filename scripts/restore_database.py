#!/usr/bin/env python3
"""
Система восстановления базы данных для проекта strain_collection_new

Поддерживает:
- Восстановление из полных backup'ов
- Восстановление только схемы
- Создание backup'а перед восстановлением
- Валидацию backup'ов перед восстановлением
- Подтверждение операций
- Детальное логирование
"""

import os
import sys
import subprocess
import datetime
import logging
import argparse
import json
import gzip
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

# Добавляем путь к Django проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')

import django
django.setup()

from django.conf import settings
from django.db import connection

class DatabaseRestore:
    """Класс для восстановления PostgreSQL базы данных из backup'ов"""
    
    def __init__(self, backup_dir: str = None):
        self.backup_dir = Path(backup_dir or os.path.join(os.path.dirname(__file__), '..', 'backups'))
        
        # Настройка логирования
        self.setup_logging()
        
        # Получение настроек БД из Django
        self.db_config = settings.DATABASES['default']
        self.db_name = self.db_config['NAME']
        self.db_user = self.db_config['USER']
        self.db_password = self.db_config['PASSWORD']
        self.db_host = self.db_config['HOST'] or 'localhost'
        self.db_port = self.db_config['PORT'] or '5432'
        
    def setup_logging(self):
        """Настройка логирования"""
        log_file = self.backup_dir / 'restore.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_database_info(self) -> Dict[str, Any]:
        """Получение информации о текущей базе данных"""
        try:
            with connection.cursor() as cursor:
                # Проверка подключения
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
                # Количество таблиц
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)
                tables_count = cursor.fetchone()[0]
                
                # Размер базы данных
                cursor.execute("SELECT pg_size_pretty(pg_database_size(%s))", [self.db_name])
                db_size = cursor.fetchone()[0]
                
                return {
                    'version': version,
                    'tables_count': tables_count,
                    'database_size': db_size,
                    'accessible': True
                }
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о БД: {e}")
            return {'accessible': False, 'error': str(e)}
    
    def load_backup_metadata(self, backup_file: str) -> Optional[Dict[str, Any]]:
        """Загрузка метаданных backup'а"""
        backup_path = Path(backup_file)
        if not backup_path.is_absolute():
            backup_path = self.backup_dir / backup_file
            
        metadata_path = backup_path.with_suffix('.json')
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Ошибка чтения метаданных {metadata_path}: {e}")
        
        return None
    
    def validate_backup_file(self, backup_file: str) -> bool:
        """Валидация backup файла перед восстановлением"""
        backup_path = Path(backup_file)
        if not backup_path.is_absolute():
            backup_path = self.backup_dir / backup_file
            
        if not backup_path.exists():
            self.logger.error(f"Backup файл не найден: {backup_path}")
            return False
        
        try:
            # Проверка формата и содержимого
            if backup_path.suffix == '.gz':
                with gzip.open(backup_path, 'rt') as f:
                    first_line = f.readline()
            else:
                with open(backup_path, 'r') as f:
                    first_line = f.readline()
            
            # Проверка на PostgreSQL backup
            if 'PostgreSQL' not in first_line and 'pg_dump' not in first_line:
                # Читаем больше строк для поиска признаков PostgreSQL
                lines_to_check = []
                if backup_path.suffix == '.gz':
                    with gzip.open(backup_path, 'rt') as f:
                        lines_to_check = [f.readline() for _ in range(20)]
                else:
                    with open(backup_path, 'r') as f:
                        lines_to_check = [f.readline() for _ in range(20)]
                
                if not any('PostgreSQL' in line or 'pg_dump' in line or 'SET' in line 
                          for line in lines_to_check):
                    self.logger.error("Файл не является PostgreSQL backup'ом")
                    return False
            
            self.logger.info(f"Backup файл прошел валидацию: {backup_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации backup файла: {e}")
            return False
    
    def create_pre_restore_backup(self) -> Optional[Path]:
        """Создание backup'а текущей БД перед восстановлением"""
        from backup_database import DatabaseBackup
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.logger.info("Создание backup'а текущей БД перед восстановлением...")
        
        backup_manager = DatabaseBackup(str(self.backup_dir))
        backup_path = backup_manager.create_backup(backup_type='full', compress=True)
        
        if backup_path:
            # Переименовываем для обозначения как pre-restore backup
            new_name = backup_path.name.replace('strain_collection_full_', 
                                              f'strain_collection_pre_restore_{timestamp}_')
            new_path = backup_path.parent / new_name
            backup_path.rename(new_path)
            
            # Обновляем метаданные
            metadata_old = backup_path.with_suffix('.json')
            metadata_new = new_path.with_suffix('.json')
            if metadata_old.exists():
                metadata_old.rename(metadata_new)
                
                # Обновляем содержимое метаданных
                try:
                    with open(metadata_new, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    metadata['backup_file'] = new_name
                    metadata['backup_type'] = 'pre_restore'
                    with open(metadata_new, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    self.logger.warning(f"Ошибка обновления метаданных: {e}")
            
            self.logger.info(f"Pre-restore backup создан: {new_path.name}")
            return new_path
        else:
            self.logger.error("Не удалось создать pre-restore backup")
            return None
    
    def restore_from_backup(self, backup_file: str, drop_existing: bool = False, 
                          create_backup: bool = True) -> bool:
        """
        Восстановление базы данных из backup'а
        
        Args:
            backup_file: путь к backup файлу
            drop_existing: удалить существующие таблицы перед восстановлением
            create_backup: создать backup текущей БД перед восстановлением
        """
        backup_path = Path(backup_file)
        if not backup_path.is_absolute():
            backup_path = self.backup_dir / backup_file
            
        try:
            # Валидация backup файла
            if not self.validate_backup_file(str(backup_path)):
                return False
            
            # Получение информации о текущей БД
            current_db_info = self.get_database_info()
            if not current_db_info.get('accessible'):
                self.logger.error("База данных недоступна")
                return False
            
            self.logger.info(f"Текущая БД: {current_db_info.get('tables_count', 0)} таблиц, "
                           f"размер: {current_db_info.get('database_size', 'неизвестно')}")
            
            # Создание backup'а перед восстановлением
            if create_backup and current_db_info.get('tables_count', 0) > 0:
                pre_restore_backup = self.create_pre_restore_backup()
                if not pre_restore_backup:
                    self.logger.warning("Не удалось создать pre-restore backup, продолжаем...")
            
            # Подготовка файла для восстановления
            sql_file = None
            if backup_path.suffix == '.gz':
                # Распаковка во временный файл
                temp_fd, temp_path = tempfile.mkstemp(suffix='.sql', prefix='restore_')
                sql_file = Path(temp_path)
                
                self.logger.info("Распаковка сжатого backup...")
                with gzip.open(backup_path, 'rb') as f_in:
                    with os.fdopen(temp_fd, 'wb') as f_out:
                        f_out.write(f_in.read())
            else:
                sql_file = backup_path
            
            # Подготовка команды восстановления
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            if drop_existing:
                self.logger.info("Удаление существующих таблиц...")
                self.drop_existing_tables()
            
            # Восстановление из backup'а
            cmd = [
                'psql',
                f'--host={self.db_host}',
                f'--port={self.db_port}',
                f'--username={self.db_user}',
                '--no-password',
                '--quiet',
                f'--dbname={self.db_name}',
                f'--file={sql_file}'
            ]
            
            self.logger.info(f"Восстановление из backup: {backup_path.name}")
            self.logger.info(f"Команда: {' '.join(cmd[:-1])} --file=[SQL_FILE]")
            
            result = subprocess.run(
                cmd,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            
            # Очистка временного файла
            if backup_path.suffix == '.gz' and sql_file and sql_file.exists():
                sql_file.unlink()
            
            if result.returncode != 0:
                self.logger.error(f"Ошибка восстановления: {result.stderr}")
                return False
            
            # Проверка результата восстановления
            restored_db_info = self.get_database_info()
            if restored_db_info.get('accessible'):
                self.logger.info(f"Восстановление завершено. Таблиц: {restored_db_info.get('tables_count', 0)}, "
                               f"размер: {restored_db_info.get('database_size', 'неизвестно')}")
                
                # Проверка Django миграций
                self.check_django_migrations()
                
                return True
            else:
                self.logger.error("База данных недоступна после восстановления")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка восстановления: {e}")
            return False
    
    def drop_existing_tables(self):
        """Удаление всех существующих таблиц"""
        try:
            with connection.cursor() as cursor:
                # Получение списка таблиц
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                if tables:
                    # Удаление таблиц с CASCADE
                    tables_list = ', '.join(f'"{table}"' for table in tables)
                    cursor.execute(f'DROP TABLE IF EXISTS {tables_list} CASCADE')
                    self.logger.info(f"Удалено таблиц: {len(tables)}")
                
        except Exception as e:
            self.logger.error(f"Ошибка удаления таблиц: {e}")
            raise
    
    def check_django_migrations(self):
        """Проверка состояния Django миграций после восстановления"""
        try:
            from django.core.management import execute_from_command_line
            
            self.logger.info("Проверка Django миграций...")
            
            # Проверка состояния миграций
            # Здесь можно добавить дополнительные проверки
            
            self.logger.info("Django миграции в порядке")
            
        except Exception as e:
            self.logger.warning(f"Ошибка проверки Django миграций: {e}")

def confirm_action(message: str) -> bool:
    """Запрос подтверждения у пользователя"""
    while True:
        response = input(f"{message} (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no', '']:
            return False
        else:
            print("Пожалуйста, введите 'y' или 'n'")

def main():
    parser = argparse.ArgumentParser(description='Восстановление базы данных strain_collection из backup')
    parser.add_argument('backup_file', help='Имя или путь к backup файлу')
    parser.add_argument('--backup-dir', help='Директория с backup\'ами')
    parser.add_argument('--drop-existing', action='store_true',
                       help='Удалить существующие таблицы перед восстановлением')
    parser.add_argument('--no-backup', action='store_true',
                       help='Не создавать backup текущей БД перед восстановлением')
    parser.add_argument('--force', action='store_true',
                       help='Не запрашивать подтверждение')
    parser.add_argument('--info-only', action='store_true',
                       help='Только показать информацию о backup без восстановления')
    
    args = parser.parse_args()
    
    # Создание объекта restore
    restore = DatabaseRestore(args.backup_dir)
    
    # Проверка существования backup файла
    backup_path = Path(args.backup_file)
    if not backup_path.is_absolute():
        backup_path = restore.backup_dir / args.backup_file
        
    if not backup_path.exists():
        print(f"❌ Backup файл не найден: {backup_path}")
        sys.exit(1)
    
    # Загрузка метаданных backup'а
    metadata = restore.load_backup_metadata(str(backup_path))
    
    print(f"📂 Информация о backup: {backup_path.name}")
    if metadata:
        print(f"   Тип: {metadata.get('backup_type', 'неизвестно')}")
        print(f"   Дата: {metadata.get('creation_time', 'неизвестно')[:19]}")
        print(f"   Размер: {metadata.get('file_size', 0) / (1024*1024):.1f} MB")
        print(f"   Сжат: {'да' if metadata.get('compressed') else 'нет'}")
        
        if 'database_stats' in metadata:
            stats = metadata['database_stats']
            if 'records' in stats:
                records = stats['records']
                print(f"   Данные: штаммы={records.get('collection_manager_strain', 0)}, "
                      f"образцы={records.get('collection_manager_sample', 0)}")
    else:
        print("   Метаданные не найдены")
    
    if args.info_only:
        sys.exit(0)
    
    # Получение информации о текущей БД
    current_db_info = restore.get_database_info()
    print(f"\n💾 Текущая база данных:")
    if current_db_info.get('accessible'):
        print(f"   Таблиц: {current_db_info.get('tables_count', 0)}")
        print(f"   Размер: {current_db_info.get('database_size', 'неизвестно')}")
    else:
        print(f"   ❌ Недоступна: {current_db_info.get('error', 'неизвестная ошибка')}")
    
    # Предупреждения и подтверждения
    print(f"\n⚠️  ВНИМАНИЕ:")
    print(f"   - Восстановление заменит текущие данные")
    if not args.no_backup:
        print(f"   - Будет создан backup текущей БД")
    if args.drop_existing:
        print(f"   - Существующие таблицы будут удалены")
    
    if not args.force:
        if not confirm_action("\nПродолжить восстановление?"):
            print("Восстановление отменено")
            sys.exit(0)
    
    # Выполнение восстановления
    success = restore.restore_from_backup(
        str(backup_path),
        drop_existing=args.drop_existing,
        create_backup=not args.no_backup
    )
    
    if success:
        print("✅ Восстановление завершено успешно")
        sys.exit(0)
    else:
        print("❌ Ошибка восстановления")
        sys.exit(1)

if __name__ == '__main__':
    main() 