import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print(f"Error: No se pudieron cargar las variables de entorno desde {dotenv_path}")
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        table_name_to_find = "propuestas"

        # Usar una llamada a una función de base de datos (RPC) para consultar el esquema
        # Esta función ejecuta una consulta SQL para obtener los nombres de las columnas
        print(f"Consultando columnas para la tabla '{table_name_to_find}'...")
        
        # La función RPC ejecutará una consulta SQL en el servidor
        # para obtener los nombres de las columnas de la tabla especificada.
        # Esto es más seguro y directo que intentar adivinar la URL de la API del esquema.
        response = supabase.rpc(
            'get_table_columns',
            {'p_table_name': table_name_to_find}
        ).execute()

        # El siguiente bloque de código es una función SQL que se debe crear en Supabase
        # para que la llamada RPC funcione. El usuario deberá crearla desde el editor SQL.
        # 
        # CREATE OR REPLACE FUNCTION get_table_columns(p_table_name TEXT)
        # RETURNS TABLE(column_name TEXT, data_type TEXT) AS $$
        # BEGIN
        #     RETURN QUERY
        #     SELECT
        #         isc.column_name::TEXT,
        #         isc.data_type::TEXT
        #     FROM
        #         information_schema.columns AS isc
        #     WHERE
        #         isc.table_schema = 'public' AND
        #         isc.table_name = p_table_name;
        # END;
        # $$ LANGUAGE plpgsql;

        if response.data:
            print(f"\n--- Columnas de la tabla '{table_name_to_find}' ---")
            # La respuesta será una lista de diccionarios, cada uno con 'column_name' y 'data_type'
            for col_info in sorted(response.data, key=lambda x: x['column_name']):
                print(f"- {col_info['column_name']} (Tipo: {col_info['data_type']})")
            print("----------------------------------------")
        else:
            print(f"No se pudieron obtener las columnas para la tabla '{table_name_to_find}'.")
            print("Por favor, asegúrese de que la tabla existe y que la función 'get_table_columns' está creada en Supabase.")

    except Exception as e:
        # Capturar el error específico de la base de datos si está disponible
        if 'message' in str(e):
            import json
            error_details = json.loads(str(e))
            print(f"Error de Supabase: {error_details.get('message')}")
            if error_details.get('hint') and "does not exist" in error_details.get('hint'):
                 print("\n[!] Pista: Parece que la función 'get_table_columns' no existe en tu base de datos.")
                 print("Por favor, ve al Editor SQL de Supabase y ejecuta el código SQL que se encuentra comentado en el script.")
        else:
            print(f"Ocurrió un error inesperado: {e}")
