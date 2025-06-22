# Используем готовый nginx образ
FROM nginx:1.25-alpine

# Копируем собранные статические файлы из локальной папки dist
COPY ./dist /usr/share/nginx/html

# Копируем конфигурацию Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт 80
EXPOSE 80

# Запускаем Nginx
CMD ["nginx", "-g", "daemon off;"] 