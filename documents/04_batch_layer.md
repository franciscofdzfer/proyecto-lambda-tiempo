# Fase 4 — Batch Layer

## Objetivo

Construir el camino de persistencia histórica: Kafka Connect exporta los mismos mensajes que consume la Speed Layer hacia HDFS, y sobre esos datos se construyen tablas Hive consultables por SQL, una en el formato original y otra en Parquet.

## Decisión de arquitectura: todo en Docker Compose, incluido HDFS/Hive

Inicialmente se valoró mantener HDFS y Hive corriendo de forma nativa en la VM del curso (ya que estaban instalados y funcionando de ejercicios anteriores), y levantar solo los componentes nuevos (Kafka, MinIO, Kafka Connect) en Docker. Un requisito posterior del enunciado — que todo el ejercicio se realizara con Docker Compose — obligó a reconsiderar esta decisión: se evaluó el coste de tiempo de reconstruir Hadoop/Hive en contenedores desde cero frente a mantenerlos en la VM, concluyendo que, si el requisito exige Docker Compose de forma explícita, una instalación nativa no lo cumpliría aunque funcionara igual de bien técnicamente. Se optó por migrar todo el proyecto — incluida esta capa — a Docker Compose, ejecutado desde Docker Desktop en Windows en lugar de dentro de la VM, para evitar la sobrecarga de virtualización anidada (Windows → VirtualBox → VM → Docker).

## Elección de versiones: Hadoop 2.7.4 + Hive 2.3.2, no las más recientes

Se descartó deliberadamente usar las versiones de Hadoop más nuevas disponibles como imágenes Docker (por ejemplo, Hadoop 3.2.1 o 3.3.x) en favor de la combinación **Hadoop 2.7.4 + Hive 2.3.2 + PostgreSQL como metastore**, por ser exactamente la combinación de versiones documentada, probada y mantenida como referencia oficial por el proyecto `big-data-europe/docker-hive` — el stack HDFS+Hive en Docker más usado y verificado de la comunidad. Con presupuesto de horas limitado, minimizar el riesgo de incompatibilidades entre Hadoop y Hive pesó más que usar la versión más reciente disponible.

Esta decisión de versión tuvo una consecuencia importante más adelante: al elegir el conector de Kafka Connect para HDFS, se descubrió que el conector **HDFS 3 Sink** de Confluent usa cliente HDFS 3.x y no es compatible con clústeres HDFS 2.x. Se cambió al conector **HDFS 2 Sink** (`confluentinc/kafka-connect-hdfs`, sin el sufijo "3"), coherente con la versión de Hadoop realmente desplegada.

## Solo HDFS, sin YARN

A diferencia de otros ejercicios del curso, esta arquitectura no despliega YARN (ResourceManager, NodeManager, HistoryServer). La razón es que ningún componente de la Batch Layer ejecuta trabajos MapReduce o necesita gestión de recursos distribuidos: Kafka Connect escribe directamente a HDFS vía su propio conector, sin pasar por YARN. Se simplificó el fichero de variables de entorno compartido (`hadoop-hive.env`) eliminando toda la configuración `YARN_CONF_*` de la plantilla de referencia, ya que esas propiedades no tienen efecto sin los servicios YARN correspondientes.

## Kafka Connect: formato sencillo en vez de Avro con Schema Registry

Antes de construir el conector se valoraron dos caminos para cumplir el requisito de usar Avro o Parquet también en esta capa: (a) montar un Schema Registry y serializar los mensajes en Avro desde el propio conector, o (b) escribir JSON plano en HDFS y generar el Parquet en el punto natural de persistencia analítica, dentro de Hive. Se eligió la segunda opción por su menor complejidad — evita añadir un componente nuevo (Schema Registry) y una capa de serialización adicional en el productor — sin renunciar al requisito, que queda cumplido igualmente mediante la tabla Parquet creada en Hive.

Configuración del conector:
- **`hive.integration: false`**: se desactivó la creación automática de tablas Hive por parte del conector, en favor de crearlas manualmente después, con control total sobre su definición.
- **`flush.size: 5`**: cada fichero en HDFS agrupa 5 registros (aproximadamente un ciclo de polling completo del productor, ya que hay 5 ciudades), dando una cadencia de escritura razonable para observar resultados durante una demo de clase sin esperar demasiado.
- **Conversores JSON sin schema** (`JsonConverter` con `schemas.enable: false`): coherente con el formato de mensaje que ya publica el productor de la Speed Layer, sin envoltorio de schema adicional.

### Elección de imagen base: Confluent 7.6.x, no 8.x

Se descartaron las imágenes más recientes de Confluent (serie 8.x) porque, desde la versión 8.1.0, eliminan herramientas como `python`, `git`, `tar` y `wget` de la imagen base para reducir tamaño — herramientas que el instalador `confluent-hub` necesita para descargar y descomprimir plugins de conectores. Se usó la etiqueta `7.6.12`, que conserva el conjunto completo de herramientas.

## Las dos tablas Hive

1. **`lecturas_tiempo_raw`** (tabla externa, formato texto con `JsonSerDe`): apunta directamente a la carpeta HDFS donde Kafka Connect escribe los ficheros JSON. Al ser `EXTERNAL`, Hive no gestiona ni borra los ficheros físicos — coherente con el hecho de que esos datos ya están gestionados por Kafka Connect, no por Hive.
2. **`lecturas_tiempo_parquet`** (tabla gestionada, formato Parquet): creada con `CREATE TABLE ... AS SELECT` a partir de la tabla anterior, en un solo paso que crea la tabla y convierte el formato de texto a columnar. Esta es la tabla que cumple el requisito de Parquet en la Batch Layer, y sigue el mismo patrón conceptual Bronze→Silver visto en la arquitectura Medallion del curso: datos crudos sin transformar, seguidos de una versión depurada y optimizada para análisis.
