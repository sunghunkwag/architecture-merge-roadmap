# Sample Dockerfile for integration test environment
# Base Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt || echo "No requirements.txt found, skipping..."

# Run simple test script
CMD ["python", "-m", "pytest", "tests/", "-v"]
