FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir setuptools wheel

RUN python setup.py develop && pip install -e .[dev]
