# Frontend Multi-stage Build
# React/Vite application with nginx serving

# ===== Build Stage =====
FROM node:20 AS builder

ARG VITE_API_URL=http://localhost:8000/api
ENV VITE_API_URL=$VITE_API_URL

WORKDIR /app

# Copy package files
COPY package.json ./
COPY package-lock.json* ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Ensure node_modules/.bin is executable
RUN chmod -R +x /app/node_modules/.bin

# Build React/Vite application with environment variable
RUN VITE_API_URL=$VITE_API_URL npx vite build

# Verify build output exists
RUN test -d dist || (echo "Build failed: dist directory not found" && exit 1)

# ===== Runtime Stage =====
# Use lightweight nginx image for serving static files
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
