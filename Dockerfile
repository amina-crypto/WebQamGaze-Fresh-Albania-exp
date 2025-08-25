# Dockerfile — run the Heroku webgazer Flask app
FROM python:3.10-slim

# (optional) graceful stop
RUN apt-get update && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy the Heroku app into the image
COPY HerokuCode/heroku-webgazer/ /app/

# install deps (use the app’s requirements.txt if present)
RUN if [ -f requirements.txt ]; then \
      pip install --no-cache-dir -r requirements.txt ; \
    else \
      pip install --no-cache-dir flask==2.2.* gunicorn==21.* ; \
    fi

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["/usr/bin/tini","--"]

# EITHER run via python…
# CMD ["python", "herokuapp.py", "--port", "8080"]

# …or recommended: run via gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "herokuapp:app"]
# Use slim Python
FROM python:3.10-slim

# Install system dependencies required for building psiturk + psycopg2 + psutil
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpq-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Heroku webgazer app
COPY HerokuCode/heroku-webgazer/ /app/

# Install Python requirements (from HerokuCode requirements.txt)
RUN pip install --upgrade pip \
    && if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; \
       else pip install --no-cache-dir flask gunicorn; fi

# Expose port 8080 for the Flask server
EXPOSE 8080

# Start Flask app via gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "herokuapp:app"]
