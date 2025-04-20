FROM node:23-alpine AS builder

WORKDIR /app
RUN apk add --no-cache bash findutils

COPY package*.json ./
COPY tsconfig.json ./
RUN npm install --production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
