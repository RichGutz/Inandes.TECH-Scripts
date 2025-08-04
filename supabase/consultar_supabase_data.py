import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

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
        table_name = "propuestas"

        print(f"Consultando los primeros 5 registros de la tabla '{table_name}'...")
        response = supabase.table(table_name).select("*").limit(5).execute()

        if response.data:
            print(f"\n--- Primeros {len(response.data)} registros de la tabla '{table_name}' ---")
            print(json.dumps(response.data, indent=4, ensure_ascii=False))
            print("--------------------------------------------------")
        else:
            print(f"La tabla '{table_name}' está vacía. Por favor, guarda una propuesta desde la aplicación para poder consultar datos.")

    except Exception as e:
        print(f"Ocurrió un error al conectar o consultar Supabase: {e}")
