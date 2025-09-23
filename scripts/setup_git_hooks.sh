#!/bin/bash

# Настройка Git hooks для автоматического деплоя
# Использование: ./scripts/setup_git_hooks.sh

set -e

HOOK_DIR=".git/hooks"
PROJECT_DIR="$(pwd)"

echo "🔧 Настройка Git hooks для автоматического деплоя..."

# Проверяем, что мы в git репозитории
if [ ! -d ".git" ]; then
    echo "❌ Это не git репозиторий"
    exit 1
fi

# Создаем pre-commit hook
cat > "$HOOK_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook для strain-collection

echo "🔍 Pre-commit проверки..."

# Проверка синхронизации фронтенда
if [[ -n $(git diff --cached --name-only | grep "frontend/src/") ]]; then
    echo "⚠️  Обнаружены изменения в фронтенде"
    
    # Автоматическая пересборка
    echo "🔨 Автоматическая пересборка фронтенда..."
    cd frontend
    npm run build > /dev/null 2>&1
    cd ..
    
    # Добавляем измененный dist в коммит
    git add frontend/dist/
    
    echo "✅ Фронтенд пересобран и добавлен в коммит"
fi

echo "✅ Pre-commit проверки пройдены"
EOF

# Создаем post-commit hook для автодеплоя (опционально)
cat > "$HOOK_DIR/post-commit" << 'EOF'
#!/bin/bash
# Post-commit hook для автоматического деплоя

# Проверяем ветку
BRANCH=$(git branch --show-current)
AUTO_DEPLOY_BRANCHES="main master"

if [[ " $AUTO_DEPLOY_BRANCHES " =~ " $BRANCH " ]]; then
    echo "🚀 Автоматический деплой для ветки $BRANCH..."
    
    # Запускаем автодеплой в фоне
    nohup ./scripts/auto_deploy.sh --force > deploy.log 2>&1 &
    
    echo "📝 Логи деплоя: tail -f deploy.log"
else
    echo "ℹ️  Автодеплой не настроен для ветки $BRANCH"
fi
EOF

# Делаем hooks исполняемыми
chmod +x "$HOOK_DIR/pre-commit"
chmod +x "$HOOK_DIR/post-commit"

echo "✅ Git hooks настроены:"
echo "  📝 pre-commit:  автоматическая пересборка фронтенда"
echo "  🚀 post-commit: автодеплой для веток main/master"
echo ""
echo "📋 Управление:"
echo "  Включить автодеплой:  git config hooks.autodeploy true"
echo "  Отключить автодеплой: git config hooks.autodeploy false"
echo "" 