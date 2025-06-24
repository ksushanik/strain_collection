# 🚀 Быстрый старт разработки (Очищенная версия)

Данная документация соответствует **очищенному Makefile** без устаревших команд.

## ⚡ Концепция

- **PostgreSQL** работает в Docker контейнере (порт 5432)
- **Django backend** запускается локально с auto-reload (порт 8000)  
- **React frontend** запускается локально с hot-reload (порт 3000)

## 🛠️ Первоначальная настройка (один раз)

```bash
# Настройка среды разработки
make -f Makefile.clean dev-setup
```

Эта команда автоматически:
- ✅ Создает виртуальную среду Python для backend
- ✅ Устанавливает зависимости Django  
- ✅ Устанавливает зависимости React (npm)
- ✅ Запускает PostgreSQL в Docker
- ✅ Применяет миграции базы данных
- ✅ Импортирует тестовые данные (881 штамм, 1,796 образцов)

## 🚀 Ежедневная разработка

### 1. Запуск PostgreSQL
```bash
make -f Makefile.clean dev-start
```

### 2. В отдельных терминалах запустите:

**Терминал 1 - Django backend:**
```bash
make -f Makefile.clean dev-backend
```

**Терминал 2 - React frontend:**
```bash
make -f Makefile.clean dev-frontend
```

### 3. Работайте с системой:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000/api/
- **Админ-панель**: http://localhost:8000/admin/

## 🔧 Дополнительные команды

```bash
# Проверка статуса
make -f Makefile.clean dev-status

# Остановка PostgreSQL
make -f Makefile.clean dev-stop

# Статус всей системы
make -f Makefile.clean status

# Информация о системе
make -f Makefile.clean info
```

## ⚡ Преимущества очищенного подхода

✅ **Простота**: только необходимые команды  
✅ **Скорость**: быстрая разработка без лишних Docker накладных расходов  
✅ **Ясность**: четкое разделение команд по категориям  
✅ **Актуальность**: убраны устаревшие и дублирующиеся команды  

## 🔄 Переключение в продакшн

Когда готово к развертыванию:

```bash
# Остановить разработку
make -f Makefile.clean dev-stop

# Запустить продакшн
make -f Makefile.clean quick-deploy
```

## 📋 Сравнение с оригинальным Makefile

| **Оригинальный** | **Очищенный** | **Экономия** |
|------------------|---------------|--------------|
| 716 строк        | ~200 строк    | 70% меньше   |
| ~80 команд       | ~20 команд    | 75% меньше   |
| Много дублей     | Без дублей    | 100% четко   |

## 🎯 Рекомендуемый workflow

1. **Используйте очищенный Makefile** для ежедневной работы:
   ```bash
   make -f Makefile.clean dev-start
   make -f Makefile.clean dev-backend   # терминал 1
   make -f Makefile.clean dev-frontend  # терминал 2
   ```

2. **Оригинальный Makefile** оставьте для специальных задач (backup, деплой на удаленные серверы и т.д.)

## 🚀 Быстрый старт прямо сейчас

Если у вас уже настроена система:

```bash
# Запуск существующей системы (3 команды в разных терминалах):
docker-compose -f docker-compose.dev.yml up -d  # PostgreSQL
make -f Makefile.clean dev-backend               # Django
make -f Makefile.clean dev-frontend              # React
```

Готово! ✨ 