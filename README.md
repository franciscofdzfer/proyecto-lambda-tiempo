# Proyecto Lambda Tiempo

Arquitectura Lambda (Speed Layer + Batch Layer) para ingesta y analisis de datos meteorologicos en tiempo real, usando la API publica de Open-Meteo, orquestada completamente con Docker Compose.

## Arquitectura

API Open-Meteo -> Kafka
  - Speed Layer -> Spark Streaming -> MinIO
  - Batch Layer -> Kafka Connect -> HDFS -> Hive

## Ciudades monitorizadas

Bilbao, Lugo, Valencia, Sevilla, Palma - elegidas por su variedad climatica (costa cantabrica, interior gallego, mediterraneo, interior-sur, insular).

## Estructura del repositorio

proyecto-lambda-tiempo/
- documents/       Documentacion de cada fase (modelo relacional, Kafka, Speed Layer, Batch Layer, visualizacion)
- README.md
- docker-compose.yml

## Estado del proyecto

En desarrollo. Ver documents/ para el detalle de cada fase.
