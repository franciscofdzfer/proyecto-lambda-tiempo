FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends openjdk-21-jdk-headless && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY consumidor.py .

CMD ["python", "-u", "consumidor.py"]
