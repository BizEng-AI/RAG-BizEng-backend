# ---------- build stage ----------
FROM python:3.13.8 AS builder
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# venv lives in /opt/venv (standard path)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.13.8-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# copy venv and make it default
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# copy app code last for faster rebuilds
COPY . .

# Render provides the listening port at runtime through $PORT.
CMD ["/bin/sh", "-c", "exec /opt/venv/bin/uvicorn app:app --host 0.0.0.0 --port ${PORT:-8020}"]
