#!/bin/bash
cd frontend
echo "=== Запуск ESLint проверки ==="
npm run lint > lint_results.txt 2>&1
echo "Результаты записаны в frontend/lint_results.txt"
echo "=== Результаты линтинга ==="
cat lint_results.txt 