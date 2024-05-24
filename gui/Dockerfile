# Start from the official Python 3.12 image
FROM python:3.12-rc-slim-buster

# Set working directory
WORKDIR /app

# Take advantage of layering to prevent re-installing dependencies
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

# Copy source files
COPY ./app.py /app/
COPY ./templates /app/templates

CMD python -m flask run --host 0.0.0.0
