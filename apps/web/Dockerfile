# Multi-stage build: the runtime image holds only Next.js' traced standalone server, not node_modules.
FROM node:22-alpine AS build
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Inlined into the client bundle at build time. The default (relative) works behind the Caddy proxy
# on any host; set an absolute URL only when the API lives on a different origin.
ARG NEXT_PUBLIC_API_BASE_URL=/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN NEXT_OUTPUT=standalone npm run build


FROM node:22-alpine
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000
WORKDIR /app

COPY --from=build --chown=node /app/.next/standalone ./
COPY --from=build --chown=node /app/.next/static ./.next/static
COPY --from=build --chown=node /app/public ./public

USER node
EXPOSE 3000
CMD ["node", "server.js"]
