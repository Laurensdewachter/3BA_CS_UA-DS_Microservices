# Start from the official Python 3.12 image
FROM python:3.12-bookworm

# Set working directory
WORKDIR /app

# Take advantage of layering to prevent re-installing dependencies
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

# Copy prisma schema and generate client
COPY ./schema.prisma /app
RUN prisma generate

# Copy source files
COPY app.py /app

# Push the database schema to the database on container start
CMD prisma db push; python -m flask --app app run --host 0.0.0.0 --port 5002
