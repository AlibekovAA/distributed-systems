FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache bash findutils

COPY package*.json ./
COPY tsconfig.json ./
COPY bs-config.json ./

RUN npm install

COPY src/ src/

RUN mkdir -p dist
RUN npm run build

EXPOSE 3000

CMD ["npx", "lite-server", "--config", "bs-config.json"]
