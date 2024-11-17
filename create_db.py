import sqlite3

# SQLite database setup
DB_PATH = './data/database.db'

# Initialize database and create tables
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                UsuarioID INTEGER PRIMARY KEY AUTOINCREMENT,
                Usuario TEXT UNIQUE,
                Password TEXT,
                NombreCompleto TEXT,
                Rol TEXT, 
                Foto TEXT
            )
        ''')
        
        # Camiones table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camiones (
                CamionID TEXT PRIMARY KEY,
                Placa TEXT,
                ConductorID INTEGER,
                NumeroRemolques INTEGER,
                HoraLlegada TEXT,
                Estado TEXT,
                LugarEstacionamiento TEXT,
                FOREIGN KEY (ConductorID) REFERENCES usuarios (UsuarioID)
            )
        ''')

         # Demanda Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS demanda (
                Orden INTEGER PRIMARY KEY,
                "800" INTEGER, "2530" INTEGER, "6011" INTEGER, "6444" INTEGER, "31090" INTEGER,
                "31811" INTEGER, "35549" INTEGER, "38447" INTEGER, "38582" INTEGER, "38585" INTEGER,
                "38612" INTEGER, "45973" INTEGER, "48205" INTEGER, "123051" INTEGER, "123052" INTEGER,
                "123258" INTEGER, "123308" INTEGER, "123310" INTEGER, "123316" INTEGER, "124239" INTEGER,
                "124358" INTEGER, "124381" INTEGER, "124382" INTEGER, "124440" INTEGER, "124443" INTEGER,
                "124445" INTEGER, "124447" INTEGER, "124543" INTEGER, "124699" INTEGER, "124824" INTEGER,
                "125030" INTEGER, "125031" INTEGER, "125034" INTEGER, "125056" INTEGER, "125191" INTEGER,
                "125192" INTEGER, "125193" INTEGER, "126133" INTEGER, "126135" INTEGER, "126312" INTEGER,
                "126471" INTEGER, "126473" INTEGER, "126475" INTEGER, "126481" INTEGER, "126483" INTEGER,
                "126485" INTEGER, "126497" INTEGER, "126578" INTEGER, "126736" INTEGER, "126894" INTEGER,
                "126895" INTEGER, "126950" INTEGER, "127111" INTEGER, "127114" INTEGER, "127263" INTEGER,
                "127264" INTEGER, "127436" INTEGER, "127548" INTEGER, "127550" INTEGER, "127556" INTEGER,
                "127571" INTEGER, "127575" INTEGER, "127577" INTEGER, "127711" INTEGER, "127802" INTEGER,
                "127923" INTEGER, "127924" INTEGER, "127925" INTEGER, "127995" INTEGER, "128192" INTEGER,
                "128193" INTEGER, "128317" INTEGER, "128318" INTEGER, "128319" INTEGER, "128343" INTEGER,
                "128375" INTEGER, "128376" INTEGER, "128377" INTEGER, "128378" INTEGER, "128429" INTEGER,
                "128430" INTEGER, "128431" INTEGER, "128432" INTEGER, "128450" INTEGER, "128477" INTEGER,
                "128501" INTEGER, "128504" INTEGER, "128588" INTEGER, "128715" INTEGER, "128729" INTEGER,
                "128771" INTEGER, "128814" INTEGER, "128940" INTEGER, "128941" INTEGER, "128942" INTEGER,
                "514419" INTEGER, "514472" INTEGER, "514475" INTEGER, "514480" INTEGER, "514483" INTEGER,
                "514490" INTEGER, "514491" INTEGER, "514494" INTEGER, "514506" INTEGER, "514507" INTEGER,
                "514536" INTEGER, "514537" INTEGER, "514568" INTEGER, "514578" INTEGER, "514649" INTEGER,
                "514719" INTEGER, "514840" INTEGER, "514846" INTEGER, "514853" INTEGER, "514854" INTEGER,
                "514855" INTEGER, "514859" INTEGER, "514861" INTEGER, "514862" INTEGER, "514863" INTEGER,
                "514865" INTEGER, "514866" INTEGER, "514867" INTEGER, "514879" INTEGER, "514881" INTEGER,
                "514882" INTEGER, "514903" INTEGER, "514913" INTEGER, "514926" INTEGER, "514929" INTEGER,
                "514949" INTEGER, "514950" INTEGER, "514961" INTEGER, "514976" INTEGER, "514988" INTEGER,
                "515007" INTEGER, "515069" INTEGER, "515101" INTEGER, "515108" INTEGER, "515120" INTEGER,
                "515122" INTEGER, "515123" INTEGER,
                PrecioVentaTotal REAL
            )
        ''')
        
        # CamionesContenido Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS camionesContenido (
                Carga TEXT,
                Pallet INTEGER,
                FechaCierre TEXT,
                "124440" INTEGER, "124543" INTEGER, "126475" INTEGER, "126800" INTEGER, "126894" INTEGER,
                "127550" INTEGER, "127556" INTEGER, "127571" INTEGER, "127575" INTEGER, "127802" INTEGER,
                "127923" INTEGER, "127924" INTEGER, "127925" INTEGER, "128193" INTEGER, "128378" INTEGER,
                "128431" INTEGER, "128432" INTEGER, "128450" INTEGER, "128715" INTEGER, "31811" INTEGER,
                "44825" INTEGER, "48205" INTEGER, "514475" INTEGER, "514494" INTEGER, "514496" INTEGER,
                "514719" INTEGER, "514846" INTEGER, "514855" INTEGER, "514863" INTEGER, "514866" INTEGER,
                "514867" INTEGER, "514926" INTEGER, "514929" INTEGER, "514949" INTEGER, "514950" INTEGER,
                "515101" INTEGER, "515108" INTEGER, "515120" INTEGER, "515122" INTEGER, "515123" INTEGER,
                C3H INTEGER,
                CB2 INTEGER,
                CT1 INTEGER,
                TARIMA INTEGER
            )
        ''')
        # Productos Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                ProductoID INTEGER PRIMARY KEY,
                Nombre TEXT,
                Precio INTEGER
            )
        ''')

        conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
