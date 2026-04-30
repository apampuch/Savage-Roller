# Use an official Python runtime
FROM python:3.13-alpine

# Set working directory
WORKDIR /app

# Copy dependency list first (better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# make data dir
RUN mkdir -p /app/data

# Run your app (change this!)
CMD ["python", "savageroller.py", "docker"]
