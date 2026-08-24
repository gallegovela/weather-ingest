# Ingest job worker image.
# See spec/ingest/general.md, "Deployment": containerized with Docker,
# as a new service in the project root's docker-compose.yml.
#
# Build context is the project root, not ingest/ (see docker-compose.yml):
# ingest/*.py uses absolute imports (`from ingest import db`, etc.), same
# as running `python -m ingest.stations` from the project root locally,
# so the `ingest` package needs to sit under /app, not *be* /app.

FROM python:3.12-slim

WORKDIR /app

COPY ingest/requirements.txt ingest/requirements.txt
RUN pip install --no-cache-dir -r ingest/requirements.txt

COPY ingest/ ingest/

CMD ["python", "-m", "ingest.worker"]
