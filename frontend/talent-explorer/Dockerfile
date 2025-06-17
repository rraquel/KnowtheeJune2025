# Dockerfile for Talent Explorer frontend
FROM node:20-alpine

WORKDIR /app

# Copy package files first to leverage Docker cache
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Expose the port
EXPOSE 5173

# Start the development server with host flag to allow external access
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"] 