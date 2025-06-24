# 🧬 Strain Collection Management System

[![Production Status](https://img.shields.io/badge/Production-Ready-green.svg)](https://culturedb.elcity.ru)
[![Django](https://img.shields.io/badge/Django-4.2.7-green.svg)](https://djangoproject.com/)
[![React](https://img.shields.io/badge/React-18.0-blue.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org/)

Профессиональная система управления коллекцией штаммов микроорганизмов для научных лабораторий.

## 🌟 Возможности

### 📊 Управление данными
- **881 штамм** микроорганизмов с полной характеризацией
- **1,796 образцов** с детальным отслеживанием
- **1,796 ячеек хранения** с интеллектуальным управлением
- Связанные данные: источники, местоположения, таксономия

### 🔍 Поиск и фильтрация
- **Расширенные фильтры** с множественными условиями И/ИЛИ
- **7 операторов поиска**: equals, contains, starts_with, ends_with, greater_than, less_than, date_range
- **Автоматический поиск** с debounce оптимизацией
- **Полнотекстовый поиск** по всем полям
- Сохранение состояния фильтров в localStorage

### 📈 Аналитика и отчеты
- **Интерактивный дашборд** с метриками в реальном времени
- **Статистика хранилища** с визуализацией заполненности
- **Настраиваемый экспорт** в CSV, JSON, Excel форматах
- **Массовые операции** для редактирования множества записей

### 🏗️ Архитектура
- **Django REST API** с оптимизированными SQL запросами
- **React + TypeScript** frontend с современным UI
- **PostgreSQL** с полнотекстовым поиском и индексацией
- **Docker** контейнеризация для easy deployment

## 🚀 Быстрый старт

### Вариант 1: Продуктивное развертывание (Docker)
```bash
git clone https://github.com/ksushanik/strain_collection.git
cd strain_collection
make quick-deploy
```

### Вариант 2: Разработка (локально)
```bash
git clone https://github.com/ksushanik/strain_collection.git
cd strain_collection
make -f Makefile.clean dev-setup
make -f Makefile.clean dev-start     # PostgreSQL в Docker
make -f Makefile.clean dev-backend   # Django локально (порт 8000)
make -f Makefile.clean dev-frontend  # React локально (порт 3000)
```

## 📱 Демо

🌐 **Live Demo**: [https://culturedb.elcity.ru](https://culturedb.elcity.ru)

### Скриншоты интерфейса

- 📋 **Таблица штаммов** с расширенной фильтрацией
- 🔬 **Детальные карточки** с полной информацией
- 📦 **Управление хранилищем** с визуализацией ячеек
- 📊 **Аналитический дашборд** с метриками

## 🛠️ Технологический стек

### Backend
- **Django 4.2.7** - web framework
- **Django REST Framework** - API
- **PostgreSQL 15** - база данных
- **Pydantic 2.x** - валидация данных
- **Gunicorn** - WSGI сервер

### Frontend
- **React 18** - UI библиотека
- **TypeScript** - типизация
- **Vite** - build tool
- **Tailwind CSS** - стилизация

### DevOps & Инфраструктура
- **Docker & Docker Compose** - контейнеризация
- **Nginx** - reverse proxy и статические файлы
- **GitHub Actions** - CI/CD pipeline
- **Let's Encrypt** - SSL сертификаты

## 📂 Структура проекта

```
strain_collection/
├── backend/                 # Django API
│   ├── collection_manager/  # Основное приложение
│   ├── scripts/            # Утилиты и скрипты
│   └── requirements.txt
├── frontend/               # React приложение
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── pages/         # Страницы приложения
│   │   └── services/      # API сервисы
│   └── package.json
├── data/                  # CSV данные для импорта
├── memory-bank/           # Документация проекта
├── scripts/              # Автоматизация деплоя
└── docker-compose.yml    # Docker конфигурация
```

## 📖 Документация

- 📋 [Быстрый старт](QUICK_START.md)
- 🚀 [Руководство по развертыванию](DEPLOYMENT_README.md)
- 🧪 [Разработка](DEV_QUICK_START_CLEAN.md)
- 💾 [Система backup](BACKUP_QUICK_START.md)
- 🔄 [CI/CD автоматизация](DEPLOYMENT_AUTOMATION.md)

## ⚡ Производительность

### Оптимизированные API endpoints
- **Хранилище**: 2.17s → 0.018s (120x быстрее)
- **Образцы**: 0.043s → 0.017s (2.5x быстрее)
- **Поиск**: все запросы < 0.037s

### Масштабируемость
- Поддержка 10,000+ записей
- Пагинация server-side
- Lazy loading компонентов
- Оптимизированные SQL запросы

## 🔒 Безопасность

- ✅ Валидация данных с Pydantic
- ✅ SQL injection защита через Django ORM
- ✅ CSRF protection
- ✅ SSL/TLS encryption
- ✅ Environment-based конфигурация

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Проект распространяется под MIT лицензией. См. [LICENSE](LICENSE) для деталей.

## 📞 Контакты

- **GitHub**: [@ksushanik](https://github.com/ksushanik)
- **Demo**: [https://culturedb.elcity.ru](https://culturedb.elcity.ru)

---

**🧬 Создано для научного сообщества с ❤️** 