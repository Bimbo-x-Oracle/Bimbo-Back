import csv
import random
import json
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
import pandas as pd
import os
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
@app.route('/camiones/<camion_id>', methods=['GET'])
def get_camionPrueba(camion_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.CamionID, c.Placa, c.ConductorID, c.NumeroRemolques, c.HoraLlegada, c.Estado, cc.*
            FROM camiones c
            JOIN camionesContenido cc ON c.CamionID = cc.Carga
            WHERE c.CamionID = ?
        ''', (camion_id,))
        
         # Obtiene todos los registros
        trucks = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        
        if trucks:
            # Asigna los datos básicos del camión
            truck_data = {
                'CamionID': trucks[0][0],
                'Placa': trucks[0][1],
                'ConductorID': trucks[0][2],
                'NumeroRemolques': trucks[0][3],
                'HoraLlegada': trucks[0][4],
                'Estado': trucks[0][5],
                'Contenido': []
            }

            # Itera sobre cada registro en camionesContenido
            for truck in trucks:
                contenido = {columns[i]: truck[i] for i in range(6, len(columns)) if truck[i] != 0}
                truck_data['Contenido'].append(contenido)
                
            return jsonify(truck_data), 200
        else:
            return jsonify({'message': 'Camión no encontrado'}), 404

# /camiones: Insertar nuevo set de camiones como csv (insertdb function) DO NOT DO THIS FOR NOW
#@app.route('/camiones/insert', methods=['DELETE'])

# /camiones/<camion-id>: Obtener el contenido de un camión por ID (Join tabla camiones y camionesContenido)
@app.route('/camionesGet/<camion_id>', methods=['GET'])
def get_all_camiones_contenido(camion_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Ejecutar el query para obtener todo el contenido de camionesContenido
        cursor.execute('SELECT * FROM camionesContenido WHERE Carga = ?', (camion_id,))
        
        # Obtener todas las filas del resultado
        contenido_camion = cursor.fetchall()
        
        # Convertir cada fila a diccionario y devolver como JSON
        return jsonify([dict(row) for row in contenido_camion]), 200

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


# /demanda: Insertar nuevo set de demanda como csv (insert_db function)
@app.route('/demanda/insert', methods=['POST'])
def insert_demanda():
    try:
        # Ensure a file is provided in the request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        
        # Verify file format
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Only CSV files are allowed"}), 400

        # Save the file temporarily
        temp_file_path = os.path.join('uploads', file.filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(temp_file_path)

        # Process the CSV file
        df = pd.read_csv(temp_file_path)

        # Ensure required columns exist
        required_columns = ["Orden", "Articulo", "Cantidad solicitada", "Precio de venta", "orderdtlstatus"]
        if not all(col in df.columns for col in required_columns):
            return jsonify({"error": f"Missing required columns. Expected: {required_columns}"}), 400

        # Filter rows where 'orderdtlstatus' == 'Created'
        df = df[df['orderdtlstatus'] == 'Created']
        df = df[["Orden", "Articulo", "Cantidad solicitada", "Precio de venta"]]

        # Group by 'Orden' and 'Articulo', then pivot
        df_grouped = df.groupby(['Orden', 'Articulo'])['Cantidad solicitada'].sum().reset_index()
        df_pivot = df_grouped.pivot(index='Orden', columns='Articulo', values='Cantidad solicitada').fillna(0)
        df_pivot.reset_index(inplace=True)

        # Calculate total price per order
        total_price = df.groupby('Orden')['Precio de venta'].sum().reset_index()
        total_price = total_price.rename(columns={'Precio de venta': 'PrecioVentaTotal'})

        # Merge total price with pivoted order data
        df_final = pd.merge(df_pivot, total_price, on='Orden', how='left')

        # Insert into the database
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Prepare insert statement
            for _, row in df_final.iterrows():
                # Prepare columns for pivoted items
                item_columns = ', '.join([f'"{str(col)}"' for col in df_pivot.columns if col != 'Orden'])
                item_values = ', '.join([str(row[col]) if col in row else '0' for col in df_pivot.columns if col != 'Orden'])

                # Insert query
                query = f'''
                    INSERT INTO demanda (Orden, {item_columns}, PrecioVentaTotal)
                    VALUES (?, {item_values}, ?)
                '''
                cursor.execute(query, (row['Orden'], row['PrecioVentaTotal']))

            conn.commit()

        # Remove temporary file
        os.remove(temp_file_path)

        return jsonify({"message": "Data inserted successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

# Modelo: Correr algoritmo con una lista de IDCamiones
@app.route('/modelo/ids', methods=['POST'])
def modelo_with_ids():
    try:
        data = request.get_json()

        if not data or 'IDCamiones' not in data:
            return jsonify({'message': 'Invalid input. Provide a list of IDCamiones.'}), 400

        id_camiones = data['IDCamiones']

        # Fetch camiones and demanda data
        camiones_df, demanda_df = fetch_data_from_db()

        if camiones_df.empty or demanda_df.empty:
            return jsonify({'message': 'No data found for trucks or demand.'}), 400

        # Filter camiones_df to only include rows matching the provided IDs
        camiones_df = camiones_df[camiones_df['Carga'].isin(id_camiones)]

        if camiones_df.empty:
            return jsonify({'message': 'No matching trucks found for provided IDs.'}), 404

        # Run the genetic algorithm with the filtered data
        mejor_individuo, tiempo_total_ganador = algoritmo_genetico_experiment(camiones_df, demanda_df)

        result = {
            'mejor_individuo': mejor_individuo,  # List of trucks assigned to each bay
            'tiempo_total_ganador': tiempo_total_ganador  # Total time for the best solution
        }
        
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# Punto de entrada
if __name__ == '__main__':
    app.run(debug=True)
