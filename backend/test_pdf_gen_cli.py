
import os
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from pdf_generator_v_cli import generate_pdf

# Cargar variables de entorno desde el .env en el directorio 'supabase'
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'supabase', '.env')
load_dotenv(dotenv_path=dotenv_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def fetch_latest_proposals(supabase_client, limit=5):
    """Fetches the most recent proposals from Supabase."""
    try:
        response = supabase_client.table('propuestas').select('*').order('fecha_emision_factura', desc=True).limit(limit).execute()
        if response.data:
            return response.data
        else:
            print("No proposals found in Supabase.")
            return []
    except Exception as e:
        print(f"Error fetching data from Supabase: {e}")
        return []

import pandas as pd

def create_consolidated_pdf_data(proposals):
    """Creates a consolidated data dictionary for the PDF generator from a list of proposals."""
    if not proposals:
        return None

    df = pd.DataFrame(proposals)

    # Convert numeric columns to numeric types, coercing errors
    numeric_cols = [
        'monto_neto_factura', 'capital_calculado', 'interes_calculado', 
        'igv_interes_calculado', 'abono_real_calculado', 'margen_seguridad_calculado',
        'comision_estructuracion_monto_calculado', 'igv_comision_estructuracion_calculado',
        'comision_afiliacion_monto_calculado', 'igv_afiliacion_calculado'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Consolidate data
    total_monto_neto = df['monto_neto_factura'].sum()
    total_capital_calculado = df['capital_calculado'].sum()
    total_interes_calculado = df['interes_calculado'].sum()
    total_igv_interes_calculado = df['igv_interes_calculado'].sum()
    total_abono_real_calculado = df['abono_real_calculado'].sum()
    total_margen_seguridad_calculado = df['margen_seguridad_calculado'].sum()
    total_comision_estructuracion_monto_calculado = df['comision_estructuracion_monto_calculado'].sum()
    total_igv_comision_estructuracion_calculado = df['igv_comision_estructuracion_calculado'].sum()
    total_comision_afiliacion_monto_calculado = df['comision_afiliacion_monto_calculado'].sum()
    total_igv_afiliacion_calculado = df['igv_afiliacion_calculado'].sum()

    facturas_list = df.to_dict('records')

    pdf_data = {
        'emisor_nombre': proposals[0].get('emisor_nombre'),
        'emisor_ruc': proposals[0].get('emisor_ruc'),
        'facturas': facturas_list,
        'total_monto_neto': f"{total_monto_neto:,.2f}",
        'detracciones_total': '0.00',  # Placeholder
        'total_neto': f"{total_monto_neto:,.2f}", # Placeholder
        'total_capital_calculado': f"{total_capital_calculado:,.2f}",
        'total_interes_calculado': f"{total_interes_calculado:,.2f}",
        'total_igv_interes_calculado': f"{total_igv_interes_calculado:,.2f}",
        'total_abono_real_calculado': f"{total_abono_real_calculado:,.2f}",
        'total_margen_seguridad_calculado': f"{total_margen_seguridad_calculado:,.2f}",
        'total_comision_estructuracion_monto_calculado': f"{total_comision_estructuracion_monto_calculado:,.2f}",
        'total_a_depositar': '0.00', # Placeholder
        'total_interes_pactados': f"{(total_interes_calculado + total_igv_interes_calculado):,.2f}",
        'total_comision_estructuracion': f"{(total_comision_estructuracion_monto_calculado + total_igv_comision_estructuracion_calculado):,.2f}",
        'imprimir_comision_afiliacion': any(df['aplicar_comision_afiliacion']),
        'total_comision_afiliacion_monto_calculado': f"{total_comision_afiliacion_monto_calculado:,.2f}",
        'total_igv_afiliacion_calculado': f"{total_igv_afiliacion_calculado:,.2f}",
        'total_comision_afiliacion': f"{(total_comision_afiliacion_monto_calculado + total_igv_afiliacion_calculado):,.2f}",
        'signatures': [  # Placeholder
            {'name': 'Juan Perez', 'dni': '12345678', 'role': 'Gerente General'},
            {'name': 'Maria Rodriguez', 'dni': '87654321', 'role': 'Gerente de Finanzas'}
        ]
    }
    return pdf_data

def main():
    """Main function to fetch data and generate the PDF."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Supabase URL and Key are required. Check your .env file.")
        return

    supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    proposals = fetch_latest_proposals(supabase_client)

    if not proposals:
        return

    pdf_data = create_consolidated_pdf_data(proposals)

    if not pdf_data:
        print("Failed to map Supabase data to PDF data.")
        return

    output_dir = "C:/Users/rguti/Inandes.TECH/generated_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filepath = os.path.join(output_dir, f"consolidated_output_{timestamp}.pdf")

    try:
        generate_pdf(output_filepath, pdf_data)
        print(f"Successfully generated PDF: {output_filepath}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

if __name__ == "__main__":
    main()
