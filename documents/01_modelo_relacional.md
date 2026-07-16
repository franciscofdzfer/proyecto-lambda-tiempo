# Fase 1 — Modelo Relacional y Puesta en Marcha del Proyecto

## Creación de la estructura de carpetas del proyecto

El primer paso práctico fue crear la carpeta del proyecto con una subcarpeta `documents` dentro, destinada a alojar toda la documentación que se escribiría al final. Esta creación de carpetas se intentó primero en una ubicación por defecto del sistema, pero se corrigió de inmediato para colocar el proyecto dentro de la estructura de carpetas específica ya usada para el resto de material del curso, de forma que todo el trabajo quedara organizado bajo el mismo árbol de directorios en lugar de disperso por el sistema.

## Decisión sobre cómo organizar la documentación

Se decidió explícitamente que la documentación del proyecto se estructuraría como un documento independiente por cada fase, alojado en la carpeta `documents/`, en lugar de un único documento monolítico — permitiendo centrarse en el razonamiento de cada parte de la arquitectura por separado. También se decidió, en ese mismo momento, posponer la redacción de toda esta documentación hasta el final del proyecto, una vez completada la parte técnica, para evitar tener que reescribir contenido ya redactado si alguna decisión técnica cambiaba sobre la marcha — algo que, de hecho, ocurrió más de una vez a lo largo del proyecto.

## Inicialización del repositorio Git

Dentro de la carpeta del proyecto se intentó inicializar un repositorio Git nuevo, vacío. En este punto surgió el primer obstáculo real del proyecto: el comando de Git no fue reconocido por la terminal, indicando que no estaba instalado o no era accesible desde el `PATH` del sistema en esa máquina.

Antes de asumir que había que instalarlo desde cero, se hizo una comprobación adicional para descartar que estuviera instalado pero simplemente no localizable desde esa sesión. Esa comprobación devolvió un resultado confuso: los mensajes de error mostrados no se correspondían con el formato habitual de PowerShell, sino con un formato más propio de una terminal de tipo Unix. Esto generó una duda legítima sobre si, sin darse cuenta, se había cambiado de terminal en algún punto. Para resolver la duda de forma inequívoca, se consultó la variable de versión propia de PowerShell, cuya respuesta confirmó sin ambigüedad que se seguía trabajando dentro de una sesión de PowerShell — el mensaje de error anómalo se atribuyó a una particularidad puntual sin mayor trascendencia, y se continuó.

Confirmada la ausencia real de Git, se instaló usando el gestor de paquetes integrado del sistema. Tras completar la instalación fue necesario cerrar la ventana de terminal existente y abrir una nueva, ya que una sesión ya abierta no recarga automáticamente los cambios de `PATH` aplicados por una instalación reciente. Con la nueva sesión, se verificó que el comando de Git ya respondía correctamente. A partir de ahí se completó la inicialización del repositorio: se creó vacío, se configuró el nombre de usuario y correo asociados a los commits de forma local a este repositorio (no de forma global en el sistema), y se verificó el estado del repositorio, confirmando que quedaba vacío y en la rama por defecto, sin ningún commit todavía.

Antes de crear más contenido, se intentó crear de nuevo la carpeta `documents` como paso explícito, comprobándose en ese momento que ya existía —había quedado creada en el primer paso de esta misma fase, junto con la carpeta del proyecto— y se verificó el contenido de la carpeta del proyecto en ese punto para confirmar que el punto de partida estaba limpio antes de seguir añadiendo ficheros.

## Creación del README y las dificultades reales de ese proceso

El primer fichero de contenido real del proyecto fue un `README.md` en la raíz del repositorio, con una descripción general de la arquitectura, las ciudades monitorizadas y la estructura de carpetas del proyecto. Este paso, en apariencia trivial, requirió varios intentos antes de completarse con éxito.

En un primer intento, el contenido se entregó troceado en varios bloques separados en lugar de en uno solo, lo que generó una queja explícita: se pidió recibir el contenido en un único bloque completo, pensado para poder copiarlo y pegarlo de una sola vez sin tener que ir ensamblando fragmentos manualmente. En un segundo intento, ya con el contenido unificado en un solo bloque, el resultado seguía sin ser fiable al pegarlo. La causa concreta se relacionó con cómo estaba compuesto el propio contenido a pegar —en particular, la presencia de bloques de código anidados dentro del propio texto del README (usados para mostrar visualmente un diagrama de la arquitectura y el árbol de carpetas), que podían confundir el mecanismo de pegado en la terminal. Ajustando el contenido para retirar esa anidación de bloques, el resultado final se pegó de forma limpia y se verificó leyendo el fichero de vuelta, confirmando que el contenido había quedado exactamente como se pretendía.

Este episodio con el README no fue un simple detalle anecdótico: dejó establecido, para el resto del proyecto, el criterio de entregar cualquier contenido extenso destinado a pegarse en la terminal como un único bloque completo y sin elementos internos que pudieran interferir con el mecanismo de pegado, en lugar de trocearlo en pasos sucesivos.

## Requisito de usar Avro o Parquet

El enunciado del ejercicio exigía el uso de Apache Avro o Apache Parquet en algún punto de la arquitectura, sin limitar ese requisito a una capa concreta. Esto se tuvo presente desde el diseño de datos: los dos destinos finales de persistencia previstos (un almacén de objetos tipo S3 para la Speed Layer, y HDFS para la Batch Layer) son almacenes de ficheros donde Parquet encaja de forma natural, así que se planteó desde el principio que el formato de persistencia final en ambas capas fuera Parquet, quedando resuelto el requisito sin necesidad de introducir Avro ni un Schema Registry adicional.

## Decisión de entorno de ejecución: Docker Compose en Windows

Se decidió ejecutar todo el proyecto mediante Docker Compose, en un entorno de escritorio Windows con Docker instalado de forma nativa, como un proyecto nuevo e independiente de cualquier otro entorno de contenedores usado anteriormente en el curso. Esta decisión respondía tanto al requisito explícito del enunciado de realizar el ejercicio con Docker Compose, como a la ventaja práctica de evitar cualquier capa adicional de virtualización: los contenedores se ejecutan directamente sobre el sistema anfitrión, sin intermediarios, con acceso directo a los recursos de memoria y procesador de la máquina y sin necesidad de gestionar reglas de reenvío de puertos de ningún tipo de virtualización adicional.

El resultado fue un proyecto completamente autocontenido en un único fichero de definición de servicios de Docker Compose, sin ninguna dependencia de infraestructura instalada previamente por fuera de ese fichero.

## Decisión de no subir el proyecto a un repositorio remoto todavía

En este punto del proyecto se decidió explícitamente mantener el trabajo únicamente en el historial local de Git, sin subirlo todavía a ningún repositorio remoto en GitHub. La razón fue centrarse primero en avanzar con la parte técnica del proyecto, dejando la publicación remota (con la creación del repositorio correspondiente) para un momento posterior, cuando ya hubiera avances sólidos que mereciera la pena subir de una vez.

## Elección de la fuente de datos: por qué Open-Meteo

El proyecto necesitaba una fuente de datos real y viva para justificar el uso de una arquitectura de streaming. Se eligió **Open-Meteo** como API meteorológica de origen, comprobando de antemano tres características concretas antes de decidir:

- **No requiere clave de acceso (API key) ni registro previo**: evita añadir gestión de credenciales o secretos al proyecto.
- **Límite de uso gratuito generoso**: hasta 10.000 llamadas al día, 5.000 por hora y 600 por minuto, según su documentación oficial de condiciones de uso — este dato se verificó explícitamente antes de diseñar la frecuencia de sondeo del productor de datos, para no comprometerse a un diseño que pudiera chocar con el límite del servicio.
- **Soporte de múltiples ubicaciones en una sola llamada**: la API permite pasar listas de coordenadas de latitud y longitud separadas por comas en una única petición HTTP, en lugar de exigir una llamada independiente por cada punto geográfico consultado.

Esta última característica influyó directamente en el diseño posterior del productor de datos, decisión que se detalla con su razonamiento completo en el documento de la Speed Layer.

## Elección de las cinco ciudades a monitorizar

Las ciudades elegidas para monitorizar —**Bilbao, Lugo, Valencia, Sevilla y Palma**— no se seleccionaron de forma arbitraria. El criterio explícito fue buscar variedad climática real dentro de España: costa cantábrica húmeda (Bilbao), interior gallego (Lugo), clima mediterráneo (Valencia), interior-sur cálido (Sevilla), y clima insular (Palma). El motivo de este criterio es que, más adelante, la capa de procesamiento por lotes (Batch Layer) calcularía agregados y comparativas entre ciudades — y esos agregados solo tienen valor analítico real si existe contraste genuino entre los datos de cada ciudad. Cinco ciudades con climas muy similares entre sí habrían producido comparativas prácticamente planas, sin nada interesante que mostrar ni analizar.

## Diseño del modelo de datos: dos entidades relacionadas, no una sola

El modelo se diseñó como dos tablas relacionadas entre sí, siguiendo un patrón estándar de normalización en el que se separa la información que cambia poco de la información que crece de forma continua:

- **`ubicaciones`**: una tabla de dimensión, con una fila fija por cada una de las cinco ciudades, conteniendo su nombre y sus coordenadas geográficas (latitud y longitud). Esta tabla cumple dos funciones: evita repetir las mismas coordenadas una y otra vez en cada dato capturado, y actúa como la fuente única de los parámetros que el productor de datos necesita para construir cada llamada a la API de Open-Meteo.
- **`lecturas_tiempo`**: la tabla de hechos, donde cada fila representa una lectura meteorológica puntual de una ciudad concreta en un instante concreto: temperatura, humedad relativa, precipitación, velocidad del viento, dirección del viento, y el código de condición meteorológica que devuelve la API. A diferencia de la anterior, esta tabla está pensada para crecer de forma indefinida, con una nueva fila por cada ciclo de sondeo y por cada ciudad.

Dentro del diseño de columnas de `lecturas_tiempo` se tomaron dos decisiones concretas que merece la pena explicar con su razonamiento:

1. **El código de condición meteorológica se guarda tal cual lo devuelve la API, sin traducir** a una etiqueta legible como "despejado" o "lluvia moderada". La razón es no tomar una decisión irreversible en el punto de captura de los datos: guardar el código numérico original permite decodificarlo más adelante, en cualquier capa de presentación que lo necesite, sin haber perdido la información original en el camino.
2. **Se usan tipos numéricos decimales de precisión fija en lugar de tipos de coma flotante** para todas las magnitudes capturadas (temperatura, humedad, viento, etc.). El motivo es evitar la acumulación de pequeños errores de redondeo que los tipos de coma flotante pueden introducir, algo especialmente relevante teniendo en cuenta que, en la capa de procesamiento por lotes, estos valores se usarían para calcular medias y otros agregados sobre un volumen creciente de datos.

## Decisión de incorporar una capa de visualización al plan del proyecto

Durante esta fase de diseño se planteó explícitamente cómo se mostrarían finalmente los resultados del proyecto una vez construida toda la arquitectura, más allá de los datos quedando almacenados sin más. Aunque el diagrama de referencia de esta arquitectura no incluía ningún componente de visualización explícito, se decidió incorporar una fase adicional al plan dedicada a mostrar los resultados de forma visual, considerando que sin ella no habría manera sencilla de demostrar que las distintas partes de la arquitectura contenían datos coherentes entre sí. Esta fase se construiría más adelante, pero la decisión de incluirla en el alcance del proyecto se tomó en este momento, junto con el resto de decisiones de diseño.

## Este modelo como contrato de datos para el resto del proyecto

El resultado de esta fase no fue solo un diagrama o una definición de tablas: fue la referencia exacta de campos y tipos que se reutilizó, sin cambios ni reinterpretaciones, en tres puntos distintos y posteriores de la arquitectura. Cada mensaje publicado en el topic de Kafka contiene exactamente estos campos. El esquema que el consumidor de Spark Streaming declara de forma explícita para interpretar esos mensajes usa los mismos nombres y tipos. Y las columnas de las tablas creadas en Hive, en la capa de procesamiento por lotes, replican también esta misma estructura. Haber invertido tiempo en pensar bien este modelo desde el principio, y en dejar bien resuelto el propio entorno de trabajo (repositorio, Git, forma de crear ficheros sin corrupción de contenido), evitó tener que rehacer trabajo ya avanzado en cada fase posterior del proyecto.
