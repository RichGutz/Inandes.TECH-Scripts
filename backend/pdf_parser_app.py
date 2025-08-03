import streamlit as st
import os
import pdf_parser # Import the parser

st.set_page_config(layout="centered", page_title="PDF Parser Test")

st.title("Herramienta de Prueba del Parser de PDF")

st.write("Sube un archivo PDF para extraer y ver los datos crudos directamente del parser.")

uploaded_file = st.file_uploader("Elige un archivo PDF", type="pdf")

if uploaded_file is not None:
    # Define a temporary directory to store the uploaded file
    temp_dir = "C:/Users/rguti/Inandes.TECH/backend/temp_files"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    temp_file_path = os.path.join(temp_dir, uploaded_file.name)

    try:
        # Save the uploaded file to the temporary path
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write(f"Archivo temporal guardado en: `{temp_file_path}`")
        print(f"[DEBUG - APP] Processing file: {temp_file_path}")

        # Call the PDF parser function
        with st.spinner("Ejecutando el parser en el PDF..."):
            extracted_data = pdf_parser.extract_fields_from_pdf(temp_file_path)

        # Display the results
        if "error" in extracted_data:
            st.error(f"Error al procesar el PDF: {extracted_data['error']}")
        elif not extracted_data:
             st.warning("No se pudo extraer ningún dato del PDF. El parser no encontró campos reconocibles.")
        else:
            st.success("¡Datos extraídos con éxito!")
            st.write("A continuación se muestran los datos extraídos directamente desde `pdf_parser.py`:")
            st.json(extracted_data)

    except Exception as e:
        st.error(f"Ocurrió un error inesperado durante el procesamiento: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            st.write(f"Archivo temporal `{temp_file_path}` eliminado.")

else:
    st.info("Esperando que se suba un archivo PDF.")
