FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set working directory
WORKDIR /app

# Copy dependency files first (for better caching)
COPY pkg/op-core /app/pkg/op-core
COPY pkg/op-artifacts /app/pkg/op-artifacts
COPY pkg/op-brains /app/pkg/op-brains
COPY pkg/op-data /app/pkg/op-data
COPY pkg/op-app /app/pkg/op-app

# Install dependencies for all packages
RUN cd /app/pkg/op-core && poetry install --no-root --only main
RUN cd /app/pkg/op-artifacts && poetry install --no-root --only main
RUN cd /app/pkg/op-brains && poetry install --no-root --only main
RUN cd /app/pkg/op-data && poetry install --no-root --only main
RUN cd /app/pkg/op-app && poetry install --only main

# Set working directory to op-app
WORKDIR /app/pkg/op-app

# Expose port
EXPOSE 8000

# Health check
# HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
#   CMD curl -f http://localhost:8000/up || exit 1

# Run the application
CMD ["poetry", "run", "python", "-m", "uvicorn", "op_app.api:app", "--host", "0.0.0.0", "--port", "8000"]
