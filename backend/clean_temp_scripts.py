import os

files_to_delete = [
    "C:/Users/rguti/Inandes.TECH/backend/delete_xml_parser.py",
    "C:/Users/rguti/Inandes.TECH/backend/create_recycle_dir.py",
    "C:/Users/rguti/Inandes.TECH/backend/move_xml_parser.py"
]

for file_path in files_to_delete:
    try:
        os.remove(file_path)
        print(f"Archivo {file_path} eliminado exitosamente.")
    except FileNotFoundError:
        print(f"Advertencia: El archivo {file_path} no fue encontrado (ya podría haber sido eliminado).")
    except Exception as e:
        print(f"Error al eliminar el archivo {file_path}: {e}")
