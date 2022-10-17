
FROM python:3.9
COPY ./app /app
COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --no-cache-dir -r /app/requirements.txt
ENTRYPOINT bash ./run.sh