import argparse
import json
import os
from pdf_formatter import generate_pdf
import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a PDF from factoring details.")
    parser.add_argument("--output_filepath", required=True, help="The full path to save the output PDF.")
    parser.add_argument("--json_filepath", required=True, help="The full path to the JSON file containing the invoice data.")
    
    args = parser.parse_args()

    # Leer los datos desde el archivo JSON
    with open(args.json_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # --- SOLUCIÓN TEMPORAL: Inyectar valores correctos de invoice_net_amount ---
    # Esto es para depuración y debe ser eliminado una vez que el JSON de origen sea correcto.
    for item in data.get('facturas', []):
        if item.get('invoice_series_and_number') == 'E001-677':
            item['invoice_net_amount'] = 8178.82
        elif item.get('invoice_series_and_number') == 'E001-678':
            item['invoice_net_amount'] = 6456.96
    # --- FIN SOLUCIÓN TEMPORAL ---

    output_dir = os.path.dirname(args.output_filepath)
    output_filename = os.path.basename(args.output_filepath)
    name, ext = os.path.splitext(output_filename)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    new_output_filename = f"{name}_{timestamp}{ext}"
    new_output_filepath = os.path.join(output_dir, new_output_filename)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        generate_pdf(new_output_filepath, data)
    except Exception as e:
        print(f"Error generating PDF: {e}")