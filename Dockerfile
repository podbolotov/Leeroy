FROM python:3.12.5

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./controllers /code/controllers
COPY ./data /code/data
COPY ./database /code/database
COPY ./models /code/models
COPY ./README.md /code/README.md
COPY ./main.py /code/main.py

CMD ["python3", "./main.py", "--port", "8080"]
