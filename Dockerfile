FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip

# Copy the Google Cloud credentials file into the container
COPY service_account_credentials.json /app/keyfile.json

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "main.py"]