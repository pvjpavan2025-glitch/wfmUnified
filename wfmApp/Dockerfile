FROM node:18-alpine

# Install dependencies needed for native modules
RUN apk add --no-cache libc6-compat

# Set the working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install all dependencies including dev dependencies for TypeScript
RUN npm ci --silent

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start in development mode (faster startup)
CMD ["npm", "run", "dev"]
