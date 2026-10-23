ARG NODE_IMAGE=node:24.22.1-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205
FROM ${NODE_IMAGE} AS build
WORKDIR /usr/app
COPY package.json package-lock.json tsconfig.json ./
RUN npm ci
COPY src ./src
COPY tests ./tests
RUN npm test
FROM ${NODE_IMAGE} AS dependencies
WORKDIR /usr/app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force
FROM ${NODE_IMAGE} AS runtime
ENV NODE_ENV=production LANG=C.UTF-8 LC_ALL=C.UTF-8
WORKDIR /usr/app
COPY --from=dependencies /usr/app/node_modules ./node_modules
COPY --from=build /usr/app/dist ./dist
COPY package.json ./
EXPOSE 5000
CMD ["node", "dist/server.js"]
