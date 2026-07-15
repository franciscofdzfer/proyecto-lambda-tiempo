# Fase 2 — Kafka y Conexión

## Objetivo

Levantar el clúster Kafka que actúa como columna vertebral de la arquitectura Lambda: todo mensaje meteorológico pasa por aquí antes de dividirse hacia la Speed Layer y la Batch Layer.

## Elección de versión: Kafka 4.3.1 en modo KRaft

Se eligió la versión estable más reciente de Apache Kafka (4.3.1) en lugar de una versión anterior, por dos motivos:

1. **Sin ZooKeeper**: la serie 4.x de Kafka eliminó por completo la dependencia de ZooKeeper, sustituyéndola por el protocolo KRaft integrado en el propio broker. Esto simplifica la arquitectura — un componente menos que instalar, configurar y mantener sincronizado — frente a versiones anteriores que hubieran obligado a levantar también un contenedor de ZooKeeper.
2. **Imagen oficial con Java empaquetado**: al usar la imagen `apache/kafka:4.3.1`, el propio contenedor trae su runtime Java, evitando la gestión manual de versiones de Java que sí fue necesaria en un primer intento de instalación nativa en la VM (ver nota más abajo).

## Nota sobre el intento inicial en la VM

Antes de decidir migrar todo el proyecto a Docker Compose, se instaló Kafka de forma nativa en la VM `UbuntuServerHadoop`. Este intento reveló una incompatibilidad real: Kafka 4.x requiere Java 17 o superior para el broker, mientras que la VM tenía Java 11 como versión por defecto (usada por Hadoop/Hive/Spark). La solución adoptada en ese momento fue instalar Java 17 en paralelo sin alterar el Java por defecto del sistema, usando `JAVA_HOME` específico solo para el proceso de Kafka. Este trabajo quedó descartado al migrar a Docker Compose, pero el aprendizaje sobre la incompatibilidad de versión Java/Kafka se mantiene relevante como antecedente de otras decisiones de versión tomadas más adelante en el proyecto (por ejemplo, Java 21 en los contenedores de Spark).

## Configuración de listeners: interno vs externo

Uno de los primeros problemas reales al levantar Kafka en Docker fue un fallo de conexión de Kafka UI: el broker anunciaba su dirección como `localhost:9092`, que desde dentro de otro contenedor (Kafka UI) apunta al propio contenedor de Kafka UI, no al broker. La solución fue declarar dos listeners separados:

- **`PLAINTEXT` (puerto interno 9092)**: anunciado como `kafka:9092`, usado por otros contenedores de la misma red Docker (Kafka UI, el productor, Spark Streaming, Kafka Connect).
- **`PLAINTEXT_HOST` (puerto 29092)**: anunciado como `localhost:29092`, para conexiones futuras desde herramientas ejecutadas directamente en Windows, fuera de Docker.

Esta separación es el patrón estándar para evitar el error de "advertised listener" al mezclar clientes internos (otros contenedores) y externos (el host) contra el mismo broker.

## Kafka UI: elección de Kafbat en vez de Provectus

Para monitorizar el clúster se añadió una interfaz web. Se descartó `provectuslabs/kafka-ui` (la opción históricamente más conocida) en favor de `ghcr.io/kafbat/kafka-ui`, el fork de la comunidad que continúa el desarrollo activo del proyecto original tras la ralentización de las actualizaciones de Provectus. Kafbat UI ofrece el mismo conjunto de funcionalidades (visualización de topics, mensajes, particiones, brokers) bajo mantenimiento más reciente.

## Puertos elegidos

Kafka UI quedó expuesta en el puerto **8080** del host, y el broker en **29092** (el listener externo). Esta elección de puertos se revisó más adelante al incorporar el clúster Spark, cuya interfaz web por defecto también usa el 8080 — en ese momento se remapeó Spark Master a 8082 para evitar el conflicto, dejando 8080 reservado para Kafka UI por haber sido el primer servicio en tomarlo.
