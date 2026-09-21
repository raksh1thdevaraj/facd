# ==============================================================================
# Multi-Stage Production Dockerfile for React Frontend
# Stage 1: Build bundle using Node 18 Alpine
# Stage 2: Serve static files with lightweight Nginx Alpine (< 30MB)
# ==============================================================================

# --- STAGE 1: Frontend Build ---
FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependency specifications and install dependencies
COPY package*.json ./
RUN npm ci

# Copy frontend source files
COPY . .

# Build production bundle (tsc && vite build -> dist)
RUN npm run build


# --- STAGE 2: Lightweight Nginx Web Server ---
FROM nginx:1.25-alpine AS runtime

# Remove default Nginx welcome site
RUN rm -rf /usr/share/nginx/html/*

# Copy built distribution assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom production Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Health check for web server availability
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
