import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType

import boto3
from botocore.client import Config

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "speed-layer"

KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
KAFKA_TOPIC = "lecturas-tiempo"


def asegurar_bucket():
    cliente = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )
    buckets_existentes = [b["Name"] for b in cliente.list_buckets()["Buckets"]]
    if BUCKET_NAME not in buckets_existentes:
        cliente.create_bucket(Bucket=BUCKET_NAME)
        print(f"Bucket '{BUCKET_NAME}' creado en MinIO.")
    else:
        print(f"Bucket '{BUCKET_NAME}' ya existe.")


ESQUEMA_LECTURA = StructType([
    StructField("id_ubicacion", IntegerType()),
    StructField("nombre", StringType()),
    StructField("timestamp_lectura", StringType()),
    StructField("temperatura", DoubleType()),
    StructField("humedad", DoubleType()),
    StructField("precipitacion", DoubleType()),
    StructField("velocidad_viento", DoubleType()),
    StructField("direccion_viento", DoubleType()),
    StructField("codigo_tiempo", IntegerType()),
])


def main():
    asegurar_bucket()

    spark = SparkSession.builder \
        .appName("SpeedLayerLecturasTiempo") \
	.master("spark://spark-master:7077") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.8,org.apache.hadoop:hadoop-aws:3.3.4") \
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    df_kafka = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .load()

    df_parseado = df_kafka.selectExpr("CAST(value AS STRING) as json_str") \
        .select(from_json(col("json_str"), ESQUEMA_LECTURA).alias("datos")) \
        .select("datos.*")

    query = df_parseado.writeStream \
        .format("parquet") \
        .option("path", f"s3a://{BUCKET_NAME}/lecturas-tiempo/") \
        .option("checkpointLocation", "/tmp/checkpoint") \
        .outputMode("append") \
        .trigger(processingTime="30 seconds") \
        .start()

    query.awaitTermination()


if __name__ == "__main__":
    main()
