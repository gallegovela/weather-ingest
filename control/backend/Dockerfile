# Control panel backend image (FastAPI API).
# See spec/control/core.md, "Deployment": containerized with Docker,
# as a new service in the project root's docker-compose.yml.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
