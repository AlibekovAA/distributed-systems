FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache bash findutils

COPY package*.json ./
COPY tsconfig.json ./
COPY bs-config.json ./

RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
