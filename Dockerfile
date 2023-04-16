# Use the official Python image as the base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the pyproject.toml and poetry.lock files into the container
COPY pyproject.toml poetry.lock ./

# Install Poetry and set the PATH to include Poetry binaries
ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PATH="$POETRY_HOME/bin:$PATH" \
    POETRY_VERSION=1.3.2

# System deps:
RUN pip install "poetry==$POETRY_VERSION"
COPY poetry.lock pyproject.toml ./

# Project initialization:
RUN poetry config virtualenvs.create false \
    && poetry install  --no-interaction --no-ansi --only main --no-root

# Copy the rest of the application code
COPY bot/ bot/
COPY .env ./

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/app

# Expose the port the bot will run on
EXPOSE 8080

# Set the entrypoint for running the bot
CMD ["poetry", "run", "python", "bot/main.py"]