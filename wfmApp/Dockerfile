# Use the official Node.js runtime as the base image
FROM node:18-alpine AS base

# Install dependencies needed for native modules
RUN apk add --no-cache libc6-compat

# Set the working directory in the container
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install pnpm if not available
RUN npm install -g pnpm

# Install all dependencies (including dev dependencies for build)
RUN pnpm install

# Copy the rest of the application code
COPY . .

# Build the Next.js application
RUN pnpm run build

# Production stage
FROM node:18-alpine AS production

# Install dependencies needed for native modules
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install pnpm if not available
RUN npm install -g pnpm

# Install only production dependencies
RUN pnpm install --prod

# Copy built application from build stage
COPY --from=base /app/.next ./.next
COPY --from=base /app/public ./public
COPY --from=base /app/next.config.mjs ./

# Expose the port the app runs on
EXPOSE 3000

# Start the application
CMD ["pnpm", "start"]
