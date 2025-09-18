# Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001 -G appuser

# Copy package files first for better caching
COPY package*.json ./
RUN npm ci 
# clean install (ci)

# Copy source code and set ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3000

# Default command
CMD ["npm", "start"]
