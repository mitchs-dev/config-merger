ARG PYTHON_VERSION=3.13-slim-bullseye

# Build stage
FROM python:${PYTHON_VERSION} AS builder

WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:${PYTHON_VERSION}

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY . .

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "merge.py"]