# Fase 4 — Batch Layer

## Comprobación de alcance y tiempo antes de empezar

Antes de construir nada de esta fase, se hizo una comprobación explícita de dos cosas: que el plan seguía siendo montar HDFS y Hive en contenedores nuevos, en modo pseudo-distribuido de un solo nodo, tal como se había decidido al migrar el proyecto a Docker Compose; y cuánto tiempo quedaba disponible del presupuesto total de horas del ejercicio, dado que esta era la pieza más compleja de todas las que quedaban por construir, sin apoyo en nada ya hecho previamente. Confirmado que quedaban horas suficientes, se procedió.

## Decisión de no desplegar YARN

A diferencia de otros contextos donde Hadoop se despliega con su gestor de recursos completo, en esta fase se decidió desplegar únicamente los componentes de almacenamiento (HDFS: namenode y datanode), sin YARN (sin ResourceManager, NodeManager ni HistoryServer). La razón fue que ningún componente de la Batch Layer necesitaba ejecutar trabajos de procesamiento distribuido de tipo MapReduce: Kafka Connect escribe directamente en HDFS a través de su propio conector, sin pasar por YARN en ningún momento. Añadir YARN habría sido infraestructura sin ningún consumidor real dentro de esta arquitectura concreta.

## Investigación del stack de referencia y elección de versiones

Antes de elegir qué imágenes de contenedor usar para HDFS y Hive, se investigó cuál era la combinación de versiones más probada y documentada por la comunidad para desplegar ambos juntos, en lugar de elegir cada componente por separado según la versión más reciente disponible de cada uno. Esa investigación llevó a un cambio de planteamiento: la versión de Hadoop que se había valorado inicialmente (una de la serie 3.2) no era la que aparecía verificada y documentada junto con la versión de Hive finalmente elegida (2.3.2) en el proyecto de referencia consultado. Se optó por bajar a una versión de Hadoop anterior (2.7.4), sacrificando modernidad a cambio de una combinación de versiones con compatibilidad realmente comprobada por terceros — una decisión coherente con el criterio de minimizar riesgo dado el presupuesto de horas limitado del ejercicio.

## Construcción del fichero de variables de entorno compartido

Se preparó un fichero de variables de entorno común, reutilizado por los distintos servicios de Hadoop y Hive, basado en la plantilla de referencia del mismo proyecto consultado en el paso anterior. Sobre esa plantilla se tomó una decisión explícita de recorte: se eliminó toda la configuración relativa a YARN, coherente con la decisión ya tomada de no desplegar esos componentes — dejar esas variables sin usar no habría causado ningún error, pero mantenerlas sin ningún servicio real detrás habría sido confuso para cualquiera que revisara la configuración más adelante.

## Construcción de HDFS: namenode y datanode

Se añadieron al proyecto los dos contenedores necesarios para un HDFS de un solo nodo: el namenode (que gestiona los metadatos del sistema de ficheros) y el datanode (que almacena los bloques de datos reales). Para el puerto de la interfaz web del namenode, se decidió mapear el puerto interno real de la imagen elegida (el puerto clásico de Hadoop 2.x para esa interfaz) hacia un puerto distinto en el sistema anfitrión, coincidente con el que se recordaba de memoria de otros contextos del curso para esa misma interfaz — de forma que acceder a ella resultara familiar sin tener que recordar un número de puerto nuevo y distinto solo para este proyecto.

Tras levantar ambos contenedores, se verificó explícitamente que HDFS funcionaba correctamente en dos niveles: primero, revisando los registros de arranque del namenode, donde se buscó y se confirmó el registro exitoso del datanode contra el namenode (aparición del datanode con su identificador de almacenamiento, sin errores de fallo de almacenamiento); y segundo, accediendo por navegador a la interfaz web del namenode, confirmando que mostraba **1 nodo activo** ("Live Node"), con capacidad de almacenamiento disponible y el modo seguro ya desactivado. Solo con esta doble verificación se dio por buena la base de HDFS antes de continuar.

## Cambio en el criterio de verificación explícita durante esta fase

En el punto en que se guardó en el control de versiones el avance de HDFS, se planteó explícitamente que pegar la salida completa de un simple registro de cambios en el control de versiones tenía un coste desproporcionado frente a su utilidad, dado que es un paso de bajo riesgo y fácilmente detectable si falla. Se acordó, en ese momento, dejar de exigir la salida completa específicamente para los registros de cambios (commits), aceptando una confirmación breve en su lugar. Más adelante en esta misma fase, ya con Kafka Connect en construcción, este criterio se amplió de forma más general: dejar de pedir la salida completa de cualquier comando salvo que hubiera fallos evidentes que reportar. Este cambio de criterio, ocurrido a mitad de la fase, es la razón real por la que la segunda mitad de este trabajo (Kafka Connect y las tablas de Hive) cuenta con menos evidencia de verificación literal registrada que la primera mitad (HDFS) — no porque se dejara de verificar, sino porque se dejó de exigir y mostrar la prueba completa de cada verificación menor, mientras que las comprobaciones técnicamente relevantes (estado de servicios, existencia de ficheros, datos reales en las tablas) se siguieron haciendo y confirmando explícitamente.

## Construcción de Hive: los tres servicios y su verificación diferida

Sobre la base de HDFS ya operativa, se añadieron los tres componentes necesarios para Hive: una base de datos de apoyo dedicada al catálogo de metadatos de Hive (el metastore), el propio servicio de metastore de Hive (que expone ese catálogo mediante un protocolo estándar en su puerto habitual, 9083), y el servidor de Hive que acepta consultas de clientes en su puerto habitual (10000, el puerto estándar de ese servicio). Cada uno de estos servicios se configuró para esperar activamente a que sus dependencias reales estuvieran respondiendo en el puerto correcto antes de arrancar él mismo, encadenando namenode, datanode, la base de datos del metastore, y el propio metastore como precondiciones según de qué servicio dependiera cada uno — el mismo tipo de comprobación activa de disponibilidad (no solo de existencia del contenedor) que ya se había aprendido como necesaria en la fase de Kafka, al diagnosticar entonces que una dependencia declarada simple no garantiza que el servicio esté realmente listo.

Las credenciales de acceso entre el metastore de Hive y su base de datos de apoyo se dejaron con los valores sencillos que trae la imagen por defecto, siguiendo el mismo criterio ya aplicado en otras partes del proyecto: al tratarse de un entorno de desarrollo local sin exposición externa, una gestión de credenciales más elaborada no aporta beneficio real y sí complejidad innecesaria.

A diferencia de HDFS, el correcto funcionamiento de Hive no se verificó revisando sus registros de arranque inmediatamente después de levantarlo. Esa verificación quedó diferida hasta el momento en que se usó por primera vez de verdad, más adelante en esta misma fase: la propia conexión exitosa de un cliente de consultas contra Hive sirvió como la prueba real de que el servicio funcionaba, en lugar de comprobarlo de forma aislada antes de tener algo concreto que consultar. Mientras el metastore de Hive tardaba un cierto tiempo en inicializar su esquema dentro de la base de datos de apoyo la primera vez que arrancaba, ese tiempo de espera se aprovechó para empezar a preparar la siguiente pieza de esta fase (Kafka Connect), en lugar de esperar sin avanzar en nada.

## Diseño de Kafka Connect: formato sencillo en lugar de Avro con Schema Registry

Antes de construir el conector que exportaría los mensajes de Kafka hacia HDFS, se valoraron dos caminos posibles para cumplir también en esta capa el requisito general del enunciado de usar Avro o Parquet: montar un registro de esquemas y serializar los mensajes en Avro directamente desde el conector, o escribir los mensajes tal cual (en formato JSON simple) en HDFS, y resolver el requisito de Parquet más adelante, en el punto de persistencia analítica final dentro de Hive. Se eligió la segunda opción por su menor complejidad — evita añadir un componente nuevo (el registro de esquemas) y una capa de serialización adicional en el productor de datos — sin renunciar al cumplimiento del requisito, que quedaría satisfecho igualmente mediante una tabla Parquet creada más adelante en Hive.

## Incompatibilidad de conector: dos motivos independientes para descartar la opción más habitual

Al buscar qué conector de sincronización usar para exportar de Kafka a HDFS, se investigó primero la opción más reciente y habitual para este propósito, encontrando dos motivos independientes que la descartaban para este proyecto concreto, no solo uno:

1. Esa versión más reciente del conector usa un cliente de HDFS de la serie 3.x, que no es compatible con un clúster HDFS de la serie 2.x como el que se había construido en este proyecto.
2. La misma documentación de esa versión advertía, además, de una exigencia de versión mínima del metastore de Hive (una serie 4.x) muy por encima de la versión de Hive realmente desplegada en este proyecto (2.3.2).

Ambos motivos apuntaban en la misma dirección de forma independiente, así que se optó por una versión anterior y menos habitual de ese mismo conector, pensada específicamente para clústeres HDFS de la serie 2.x, coherente con la versión de Hadoop realmente desplegada.

## Elección de la imagen base para Kafka Connect

Para construir la imagen de Kafka Connect con el conector instalado, se descartó deliberadamente la serie más reciente de imágenes del fabricante de referencia, porque esas versiones recientes eliminan de la imagen base herramientas (como las necesarias para descomprimir y gestionar paquetes) que el instalador del conector necesita para funcionar. Se usó en su lugar una imagen de una serie anterior, que sí conserva ese conjunto completo de herramientas.

## Configuración interna del conector

Dentro de la configuración del propio servicio de Kafka Connect y del conector registrado sobre él, se tomaron varias decisiones concretas:

- **Factor de replicación fijado explícitamente a 1** para los topics internos que Kafka Connect usa para su propio funcionamiento (almacenamiento de su configuración, de los desplazamientos de lectura, y de su estado). Sin esta indicación explícita, Kafka Connect intenta crear esos topics internos con un factor de replicación por defecto de 3, lo cual habría fallado directamente porque el clúster de Kafka de este proyecto solo cuenta con un único broker.
- **Desactivación del uso de esquemas en el conversor de formato JSON** empleado por Kafka Connect, haciendo coincidir esta configuración con la forma en que el productor de datos ya envía sus mensajes (JSON simple, sin ningún envoltorio de metadatos de esquema). Esta coincidencia era necesaria para evitar un error conocido de mezclar, dentro del mismo flujo, mensajes que sí llevan metadatos de esquema con mensajes que no los llevan.
- **Rutas de destino en HDFS organizadas de forma descriptiva**, en una carpeta propia dedicada en lugar de dejar los datos en una ubicación genérica o por defecto — mismo criterio ya aplicado antes al nombrar el contenedor lógico del almacén de objetos de la Speed Layer, de forma que la procedencia de los datos resultara identificable con solo mirar la ruta.
- **Tamaño de lote para el volcado a fichero fijado en 5 registros**, coincidiendo deliberadamente con el número de ciudades monitorizadas, de forma que cada fichero nuevo escrito en HDFS representara aproximadamente un ciclo completo de sondeo del productor — dando una cadencia de aparición de resultados razonable para poder observarlos durante una sesión de trabajo, sin que se acumularan demasiados registros antes de ver el primer fichero.
- **Integración automática con Hive desactivada** en la configuración del propio conector, dejando la creación de las tablas de Hive como un paso manual y controlado posterior, en lugar de delegarla en el conector.

## Registro del conector y verificación en dos niveles

Una vez levantado el servicio de Kafka Connect, se registró el conector enviando su configuración a la interfaz de programación del propio servicio. Tras el registro, se verificó su estado en dos niveles distintos, no solo uno: primero el estado general del conector, y por separado el estado de su tarea concreta de ejecución — porque el conector en su conjunto puede aparecer en buen estado mientras su tarea real, la que efectivamente mueve los datos, ha fallado por dentro sin que eso se refleje en el estado general. Solo al confirmar ambos niveles en estado correcto se dio por buena esta pieza.

## Verificación progresiva en HDFS

Para comprobar que el conector realmente estaba escribiendo datos, se navegó de forma progresiva por la interfaz web de HDFS: primero comprobando la existencia de la carpeta general de destino, después entrando en la subcarpeta correspondiente a la partición concreta del topic de Kafka (al haber una sola partición configurada, y por tanto una sola tarea del conector, toda la información quedaba concentrada en esa única subcarpeta), y finalmente confirmando la presencia de ficheros con nombres que codificaban los desplazamientos de lectura correspondientes, con tamaños y fechas de modificación coherentes con el tiempo transcurrido.

## Creación de las dos tablas de Hive

Con los datos ya confirmados en HDFS, se crearon dos tablas dentro de Hive, cada una con su propio razonamiento:

1. **Una tabla externa**, apuntando directamente a la misma subcarpeta de partición donde escribe el conector, interpretando cada línea de los ficheros como un objeto JSON mediante un intérprete de datos específico para ese formato. Se eligió que fuera externa (y no una tabla gestionada por Hive) porque los ficheros físicos ya están gestionados por Kafka Connect, no por Hive — al ser externa, Hive no intenta gestionar ni borrar esos ficheros si la tabla se elimina algún día.
2. **Una segunda tabla, en formato Parquet**, creada a partir de la primera mediante una única sentencia que crea la tabla y la puebla con los datos convertidos de formato en el mismo paso. Esta segunda tabla, a diferencia de la primera, sí queda completamente gestionada por Hive, y es la que cumple de forma concreta el requisito del enunciado de usar Parquet, aplicado aquí en el punto de persistencia analítica final de la Batch Layer — el mismo patrón conceptual de datos crudos seguidos de una versión depurada que ya aparecía en otras arquitecturas planteadas al inicio del proyecto.

## Verificación de trazabilidad de datos de extremo a extremo

Al consultar por primera vez los datos dentro de la tabla externa recién creada, las lecturas devueltas coincidían exactamente —misma ciudad, misma temperatura, mismo instante— con las primerísimas lecturas que había generado el productor de datos al principio de la fase de Speed Layer, muchas horas antes. Esta coincidencia sirvió como una confirmación tangible, no solo teórica, de que un mismo dato había recorrido correctamente toda la cadena completa de la arquitectura (productor, Kafka, Kafka Connect, HDFS, y finalmente Hive) sin corromperse ni perderse en ningún punto intermedio del camino.

## Verificación final antes de cerrar la fase

Antes de dar esta fase por completa, se hizo una comprobación explícita de sí/no sobre si la segunda tabla, la de formato Parquet, devolvía realmente datos al consultarla — no se asumió que la sentencia de creación hubiera funcionado correctamente solo porque no había arrojado ningún error visible. Confirmada esa comprobación, se dio la Batch Layer por completa: datos meteorológicos fluyendo de extremo a extremo desde la API de origen hasta dos tablas consultables por SQL, una con los datos en su forma original y otra ya en formato columnar Parquet.
