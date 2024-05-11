FROM python:3.12-bookworm

COPY ./src /app
COPY ./requirements.txt /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "app.py"]
