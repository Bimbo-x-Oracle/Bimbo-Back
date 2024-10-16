import csv
import random
import json
from flask import Flask, jsonify, request

app = Flask(__name__)

# Ruta de almacenamiento para el archivo CSV
CSV_FILE_PATH = './data/camiones.csv'

# Lista de nombres de choferes
nombres_conductores = ["Carlos", "Luis", "Miguel", "Jose", "Pedro", "Raul", "Diego", "Juan", "Javier"]

# Función para generar un lugar de estacionamiento aleatorio
def generar_lugar_estacionamiento():
    digito = random.randint(1, 9)  # Número de 1 a 9
    letra = chr(random.randint(65, 90))  # Letra de A a Z (ASCII)
    return f"{digito}{letra}"

# Create: Genera camiones y guarda en un CSV
@app.route('/camiones/create/<int:seed>', methods=['POST'])
def create_camiones(seed):
    random.seed(seed)
    
    camiones = []
    for i in range(30):  # Crearemos 10 camiones por ejemplo
        camion_id = hex(random.randint(0x100000, 0xFFFFFF))[2:].upper()  # ID en formato Hex
        contenido = [{"IdProducto": random.randint(1, 56), "Cantidad": random.randint(40, 2000)} for _ in range(5)]  # 5 productos por camión
        descargado = random.choices([True, False], [0.2, 0.8])[0]
        placa = f"{random.randint(100, 999)}-XYZ-{random.randint(100, 999)}"
        chofer = random.choice(nombres_conductores)
        num_remolques = random.randint(1, 2)
        hora_llegada = f"{random.randint(0, 23)}:{random.randint(0, 59):02d}"
        lugar_estacionamiento = generar_lugar_estacionamiento()


        camiones.append([camion_id, json.dumps(contenido), descargado, placa, chofer, num_remolques, hora_llegada, lugar_estacionamiento])

    # Guardar en CSV
    with open(CSV_FILE_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["CamionID", "Contenido", "Descargado", "Placa", "Chofer", "NumeroRemolques", "HoraLlegada", "LugarEstacionamiento"])
        writer.writerows(camiones)

    return jsonify({"message": "Camiones generados correctamente."}), 201

# Read: Listar camiones no descargados
@app.route('/camiones/list', methods=['GET'])
def list_camiones():
    camiones = []
    
    with open(CSV_FILE_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Descargado'] == 'False':
                camiones.append({
                    "CamionID": row['CamionID'], 
                    "HoraLlegada": row['HoraLlegada'],
                    "LugarEstacionamiento": row['LugarEstacionamiento']
                })

    return jsonify(camiones), 200

# Read: Obtener el contenido de un camión por ID
@app.route('/camiones/<camion_id>', methods=['GET'])
def get_camion_content(camion_id):
    with open(CSV_FILE_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['CamionID'] == camion_id:
                contenido = json.loads(row['Contenido'])
                return jsonify({
                    "CamionID": camion_id,
                    "Contenido": contenido,
                    "LugarEstacionamiento": row['LugarEstacionamiento']
                }), 200
    
    return jsonify({"message": "Camion no encontrado"}), 404

# Update: Actualizar el estado de descarga de un camión
@app.route('/camiones/update/<camion_id>', methods=['PUT'])
def update_camion(camion_id):
    updated = False
    camiones = []
    
    # Leer y actualizar el archivo CSV
    with open(CSV_FILE_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['CamionID'] == camion_id:
                row['Descargado'] = 'True'
                updated = True
            camiones.append(row)

    # Sobrescribir el CSV con los cambios
    with open(CSV_FILE_PATH, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["CamionID", "Contenido", "Descargado", "Placa", "Chofer", "NumeroRemolques", "HoraLlegada", "LugarEstacionamiento"])
        writer.writeheader()
        writer.writerows(camiones)

    if updated:
        return jsonify({"message": "Camion actualizado correctamente."}), 200
    else:
        return jsonify({"message": "Camion no encontrado"}), 404

# Ruta de almacenamiento para el archivo CSV de demanda
CSV_DEMANDA_PATH = './data/demanda.csv'

# Create: Generar demanda y guardar en un CSV
@app.route('/demanda/create/<int:seed>', methods=['POST'])
def create_demanda(seed):
    random.seed(seed)
    
    demanda = []
    for i in range(20):  # Generaremos 20 productos
        id_producto = random.randint(1, 56)
        cantidad = random.randint(40, 2000)
        demanda.append([id_producto, cantidad])

    # Guardar en CSV
    with open(CSV_DEMANDA_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["IdProducto", "Cantidad"])
        writer.writerows(demanda)

    return jsonify({"message": "Demanda generada correctamente."}), 201

# Read: Listar el contenido del CSV de demanda
@app.route('/demanda/list', methods=['GET'])
def list_demanda():
    demanda = []
    
    with open(CSV_DEMANDA_PATH, mode='r') as file:
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

    # Cargar el contenido del camión desde el CSV
    with open(CSV_FILE_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['CamionID'] == camion_id:
                productos_camion = json.loads(row['Contenido'])  # Obtener el contenido del camión

    if not productos_camion:
        return jsonify({"message": "Camion no encontrado o no tiene productos"}), 404

    # Actualizar la demanda en función de los productos descargados
    with open(CSV_DEMANDA_PATH, mode='r') as file:
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
    with open(CSV_DEMANDA_PATH, mode='w', newline='') as file:
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
    with open(CSV_FILE_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Descargado'] == 'False':  # Solo camiones no descargados
                camiones.append({
                    "CamionID": row['CamionID'],
                    "HoraLlegada": row['HoraLlegada'],
                    "LugarEstacionamiento": row['LugarEstacionamiento']
                })

    # Si hay menos de 10 camiones disponibles, usar los que haya
    cantidad_a_seleccionar = min(10, len(camiones))

    # Seleccionar 10 camiones al azar
    camiones_recomendados = random.sample(camiones, cantidad_a_seleccionar)

    # Añadir índice de orden (1-10)
    for i, camion in enumerate(camiones_recomendados):
        camion['Orden'] = i + 1

    return jsonify(camiones_recomendados), 200

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