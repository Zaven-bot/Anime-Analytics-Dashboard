# Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
RUN npm ci 
# clean install (ci)

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Default command
CMD ["npm", "start"]
