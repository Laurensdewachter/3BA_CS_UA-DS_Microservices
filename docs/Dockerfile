# Start from the official Python 3.12 image
FROM python:3.12-bookworm as base

# Set working directory
WORKDIR /docs

# Install mkdocs
RUN pip install mkdocs mkdocs-material

COPY . .

RUN mkdocs build

FROM nginx:1.25-bookworm
COPY --from=base /docs/site /usr/share/nginx/html
