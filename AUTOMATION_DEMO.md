# 🎮 Демонстрация автоматизации деплоя

Практические примеры использования системы автоматизации strain-collection.

## 🌟 Текущий статус системы

✅ **Удаленный сервер работает:**
- 🌐 URL: http://89.169.171.236:8081
- 🐳 3 контейнера healthy (backend, frontend, db)
- 📊 881 штамм + 1796 образцов
- 💾 Использование диска: 97% (/dev/vda2 - 30GB)

## 🚀 Сценарии использования

### 1. Обычный деплой после разработки

```bash
# После внесения изменений в код
git add .
git commit -m "feat: новая функциональность"

# Автоматический деплой
make auto-deploy
```

**Что произойдет:**
- ✅ Проверка требований (Docker, SSH, авторизация)
- ✅ Анализ изменений (git status, фронтенд)
- ✅ Тестирование (TypeScript build)
- ✅ Сборка (фронтенд + Docker образы)
- ✅ Публикация на Docker Hub
- ✅ Деплой на сервер
- ✅ Health checks

### 2. Экстренный деплой (hotfix)

```bash
# Быстрый деплой без тестов
make auto-deploy-fast
```

**Особенности:**
- ⚡ Пропуск тестов
- ⚡ Принудительный режим
- ⚡ Минимальное время деплоя

### 3. CI/CD автоматизация

```bash
# Настройка Git hooks
make setup-git-hooks

# Включение автодеплоя
git config hooks.autodeploy true

# Теперь каждый коммит в main/master = автодеплой
git commit -m "fix: критическое исправление"
# → Автоматически запустится деплой в фоне
```

### 4. Мониторинг и диагностика

```bash
# Проверка статуса системы
make remote-status

# Просмотр логов
make remote-logs

# Перезапуск при проблемах
make remote-restart
```

## 📊 Пример полного цикла разработки

### Шаг 1: Разработка в dev режиме
```bash
# Запуск dev окружения
make dev-start    # PostgreSQL в Docker
make dev-backend  # Django на 8000
make dev-frontend # React на 3000

# Разработка...
# Изменения в frontend/src/components/
```

### Шаг 2: Коммит изменений
```bash
git add frontend/src/
git commit -m "feat: улучшение UX фильтров"

# Pre-commit hook автоматически:
# - Пересоберет фронтенд
# - Добавит frontend/dist/ в коммит
```

### Шаг 3: Автоматический деплой
```bash
# Post-commit hook автоматически запустит:
./scripts/auto_deploy.sh --force

# Логи деплоя:
tail -f deploy.log
```

### Шаг 4: Проверка результата
```bash
# Статус системы
make remote-status

# Проверка в браузере
curl http://89.169.171.236:8081/api/health/
```

## 🎯 Конкретные команды для разных случаев

### Разработчик делает изменения
```bash
# 1. Обычная разработка
vim frontend/src/pages/Strains.tsx

# 2. Тестирование локально
make dev-frontend

# 3. Коммит
git add .
git commit -m "feat: добавил новые фильтры"

# 4. Деплой (интерактивный)
make auto-deploy
```

### DevOps обновляет продакшн
```bash
# 1. Принудительный деплой
make auto-deploy-force

# 2. Мониторинг
watch "make remote-status"

# 3. При проблемах
make remote-logs
make remote-restart
```

### CI/CD pipeline
```bash
# В .github/workflows/deploy.yml
- name: Deploy to production
  run: ./scripts/auto_deploy.sh --force --skip-tests
  env:
    SSH_PRIVATE_KEY: ${{ secrets.SSH_KEY }}
```

## 🔧 Настройка для вашего проекта

### 1. Изменение конфигурации
```bash
# Редактирование настроек
vim deploy.config

# Основные параметры:
REMOTE_HOST=ваш_сервер
REMOTE_URL=http://ваш_сервер:порт
DOCKER_REGISTRY=ваш_registry
```

### 2. Кастомизация скриптов
```bash
# Копирование и адаптация
cp scripts/auto_deploy.sh scripts/my_deploy.sh
vim scripts/my_deploy.sh

# Добавление в Makefile
echo "my-deploy: ./scripts/my_deploy.sh" >> Makefile
```

## 📈 Производительность

### Времена выполнения (примерные)
- 🔍 Проверки: 5-10 секунд
- 🔨 Сборка фронтенда: 30-60 секунд
- 🐳 Сборка Docker: 2-5 минут
- 📤 Push на Hub: 1-3 минуты
- 🚀 Деплой на сервер: 1-2 минуты
- 🏥 Health checks: 30 секунд

**Общее время:** 5-12 минут

### Оптимизация
```bash
# Быстрый деплой (без тестов)
make auto-deploy-fast  # 3-8 минут

# Только обновление сервера (образы уже на Hub)
make update-remote     # 1-3 минуты
```

## 🛡️ Безопасность в действии

### Автоматические резервные копии
```bash
# Каждый деплой создает backup
ssh 4feb "ls ~/strain_ultra_minimal/.env.backup.*"

# Ручное восстановление
ssh 4feb "cd ~/strain_ultra_minimal && 
  cp .env.backup.20241222_140530 .env && 
  docker compose restart"
```

### Валидация перед деплоем
```bash
# Проверка SSH доступа
ssh 4feb "echo 'Сервер доступен'"

# Проверка Docker Hub авторизации
docker system info | grep Username

# Проверка здоровья системы
curl -f http://89.169.171.236:8081/api/health/
```

## 🎉 Результат автоматизации

**До автоматизации:**
- 🕐 15-30 минут ручной работы
- 🐛 Высокий риск ошибок
- 📝 Много ручных команд
- 😰 Стресс при деплое

**После автоматизации:**
- ⚡ 5-12 минут автоматически
- ✅ Минимальный риск ошибок
- 🤖 Одна команда
- 😌 Спокойствие и уверенность

## 🔮 Дальнейшее развитие

### Планируемые улучшения:
1. **Уведомления:** Slack/Telegram о статусе деплоя
2. **Rollback:** Автоматический откат при ошибках
3. **Staging:** Деплой в тестовую среду
4. **Metrics:** Сбор метрик времени деплоя
5. **Blue-Green:** Деплой без простоя

### Интеграции:
- GitHub Actions / GitLab CI
- Prometheus мониторинг
- ELK Stack для логов
- Kubernetes поддержка 