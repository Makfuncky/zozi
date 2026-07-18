# Frontend Dockerfile
# Build context is the top-level frontend/ directory so the web app can resolve
# the local ../shared package dependency during npm ci.
FROM node:20-alpine AS builder

WORKDIR /app

COPY shared ./shared
COPY web_app ./web_app

WORKDIR /app/shared
RUN npm ci --legacy-peer-deps

WORKDIR /app/web_app
RUN npm ci --legacy-peer-deps
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app/web_app

COPY --from=builder /app/shared /app/shared
COPY --from=builder /app/web_app/.next ./.next
COPY --from=builder /app/web_app/node_modules ./node_modules
COPY --from=builder /app/web_app/package.json ./package.json
COPY --from=builder /app/web_app/public ./public

EXPOSE 3000

ENV NODE_ENV=production

CMD ["npm", "start"]