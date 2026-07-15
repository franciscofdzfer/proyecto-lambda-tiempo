# Fase 5 — Visualización

## Objetivo

Cerrar el ciclo de la arquitectura con una capa de presentación: un notebook Jupyter con PySpark que lee los datos ya persistidos tanto de la Speed Layer (MinIO) como de la Batch Layer (Hive/HDFS), y genera gráficos comparativos.

## Por qué esta capa no aparece en el diagrama original

El diagrama de la arquitectura Lambda dibujado en la pizarra no incluye ningún componente de visualización explícito — a diferencia de la Arquitectura 1 (Kappa), que sí tiene un "Dashboard" marcado. Se decidió añadir esta fase igualmente porque, sin ella, no habría forma sencilla de demostrar visualmente que ambas capas (Speed y Batch) contienen datos coherentes entre sí, algo central para defender el ejercicio.

Entre las opciones valoradas (consultas directas por CLI, Metabase conectado a Hive, o un notebook con gráficos), se eligió el notebook por reutilizar el mismo entorno Spark ya construido en el resto del proyecto, sin añadir un componente de infraestructura nuevo como Metabase.

## Imagen propia en vez de la imagen oficial de Jupyter

Se descartó la imagen oficial `jupyter/pyspark-notebook` porque trae su propia versión de Spark empaquetada, no necesariamente la 3.5.8 usada en el resto del proyecto — usar una versión distinta de Spark en el notebook frente al clúster habría sido una fuente de riesgo innecesaria. En su lugar, se construyó una imagen propia con el mismo patrón ya validado en `spark-cluster` y `spark-streaming`: Java 21 + PySpark 3.5.8 instalado vía pip, añadiendo JupyterLab, matplotlib, pandas y boto3.

## Incidencia resuelta: `distutils` no existe en Python 3.12

Al ejecutar `toPandas()` sobre un DataFrame de Spark, apareció `ModuleNotFoundError: No module named 'distutils'`. La causa es que Python 3.12 eliminó el módulo `distutils` de la librería estándar, mientras que PySpark 3.5.8 todavía depende de él internamente para esa operación. En lugar de parchear el código interno de PySpark, se resolvió bajando la imagen base del notebook a **Python 3.11** (versión donde `distutils` todavía existe), replicando el mismo tipo de incompatibilidad de versión de Python que ya se había documentado y resuelto en ejercicios anteriores del curso con Python 3.14.

## Sesión Spark en modo local, no contra el clúster

A diferencia del consumidor de la Speed Layer, el notebook ejecuta Spark en **modo local** dentro del propio contenedor, en lugar de conectarse al clúster `spark-master`. La razón es que se trata de consultas puntuales sobre datos ya persistidos (no un job de streaming continuo), por lo que no se necesita la potencia distribuida del clúster — y evita además cualquier posible desajuste de versión entre el notebook y los workers.

## Lectura de la Batch Layer sin pasar por el metastore de Hive

Para leer la tabla `lecturas_tiempo_parquet` desde Spark no se estableció una conexión al metastore Thrift de Hive. En su lugar, se leyó directamente la ubicación física donde Hive almacena los ficheros Parquet de una tabla gestionada (`/user/hive/warehouse/<nombre_tabla>`), ya que son ficheros Parquet estándar que Spark puede leer sin necesitar hablar con el metastore — evitando configuración adicional de integración Spark-Hive innecesaria para este caso de uso puntual.

## Código de las celdas

### Celda 1 — Sesión Spark con acceso a MinIO

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("VisualizacionLambdaTiempo") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

print("Spark version:", spark.version)
```

### Celda 2 — Lectura de la Speed Layer (MinIO)

```python
df_speed = spark.read.parquet("s3a://speed-layer/lecturas-tiempo/")
df_speed.show(10)
print("Total registros Speed Layer:", df_speed.count())
```

### Celda 3 — Gráfico: temperatura media por ciudad (Speed Layer)

```python
import matplotlib.pyplot as plt

df_pandas = df_speed.groupBy("nombre").avg("temperatura").toPandas()
df_pandas = df_pandas.rename(columns={"avg(temperatura)": "temperatura_media"})
df_pandas = df_pandas.sort_values("temperatura_media", ascending=False)

plt.figure(figsize=(8, 5))
plt.bar(df_pandas["nombre"], df_pandas["temperatura_media"], color="steelblue")
plt.title("Temperatura media por ciudad (Speed Layer)")
plt.ylabel("Temperatura (°C)")
plt.xlabel("Ciudad")
plt.tight_layout()
plt.show()
```

![Temperatura media por ciudad - Speed Layer](imagenes/speedLayer.png)

### Celda 4 — Lectura de la Batch Layer (Hive/HDFS)

```python
df_batch = spark.read.parquet("hdfs://namenode:8020/user/hive/warehouse/lecturas_tiempo_parquet")
df_batch.show(5)
print("Total registros Batch Layer:", df_batch.count())
```

### Celda 5 — Gráfico comparativo: Speed Layer vs Batch Layer

```python
df_speed_avg = df_speed.groupBy("nombre").avg("temperatura").toPandas()
df_speed_avg = df_speed_avg.rename(columns={"avg(temperatura)": "speed_layer"})

df_batch_avg = df_batch.groupBy("nombre").avg("temperatura").toPandas()
df_batch_avg = df_batch_avg.rename(columns={"avg(temperatura)": "batch_layer"})

comparativa = df_speed_avg.merge(df_batch_avg, on="nombre").sort_values("nombre")

x = range(len(comparativa))
plt.figure(figsize=(9, 5))
plt.bar([i - 0.2 for i in x], comparativa["speed_layer"], width=0.4, label="Speed Layer", color="steelblue")
plt.bar([i + 0.2 for i in x], comparativa["batch_layer"], width=0.4, label="Batch Layer", color="darkorange")
plt.xticks(x, comparativa["nombre"])
plt.title("Comparativa Speed Layer vs Batch Layer — Temperatura media")
plt.ylabel("Temperatura (°C)")
plt.legend()
plt.tight_layout()
plt.show()
```

![Comparativa Speed Layer vs Batch Layer](imagenes/batchLayer.png)
