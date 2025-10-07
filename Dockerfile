FROM node:24-bookworm-slim AS build

WORKDIR /usr/app

COPY package.json ./
COPY tsconfig.json ./
COPY src ./src

RUN npm install
RUN npm run build

FROM node:24-bookworm-slim

WORKDIR /usr/app

COPY package.json ./
RUN npm install --production

COPY --from=build /usr/app/dist ./dist

RUN npm install pm2 -g

EXPOSE 5000
CMD ["pm2-runtime", "dist/server.js"]

