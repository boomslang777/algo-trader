FROM node:16-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Build the app
RUN npm run build

# Install serve to run the built app
RUN npm install -g serve

# Command to serve the app
CMD ["serve", "-s", "dist", "-l", "5173"] 