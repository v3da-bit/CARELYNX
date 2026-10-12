FROM node:22-alpine

ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Inlined into the client bundle at build time.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build && chown -R node /app/.next

ENV NODE_ENV=production
USER node
EXPOSE 3000
CMD ["npx", "next", "start", "-H", "0.0.0.0", "-p", "3000"]
