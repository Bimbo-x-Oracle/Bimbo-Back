import sqlite3

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

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
