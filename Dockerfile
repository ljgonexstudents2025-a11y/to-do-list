# Use a lightweight Python image
FROM python:3.11-slim

# Where our app will live inside the container
WORKDIR /app

# Install system deps (optional but often useful)
RUN apt-get clean && rm -rf /var/lib/apt/lists/* \
 && apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*


# Copy dependency list and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set env vars for Flask
ENV FLASK_ENV=production
ENV PORT=5000

# Expose the port the app listens on
EXPOSE 5000

# Start the app
CMD ["python", "server.py"]
