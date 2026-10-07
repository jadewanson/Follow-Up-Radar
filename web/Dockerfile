FROM node:24-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY index.html dev-server.mjs ./
COPY src ./src

EXPOSE 5173

CMD ["node", "dev-server.mjs"]
