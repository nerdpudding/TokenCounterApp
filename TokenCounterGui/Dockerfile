FROM python:3.10-slim

WORKDIR /app

# Install git for repo cloning functionality
RUN apt-get update && apt-get install -y git && apt-get clean

# Copy requirements and install dependencies
COPY TokenCounterGui/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the codebase-token-counter package
COPY codebase_token_counter /app/codebase_token_counter
COPY requirements.txt /app/original_requirements.txt
COPY setup.py /app/setup.py
COPY README.md /app/README.md
COPY MANIFEST.in /app/MANIFEST.in
RUN pip install -e .

# Copy web application files
COPY TokenCounterGui/app /app/app
COPY TokenCounterGui/static /app/static
COPY TokenCounterGui/templates /app/templates

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app/app.py

# Expose the port (we'll use an uncommon port like 7654)
EXPOSE 7654

# Command to run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=7654"]