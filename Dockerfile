FROM python:3.12-slim

RUN apt-get update; apt-get install -y curl gcc

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false && pip install --upgrade pip

COPY README.md /
COPY poetry.lock /
COPY pyproject.toml /

# Install only dependencies, not the project itself
RUN poetry install --no-root

COPY migrations /migrations
COPY ./src/voice_bridge_be/__init__.py /src/voice_bridge_be/__init__.py
COPY ./src/voice_bridge_be /src/voice_bridge_be

ENV PYTHONPATH=/src

EXPOSE 80
CMD uvicorn voice_bridge_be.main:app --host 0.0.0.0 --port 80 --no-access-log