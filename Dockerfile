FROM python:3.10-slim

WORKDIR /app

# Install git for repo cloning functionality
RUN apt-get update && apt-get install -y git && apt-get clean

# Copy and install GUI requirements (from root requirements.txt)
COPY requirements.txt /app/gui_requirements.txt
RUN pip install --no-cache-dir -r /app/gui_requirements.txt

# Copy codebase-token-counter requirements (needed by setup.py)
COPY codebase-token-counter/requirements.txt /app/requirements.txt
# Install codebase-token-counter requirements
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the codebase-token-counter source files
COPY codebase-token-counter/codebase_token_counter /app/codebase_token_counter
COPY codebase-token-counter/setup.py /app/setup.py
COPY codebase-token-counter/README.md /app/README.md
COPY codebase-token-counter/MANIFEST.in /app/MANIFEST.in
# Add any other necessary files from codebase-token-counter if needed

# Install the codebase-token-counter package in editable mode
RUN pip install -e .

# Copy web application files
COPY TokenCounterGui/app /app/app
COPY TokenCounterGui/static /app/static
COPY TokenCounterGui/templates /app/templates

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app/app.py

# Expose the port
EXPOSE 7654

# Command to run the application using Waitress (more production-ready than flask run)
CMD ["waitress-serve", "--host=0.0.0.0", "--port=7654", "app.app:app"]