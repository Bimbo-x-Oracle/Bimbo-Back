import pandas as pd
import sqlite3
from datetime import datetime
import os
import random

## Lista de nombres de choferes y URLs para fotos
nombres = ["Rubí", "Raúl", "Rafael", "Sebastián", "Gustavo", "Gus", "Daniel", "Pablo", "Daniela", "Humberto", "Mariluz", "Alejandro", "Emiliano"]
fotos = [
    "https://example.com/foto_rubi.png",
    "https://example.com/foto_raul.png",
    "https://example.com/foto_rafael.png",
    "https://example.com/foto_sebastian.png",
    "https://example.com/foto_gustavo.png",
    "https://example.com/foto_gus.png",
    "https://example.com/foto_daniel.png",
    "https://example.com/foto_pablo.png",
    "https://example.com/foto_daniela.png",
    "https://example.com/foto_humberto.png",
    "https://example.com/foto_mariluz.png",
    "https://example.com/foto_alejandro.png",
    "https://example.com/foto_emiliano.png"
]

# Database path
DB_PATH = './data/database.db'

# Function to process and insert data into camionesContenido table
def process_and_insert_pending(file_path):
    # Load CSV
    df = pd.read_csv(file_path)

    # Keep specific columns
    df = df[["FECHA DE CIERRE", "CARGA", "ITEM", "CANTIDAD"]]

    # Create new DataFrame 'dft' with 'FECHA DE CIERRE' and 'CARGA' columns only
    dft = df[["FECHA DE CIERRE", "CARGA"]]

    # Count occurrences of each unique value in 'CARGA'
    dfv = df["CARGA"].value_counts().reset_index()
    dfv.columns = ['CARGA', 'Pallet']

    # Group data by 'CARGA' and 'ITEM' and sum 'CANTIDAD'
    df_grouped = df.groupby(['CARGA', 'ITEM']).agg({'CANTIDAD': 'sum'}).reset_index()

    # Create pivot table with 'CARGA' as rows, 'ITEM' as columns, and sum of 'CANTIDAD' as values
    dfl = df_grouped.pivot_table(index='CARGA', columns='ITEM', values='CANTIDAD', fill_value=0)
    dfl.reset_index(inplace=True)

    # Merge unique dates and load counts with pivot table
    df_final = pd.merge(dft.drop_duplicates(), dfl, on='CARGA', how="inner")
    df_final = pd.merge(dfv, df_final, on='CARGA', how="inner")

    # Rename column 'count' to 'Pallet'
    df_final = df_final.rename(columns={'Pallet': 'Pallet'})

    # Convert 'FECHA DE CIERRE' to datetime
    df_final['FECHA DE CIERRE'] = pd.to_datetime(df_final['FECHA DE CIERRE'], format='%d/%m/%Y %H:%M:%S')
    df_final['FECHA DE CIERRE'] = ((datetime.now() - df_final['FECHA DE CIERRE']).dt.total_seconds() / 60).apply(lambda x: int(x))
    df_final["FECHA DE CIERRE"] = df_final["FECHA DE CIERRE"].abs()

    # Insert data into the database
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for _, row in df_final.iterrows():
            # Prepare values for camionesContenido table
            values = (row['CARGA'], row['Pallet'], int(row['FECHA DE CIERRE']))
            
            # Quote columns that are numeric strings for SQL syntax compatibility
            item_columns = ', '.join([f'"{str(item)}"' for item in dfl.columns if item != 'CARGA'])
            item_values = ', '.join([str(row[item]) if item in row else '0' for item in dfl.columns if item != 'CARGA'])
            
            query = f'''
                INSERT INTO camionesContenido (Carga, Pallet, FechaCierre, {item_columns})
                VALUES (?, ?, ?, {item_values})
            '''
            cursor.execute(query, values)
        conn.commit()

    print("Pending data inserted successfully into camionesContenido table.")

# Function to process and insert data into demanda table
def process_and_insert_demand(file_path):
    # Load CSV
    df = pd.read_csv(file_path)

    # Keep required columns and filter rows where 'orderdtlstatus' == 'Created'
    df = df[df['orderdtlstatus'] == 'Created']
    df = df[["Orden", "Articulo", "Cantidad solicitada", "Precio de venta"]]

    # Group by 'Orden' and 'Articulo' to sum quantities, then pivot
    df_grouped = df.groupby(['Orden', 'Articulo'])['Cantidad solicitada'].sum().reset_index()
    df_pivot = df_grouped.pivot(index='Orden', columns='Articulo', values='Cantidad solicitada').fillna(0)
    df_pivot.reset_index(inplace=True)

    # Calculate total price per order
    total_price = df.groupby('Orden')['Precio de venta'].sum().reset_index()
    total_price = total_price.rename(columns={'Precio de venta': 'PrecioVentaTotal'})

    # Merge total price data with pivoted order data
    df_final = pd.merge(df_pivot, total_price, on='Orden', how='left')

    # Insert data into the database
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for _, row in df_final.iterrows():
            # Prepare values for demanda table
            values = (row['Orden'], row['PrecioVentaTotal'])
            
            # Quote columns that are numeric strings for SQL syntax compatibility
            item_columns = ', '.join([f'"{str(item)}"' for item in df_pivot.columns if item != 'Orden'])
            item_values = ', '.join([str(row[item]) if item in row else '0' for item in df_pivot.columns if item != 'Orden'])
            
            query = f'''
                INSERT INTO demanda (Orden, {item_columns}, PrecioVentaTotal)
                VALUES (?, {item_values}, ?)
            '''
            cursor.execute(query, values)
        conn.commit()

    print("Demand data inserted successfully into demanda table.")

def process_and_insert_trucks():
    """
    # CamionID: should be an item from pending_camiones_cleanformat.csv CARGA column
    # Placa: randomly generate license plate
    # ConductorID: count+1
    # NumeroRemolques: random1-2
    # HoraLlegada: leave at null for now, value changes in app
    # Estado: leave at "EnFabrica", value changes in app
    # LugarEstacionamiento: leave at null for now, value changes in app
    """
    # Insert data into the database for camiones table
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Get a list of CARGA values from pending data
        cursor.execute("SELECT DISTINCT Carga FROM camionesContenido")
        camiones_data = cursor.fetchall()
        
        # Generate trucks data
        for camion in camiones_data:
            camion_id = camion[0]
            placa = f"{random.choice(['ABC', 'XYZ', 'LMN'])}-{random.randint(100, 999)}"  # Random license plate
            conductor_id = random.randint(1, len(nombres))  # Random conductor ID (assuming users are in a list)
            numero_remolques = random.randint(1, 2)  # Random number of trailers (1 or 2)
            hora_llegada = None  # Leaving it null for now
            estado = "EnFabrica"
            lugar_estacionamiento = None  # Leaving it null for now
            
            # Insert into camiones table
            query = '''
                INSERT INTO camiones (CamionID, Placa, ConductorID, NumeroRemolques, HoraLlegada, Estado, LugarEstacionamiento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (camion_id, placa, conductor_id, numero_remolques, hora_llegada, estado, lugar_estacionamiento))
        
        conn.commit()
    print("Trucks data inserted successfully into camiones table.")

def process_and_insert_users():
    # Insert data into the database for usuarios table
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # UsuarioID: count+1
        # Usuario: randomly generate username
        # Password: password123
        # NombreCompleto: randomly pick from nombres list
        # Rol: randomly pick from "Conductor", "Supervisor", "Administrador"
        # Foto: randomly pick from fotos list

        # Generate user data
        for user_id in range(1, len(nombres) + 1):  # We generate one user per name in the list
            usuario = f"user{user_id}"  # Generating username
            password = "password123"  # Default password
            nombre_completo = nombres[user_id - 1]  # Pick name from list
            rol = random.choice(["Conductor", "Supervisor", "Administrador"])  # Random role
            foto = fotos[user_id - 1]  # Pick photo from the list
            
            # Insert into usuarios table
            query = '''
                INSERT INTO usuarios (UsuarioID, Usuario, Password, NombreCompleto, Rol, Foto)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (user_id, usuario, password, nombre_completo, rol, foto))
        
        conn.commit()
    print("Users data inserted successfully into usuarios table.")

# Main function to call for processing and inserting data
def main():
    input_dir = "data/original_bimbo_data"
    process_and_insert_pending(os.path.join(input_dir, "Pendientes.csv"))
    process_and_insert_demand(os.path.join(input_dir, "Ordenes.csv"))
    process_and_insert_users()
    process_and_insert_trucks()

if __name__ == '__main__':
    main()