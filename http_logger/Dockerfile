FROM python:3.12-slim
WORKDIR /code
EXPOSE 8000
COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY *.py /code

CMD ["uvicorn", "http_logger:app", "--host", "0.0.0.0", "--port", "8000"]
