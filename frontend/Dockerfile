# Use Node.js LTS version
FROM node:18

# Install git and bash
RUN apk add --no-cache git bash

# Install pnpm globally
RUN npm install -g pnpm

# Set working directory
WORKDIR /app

# Copy package files for better Docker layer caching
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Expose ports
EXPOSE 5173 4173

# Default command for development (can be overridden in docker-compose)
CMD ["pnpm", "dev"]