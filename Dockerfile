# Первая стадия
FROM python:3.13.1-alpine AS builder

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Вторая стадия
FROM python:3.13.1-alpine

COPY --from=builder /opt/venv /opt/venv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /code

COPY ./controllers /code/controllers
COPY ./data /code/data
COPY ./database /code/database
COPY ./models /code/models
COPY ./docs/swagger_descriptions.md /code/docs/swagger_descriptions.md
COPY ./main.py /code/main.py

CMD ["python3", "./main.py", "--port", "8080"]
