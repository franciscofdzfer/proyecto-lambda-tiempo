# Fase 1 — Modelo Relacional

## Objetivo

Diseñar el esquema de datos que representa una lectura meteorológica antes de construir cualquier pieza de infraestructura. Este modelo actúa como el contrato de datos que después se traduce en: la estructura de los mensajes Kafka, las columnas de las tablas Hive, y el esquema declarado en el consumidor Spark Streaming.

## Fuente de datos: Open-Meteo

Se eligió Open-Meteo como API de origen por ser gratuita, sin necesidad de API key, y con límites de uso (10.000 llamadas/día, 600/minuto) muy por encima de las necesidades de un ejercicio de varias horas de clase. Además, permite consultar varias ubicaciones en una sola llamada HTTP (coordenadas separadas por comas), lo cual simplifica el diseño del productor: una única petición trae los datos de las cinco ciudades a la vez, en vez de cinco peticiones independientes.

## Ciudades seleccionadas

Bilbao, Lugo, Valencia, Sevilla y Palma. La elección busca variedad climática real (costa cantábrica húmeda, interior gallego, mediterráneo, interior-sur cálido, insular) para que los agregados de la Batch Layer tengan contraste analítico real entre ciudades, en lugar de datos casi idénticos que no aportarían valor a la hora de comparar comportamientos climáticos.

## Diseño de las dos entidades

- **`ubicaciones`**: tabla de dimensión con el nombre y coordenadas de cada ciudad. Separarla de las lecturas evita repetir latitud/longitud en cada mensaje y sirve como fuente de parámetros para las llamadas a la API — el productor lee esta tabla conceptual (materializada como una lista de constantes) para saber qué coordenadas consultar en cada ciclo de polling.
- **`lecturas_tiempo`**: tabla de hechos, una fila por lectura puntual de una ciudad. Contiene temperatura, humedad, precipitación, velocidad y dirección del viento, y el código de tiempo (`weathercode`) de Open-Meteo sin traducir, para no perder información original que se pudiera necesitar decodificar más adelante en la capa de presentación.

Esta normalización en dos tablas es el patrón estándar para separar información que cambia poco (ubicaciones) de información que crece constantemente (lecturas) — la misma lógica que después se refleja en cómo se estructura cada mensaje Kafka (una lectura, con su ubicación embebida como campos `id_ubicacion` y `nombre`).

## Motor de referencia: PostgreSQL

Se diseñó el modelo pensando en PostgreSQL como motor relacional de referencia, coherente con el motor ya usado en el proyecto cripto del curso. Este diseño relacional funcionó como el plano de datos: las columnas de `lecturas_tiempo` son exactamente las que después aparecen en los mensajes JSON de Kafka, en el esquema declarado en PySpark (`StructType`), y en las columnas de las tablas Hive de la Batch Layer — de modo que el mismo contrato de datos atraviesa toda la arquitectura sin traducciones intermedias entre capas.

## Nota sobre la implementación final

Durante el desarrollo se instaló PostgreSQL de forma nativa en la VM para validar este modelo (tablas creadas, usuario propietario corregido, datos de las cinco ciudades insertados y verificados con éxito). Al decidir migrar todo el proyecto a Docker Compose en Windows — requisito posterior del enunciado — esa instalación nativa se retiró para evitar mezclar entornos y mantener el proyecto autocontenido en un único `docker-compose.yml`. El modelo relacional diseñado en esta fase siguió cumpliendo su función principal como especificación del esquema de datos, que se materializó directamente en Kafka y Hive en las fases siguientes, sin necesidad de una base de datos relacional corriendo en la arquitectura final.
