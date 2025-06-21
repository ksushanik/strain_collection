# Быстрый старт системы backup

## 🚀 Немедленная настройка защиты данных

### 1. Создание первого backup'а
```bash
# Полный backup базы данных
make backup-create
```

### 2. Проверка backup'а
```bash
# Просмотр созданных backup'ов
make backup-list

# Информация о конкретном backup'е  
make restore-info
```

### 3. Настройка автоматических backup'ов
```bash
# Ежедневные backup'ы в 2:00
make backup-auto-install

# Проверка установки
make backup-auto-show
```

## ⚡ Команды на каждый день

```bash
# Создать backup перед важными изменениями
make backup-create

# Посмотреть все backup'ы
make backup-list

# Протестировать систему
make backup-test

# Очистить старые backup'ы
make backup-cleanup
```

## 🆘 Восстановление в экстренной ситуации

```bash
# 1. Просмотреть доступные backup'ы
make backup-list

# 2. Восстановить из backup'а (с защитным backup'ом)
make restore-db

# 3. Проверить состояние системы
make status
```

## 📋 Рекомендуемое расписание

- **Перед обновлениями**: `make backup-create`
- **Еженедельно**: `make backup-cleanup` 
- **Ежемесячно**: проверка `make backup-list`

## 🔐 Безопасность

- ✅ Backup'ы автоматически сжимаются
- ✅ Создается защитный backup перед восстановлением  
- ✅ Валидация backup'ов перед использованием
- ✅ Метаданные с информацией о содержимом
- ✅ Автоматическая ротация старых backup'ов

**⚠️ Backup'ы содержат все данные базы. Храните их в безопасном месте!**

---

Полная документация: [backups/README.md](backups/README.md) 