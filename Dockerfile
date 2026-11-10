FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY alembic.ini ./
COPY migrations ./migrations

# Numeric UID so Kubernetes can enforce runAsNonRoot. No writes to the image filesystem:
# compatible with readOnlyRootFilesystem.
RUN useradd --system --no-create-home --uid 10001 kairos
USER 10001

EXPOSE 8000
# Stateless API only. Migrations run separately (compose "migrate" service,
# Kubernetes Job), never at API startup: several replicas would race.
CMD ["uvicorn", "kairos.main:app", "--host", "0.0.0.0", "--port", "8000"]
