# Use an official Node runtime as the base image
FROM node:14

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the current directory contents into the container at /app
COPY . .

# Set the backend URL environment variable
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}

# Build the app
RUN npm run build

# Install serve to run the application
RUN npm install -g serve

# Make port 3001 available to the world outside this container
EXPOSE 3001

# Run the app when the container launches
CMD ["serve", "-s", "build", "-l", "3001"]
