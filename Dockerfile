# Use an official Python 3.9 base image for compatibility
FROM python:3.9-slim

# Set working directory
WORKDIR /psiturk

# Copy the contents of heroku-webgazer into the container root
COPY HerokuCode/heroku-webgazer/. /psiturk

# Debug: List contents of /psiturk to verify static/js is copied
RUN ls -l /psiturk

# Install system dependencies (Node.js/npm for WebGazer/jsPsych, build tools for cffi and npm builds)
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies compatible with psiturk==2.3.3
RUN pip install --no-cache-dir \
    psiturk==2.3.3 \
    flask==1.0.3 \
    werkzeug==0.15.4

# Configure npm to handle network issues (increase timeout and retries)
RUN npm config set fetch-retries 5 \
    && npm config set fetch-retry-mintimeout 20000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && npm config set fetch-timeout 120000

# Install WebGazer and jsPsych via npm, ensuring build tools are available
RUN npm install --build-from-source webgazer jspsych

# Debug: List contents of node_modules/jspsych to verify dist/jspsych.js is built
RUN ls -l /psiturk/node_modules/jspsych/

# Ensure static/js exists and copy npm-installed files to it
RUN mkdir -p /psiturk/static/js \
    && cp node_modules/webgazer/dist/webgazer.js /psiturk/static/js/ \
    && [ -f "node_modules/jspsych/dist/jspsych.js" ] && cp node_modules/jspsych/dist/jspsych.js /psiturk/static/js/ || echo "jspsych.js not found, using local file"

# Expose the default psiTurk port
EXPOSE 22362

# Start psiTurk server
CMD ["psiturk-server"]