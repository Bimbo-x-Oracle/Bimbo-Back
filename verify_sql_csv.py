import sqlite3
import pandas as pd
import numpy as np

# SQLite connection
def connect_to_db(db_path):
    conn = sqlite3.connect(db_path)
    return conn

# Fetch data from SQL database for 'demanda' and 'camiones'
def fetch_sql_data(conn):
    demanda_query = "SELECT * FROM demanda"  # Replace with your actual table and columns
    camiones_query = "SELECT * FROM camionesContenido"  # Replace with your actual table and columns

    demanda_df = pd.read_sql(demanda_query, conn)
    camiones_df = pd.read_sql(camiones_query, conn)

    return demanda_df, camiones_df

# Load data from CSV files
def load_csv_data(demanda_csv, camiones_csv):
    demanda_df = pd.read_csv(demanda_csv)
    camiones_df = pd.read_csv(camiones_csv)

    return demanda_df, camiones_df


# Normalize column names (strip spaces, convert to lowercase)
def normalize_column_names(df):
    df.columns = [col.strip().lower() for col in df.columns]  # Convert to lowercase and strip spaces
    return df

# Mapping to fix known column name mismatches
def fix_column_names(df, table_name):
    if table_name == "demanda":
        df = df.rename(columns={"precio de venta total": "precioventatotal"})  # Fix column name mismatch
    elif table_name == "camiones":
        df = df.rename(columns={"fecha de cierre": "fechacierre", "carga": "carga"})  # Fix column name mismatch
    return df

# Compare two dataframes row by row, column by column
# Compare two dataframes row by row, column by column
def compare_dataframes(df1, df2, table_name):
    # Normalize columns
    df1 = normalize_column_names(df1)
    df2 = normalize_column_names(df2)
    
    # Fix known mismatches in column names
    df1 = fix_column_names(df1, table_name)
    df2 = fix_column_names(df2, table_name)

    if df1.shape != df2.shape:
        print(f"Data mismatch in {table_name}: Different shapes")
        print(f"Database shape: {df1.shape}")
        print(f"CSV shape: {df2.shape}")
        return False

    # Ensure the columns are in the same order
    if list(df1.columns) != list(df2.columns):
        print(f"Data mismatch in {table_name}: Columns do not match")
        print(f"Database columns: {list(df1.columns)}")
        print(f"CSV columns: {list(df2.columns)}")
        return False

    # Check for data differences
    if not np.array_equal(df1.values, df2.values):
        print(f"Data mismatch in {table_name}: Row data does not match")
        # Get the rows where there is a difference
        diff = df1 != df2
        diff_rows = diff[diff.any(axis=1)]

        # Print mismatches with actual (SQL) vs expected (CSV) values
        for row_idx in diff_rows.index:
            print(f"\nRow {row_idx} mismatch in {table_name}:")
            for col in diff_rows.columns:
                if diff_rows.at[row_idx, col]:
                    print(f"  Column: {col}")
                    print(f"    SQL Value: {df1.at[row_idx, col]}")
                    print(f"    CSV Value: {df2.at[row_idx, col]}")

        return False

    print(f"Data in {table_name} matches perfectly.")
    return True

# Main function to run the checks
def verify_data(db_path, demanda_csv, camiones_csv):
    # Connect to the SQLite database
    conn = connect_to_db(db_path)

    # Fetch data from SQL
    demanda_sql, camiones_sql = fetch_sql_data(conn)

    # Load CSV data
    demanda_csv_data, camiones_csv_data = load_csv_data(demanda_csv, camiones_csv)

    # Compare the SQL data with the CSV data
    print("Verifying 'demanda' data...")
    compare_dataframes(demanda_sql, demanda_csv_data, "demanda")

    print("\nVerifying 'camiones' data...")
    compare_dataframes(camiones_sql, camiones_csv_data, "camiones")

    # Close database connection
    conn.close()

if __name__ == "__main__":
    # Define paths
    db_path = "data/database.db"  # Update with the actual path to your SQLite DB
    demanda_csv = "data/output_data/ordenes_demanda_cleanformat.csv"  # Update with the actual path to your CSV file
    camiones_csv = "data/output_data/pending_camiones_cleanformat.csv"  # Update with the actual path to your CSV file

    # Run the verification
    verify_data(db_path, demanda_csv, camiones_csv)
