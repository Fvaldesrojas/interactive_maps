import redis
import json
import os
import redis
from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, Union

# Obtener variables de entorno para Redis
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))

# Crea la conexión con la base de datos Redis
r = redis.Redis(
    host=redis_host,
    port=redis_port,
    db=0
)

# Ruta del archivo JSON con los IDs
hexagonos_id5 = 'placa_5.json'
hexagonos_id6 = 'placa_6.json'
hexagonos_id7 = 'placa_7.json'
hexagonos_id8 = 'placa_8.json'
hexagonos_id9 = 'placa_9.json'
hexagonos_id10 = 'placa_10.json'
# Leer el archivo JSON placa 5 
with open(hexagonos_id5, 'r') as file:
    ids_hexagonos5 = set(str(id_) for id_ in json.load(file))  # Convertir IDs a un set para búsquedas rápidas

#leer el archivo json placa 6
with open(hexagonos_id6, 'r') as file:
    ids_hexagonos6 = set(str(id_) for id_ in json.load(file))

#leer el archivo json placa 7
with open(hexagonos_id7, 'r') as file:
    ids_hexagonos7 = set(str(id_) for id_ in json.load(file))

#leer el archivo json placa 8
with open(hexagonos_id8, 'r') as file:
    ids_hexagonos8 = set(str(id_) for id_ in json.load(file))

#leer el archivo json placa 9
with open(hexagonos_id9, 'r') as file:
    ids_hexagonos9 = set(str(id_) for id_ in json.load(file))

#leer el archivo json placa 10
with open(hexagonos_id10, 'r') as file:
    ids_hexagonos10 = set(str(id_) for id_ in json.load(file))

def geometria_a_tupla(geometry):
    # Convierte la geometría GeoJSON a una tupla inmutable para su uso en diccionarios.
    def lista_a_tupla(lst):
        # Convierte una lista en tupla recursivamente.
        return tuple(lista_a_tupla(x) if isinstance(x, list) else x for x in lst)
    
    return lista_a_tupla(geometry['coordinates'])

def extraer_geometrias_y_ids(geojson_data, ids_hexagonos):
    # Extrae las geometrías de los IDs de un GeoJSON para los IDs dados.
    return {
        geometria_a_tupla(feature['geometry']): feature['id']
        for feature in geojson_data['features'] if feature['id'] in ids_hexagonos
    }

def extraer_path_lengths(geojson_data):
    # Extrae los path_lengths de un GeoJSON por geometría, convirtiéndolas a tuplas.
    return {
        geometria_a_tupla(feature['geometry']): feature['properties']['path_length']
        for feature in geojson_data['features']
    }

def actualizar_path_length(valor_temporal, path_lengths_futuro, geometrias_ids_futuro):
    # Actualiza la propiedad path_length en valor_temporal usando los valores de valor_futuro para las geometrias comunes.
    # Crear un diccionario para mapear geometrías a path_length de valor_futuro
    geom_to_path_length = {geom: path_lengths_futuro[geom] for geom in geometrias_ids_futuro.keys() if geom in path_lengths_futuro}
    


    for feature in valor_temporal['features']:
        geom_actual = geometria_a_tupla(feature['geometry'])
        if geom_actual in geom_to_path_length:
            # Actualizar path_length
            feature['properties']['path_length'] = geom_to_path_length[geom_actual]



# Variables globales
combined_data = set()
datos_t = set()
pathsf = set()
pathsa = set()

# Añade banderas de bloqueo
esp1_received = False
esp2_received = False

# Define el modelo para el JSON que se recibira de los distintos esp32(M5stack)
class Esp1(BaseModel):
    canal_0: Optional[Union[str, int]] = None
    canal_1: Optional[Union[str, int]] = None
    canal_2: Optional[Union[str, int]] = None
    canal_3: Optional[Union[str, int]] = None
    canal_4: Optional[Union[str, int]] = None
    canal_5: Optional[Union[str, int]] = None

class Esp2(BaseModel):
    canal_6: Optional[Union[str, int]] = None
    canal_7: Optional[Union[str, int]] = None
    canal_8: Optional[Union[str, int]] = None
    canal_9: Optional[Union[str, int]] = None
    canal_10: Optional[Union[str, int]] = None
    canal_11: Optional[Union[str, int]] = None

# Almacenar los datos temporalmente
temporary_data = {
    "esp1": None,
    "esp2": None
}

def determine_data_type(data: dict) -> Union[None, type]:
    # Funcion para determinar si el dato viene del esp1 o del esp2 
    if "canal_0" in data:
        return Esp1
    elif "canal_6" in data:
        return Esp2
    return None

app = FastAPI()
# Carga los archivos de javascript y css dentro de la API
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inicializa dos variables para almacenar las conexiones de los websocket 
websocket_connections = set()
conn_websocket_connections = set()

# CREA UNA CONEXION WEBSOCKET
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Aceptar la conexión WebSocket
    await websocket.accept()
    
    # Agregar la conexión WebSocket a la lista general
    websocket_connections.add(websocket)

    try:
        # Bucle para manejar mensajes entrantes
        while True:
            # Leer mensaje del cliente
            data = await websocket.receive_json()
            # Enviar mensaje a todos los clientes conectados
            for connection in conn_websocket_connections:
                await connection.send_json(data)
    finally:
        # Eliminar la conexión WebSocket cuando se cierra
        websocket_connections.remove(websocket)

# Endpoint que retorna el archivo HTML de Mapbox.
@app.get("/")
async def get_index():
    return FileResponse("index.html")

# Endpoint que carga los datos del mapa que se quiere proyectar
@app.get("/categoria/{categoria}")
async def obtener_datos(categoria: str):
    global datos_t, pathsf, pathsa, geometrias_ids_futuro5,geometrias_ids_futuro6,geometrias_ids_futuro7,geometrias_ids_futuro8,geometrias_ids_futuro9,geometrias_ids_futuro10

    # Recuperar datos GeoJSON desde Redis
    datos_actual = r.get(f"mapa:{categoria}:1")
    datos_futuro = r.get(f"mapa:{categoria}:0")
    datos_temporal = r.get(f"mapa:{categoria}:1")

    # Verificar si la categoría existe en la base de datos
    if datos_actual is None or datos_futuro is None or datos_temporal is None:
        raise HTTPException(status_code=404, detail=f"La categoría '{categoria}' no se encuentra en la base de datos.")

    # Convertir los datos diccionarios
    datos_a = json.loads(datos_actual)
    datos_f = json.loads(datos_futuro)
    datos_t = json.loads(datos_temporal)

    # Extraer las propiedades de path lengths de los geojson tanto actual como futuro
    pathsf = extraer_path_lengths(datos_f)
    pathsa = extraer_path_lengths(datos_a)
    geometrias_ids_futuro5 = extraer_geometrias_y_ids(datos_f, ids_hexagonos5)
    # Extraer geometrías y path_lengths de ambos GeoJSONs(placa 6)
    geometrias_ids_futuro6 = extraer_geometrias_y_ids(datos_f, ids_hexagonos6)
    # Extraer geometrías y path_lengths de ambos GeoJSONs(placa 7)
    geometrias_ids_futuro7 = extraer_geometrias_y_ids(datos_f, ids_hexagonos7)

    geometrias_ids_futuro8 = extraer_geometrias_y_ids(datos_f, ids_hexagonos8)
    # Extraer geometrías y path_lengths de ambos GeoJSONs(placa 7)
    geometrias_ids_futuro9 = extraer_geometrias_y_ids(datos_f, ids_hexagonos9)

    geometrias_ids_futuro10 = extraer_geometrias_y_ids(datos_f, ids_hexagonos10)
    
    
    
    

    return {"mensaje": f"La categoría '{categoria}' fue seleccionada correctamente"}

async def envio_mapa_func():
    global datos_t, pathsf, pathsa, conn_websocket_connections, combined_data
    global geometrias_ids_futuro5, geometrias_ids_futuro6, geometrias_ids_futuro7
    global geometrias_ids_futuro8, geometrias_ids_futuro9, geometrias_ids_futuro10

    # Copia la conexión WebSocket a la variable conn
    conn_websocket_connections = websocket_connections.copy()

    # Geometrías IDs (ejemplo)
    geometrias_ids = [
        geometrias_ids_futuro5,
        geometrias_ids_futuro6,
        geometrias_ids_futuro7,
        geometrias_ids_futuro8,
        geometrias_ids_futuro9,
        geometrias_ids_futuro10
    ]

    # Recorre los canales del 0 al 5, y los compara si son un 0 o un 1, con 0 siendo el estado actual y 1 el futuro
    for i in range(6):
        canal = f'canal_{i}'
        if combined_data[canal] == '0':
            actualizar_path_length(datos_t, pathsa, geometrias_ids[i])
        elif combined_data[canal] == '1':
            actualizar_path_length(datos_t, pathsf, geometrias_ids[i])

    # Prepara el mapa GeoJSON para enviar por el WebSocket
    data_enviar = json.dumps(datos_t, indent=4)

    # Envía el JSON a todas las conexiones WebSocket
    for connection in conn_websocket_connections:   
        await connection.send_text(data_enviar)

# Modificación del endpoint process_json para llamar la nueva función
@app.post("/process-json")
async def process_json(data: dict):
    global combined_data, esp1_received, esp2_received
    data_type = determine_data_type(data)

    if data_type is Esp1 and not esp1_received:
        temporary_data["esp1"] = Esp1(**data).dict()
        esp1_received = True
        print("Datos de esp1 recibidos.")
    elif data_type is Esp2 and not esp2_received:
        temporary_data["esp2"] = Esp2(**data).dict()
        esp2_received = True
        print("Datos de esp2 recibidos.")

    # Verificar si se han recibido datos de ambos ESP32
    if esp1_received and esp2_received:
        # Combinar los datos de Esp1 y Esp2
        combined_data = {
            **temporary_data["esp1"],
            **temporary_data["esp2"]
        }

        # Convertir todos los valores a cadenas
        combined_data = {key: str(value) for key, value in combined_data.items()}

        # Limpiar los datos temporales 
        temporary_data["esp1"] = None
        temporary_data["esp2"] = None
        esp1_received = False
        esp2_received = False

        # Ejecutar el envío del mapa 
        await envio_mapa_func()

    return {"status": "waiting for all data"}
