import random
import json
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)

# SQLite database setup
DB_PATH = './data/database.db'

# Initialize database and create tables
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Camiones table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camiones (
                CamionID TEXT PRIMARY KEY,
                Contenido TEXT,
                Placa TEXT,
                Chofer TEXT,
                ConductorFoto TEXT,
                NumeroRemolques INTEGER,
                HoraLlegada TEXT,
                Descargado TEXT,
                LugarEstacionamiento TEXT
            )
        ''')
        # Patio table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patio (
                CamionID TEXT PRIMARY KEY,
                Contenido TEXT,
                Placa TEXT,
                Chofer TEXT,
                ConductorFoto TEXT,
                NumeroRemolques INTEGER,
                HoraLlegada TEXT,
                Descargado TEXT,
                LugarEstacionamiento TEXT
            )
        ''')
        # Demanda table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS demanda (
                IdProducto INTEGER PRIMARY KEY,
                Cantidad INTEGER
            )
        ''')
        conn.commit()

# List of names of drivers and URLs for photos
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

# Function to generate a random parking spot
def generar_lugar_estacionamiento():
    digito = random.randint(1, 9)  # Number from 1 to 9
    letra = chr(random.randint(65, 90))  # Letter from A to Z (ASCII)
    return f"{digito}{letra}"

# /camiones: Create trucks simulating factory origin and save them in the database
@app.route('/camiones/create/<int:seed>', methods=['POST'])
def create_camiones(seed):
    random.seed(seed)
    
    camiones = []
    for i in range(30):  # Creating 30 trucks as an example
        camion_id = hex(random.randint(0x100000, 0xFFFFFF))[2:].upper()  # ID in Hex format
        contenido = [{"IdProducto": random.randint(1, 56), "Cantidad": random.randint(40, 2000)} for _ in range(5)]  # 5 products per truck
        placa = f"{random.randint(100, 999)}-XYZ-{random.randint(100, 999)}"
        chofer = random.choice(nombres_conductores)
        foto_chofer = conductores_fotos[nombres_conductores.index(chofer)]
        num_remolques = random.randint(1, 2)
        hora_llegada = f"{random.randint(0, 23)}:{random.randint(0, 59):02d}"
        descargado = 'False'
        lugar_estacionamiento = generar_lugar_estacionamiento()

        camiones.append((camion_id, json.dumps(contenido), placa, chofer, foto_chofer, num_remolques, hora_llegada, descargado, lugar_estacionamiento))

    # Save to SQLite database
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT INTO camiones 
                (CamionID, Contenido, Placa, Chofer, ConductorFoto, NumeroRemolques, HoraLlegada, Descargado, LugarEstacionamiento) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', camiones)
            conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"message": "Error: Algunos camiones ya existen en la fábrica."}), 409

    return jsonify({"message": "Camiones creados correctamente en fábrica."}), 201

# /camiones: Get the content of a truck by ID (factory)
@app.route('/camiones/<camion_id>', methods=['GET'])
def get_camion_content(camion_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM camiones WHERE CamionID = ?", (camion_id,))
        row = cursor.fetchone()

        if row:
            contenido = json.loads(row[1])
            return jsonify({"CamionID": camion_id, "Contenido": contenido}), 200
        else:
            return jsonify({"message": "Camion no encontrado en fábrica"}), 404

# /camiones: Delete trucks from factory as reset
@app.route('/camiones/wipe', methods=['DELETE'])
def wipe_camiones():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM camiones")
        conn.commit()

    return jsonify({"message": "Todos los camiones de la fábrica han sido eliminados."}), 200

# /patio: Register trucks in the yard, entry through security
@app.route('/patio/register/<camion_id>', methods=['POST'])
def register_camion_in_patio(camion_id):
    camion_data = None

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM camiones WHERE CamionID = ?", (camion_id,))
        camion_data = cursor.fetchone()

        if not camion_data:
            return jsonify({"message": "Camión no encontrado en fábrica"}), 404

        # Register truck in the yard
        camion_data = list(camion_data)
        camion_data[7] = 'False'
        camion_data[8] = generar_lugar_estacionamiento()

        cursor.execute("SELECT * FROM patio WHERE CamionID = ?", (camion_id,))
        if cursor.fetchone():
            return jsonify({"message": f"Camion {camion_id} ya registrado en el patio. Sin cambios."}), 409

        cursor.execute('''
            INSERT INTO patio 
            (CamionID, Contenido, Placa, Chofer, ConductorFoto, NumeroRemolques, HoraLlegada, Descargado, LugarEstacionamiento) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', camion_data)
        conn.commit()

    return jsonify({"message": f"Camion {camion_id} registrado en el patio."}), 201

# /patio: List trucks in the yard that have not been unloaded
@app.route('/patio/list', methods=['GET'])
def list_camiones_in_patio():
    camiones = []
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patio WHERE Descargado = 'False'")
        rows = cursor.fetchall()

        for row in rows:
            camiones.append({
                "CamionID": row[0],
                "HoraLlegada": row[6],
                "LugarEstacionamiento": row[8],
            })

    return jsonify(camiones), 200

# /patio: Get the content of a truck by ID (yard)
@app.route('/patio/<camion_id>', methods=['GET'])
def get_camion_content_in_patio(camion_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patio WHERE CamionID = ?", (camion_id,))
        row = cursor.fetchone()

        if row:
            contenido = json.loads(row[1])
            return jsonify({
                "CamionID": camion_id,
                "Contenido": contenido,
                "LugarEstacionamiento": row[8],
                "ConductorFoto": row[4]
            }), 200
        else:
            return jsonify({"message": "Camion no encontrado en patio"}), 404

# /patio: Update the unloading status of a truck
@app.route('/patio/update/<camion_id>', methods=['PUT'])
def update_camion_in_patio(camion_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE patio SET Descargado = 'True' WHERE CamionID = ?", (camion_id,))
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({"message": f"Camion {camion_id} marcado como descargado."}), 200
        else:
            return jsonify({"message": "Camion no encontrado en patio."}), 404

# /patio: Wipe all trucks in the yard
@app.route('/patio/wipe', methods=['DELETE'])
def wipe_patio():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patio")
        conn.commit()

    return jsonify({"message": "Patio limpiado correctamente."}), 200

# /patio/fill: Move trucks from factory to the yard
@app.route('/patio/fill', methods=['POST'])
def fill_patio():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM camiones")
        camiones = cursor.fetchall()

        if not camiones:
            return jsonify({"message": "No hay camiones en la fábrica para trasladar al patio."}), 404

        for camion in camiones:
            camion_data = list(camion)
            camion_data[7] = 'False'  # Set Descargado to 'False'
            camion_data[8] = generar_lugar_estacionamiento()  # Generate a new parking spot

            cursor.execute('''
                INSERT INTO patio 
                (CamionID, Contenido, Placa, Chofer, ConductorFoto, NumeroRemolques, HoraLlegada, Descargado, LugarEstacionamiento) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', camion_data)

        conn.commit()

    return jsonify({"message": "Todos los camiones de la fábrica han sido trasladados al patio."}), 200

# /demanda: Create demand for products
@app.route('/demanda/create/<int:seed>', methods=['POST'])
def create_demanda(seed):
    random.seed(seed)
    
    # Randomly select 23 unique product IDs from 1 to 56
    selected_ids = random.sample(range(1, 57), 23)  # Select 23 unique IDs
    demanda = [(id_producto, random.randint(1, 100)) for id_producto in selected_ids]  # Generate random quantities

    updated_count = 0  # Count of updated products
    new_count = 0      # Count of new products inserted

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Process each product in the demanda list
        for id_producto, cantidad in demanda:
            cursor.execute("SELECT COUNT(*) FROM demanda WHERE IdProducto = ?", (id_producto,))
            exists = cursor.fetchone()[0]

            if exists > 0:
                # If product exists, update its quantity
                cursor.execute("UPDATE demanda SET Cantidad = ? WHERE IdProducto = ?", (cantidad, id_producto))
                updated_count += 1
            else:
                # If product does not exist, insert it
                cursor.execute("INSERT INTO demanda (IdProducto, Cantidad) VALUES (?, ?)", (id_producto, cantidad))
                new_count += 1

        conn.commit()

    # Create a message based on the number of updates and new inserts
    messages = []
    if new_count > 0:
        messages.append(f"{new_count} productos se han añadido.")
    if updated_count > 0:
        messages.append(f"{updated_count} productos se han actualizado.")

    if messages:
        return jsonify({"message": "Demanda creada correctamente. " + " ".join(messages)}), 201
    else:
        return jsonify({"message": "No se realizaron cambios en la demanda."}), 200

# /demanda: Get demand for all products
@app.route('/demanda', methods=['GET'])
def get_demanda():
    demanda = []
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM demanda")
        rows = cursor.fetchall()

        for row in rows:
            demanda.append({"IdProducto": row[0], "Cantidad": row[1]})

    return jsonify(demanda), 200

# /demanda: Generate and return a random demand of 10 items (not related to DB)
@app.route('/demanda/random', methods=['GET'])
def get_random_demanda():
    demanda = []

    # Generate a random demand of 10 items
    for i in range(10):
        id_producto = random.randint(1, 56)
        cantidad = random.randint(1, 100)
        demanda.append({"IdProducto": id_producto, "Cantidad": cantidad})

    return jsonify(demanda), 200

# /demanda: Update demand from given truck products (subtraction)
@app.route('/demanda/update/<camion_id>', methods=['PUT'])
def update_demanda(camion_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Contenido FROM patio WHERE CamionID = ?", (camion_id, ))
        row = cursor.fetchone()

        if row:
            contenido = json.loads(row[0])
            for producto in contenido:
                id_producto = producto["IdProducto"]
                cantidad = producto["Cantidad"]
                # Update demand from the contents of the truck. Capped minimum at 0
                cursor.execute("UPDATE demanda SET Cantidad = CASE WHEN Cantidad - ? < 0 THEN 0 ELSE Cantidad - ? END WHERE IdProducto = ?", (cantidad, cantidad, id_producto))
                conn.commit()
            return jsonify({"message": f"Demanda de camion {camion_id} actualizada correctamente."}), 200
        else:
            return jsonify({"message": "Camion no encontrado en patio."}), 404

# /demanda: Clear all demand data
@app.route('/demanda/wipe', methods=['DELETE'])
def wipe_demanda():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM demanda")
        conn.commit()

    return jsonify({"message": "Demanda limpiada correctamente."}), 200

# /modelo: Get model recommendation
# Tiempo de llegada (Tiempo que lleva esperando)
# Número de pallets
# Cantidad por producto (Producto:Cantidad)

# ProductoID
# Importancia 0-1
# Cantidad

# Por bahía qué camiones


# Initialize the database
init_db()

if __name__ == '__main__':
    app.run(debug=True)
