import csv
import random
import json
from flask import Flask, jsonify, request

app = Flask(__name__)

""" 
---------------------------------------------
Rutas de almacenamiento para los archivos CSV
---------------------------------------------
Cambiar por Base de Datos eventualmente
"""
CAMIONES_CSV_PATH = './data/camiones.csv'
PATIO_CSV_PATH = './data/patio.csv'
DEMANDA_CSV_PATH = './data/demanda.csv'
"""
---------------------------------------------
"""

# Lista de nombres de choferes y URLs para fotos
nombres_conductores = ["Rubí", "Raúl", "Rafael", "Sebastián", "Gustavo", "Gus", "Daniel", "Pablo", "Daniela"]
conductores_fotos = [
    "https://example.com/foto_rubi.png",
    "https://example.com/foto_raul.png",
    "https://example.com/foto_rafael.png",
    "https://example.com/foto_sebastian.png",
    "https://example.com/foto_gustavo.png",
    "https://example.com/foto_gus.png",
    "https://example.com/foto_daniel.png",
    "https://example.com/foto_pablo.png",
    "https://example.com/foto_daniela.png"
]

# Función para generar un lugar de estacionamiento aleatorio
def generar_lugar_estacionamiento():
    digito = random.randint(1, 9)  # Número de 1 a 9
    letra = chr(random.randint(65, 90))  # Letra de A a Z (ASCII)
    return f"{digito}{letra}"

# /camiones: Crea camiones simulando origen de fábrica y los guarda en un CSV
@app.route('/camiones/create/<int:seed>', methods=['POST'])
def create_camiones(seed):
    random.seed(seed)
    
    camiones = []
    for i in range(30):  # Crearemos 30 camiones como ejemplo
        camion_id = hex(random.randint(0x100000, 0xFFFFFF))[2:].upper()  # ID en formato Hex
        contenido = [{"IdProducto": random.randint(1, 56), "Cantidad": random.randint(40, 2000)} for _ in range(5)]  # 5 productos por camión
        placa = f"{random.randint(100, 999)}-XYZ-{random.randint(100, 999)}"
        chofer = random.choice(nombres_conductores)
        foto_chofer = conductores_fotos[nombres_conductores.index(chofer)]
        num_remolques = random.randint(1, 2)
        hora_llegada = f"{random.randint(0, 23)}:{random.randint(0, 59):02d}"
        descargado = 'False'  # Estado inicial
        lugar_estacionamiento = generar_lugar_estacionamiento()  # Generamos el lugar de estacionamiento

        camiones.append([
            camion_id, 
            json.dumps(contenido), 
            placa, 
            chofer, 
            foto_chofer,  # Añadimos la URL de la foto
            num_remolques, 
            hora_llegada, 
            descargado, 
            lugar_estacionamiento
        ])

    # Guardar en CSV con la nueva estructura
    with open(CAMIONES_CSV_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Columnas con la nueva estructura
        writer.writerow(["CamionID", "Contenido", "Placa", "Chofer", "ConductorFoto", "NumeroRemolques", "HoraLlegada", "Descargado", "LugarEstacionamiento"])
        writer.writerows(camiones)

    return jsonify({"message": "Camiones creados correctamente en fábrica."}), 201


# /camiones: Obtener el contenido de un camión por ID (fábrica)
@app.route('/camiones/<camion_id>', methods=['GET'])
def get_camion_content(camion_id):
    with open(CAMIONES_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['CamionID'] == camion_id:
                contenido = json.loads(row['Contenido'])
                return jsonify({
                    "CamionID": camion_id,
                    "Contenido": contenido
                }), 200
    
    return jsonify({"message": "Camion no encontrado en fábrica"}), 404

# /patio: Registrar camiones en el patio, entrada por seguridad
@app.route('/patio/register/<camion_id>', methods=['POST'])
def register_camion_in_patio(camion_id):
    camion_data = None

    # Primero leemos el archivo de camiones para obtener los datos
    with open(CAMIONES_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['CamionID'] == camion_id:
                camion_data = row
                break

    if not camion_data:
        return jsonify({"message": "Camión no encontrado en fábrica"}), 404

    # Registrar camión en el patio
    camion_data['Descargado'] = 'False'  # Estado inicial del camión en el patio
    camion_data['LugarEstacionamiento'] = generar_lugar_estacionamiento()

    # Guardar en el CSV del patio
    with open(PATIO_CSV_PATH, mode='a', newline='') as file:
        # Verificar si el camión ya está en el patio
        reader = csv.DictReader(open(PATIO_CSV_PATH, mode='r'))  # Asegúrate de abrir en modo lectura
        for row in reader:
            if row['CamionID'] == camion_id:
                return jsonify({"message": f"Camion {camion_id} ya registrado en el patio. Sin cambios."}), 409
            
        # Escribir el camión en el patio
        writer = csv.DictWriter(file, fieldnames=["CamionID", "Contenido", "Placa", "Chofer", "ConductorFoto", "NumeroRemolques", "HoraLlegada", "Descargado", "LugarEstacionamiento"])
        writer.writerow(camion_data)

    return jsonify({"message": f"Camion {camion_id} registrado en el patio."}), 201


# /patio: Listar camiones en el patio que no han sido descargados
@app.route('/patio/list', methods=['GET'])
def list_camiones_in_patio():
    camiones = []
    
    with open(PATIO_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Descargado'] == "False":
                camiones.append({
                    "CamionID": row['CamionID'], 
                    "HoraLlegada": row['HoraLlegada'],
                    "LugarEstacionamiento": row['LugarEstacionamiento'],
                })

    return jsonify(camiones), 200

# /patio: Obtener el contenido de un camión por ID (patio)
@app.route('/patio/<camion_id>', methods=['GET'])
def get_camion_content_in_patio(camion_id):
    with open(PATIO_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['CamionID'] == camion_id:
                contenido = json.loads(row['Contenido'])
                return jsonify({
                    "CamionID": camion_id,
                    "Contenido": contenido,
                    "LugarEstacionamiento": row['LugarEstacionamiento'],
                    "ConductorFoto": row['ConductorFoto']  # Añadimos la foto del chofer
                }), 200
    
    return jsonify({"message": "Camion no encontrado en patio"}), 404

# /patio: Actualizar el estado de descarga de un camión
@app.route('/patio/update/<camion_id>', methods=['PUT'])
def update_camion_in_patio(camion_id):
    updated = False
    camiones = []
    
    # Leer y actualizar el archivo CSV del patio
    with open(PATIO_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['CamionID'] == camion_id:
                row['Descargado'] = 'True'
                updated = True
            camiones.append(row)

    # Sobrescribir el CSV del patio con los cambios
    with open(PATIO_CSV_PATH, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["CamionID", "Contenido", "Placa", "Chofer", "ConductorFoto", "NumeroRemolques", "HoraLlegada", "Descargado", "LugarEstacionamiento"])
        writer.writeheader()
        writer.writerows(camiones)

    if updated:
        return jsonify({"message": f"Camion {camion_id} marcado como descargado."}), 200
    else:
        return jsonify({"message": "Camion no encontrado en patio."}), 404

# /patio: Wipe de camiones en el patio
@app.route('/patio/wipe', methods=['DELETE'])
def wipe_patio():
    with open(PATIO_CSV_PATH, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["CamionID", "Contenido", "Placa", "Chofer", "ConductorFoto", "NumeroRemolques", "HoraLlegada", "Descargado", "LugarEstacionamiento"])
        writer.writeheader()

    return jsonify({"message": "Patio limpiado correctamente."}), 200

# /patio: Llenar el patio con camiones de la fábrica (simulación)
@app.route('/patio/fill', methods=['POST'])
def fill_patio():
    camiones = []
    
    with open(CAMIONES_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            camiones.append(row)

    with open(PATIO_CSV_PATH, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["CamionID", "Contenido", "Placa", "Chofer", "ConductorFoto", "NumeroRemolques", "HoraLlegada", "Descargado", "LugarEstacionamiento"])
        writer.writeheader()
        writer.writerows(camiones)

    return jsonify({"message": "Patio llenado con camiones de fábrica."}), 201



### DEMANDA
# Create: Generar demanda y guardar en un CSV
@app.route('/demanda/create/<int:seed>', methods=['POST'])
def create_demanda(seed):
    random.seed(seed) #Revisar lo del seed****
    
    demanda = []
    productos_usados = set()  # Set para almacenar los productos ya seleccionados

    while len(productos_usados) < 20:  
        id_producto = random.randint(1, 56)
        if id_producto not in productos_usados:
            cantidad = random.randint(40, 2000)
            demanda.append([id_producto, cantidad])
            productos_usados.add(id_producto)  

    # Guardar en CSV
    with open(DEMANDA_CSV_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["IdProducto", "Cantidad"])
        writer.writerows(demanda)

    return jsonify({"message": "Demanda generada correctamente."}), 201

# Read: Listar el contenido del CSV de demanda
@app.route('/demanda/list', methods=['GET'])
def list_demanda():
    demanda = []
    
    with open(DEMANDA_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            demanda.append({"IdProducto": row['IdProducto'], "Cantidad": row['Cantidad']})

    return jsonify(demanda), 200

# Read: Obtener una lista aleatoria de demanda (sin CSV)
@app.route('/demanda/random', methods=['GET'])
def random_demanda():
    demanda = []
    
    for i in range(20):  # 20 productos aleatorios
        id_producto = random.randint(1, 56)
        cantidad = random.randint(40, 2000)
        demanda.append({"IdProducto": id_producto, "Cantidad": cantidad})

    return jsonify(demanda), 200

# Update: Actualizar demanda tras la descarga de productos de un camión
@app.route('/demanda/update/<camion_id>', methods=['PUT'])
def update_demanda(camion_id):
    camiones = []
    demanda_actualizada = []
    productos_camion = []

    # Cargar el contenido del camión en patio desde el CSV
    with open(PATIO_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['CamionID'] == camion_id:
                productos_camion = json.loads(row['Contenido'])  # Obtener el contenido del camión

    if not productos_camion:
        return jsonify({"message": "Camion no encontrado en patio o no tiene productos"}), 404

    # Actualizar la demanda en función de los productos descargados
    with open(DEMANDA_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            id_producto = int(row['IdProducto'])
            cantidad_demanda = int(row['Cantidad'])
            
            # Buscar si el producto está en el camión
            for producto in productos_camion:
                if producto['IdProducto'] == id_producto:
                    cantidad_camion = producto['Cantidad']
                    # Restar la cantidad del producto en el camión a la demanda
                    nueva_cantidad = max(0, cantidad_demanda - cantidad_camion)
                    demanda_actualizada.append({"IdProducto": id_producto, "Cantidad": nueva_cantidad})
                    break
            else:
                # Si no hay match con el camión, dejar el producto tal como está en la demanda
                demanda_actualizada.append({"IdProducto": id_producto, "Cantidad": cantidad_demanda})

    # Guardar la demanda actualizada en el CSV
    with open(DEMANDA_CSV_PATH, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["IdProducto", "Cantidad"])
        writer.writeheader()
        writer.writerows(demanda_actualizada)

    return jsonify({"message": "Demanda actualizada correctamente."}), 200

# Read: Simular una lista de 10 camiones al azar como recomendación de orden de descarga
@app.route('/modelo/recomendacion', methods=['GET'])
def modelo_recomendacion():
    camiones = []
    camiones_recomendados = []

    # Leer los camiones disponibles desde el CSV
    with open(PATIO_CSV_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Descargado'] == 'False':
                camiones.append(row)

    # Si hay menos de 10 camiones disponibles, usar los que haya
    num_camiones = min(10, len(camiones))

    # Seleccionar 10 camiones al azar
    camiones_recomendados = random.sample(camiones, num_camiones)

    # Añadir índice de orden (1-10)
    for idx, camion in enumerate(camiones_recomendados, start=1):
        camion['OrdenDescarga'] = idx
    
    # Solo retornar los atributos deseados
    camiones_filtrados = [
        {
            'IdCamion': camion['CamionID'],  
            'Placa': camion['Placa'],        
            'OrdenDescarga': camion['OrdenDescarga'] 
        }
        for camion in camiones_recomendados
    ]

    return jsonify(camiones_filtrados), 200

# Punto de entrada
if __name__ == '__main__':
    app.run(debug=True)

# Antes del juebebes 17 de octubre  
# Base de datos de perfiles de empleados para aplicación

# Antes del martes 22 de octubre
# Información de BD y cuál vamos a usar

# ActionItems Faltantes para nuestro 100%:
# Preguntar cómo se maneja inventario para la resta de la demanda (si es necesario, crear BD de inventario)
# Cómo se manejan las demandas y cómo son (Global, Minis), crear las demandas correctamente y no aleatoriamente
# Crear las bases de datos en lugar de los CSVs
# NO generar recomendaciones según aleatorios, adjuntar el modelo de recomendación.
# Agregar procesos automáticos para guardar históricos en la BD correspondiente