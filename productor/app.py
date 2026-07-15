import json
import time
import requests
from kafka import KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
KAFKA_TOPIC = "lecturas-tiempo"
POLL_INTERVAL_SECONDS = 60

CIUDADES = [
    {"id_ubicacion": 1, "nombre": "Bilbao", "latitud": 43.26300, "longitud": -2.93500},
    {"id_ubicacion": 2, "nombre": "Lugo", "latitud": 43.00992, "longitud": -7.55602},
    {"id_ubicacion": 3, "nombre": "Valencia", "latitud": 39.46975, "longitud": -0.37739},
    {"id_ubicacion": 4, "nombre": "Sevilla", "latitud": 37.38863, "longitud": -5.98317},
    {"id_ubicacion": 5, "nombre": "Palma", "latitud": 39.56951, "longitud": 2.65024},
]

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def construir_parametros():
    latitudes = ",".join(str(c["latitud"]) for c in CIUDADES)
    longitudes = ",".join(str(c["longitud"]) for c in CIUDADES)
    return {
        "latitude": latitudes,
        "longitude": longitudes,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m,weather_code",
    }


def consultar_open_meteo():
    respuesta = requests.get(OPEN_METEO_URL, params=construir_parametros(), timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


def construir_mensajes(datos_api):
    mensajes = []
    for ciudad, resultado in zip(CIUDADES, datos_api):
        actual = resultado["current"]
        mensajes.append({
            "id_ubicacion": ciudad["id_ubicacion"],
            "nombre": ciudad["nombre"],
            "timestamp_lectura": actual["time"],
            "temperatura": actual["temperature_2m"],
            "humedad": actual["relative_humidity_2m"],
            "precipitacion": actual["precipitation"],
            "velocidad_viento": actual["wind_speed_10m"],
            "direccion_viento": actual["wind_direction_10m"],
            "codigo_tiempo": actual["weather_code"],
        })
    return mensajes


def main():
    productor = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    print(f"Productor iniciado. Publicando en topic '{KAFKA_TOPIC}' cada {POLL_INTERVAL_SECONDS}s.")

    while True:
        try:
            datos_api = consultar_open_meteo()
            mensajes = construir_mensajes(datos_api)
            for mensaje in mensajes:
                productor.send(KAFKA_TOPIC, value=mensaje)
                print(f"Enviado: {mensaje['nombre']} - {mensaje['temperatura']}C")
            productor.flush()
        except Exception as error:
            print(f"Error en el ciclo de polling: {error}")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
