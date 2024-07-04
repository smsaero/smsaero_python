FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN python setup.py develop && pip install -e .[dev]
