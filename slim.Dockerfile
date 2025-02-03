FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

RUN pip install --no-cache-dir setuptools wheel

COPY setup.py .
COPY README.md .
COPY smsaero ./smsaero
COPY tests/scenario.py ./smsaero/scenario.py

RUN pip install --no-cache-dir -e .

FROM python:3.13-slim-bookworm

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/smsaero_send /usr/local/bin/smsaero_send
COPY --from=builder /app/smsaero ./smsaero
