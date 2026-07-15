# Fase 3 — Speed Layer

## Objetivo

Construir el camino de procesamiento en (casi) tiempo real: un productor que consulta Open-Meteo periódicamente, publica en Kafka, y un consumidor Spark Streaming que lee de Kafka y persiste en MinIO en formato Parquet.

## El productor: frecuencia y diseño de la llamada a la API

Se decidió una frecuencia de sondeo de **1 minuto**. Inicialmente se valoró si esa frecuencia sería excesiva para el límite gratuito de Open-Meteo (10.000 llamadas/día), pero el diseño elegido — una única llamada HTTP por ciclo, con las cinco ciudades combinadas mediante coordenadas separadas por comas — reduce el consumo a 1.440 llamadas/día en el peor caso (ejecución continua 24h), muy por debajo del límite. Además, el uso real del productor se limita a las horas de una sesión de clase, dejando aún más margen.

El productor se implementó en Python puro (`kafka-python` + `requests`), sin frameworks adicionales, publicando un mensaje JSON por ciudad en el topic `lecturas-tiempo`, replicando exactamente las columnas del modelo relacional diseñado en la fase 1.

### Elección de librería cliente de Kafka

Se usó `kafka-python`, verificando antes de instalarla que su versión actual en PyPI (3.0.8) está probada oficialmente contra brokers Kafka hasta la versión 4.0, evitando así elegir una librería que pudiera fallar por incompatibilidad de protocolo con el broker 4.3.1 ya levantado.

## MinIO como destino S3-compatible

Se eligió MinIO como almacén de objetos para la Speed Layer por ser compatible con la API S3 estándar, lo cual permite usar el conector `hadoop-aws` de Spark sin necesidad de un servicio cloud real. Las credenciales usadas (`minioadmin`/`minioadmin`) son deliberadamente simples por tratarse de un entorno de desarrollo local, no expuesto a internet.

## El consumidor Spark Streaming

### Elección de versión: PySpark 3.5.8, no la más reciente

En el momento de esta fase, la versión estable más reciente de Spark era la 4.2.0, publicada apenas el día anterior. Se descartó deliberadamente por prematura: los conectores de terceros (Kafka, S3A) que dependen de versiones específicas de Spark tardan en publicarse y estabilizarse tras cada release nueva, y un ejercicio con presupuesto de horas limitado no es el momento de asumir ese riesgo. Se optó por PySpark 3.5.8 — el último parche de la serie 3.5.x, la misma familia ya usada en otros ejercicios del curso (`jupyter/pyspark-notebook`, Spark 3.5.0), con conectores de Kafka y S3A ampliamente documentados y probados por la comunidad.

### Formato de persistencia: Parquet

La escritura en MinIO se hizo en formato Parquet, cumpliendo el requisito del enunciado de usar Avro o Parquet en la arquitectura. Parquet se eligió sobre Avro para esta capa concreta porque encaja de forma natural como formato de fichero en un sistema de almacenamiento tipo S3/HDFS, y porque Spark tiene soporte de escritura nativo y ya conocido de ejercicios anteriores del curso.

### Esquema explícito, no inferido

En Structured Streaming, Spark no puede inferir automáticamente el esquema de una fuente que llega de forma continua (a diferencia de un batch estático), así que fue necesario declarar explícitamente un `StructType` con los mismos campos y tipos que ya se habían definido en el modelo relacional de la fase 1 — otra muestra de cómo el diseño inicial de datos se propaga sin fricciones a través de las distintas piezas de la arquitectura.

### Creación automática del bucket

En lugar de crear el bucket de MinIO manualmente desde su consola web, el propio script del consumidor usa `boto3` para comprobar si el bucket existe y crearlo si no — de forma que todo el entorno se levante con `docker compose up` sin pasos manuales intermedios, coherente con el requisito de que el ejercicio se realice íntegramente con Docker Compose.

## Incidencias resueltas durante esta fase

- **Buffering de salida de Python**: los `print()` del productor y del consumidor no aparecían en `docker compose logs` hasta acumular suficiente buffer. Se resolvió añadiendo el flag `-u` (unbuffered) al comando de arranque de Python en ambos `Dockerfile`.
- **Paquete `openjdk-17-jdk-headless` no disponible**: la imagen base `python:3.12-slim` pasó a basarse en Debian trixie, cuyos repositorios ya no incluyen paquetes de OpenJDK 17. Tras comprobar que Spark 3.5.x soporta oficialmente Java 21 (añadido en esa misma versión), se cambió a `openjdk-21-jdk-headless` sin más implicaciones.

## Patrón master/worker

Tras un requisito añadido a mitad de desarrollo — usar el patrón master/worker en toda arquitectura que use Spark del proyecto — se construyó un clúster Spark standalone (1 master + 2 workers), en lugar de dejar que el consumidor corriera embebido en modo local como hasta entonces. Los tres servicios comparten una única imagen base (Java 21 + PySpark 3.5.8 instalado vía pip, que ya incluye los scripts `spark-class` necesarios para levantar master y worker sin descargar la distribución completa de Spark por separado). El único cambio en el código del consumidor fue añadir `.master("spark://spark-master:7077")` a la construcción de la `SparkSession`, redirigiendo la ejecución del job hacia el clúster en vez de ejecutarlo local.

La interfaz web del master se expuso en el puerto **8082** del host (el 8080 por defecto ya lo ocupaba Kafka UI).
