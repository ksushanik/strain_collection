# React Frontend - Система учета штаммов микроорганизмов

## 🎨 Технологический стек

- **React 18** с TypeScript
- **Vite** для быстрой разработки
- **TailwindCSS** для стилизации
- **React Router** для навигации
- **Axios** для HTTP запросов
- **Lucide React** для иконок
- **Tanstack Table** для продвинутых таблиц

## 🚀 Быстрый старт

### Установка зависимостей
```bash
npm install
```

### Запуск в режиме разработки
```bash
npm run dev
```
Frontend будет доступен на `http://localhost:3000`

### Сборка для production
```bash
npm run build
```

## 📁 Структура проекта

```
frontend/
├── src/
│   ├── components/         # Переиспользуемые компоненты
│   │   └── Layout.tsx     # Основной лейаут приложения
│   │   ├── pages/             # Страницы приложения
│   │   │   ├── Dashboard.tsx  # Главная страница с статистикой
│   │   │   └── Strains.tsx    # Страница штаммов
│   │   ├── services/          # API сервисы
│   │   │   └── api.ts         # Интеграция с Django backend
│   │   ├── types/             # TypeScript типы
│   │   │   └── index.ts       # Интерфейсы для данных
│   │   ├── App.tsx            # Главный компонент приложения
│   │   ├── main.tsx           # Точка входа
│   │   └── index.css          # Стили с TailwindCSS
│   ├── tailwind.config.js     # Конфигурация TailwindCSS
│   ├── vite.config.ts         # Конфигурация Vite
│   └── package.json           # Зависимости и скрипты
```

## 🌟 Особенности

### Дизайн
- **Современный UI** с TailwindCSS
- **Адаптивный дизайн** для всех устройств
- **Темная/светлая темы** (планируется)
- **Accessibility** соответствие стандартам

### Функциональность
- **Dashboard** с интерактивными графиками статистики
- **Поиск и фильтрация** штаммов в реальном времени
- **Таблицы** с сортировкой и пагинацией
- **Валидация форм** с Pydantic на backend
- **TypeScript** для типобезопасности

### Интеграция с Backend
- **Автоматический proxy** к Django API
- **Обработка ошибок** и состояний загрузки
- **Валидация данных** через Pydantic
- **RESTful API** взаимодействие

## 📊 Страницы

### 🏠 Dashboard (`/`)
- Общая статистика системы
- Графики распределения данных
- Индикаторы качества данных
- Информация о валидации

### 🦠 Штаммы (`/strains`)
- Список всех штаммов
- Поиск по названию, коду, таксономии
- Фильтрация по RCAM ID, таксономии
- Экспорт данных (планируется)

### 🧪 Образцы (`/samples`) - В разработке
- Просмотр образцов
- Связь со штаммами и хранилищами
- Фильтрация по свойствам

### 📦 Хранилище (`/storage`) - В разработке
- Визуализация занятости боксов
- Карта ячеек хранения
- Поиск свободных мест

## 🔧 Конфигурация

### Vite (vite.config.ts)
```typescript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
    },
  },
}
```

### TailwindCSS (tailwind.config.js)
- Кастомные цвета для primary/secondary палитры
- Переиспользуемые компоненты (`.btn-primary`, `.card`, `.input-field`)
- Адаптивные breakpoints

## 🎯 API Интеграция

### Endpoints
```typescript
// Основные
GET  /api/               // Статус API
GET  /api/stats/         // Статистика системы

// Штаммы
GET  /api/strains/       // Список штаммов с фильтрами
POST /api/strains/validate/ // Валидация данных штамма

// Образцы
GET  /api/samples/       // Список образцов с фильтрами  
POST /api/samples/validate/ // Валидация данных образца

// Хранилища
GET  /api/storage/       // Информация о хранилищах
```

### Типы данных
```typescript
interface Strain {
  id: number;
  short_code: string;
  rrna_taxonomy: string;
  identifier: string;
  name_alt?: string;
  rcam_collection_id?: string;
}
```

## 🚀 Команды разработки

### Из корня проекта (Makefile)
```bash
make frontend-install    # Установка зависимостей
make frontend-dev        # Запуск в режиме разработки
make frontend-build      # Сборка production
make full-dev           # Запуск backend + frontend
```

### Прямые команды
```bash
npm run dev              # Разработка
npm run build            # Сборка
npm run preview          # Предпросмотр production
npm run lint             # Проверка кода (если настроен)
```

## 🔮 Планы развития

### Ближайшие задачи
- [ ] Страница образцов с полным функционалом
- [ ] Интерактивная карта хранилищ
- [ ] Формы добавления/редактирования данных
- [ ] Экспорт данных в различных форматах

### Долгосрочные цели
- [ ] Графики и аналитика
- [ ] Система уведомлений
- [ ] Темная тема
- [ ] PWA возможности
- [ ] Offline режим

## 🤝 Интеграция с системой

Frontend полностью интегрирован с Django backend:
- ✅ **Валидация**: Pydantic схемы
- ✅ **API**: RESTful endpoints
- ✅ **Данные**: 881 штамм, 1796 образцов
- ✅ **Безопасность**: CORS настроен
- ✅ **Типизация**: TypeScript интерфейсы

**URL для разработки:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Admin: http://localhost:8000/admin/
