# 1. Base image
FROM python:3.9.15-slim-buster

# 2. Copy files
COPY . /src

# 3. Install dependencies
RUN pip install -r /src/requirements.txt