import csv
import random
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
import pandas as pd
import os
from modelo_noAlmacenSQL import algoritmo_genetico_experiment, fetch_data_from_db

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Variables en memoria
listaInicial = []
nuevasFosas = []
inicializado = False
listaFueraFosas = []

# Path a base de datos SQLite
DB_PATH = './data/database.db'

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
        cursor.execute('SELECT NombreCompleto, Password, Rol, Foto FROM usuarios WHERE Usuario = ?', (usuario,))
        row = cursor.fetchone()

        if row and check_password_hash(row[1], password):
            return jsonify({'message': 'Login exitoso', 'NombreCompleto': row[0], 'Rol': row[2], 'Foto': row[3]}), 200
        else:
            return jsonify({'message': 'Credenciales incorrectas'}), 401


# Función para generar un lugar de estacionamiento aleatorio
def generar_lugar_estacionamiento():
    digito = random.randint(1, 9)  # Número de 1 a 9
    letra = chr(random.randint(65, 90))  # Letra de A a Z (ASCII)
    return f"{digito}{letra}"

# /camiones: Obtener el contenido de un camión por ID (Join tabla camiones y camionesContenido)
@app.route('/camiones/<camion_id>', methods=['GET'])
def get_camion(camion_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Consulta para obtener información del camión y contenido
        cursor.execute('''
            SELECT c.CamionID, c.Placa, c.ConductorID, c.NumeroRemolques, c.HoraLlegada, c.Estado, cc.*
            FROM camiones c
            JOIN camionesContenido cc ON c.CamionID = cc.Carga
            WHERE c.CamionID = ?
        ''', (camion_id,))
        
        trucks = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        
        if not trucks:
            return jsonify({'message': 'Camión no encontrado'}), 404
        
        # Obtener el ID del conductor
        conductor_id = trucks[0][2]
        
        # Consulta para obtener el nombre del conductor
        cursor.execute('''
            SELECT NombreCompleto, Foto
            FROM usuarios
            WHERE UsuarioID = ?
        ''', (conductor_id,))
        conductor = cursor.fetchone()
        nombre_conductor = conductor[0] if conductor else "Desconocido"
        foto_usuario = conductor[1] if conductor else "Sin Imagen"
        
        # Construcción de los datos del camión
        truck_data = {
            'CamionID': trucks[0][0],
            'Placa': trucks[0][1],
            'NombreConductor': nombre_conductor,
            'Foto' : foto_usuario,
            'Contenido': []
        }

        # Obtener los IDs únicos de productos
        product_ids = []
        for truck in trucks:
            for i, column in enumerate(columns[6:], start=6):
                if truck[i] != None and column.isdigit():
                    product_ids.append(column)
        
        product_ids = list(set(product_ids))  # Eliminar duplicados
        
        # Consulta para obtener nombres de productos
        if product_ids:
            placeholders = ', '.join('?' for _ in product_ids)
            cursor.execute(f'''
                SELECT ProductoID, Nombre, Precio
                FROM productos
                WHERE ProductoID IN ({placeholders})
            ''', product_ids)
            product_names = {str(row[0]): row[1] for row in cursor.fetchall()}
        else:
            product_names = {}

        # Procesar contenido y evitar duplicados
        for truck in trucks:
            for i, column in enumerate(columns[6:], start=6):
                if truck[i] != 0 and column.isdigit():
                    nombre_producto = product_names.get(column, column)
                    if not any(item['NombreProducto'] == nombre_producto for item in truck_data['Contenido']):
                        truck_data['Contenido'].append({"NombreProducto": nombre_producto, "Cantidad": truck[i]})
        
        return jsonify(truck_data), 200
        
# /camiones/: Obtener una lista de camiones enEspera con su contenido
@app.route('/camiones/enespera', methods=['GET'])
def get_all_camion():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Consulta para obtener camiones en espera y su contenido
        cursor.execute('''
            SELECT c.CamionID, c.Placa, c.ConductorID, c.NumeroRemolques, c.HoraLlegada, c.Estado, cc.*
            FROM camiones c
            JOIN camionesContenido cc ON c.CamionID = cc.Carga
            WHERE c.Estado = "enEspera"
        ''')
        
        trucks = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        
        if not trucks:
            return jsonify({'message': 'No hay camiones en espera'}), 404

        # Obtener los IDs únicos de productos
        product_ids = []
        for truck in trucks:
            for i, column in enumerate(columns[6:], start=6):
                if truck[i] != None and column.isdigit():
                    product_ids.append(column)
        
        product_ids = list(set(product_ids))  # Eliminar duplicados
        
        # Consulta para obtener nombres de productos
        if product_ids:
            placeholders = ', '.join('?' for _ in product_ids)
            cursor.execute(f'''
                SELECT ProductoID, Nombre, Precio
                FROM productos
                WHERE ProductoID IN ({placeholders})
            ''', product_ids)
            product_names = {str(row[0]): row[1] for row in cursor.fetchall()}
        else:
            product_names = {}

        # Procesar cada camión por separado
        camiones_en_espera = {}
        for truck in trucks:
            camion_id = truck[0]
            placa = truck[1]
            conductor_id = truck[2]
            
            # Obtener nombre del conductor (si no está en caché)
            if camion_id not in camiones_en_espera:
                cursor.execute('''
                    SELECT NombreCompleto
                    FROM usuarios
                    WHERE UsuarioID = ?
                ''', (conductor_id,))
                conductor = cursor.fetchone()
                nombre_conductor = conductor[0] if conductor else "Desconocido"
                
                # Inicializar datos del camión
                camiones_en_espera[camion_id] = {
                    'CamionID': camion_id,
                    'Placa': placa,
                    'NombreConductor': nombre_conductor,
                    'Contenido': []
                }
            
            # Agregar contenido al camión actual
            for i, column in enumerate(columns[6:], start=6):
                if truck[i] != 0 and column.isdigit():
                    nombre_producto = product_names.get(column, column)
                    contenido = camiones_en_espera[camion_id]['Contenido']
                    
                    # Verificar si ya existe el producto, acumular cantidades si es necesario
                    producto_existente = next((p for p in contenido if p['NombreProducto'] == nombre_producto), None)
                    if producto_existente:
                        producto_existente['Cantidad'] += truck[i]
                    else:
                        contenido.append({"NombreProducto": nombre_producto, "Cantidad": truck[i]})

        # Convertir los datos a lista para el JSON final
        return jsonify(list(camiones_en_espera.values())), 200

# /camiones: Insertar nuevo set de camiones como csv (insertdb function) DO NOT DO THIS FOR NOW
#@app.route('/camiones/insert', methods=['DELETE'])

# /camiones: Registrar camiones en el patio, entrada por seguridad
@app.route('/camiones/inout/<camion_id>', methods=['PUT'])
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
                return jsonify({'message': f'Camión {camion_id} ya no está en espera, estado actualizado a Out.'}), 200
        else:
            return jsonify({'message': 'Camión no encontrado'}), 404


# /camiones: Actualizar el estado de descarga de un camión (descargado)
@app.route('/camiones/descargar/<camion_id>', methods=['PUT'])
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
        # TODO Actualizar la demanda con la resta de la lista de productos del camion 
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
        return jsonify({'message': 'Camión no está en estado Bahia.'}), 400

# Read: Ver la demanda (información en tabla de demanda)
@app.route('/demanda/list', methods=['GET'])
def get_demanda():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Primera consulta: obtener todos los datos de demanda
        cursor.execute('SELECT * FROM demanda')
        demanda_data = cursor.fetchall()
        columns = [col[0] for col in cursor.description]  # Nombres de las columnas

        if not demanda_data:
            return jsonify({'message': 'No hay demanda disponible.'}), 404

        # Identificar columnas que son IDs de productos (números)
        product_ids = [col for col in columns if col.isdigit()]

        # Filtrar productos con cantidades mayores a 0
        demanda_filtrada = []
        for row in demanda_data:
            for product_id in product_ids:
                idx = columns.index(product_id)
                cantidad = row[idx]
                if cantidad and cantidad > 0:  # Si hay demanda para este producto
                    demanda_filtrada.append((product_id, cantidad))

        if not demanda_filtrada:
            return jsonify({'message': 'No hay productos con demanda disponible.'}), 404

        # Segunda consulta: obtener nombres de los productos
        product_ids = [item[0] for item in demanda_filtrada]
        placeholders = ', '.join('?' for _ in product_ids)
        query = f"""
            SELECT ProductoID, Nombre
            FROM productos
            WHERE ProductoID IN ({placeholders})
        """
        cursor.execute(query, product_ids)
        product_names = {str(row[0]): row[1] for row in cursor.fetchall()}

        # Construir la lista de demanda
        demand_list = [
            {"NombreProducto": product_names.get(product_id, "Producto desconocido"), "Cantidad": cantidad}
            for product_id, cantidad in demanda_filtrada
        ]

        return jsonify({"Demanda": demand_list}), 200


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
@app.route('/modelo/custom', methods=['POST'])
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

# VARIABLES GLOBALES

# Ultima esperanza: Gets de variables global
# GET: Obtener "listaInicial"
@app.route('/listaInicial', methods=['GET'])
def get_lista_inicial():
    return jsonify({listaInicial}), 200

# GET: Obtener "nuevasFosas"
@app.route('/nuevasFosas', methods=['GET'])
def get_nuevas_fosas():
    return jsonify({nuevasFosas}), 200

# GET: Obtener "inicializado"
@app.route('/inicializado', methods=['GET'])
def get_inicializado():
    return jsonify({inicializado}), 200

# GET: Obtener "listaFueraFosas"
@app.route('/listaFueraFosas', methods=['GET'])
def get_lista_fuera_fosas():
    return jsonify({listaFueraFosas}), 200

# Ultima esperanza: Post de variables global
# POST: Modificar "listaInicial"
@app.route('/listaInicial', methods=['POST'])
def update_lista_inicial():
    global listaInicial

    # Validar que el cuerpo sea un JSON Array
    if not isinstance(request.json, list):
        return jsonify({"error": "'listaInicial' debe ser un array de objetos"}), 400

    # Actualizar la variable global
    listaInicial = request.json
    return jsonify({"message": "'listaInicial' actualizada", "listaInicial": listaInicial}), 200

# POST: Modificar "nuevasFosas"
@app.route('/nuevasFosas', methods=['POST'])
def update_nuevas_fosas():
    global nuevasFosas

    # Validar que el cuerpo sea un JSON Array y todos los elementos sean strings
    if not isinstance(request.json, list) or not all(isinstance(i, str) for i in request.json):
        return jsonify({"error": "'nuevasFosas' debe ser un array de strings"}), 400

    # Actualizar la variable global
    nuevasFosas = request.json
    return jsonify({"message": "'nuevasFosas' actualizada", "nuevasFosas": nuevasFosas}), 200

# POST: Modificar "inicializado"
@app.route('/inicializado', methods=['POST'])
def update_inicializado():
    global inicializado

    # Validar que el cuerpo sea un booleano (no un array)
    if not isinstance(request.json, bool):
        return jsonify({"error": "'inicializado' debe ser un booleano"}), 400

    # Actualizar la variable global
    inicializado = request.json
    return jsonify({"message": "'inicializado' actualizado", "inicializado": inicializado}), 200

# POST: Modificar "listaFueraFosas"
@app.route('/listaFueraFosas', methods=['POST'])
def update_lista_fuera_fosas():
    global listaFueraFosas

    # Validar que el cuerpo sea un JSON Array y todos los elementos sean objetos
    if not isinstance(request.json, list) or not all(isinstance(item, dict) for item in request.json):
        return jsonify({"error": "'listaFueraFosas' debe ser un array de objetos"}), 400

    # Actualizar la variable global
    listaFueraFosas = request.json
    return jsonify({"message": "'listaFueraFosas' actualizada", "listaFueraFosas": listaFueraFosas}), 200

# Punto de entrada
if __name__ == '__main__':
    app.run(debug=True)
