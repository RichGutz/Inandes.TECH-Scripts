import streamlit as st
import xml_parser
import pdf_parser
import json
import os

st.set_page_config(
    layout="wide",
    page_title="Document Parser INANDES",
    page_icon="📄",
)

OUTPUT_DIR = "C:/Users/rguti/Inandes.TECH/outputs"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

st.title("Herramienta Unificada de Parseo de Documentos")
st.write("Sube tus archivos de factura en las secciones correspondientes. Los datos extraídos se guardarán automáticamente en la carpeta de salida.")

# Initialize session state for extracted data
if 'xml_extracted_fields' not in st.session_state:
    st.session_state.xml_extracted_fields = {}
if 'pdf_extracted_fields' not in st.session_state:
    st.session_state.pdf_extracted_fields = {}

def save_extracted_data_to_file(extracted_data, file_name_prefix):
    if extracted_data:
        output_content = json.dumps(extracted_data, indent=4, ensure_ascii=False) if isinstance(extracted_data, dict) else str(extracted_data)
        output_file_path = os.path.join(OUTPUT_DIR, f"{file_name_prefix}_extracted_data.txt")
        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(output_content)
            st.success(f"Datos guardados en: {output_file_path}")
        except Exception as e:
            st.error(f"Error al guardar el archivo en {output_file_path}: {e}")
    else:
        st.warning("No hay datos para guardar.")

# --- XML Uploader Section ---
st.header("Cargar Archivo XML")
uploaded_xml_file = st.file_uploader("Arrastra y suelta tu archivo XML aquí o haz click para buscar", type=["xml"], key="xml_uploader")

if uploaded_xml_file is not None:
    st.subheader("Procesando XML...")
    xml_content = uploaded_xml_file.getvalue().decode("ISO-8859-1") # Decode with appropriate encoding
    try:
        # Extract specific data for display and session state
        specific_data = xml_parser.parse_invoice_xml(xml_content)
        st.session_state.xml_extracted_fields = specific_data
        save_extracted_data_to_file(specific_data, "xml_specific")
        st.success("XML procesado y datos extraídos.")

    except Exception as e:
        st.error(f"Error al parsear el XML: {e}")
        st.code(xml_content, language="xml") # Show XML content for debugging

st.markdown("---") # Separator

# --- PDF Uploader Section ---
st.header("Cargar Archivo PDF")
uploaded_pdf_file = st.file_uploader("Arrastra y suelta tu archivo PDF aquí o haz click para buscar", type=["pdf"], key="pdf_uploader")

if uploaded_pdf_file is not None:
    st.subheader("Procesando PDF...")
    # Save the uploaded file temporarily to be read by pdfplumber
    temp_file_path = os.path.join("C:/Users/rguti/Inandes.TECH/backend/temp_uploaded_pdf.pdf") # Using a fixed path for simplicity
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_pdf_file.getbuffer())

    try:
        extracted_data = pdf_parser.extract_fields_from_pdf(temp_file_path)
        
        if "error" in extracted_data:
            st.error(f"Error al procesar el PDF: {extracted_data['error']}")
        else:
            # Store specific extracted data for display and session state
            st.session_state.pdf_extracted_fields = extracted_data
            save_extracted_data_to_file(extracted_data, "pdf_specific")
            st.success("PDF procesado y datos extraídos.")

    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

st.markdown("---") # Separator

# --- Comparison Display Section ---
st.header("Comparación de Datos Extraídos")

common_fields = [
    ("emisor_nombre", "Nombre del Emisor"),
    ("emisor_ruc", "RUC del Emisor"),
    ("aceptante_nombre", "Nombre del Aceptante"),
    ("aceptante_ruc", "RUC del Aceptante"),
    ("monto_factura_neto", "Monto Neto"),
    ("igv_monto", "Monto IGV"),
    ("monto_factura_total", "Monto Total"),
    ("fecha_emision_str", "Fecha de Emisión"),
    ("moneda_factura", "Moneda de Factura"),
    ("moneda_operacion", "Moneda de Operación"),
]

col_xml, col_pdf = st.columns(2)

with col_xml:
    st.subheader("Datos Extraídos del XML")
    if st.session_state.xml_extracted_fields:
        for field_key, field_label in common_fields:
            value = st.session_state.xml_extracted_fields.get(field_key, "N/A")
            st.write(f"**{field_label}:** {value}")
    else:
        st.info("Sube un archivo XML para ver los datos aquí.")

with col_pdf:
    st.subheader("Datos Extraídos del PDF")
    if st.session_state.pdf_extracted_fields:
        for field_key, field_label in common_fields:
            value = st.session_state.pdf_extracted_fields.get(field_key, "N/A")
            st.write(f"**{field_label}:** {value}")
    else:
        st.info("Sube un archivo PDF para ver los datos aquí.")
