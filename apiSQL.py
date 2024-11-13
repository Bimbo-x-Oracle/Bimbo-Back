import csv
import random
import json
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
import pandas as pd
from modelo_noAlmacenSQL import algoritmo_genetico_experiment, fetch_data_from_db

app = Flask(__name__)

# Path a base de datos SQLite
DB_PATH = './data/database.db.'

# Registro de usuario
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    usuario = data.get('usuario')
    password = data.get('password')
    nombre_completo = data.get('nombre_completo')
    rol = data.get('rol')
    foto = data.get('foto')

    # Hash the password wiht salt using PBKDF2 and SHA256
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    # Guardar en la base de datos
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO usuarios (Usuario, Password, NombreCompleto, Rol, Foto) 
                VALUES (?, ?, ?, ?, ?)
            ''', (usuario, hashed_password, nombre_completo, rol, foto))
            conn.commit()
            return jsonify({'message': 'Usuario registrado exitosamente'}), 201
        except sqlite3.IntegrityError:
            return jsonify({'message': 'Error: El usuario ya existe'}), 409

# Login de usuario
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usuario = data.get('usuario')
    password = data.get('password')

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT Password FROM usuarios WHERE Usuario = ?', (usuario,))
        row = cursor.fetchone()

        if row and check_password_hash(row[0], password):
            return jsonify({'message': 'Login exitoso'}), 200
        else:
            return jsonify({'message': 'Credenciales incorrectas'}), 401

# Función para generar un lugar de estacionamiento aleatorio
def generar_lugar_estacionamiento():
    digito = random.randint(1, 9)  # Número de 1 a 9
    letra = chr(random.randint(65, 90))  # Letra de A a Z (ASCII)
    return f"{digito}{letra}"

# /camiones: Obtener el contenido de un camión por ID (Join tabla camiones y camionesContenido)
"""
TODO: REGRESAR CONTENIDO, TODAS LAS COLUMNAS
"""
@app.route('/camiones/<camion_id>', methods=['GET'])
def get_camion(camion_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.CamionID, c.Placa, c.ConductorID, c.NumeroRemolques, c.HoraLlegada, c.Estado, 
                   cc.Carga, cc.Pallet, cc.FechaCierre
            FROM camiones c
            JOIN camionesContenido cc ON c.CamionID = cc.Carga
            WHERE c.CamionID = ?
        ''', (camion_id,))
        truck = cursor.fetchone()
        if truck:
            truck_data = {
                'CamionID': truck[0],
                'Placa': truck[1],
                'ConductorID': truck[2],
                'NumeroRemolques': truck[3],
                'HoraLlegada': truck[4],
                'Estado': truck[5],
                'Carga': truck[6],
                'Pallet': truck[7],
                'FechaCierre': truck[8]
            }
            return jsonify(truck_data), 200
        else:
            return jsonify({'message': 'Camión no encontrado'}), 404

# /camiones: Insertar nuevo set de camiones como csv (insertdb function) DO NOT DO THIS FOR NOW
#@app.route('/camiones/insert', methods=['DELETE'])
"""
TODO: Crear
"""

# /patio: Registrar camiones en el patio, entrada por seguridad
@app.route('/patio/register/<camion_id>', methods=['POST'])
def register_patrol(camion_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Check truck state and assign parking spot if necessary
        cursor.execute('SELECT Estado FROM camiones WHERE CamionID = ?', (camion_id,))
        row = cursor.fetchone()

        if row:
            estado = row[0]
            if estado in ['enFabrica', 'Out']:  # Si el camion esta llegando:
                lugar_estacionamiento = generar_lugar_estacionamiento() # Asignar lugar de estacionamiento
                hora_llegada = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Asignar hora de llegada
                cursor.execute('''
                    UPDATE camiones 
                    SET Estado = ?, LugarEstacionamiento = ?, HoraLlegada = ? 
                    WHERE CamionID = ?
                ''', ('enEspera', lugar_estacionamiento, hora_llegada, camion_id))
                conn.commit()
                return jsonify({'message': f'Camión {camion_id} registrado en el patio, lugar: {lugar_estacionamiento}'}), 200
            else:
                # Si el camion está saliendo
                cursor.execute('UPDATE camiones SET Estado = "Out" WHERE CamionID = ?', (camion_id,)) # Cambiar estado a Out
                conn.commit()
                return jsonify({'message': f'Camión {camion_id} ya no está en espera, estado actualizado a "Out".'}), 200
        else:
            return jsonify({'message': 'Camión no encontrado'}), 404


# /patio: Actualizar el estado de descarga de un camión (descargado)
@app.route('/patio/update/<camion_id>', methods=['PUT'])
# If Estado = Bahia, Estado = Descargado
# Consulta para actualizar la demanda tras la descarga de productos con la resta del contenido del camión (MIN CAP 0)
def update_patio(camion_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Si al camion esta en bahía
        cursor.execute('SELECT Estado FROM camiones WHERE CamionID = ?', (camion_id,))
        row = cursor.fetchone()
    if row and row[0] == 'Bahia':
        # Actualizar estado a Descargado
        cursor.execute('''
            UPDATE camiones 
            SET Estado = 'Descargado'
            WHERE CamionID = ?
        ''', (camion_id,))
        conn.commit()
        # Actualizar la demanda con la resta de la lista de productos del camion
        """        cursor.execute('''
            UPDATE demanda 
            SET "124440" = "124440" - 1  -- Example adjustment, adapt as needed
            WHERE Orden = ?
        ''', (camion_id,))  # Replace with appropriate condition
        conn.commit()
        return jsonify({'message': 'Camión descargado y demanda actualizada.'}), 200
        """
        return jsonify({'message': 'Camión descargado.'}), 200
    else:
        return jsonify({'message': 'Camión no está en estado "Bahia".'}), 400

# /patio: Listar camiones (Informacion en tabla camiones)
@app.route('/patio/list', methods=['GET'])
def list_trucks_patio():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT CamionID, Placa, Estado, LugarEstacionamiento, HoraLlegada
            FROM camiones
            WHERE Estado = 'enEspera'
        ''')
        trucks = cursor.fetchall()
        if trucks:
            truck_list = [{'CamionID': truck[0], 'Placa': truck[1], 'Estado': truck[2], 'LugarEstacionamiento': truck[3], 'HoraLlegada': truck[4]} for truck in trucks]
            return jsonify(truck_list), 200
        else:
            return jsonify({'message': 'No hay camiones.'}), 404

# Read: Ver la demanda (información en tabla de demanda)
@app.route('/demanda/list', methods=['GET'])
def get_demanda():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM demanda')
        demanda_data = cursor.fetchall()
        if demanda_data:
            demand_list = [dict(zip([column[0] for column in cursor.description], row)) for row in demanda_data]
            return jsonify(demand_list), 200
        else:
            return jsonify({'message': 'No hay demanda disponible.'}), 404


# /demanda: Insertar nuevo set de demanda como csv (insert_db function) DO NOT DO THIS FOR NOW
#@app.route('/demanda/insert', methods=['DELETE'])
"""
TODO: CREAR
"""

#Métodos de modelo (con referencia a modelo_noAlmacenSQL.py)

# Modelo: Algoritmo a correr con consultas a la base de datos
@app.route('/modelo', methods=['GET'])
def modelo():
    try:
        camiones_df, demanda_df = fetch_data_from_db()

        if camiones_df.empty or demanda_df.empty:
            return jsonify({'message': 'No data found for trucks or demand.'}), 400

        # Call the genetics algorithm function from model.py
        mejor_individuo, tiempo_total_ganador = algoritmo_genetico_experiment(camiones_df, demanda_df)

        result = {
            'mejor_individuo': mejor_individuo,  # List of trucks assigned to each bay
            'tiempo_total_ganador': tiempo_total_ganador  # Total time for the best solution
        }
        
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500


## Modelo: Algoritmo a correr con csvs predeterminados para casos de prueba DO NOT DO THIS FOR NOW
#@app.route('/modelo/test', methods=['POST'])
"""
TODO: Crear
"""

# Punto de entrada
if __name__ == '__main__':
    app.run(debug=True)





    