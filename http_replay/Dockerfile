FROM python:3.12-slim
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
COPY .env /code/.env

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY *.py /code

CMD ["python", "/code/http_replay.py"]
