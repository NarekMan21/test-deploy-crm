# Используем Node.js 18 как базовый образ
FROM node:20-alpine AS base

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости только при изменении package.json
FROM base AS deps
COPY package*.json ./
RUN npm ci

# Создаем production build
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Отключаем telemetry для production
ENV NEXT_TELEMETRY_DISABLED=1

# Собираем приложение с переменными окружения
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_API_SERVER_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_API_SERVER_URL=${NEXT_PUBLIC_API_SERVER_URL}

RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Создаем пользователя для безопасности
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Копируем необходимые файлы
COPY --from=builder /app/public ./public

# Устанавливаем правильные разрешения для prerendered cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Копируем готовый build
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# Открываем порт 3000
EXPOSE 3000

ENV PORT=3000

# Запускаем приложение
CMD ["node", "server.js"]