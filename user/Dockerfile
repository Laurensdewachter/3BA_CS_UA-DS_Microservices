# Start from the official Python 3.12 image
FROM python:3.12-bookworm

# Set working directory
WORKDIR /app

# Take advantage of layering to prevent re-installing dependencies
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

# Copy prisma schema and format to force installation of prisma cli
COPY ./schema.prisma /app
RUN prisma format

# Copy source files
COPY ./src /app/src

# Push the database schema to the database on container start
CMD prisma db push
