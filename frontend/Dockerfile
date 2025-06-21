# --- 1. Этап сборки ---
FROM node:20-alpine as builder

WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем исходный код
COPY . .

# Собираем production-билд
RUN npm run build

# --- 2. Финальный образ ---
FROM nginx:1.25-alpine

# Копируем собранные статические файлы из этапа сборки
COPY --from=builder /app/dist /usr/share/nginx/html

# Копируем конфигурацию Nginx
# Этот файл мы создадим следующим шагом
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт 80
EXPOSE 80

# Запускаем Nginx
CMD ["nginx", "-g", "daemon off;"] 