FROM python:3.12-slim-bookworm
# Copy uv binary from official image for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install project dependencies globally using uv and pyproject.toml
RUN uv pip install --system .

EXPOSE 8000

# Run the application (start.sh handles secrets and launches the app)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]