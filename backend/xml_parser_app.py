import streamlit as st
import xml_parser
import json

st.set_page_config(
    layout="wide",
    page_title="XML Parser INANDES",
    page_icon="📄",
)

st.title("Herramienta de Parseo de XML de Facturas (Completo)")
st.write("Sube un archivo XML de factura para ver *todos* los datos que se pueden extraer.")

uploaded_file = st.file_uploader("Sube tu archivo XML de factura", type=["xml"])

if uploaded_file is not None:
    xml_content = uploaded_file.getvalue().decode("ISO-8859-1") # Decode with appropriate encoding
    try:
        # Use the new full parsing function
        parsed_data = xml_parser.parse_full_xml_to_dict(xml_content)
        
        st.success("XML parseado exitosamente. Aquí están *todos* los datos extraídos:")
        
        if parsed_data:
            st.json(parsed_data) # Display the full dictionary as JSON
        else:
            st.warning("No se pudieron extraer datos del XML.")

        st.write("--- Datos específicos extraídos (para referencia) ---")
        specific_data = xml_parser.parse_invoice_xml(xml_content)
        if specific_data:
            for key, value in specific_data.items():
                st.write(f"**{key}:** {value}")
        else:
            st.info("No se pudieron extraer datos específicos con la función original.")

    except Exception as e:
        st.error(f"Error al parsear el XML: {e}")
        st.code(xml_content, language="xml") # Show XML content for debugging