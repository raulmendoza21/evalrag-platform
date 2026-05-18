# syntax=docker/dockerfile:1.7
FROM node:20-alpine

WORKDIR /app

# Install deps first (cached unless package.json changes)
COPY package.json ./
RUN npm install --no-audit --no-fund

# App sources (overridden by bind mount in dev compose)
COPY . .

EXPOSE 5173
ENV HOST=0.0.0.0
CMD ["npm", "run", "dev"]
