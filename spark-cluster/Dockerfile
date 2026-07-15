FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends openjdk-21-jdk-headless && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

RUN pip install pyspark==3.5.8

WORKDIR /app
