import streamlit as st
import requests
import os
import pdf_parser
import datetime
import pdf_generator
import supabase_handler

# --- Configuración Inicial ---
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
    page_title="Calculadora de Factoring INANDES",
    page_icon="📊",
)

# --- Funciones de Ayuda y Callbacks ---
def update_date_calculations():
    try:
        if st.session_state.get('fecha_emision_factura') and st.session_state.get('plazo_credito_dias', 0) > 0:
            fecha_emision_dt = datetime.datetime.strptime(st.session_state.fecha_emision_factura, "%d-%m-%Y")
            fecha_pago_dt = fecha_emision_dt + datetime.timedelta(days=int(st.session_state.plazo_credito_dias))
            st.session_state.fecha_pago_calculada = fecha_pago_dt.strftime("%d-%m-%Y")
        else:
            st.session_state.fecha_pago_calculada = ""

        if st.session_state.get('fecha_pago_calculada') and st.session_state.get('fecha_desembolso_factoring'):
            fecha_pago_dt = datetime.datetime.strptime(st.session_state.fecha_pago_calculada, "%d-%m-%Y")
            fecha_desembolso_dt = datetime.datetime.strptime(st.session_state.fecha_desembolso_factoring, "%d-%m-%Y")
            st.session_state.plazo_operacion_calculado = (fecha_pago_dt - fecha_desembolso_dt).days if fecha_pago_dt >= fecha_desembolso_dt else 0
        else:
            st.session_state.plazo_operacion_calculado = 0
    except (ValueError, TypeError, AttributeError):
        st.session_state.fecha_pago_calculada = ""
        st.session_state.plazo_operacion_calculado = 0

def validate_inputs():
    required_fields = {
        "emisor_nombre": "Nombre del Emisor", "emisor_ruc": "RUC del Emisor",
        "aceptante_nombre": "Nombre del Aceptante", "aceptante_ruc": "RUC del Aceptante",
        "numero_factura": "Número de Factura", "moneda_factura": "Moneda de Factura",
        "fecha_emision_factura": "Fecha de Emisión", "plazo_credito_dias": "Plazo de Crédito",
        "fecha_desembolso_factoring": "Fecha de Desembolso", "tasa_de_avance": "Tasa de Avance",
        "interes_mensual": "Interés Mensual", "comision_de_estructuracion": "Comisión de Estructuración",
    }
    is_valid = True
    for key, name in required_fields.items():
        if not st.session_state.get(key):
            st.error(f"El campo '{name}' es obligatorio.")
            is_valid = False
    
    numeric_fields = {
        "monto_total_factura": "Monto Factura Total", "monto_neto_factura": "Monto Factura Neto",
        "tasa_de_avance": "Tasa de Avance", "interes_mensual": "Interés Mensual"
    }
    for key, name in numeric_fields.items():
        if st.session_state.get(key, 0) <= 0:
            st.error(f"El campo '{name}' debe ser mayor que cero.")
            is_valid = False
    return is_valid

# --- Inicialización del Session State ---
if 'emisor_nombre' not in st.session_state: st.session_state.emisor_nombre = ''
if 'emisor_ruc' not in st.session_state: st.session_state.emisor_ruc = ''
if 'aceptante_nombre' not in st.session_state: st.session_state.aceptante_nombre = ''
if 'aceptante_ruc' not in st.session_state: st.session_state.aceptante_ruc = ''
if 'fecha_emision_factura' not in st.session_state: st.session_state.fecha_emision_factura = ""
if 'fecha_desembolso_factoring' not in st.session_state: st.session_state.fecha_desembolso_factoring = datetime.date.today().strftime('%d-%m-%Y')
if 'plazo_credito_dias' not in st.session_state: st.session_state.plazo_credito_dias = 30
if 'fecha_pago_calculada' not in st.session_state: st.session_state.fecha_pago_calculada = ""
if 'plazo_operacion_calculado' not in st.session_state: st.session_state.plazo_operacion_calculado = 0
if 'monto_total_factura' not in st.session_state: st.session_state.monto_total_factura = 0.0
if 'monto_neto_factura' not in st.session_state: st.session_state.monto_neto_factura = 0.0
if 'moneda_factura' not in st.session_state: st.session_state.moneda_factura = "PEN"
if 'numero_factura' not in st.session_state: st.session_state.numero_factura = ""
if 'pdf_datos_cargados' not in st.session_state: st.session_state.pdf_datos_cargados = False
if 'initial_calc_result' not in st.session_state: st.session_state.initial_calc_result = None
if 'recalculate_result' not in st.session_state: st.session_state.recalculate_result = None
if 'comision_afiliacion_pen' not in st.session_state: st.session_state.comision_afiliacion_pen = 200.0
if 'comision_afiliacion_usd' not in st.session_state: st.session_state.comision_afiliacion_usd = 50.0
if 'aplicar_comision_afiliacion' not in st.session_state: st.session_state.aplicar_comision_afiliacion = False
if 'detraccion_porcentaje' not in st.session_state: st.session_state.detraccion_porcentaje = 0.0
if 'last_saved_proposal_id' not in st.session_state: st.session_state.last_saved_proposal_id = ''

# --- UI: Título y CSS ---
try:
    with open("C:/Users/rguti/Inandes.TECH/.streamlit/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

title_col, logo_col = st.columns([0.8, 0.2])
with title_col:
    st.write("## Modulo 1 - Factoring INANDES")
with logo_col:
    st.image("C:/Users/rguti/Inandes.TECH/inputs_para_generated_pdfs/LOGO.png", width=120, use_container_width=True)

# --- UI: Carga de Archivos ---
with st.expander("Cargar datos automáticamente desde PDF (Opcional)", expanded=True):
    uploaded_pdf_file = st.file_uploader("Sube tu archivo PDF de factura", type=["pdf"], key="pdf_uploader_main")
    if uploaded_pdf_file is not None:
        temp_file_path = os.path.join("C:/Users/rguti/Inandes.TECH/backend", "temp_uploaded_pdf.pdf")
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_pdf_file.getbuffer())

        with st.spinner("Procesando PDF y consultando base de datos..."):
            try:
                parsed_data = pdf_parser.extract_fields_from_pdf(temp_file_path)
                if parsed_data.get("error"):
                    st.error(f"Error al procesar el PDF: {parsed_data['error']}")
                else:
                    if not st.session_state.pdf_datos_cargados or uploaded_pdf_file.file_id != st.session_state.get('last_uploaded_pdf_id'):
                        st.session_state.emisor_ruc = parsed_data.get('emisor_ruc', '')
                        st.session_state.aceptante_ruc = parsed_data.get('aceptante_ruc', '')
                        st.session_state.fecha_emision_factura = parsed_data.get('fecha_emision', '')
                        st.session_state.monto_total_factura = parsed_data.get('monto_total', 0.0)
                        st.session_state.monto_neto_factura = parsed_data.get('monto_neto', 0.0)
                        st.session_state.moneda_factura = parsed_data.get('moneda', 'PEN')
                        st.session_state.numero_factura = parsed_data.get('invoice_id', '')
                        st.session_state.pdf_datos_cargados = True
                        st.session_state.last_uploaded_pdf_id = uploaded_pdf_file.file_id

                        if st.session_state.emisor_ruc:
                            st.session_state.emisor_nombre = supabase_handler.get_razon_social_by_ruc(st.session_state.emisor_ruc)
                        if st.session_state.aceptante_ruc:
                            st.session_state.aceptante_nombre = supabase_handler.get_razon_social_by_ruc(st.session_state.aceptante_ruc)
                        
                        st.success("Datos cargados y enriquecidos. Revisa el formulario.")

            except Exception as e:
                st.error(f"Error al parsear el PDF: {e}")
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

# --- UI: Formulario Principal ---
update_date_calculations()
st.write("### Ingresa los datos de la operación:")
col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
with col1:
    st.write("##### Involucrados")
    st.text_input("NOMBRE DEL EMISOR", key="emisor_nombre")
    st.text_input("RUC DEL EMISOR", key="emisor_ruc")
    st.text_input("NOMBRE DEL ACEPTANTE", key="aceptante_nombre")
    st.text_input("RUC DEL ACEPTANTE", key="aceptante_ruc")
with col2:
    st.write("##### Montos y Moneda")
    st.text_input("NÚMERO DE FACTURA", key="numero_factura")
    st.number_input("MONTO FACTURA TOTAL (CON IGV)", min_value=0.0, key="monto_total_factura", format="%.2f")
    st.number_input("MONTO FACTURA NETO", min_value=0.0, key="monto_neto_factura", format="%.2f")
    st.selectbox("MONEDA DE FACTURA", ["PEN", "USD"], key="moneda_factura")
    detraccion_retencion_pct = 0.0
    if st.session_state.monto_total_factura > 0:
        detraccion_retencion_pct = ((st.session_state.monto_total_factura - st.session_state.monto_neto_factura) / st.session_state.monto_total_factura) * 100
    st.session_state.detraccion_porcentaje = detraccion_retencion_pct
    st.text_input("Detracción / Retención (%)", value=f"{detraccion_retencion_pct:.2f}%", disabled=True)
with col3:
    st.write("##### Fechas y Plazos")
    st.text_input("Fecha de Emisión (DD-MM-YYYY)", key='fecha_emision_factura', on_change=update_date_calculations)
    st.number_input("Plazo de Crédito (días)", min_value=1, step=1, key='plazo_credito_dias', on_change=update_date_calculations)
    st.text_input("Fecha de Pago (Calculada)", key='fecha_pago_calculada', disabled=True)
    st.text_input("Fecha de Desembolso (DD-MM-YYYY)", key='fecha_desembolso_factoring', on_change=update_date_calculations)
    st.number_input("Plazo de Operación (días)", key='plazo_operacion_calculado', disabled=True)
with col4:
    st.write("##### Tasas y Comisiones")
    st.number_input("Tasa de Avance (%)", min_value=0.0, value=98.0, format="%.2f", key="tasa_de_avance")
    st.number_input("Interés Mensual (%)", min_value=0.0, value=1.25, format="%.2f", key="interes_mensual")
    st.number_input("Comisión de Estructuración (%)", min_value=0.0, value=0.5, format="%.2f", key="comision_de_estructuracion")
    st.number_input("Comisión Mínima (PEN)", min_value=0.0, value=10.0, format="%.2f", key="comision_minima_pen")
    st.number_input("Comisión Mínima (USD)", min_value=0.0, value=3.0, format="%.2f", key="comision_minima_usd")
    st.number_input("Comisión de Afiliación (PEN)", min_value=0.0, value=200.0, format="%.2f", key="comision_afiliacion_pen")
    st.number_input("Comisión de Afiliación (USD)", min_value=0.0, value=50.0, format="%.2f", key="comision_afiliacion_usd")
    st.checkbox("Aplicar Comisión de Afiliación", key="aplicar_comision_afiliacion")

st.markdown("---")

# --- Pasos de Cálculo y Acción ---
col_paso1, col_paso2 = st.columns(2)

with col_paso1:
    st.write("#### Paso 1: Calcular Desembolso Inicial")
    if st.button("Calcular Desembolso Inicial"):
        if validate_inputs():
            api_data = {
                "plazo_operacion": st.session_state.plazo_operacion_calculado,
                "mfn": st.session_state.monto_neto_factura,
                "tasa_avance": st.session_state.tasa_de_avance / 100,
                "interes_mensual": st.session_state.interes_mensual / 100,
                "comision_estructuracion_pct": st.session_state.comision_de_estructuracion / 100,
                "moneda_factura": st.session_state.moneda_factura,
                "comision_min_pen": st.session_state.comision_minima_pen,
                "comision_min_usd": st.session_state.comision_minima_usd,
                "igv_pct": 0.18,
                "comision_afiliacion_valor": st.session_state.comision_afiliacion_pen,
                "comision_afiliacion_usd_valor": st.session_state.comision_afiliacion_usd,
                "aplicar_comision_afiliacion": st.session_state.aplicar_comision_afiliacion,
                "monto_desembolsar_manual": 0
            }
            with st.spinner('Calculando desembolso...'):
                try:
                    response = requests.post(f"{API_BASE_URL}/calcular_desembolso", json=api_data)
                    response.raise_for_status()
                    st.session_state.initial_calc_result = response.json()
                    st.session_state.recalculate_result = None
                except requests.exceptions.RequestException as e:
                    st.error(f"Error de conexión con la API: {e}")

    if st.session_state.initial_calc_result:
        st.write("##### Resultado del Cálculo Inicial")
        st.json(st.session_state.initial_calc_result)

with col_paso2:
    st.write("#### Paso 2: Encontrar Tasa de Avance")
    with st.form("recalculate_form"):
        monto_desembolsar_manual = st.number_input("Monto a Desembolsar Objetivo", min_value=0.0, format="%.2f")
        submitted_recalculate = st.form_submit_button("Encontrar Tasa de Avance")
        if submitted_recalculate and monto_desembolsar_manual > 0:
            if validate_inputs():
                api_data = {
                    "plazo_operacion": st.session_state.plazo_operacion_calculado,
                    "mfn": st.session_state.monto_neto_factura,
                    "interes_mensual": st.session_state.interes_mensual / 100,
                    "comision_estructuracion_pct": st.session_state.comision_de_estructuracion / 100,
                    "moneda_factura": st.session_state.moneda_factura,
                    "comision_min_pen": st.session_state.comision_minima_pen,
                    "comision_min_usd": st.session_state.comision_minima_usd,
                    "igv_pct": 0.18,
                    "comision_afiliacion_valor": st.session_state.comision_afiliacion_pen,
                    "comision_afiliacion_usd_valor": st.session_state.comision_afiliacion_usd,
                    "aplicar_comision_afiliacion": st.session_state.aplicar_comision_afiliacion,
                    "monto_objetivo": monto_desembolsar_manual
                }
                with st.spinner('Buscando tasa de avance...'):
                    try:
                        response = requests.post(f"{API_BASE_URL}/encontrar_tasa", json=api_data)
                        response.raise_for_status()
                        st.session_state.recalculate_result = response.json()
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error de conexión con la API: {e}")
        elif submitted_recalculate:
            st.error("El Monto a Desembolsar Objetivo debe ser mayor a cero.")

    if st.session_state.recalculate_result:
        st.write("##### Resultado de la Búsqueda")
        st.json(st.session_state.recalculate_result)

# --- Pasos 3 y 4: Grabar e Imprimir ---
st.markdown("---")
st.write("#### Paso 3: Grabar Propuesta")
if st.button("GRABAR Propuesta en Base de Datos", disabled=not st.session_state.recalculate_result):
    with st.spinner("Guardando propuesta..."):
        success, message = supabase_handler.save_proposal(st.session_state)
        if success:
            st.success(message)
            # Extract proposal_id from the success message and store it
            if "Propuesta con ID" in message:
                start_index = message.find("ID ") + 3
                end_index = message.find(" guardada")
                st.session_state.last_saved_proposal_id = message[start_index:end_index]
        else:
            st.error(message)

st.markdown("---") # Divider between Paso 3 and Paso 4

st.write("#### Paso 4: Imprimir Documento")
# Botón de impresión retirado según solicitud del usuario

# --- UI: Consulta y Selección de Propuestas ---
st.markdown("---")
st.write("### Consulta y Selección de Propuestas")

with st.expander("Buscar Propuestas para Consolidar", expanded=True):
    col_id_propuesta, col_razon_social = st.columns(2)
    with col_id_propuesta:
        st.text_input("ID Propuesta (Opcional)", key="search_proposal_id", value=st.session_state.last_saved_proposal_id)
    with col_razon_social:
        st.text_input("Razón Social del Emisor", key="search_emisor_nombre")

    search_button = st.button("Seleccionar Propuestas")

    if search_button:
        if st.session_state.search_proposal_id:
            # Search by proposal ID
            proposal = supabase_handler.get_proposal_details_by_id(st.session_state.search_proposal_id)
            if proposal and 'proposal_id' in proposal:
                if 'accumulated_proposals' not in st.session_state:
                    st.session_state.accumulated_proposals = []
                # Add only if not already in the list
                if not any('proposal_id' in p and p['proposal_id'] == proposal['proposal_id'] for p in st.session_state.accumulated_proposals):
                    st.session_state.accumulated_proposals.append(proposal)
                
            else:
                st.info(f"No se encontró ninguna propuesta con el ID: {st.session_state.search_proposal_id}")
        elif st.session_state.search_emisor_nombre:
            # Search by emisor_nombre
            found_proposals_partial = supabase_handler.get_active_proposals_by_emisor_nombre(st.session_state.search_emisor_nombre)
            if found_proposals_partial:
                if 'accumulated_proposals' not in st.session_state:
                    st.session_state.accumulated_proposals = []
                for proposal_partial in found_proposals_partial:
                    full_proposal_details = supabase_handler.get_proposal_details_by_id(proposal_partial['proposal_id'])
                    if full_proposal_details and 'proposal_id' in full_proposal_details:
                        if not any('proposal_id' in p and p['proposal_id'] == full_proposal_details['proposal_id'] for p in st.session_state.accumulated_proposals):
                            st.session_state.accumulated_proposals.append(full_proposal_details)
            else:
                st.info(f"No se encontraron propuestas activas para: {st.session_state.search_emisor_nombre}")
        else:
            st.warning("Por favor, ingresa un ID de Propuesta o una Razón Social para buscar.")

    # Display the accumulated proposals (laundry list)
    if 'accumulated_proposals' in st.session_state and st.session_state.accumulated_proposals:
        st.write("##### Propuestas Seleccionadas para Consolidar:")
        if 'selected_proposals_checkboxes' not in st.session_state:
            st.session_state.selected_proposals_checkboxes = {}

        for i, proposal in enumerate(st.session_state.accumulated_proposals):
            if 'proposal_id' not in proposal: # Skip if proposal_id is missing
                continue
            checkbox_key = f"accum_prop_checkbox_{proposal['proposal_id']}"
            if checkbox_key not in st.session_state.selected_proposals_checkboxes:
                st.session_state.selected_proposals_checkboxes[checkbox_key] = True # Default to checked

            col_check, col_id, col_emisor, col_monto = st.columns([0.1, 0.3, 0.3, 0.3])
            with col_check:
                st.session_state.selected_proposals_checkboxes[checkbox_key] = st.checkbox(
                    "", value=st.session_state.selected_proposals_checkboxes[checkbox_key], key=checkbox_key
                )
            with col_id:
                st.write(f"**ID:** {proposal.get('proposal_id', 'N/A')}")
            with col_emisor:
                st.write(f"**Emisor:** {proposal.get('invoice_issuer_name', 'N/A')}")
            with col_monto:
                st.write(f"**Monto:** PEN {proposal.get('initial_disbursement', 0.0):.2f}")

    # Botón para generar PDF consolidado
    if 'accumulated_proposals' in st.session_state and st.session_state.accumulated_proposals:
        if st.button("Generar PDF Consolidado"):
            selected_invoices_data = []
            for proposal in st.session_state.accumulated_proposals:
                checkbox_key = f"accum_prop_checkbox_{proposal.get('proposal_id', 'MISSING_ID')}"
                if st.session_state.selected_proposals_checkboxes.get(checkbox_key, False):
                    full_details = supabase_handler.get_proposal_details_by_id(proposal['proposal_id'])
                    if full_details:
                        selected_invoices_data.append(full_details)
            
            if selected_invoices_data:
                import subprocess
                import json
                import time

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filepath = f"C:/Users/rguti/Inandes.TECH/generated_pdfs/consolidated_invoice_{timestamp}.pdf"

                invoices_json = json.dumps(selected_invoices_data)

                command = [
                    "python",
                    "C:/Users/rguti/Inandes.TECH/backend/pdf_generator_v_cli.py",
                    f"--output_filepath={output_filepath}",
                    f"--invoices_json={invoices_json}"
                ]

                aplicar_comision_afiliacion_overall = any(inv.get('aplicar_comision_afiliacion', False) for inv in selected_invoices_data)
                if aplicar_comision_afiliacion_overall:
                    command.append("--aplicar_comision_afiliacion")
                    total_comision_afiliacion_monto = sum(inv.get('comision_afiliacion_monto_calculado', 0) for inv in selected_invoices_data)
                    total_igv_afiliacion = sum(inv.get('igv_afiliacion_calculado', 0) for inv in selected_invoices_data)
                    command.append(f"--comision_afiliacion_monto_calculado={total_comision_afiliacion_monto}")
                    command.append(f"--igv_afiliacion_calculado={total_igv_afiliacion}")

                st.write("Generando PDF consolidado...")
                try:
                    result = subprocess.run(command, check=True, capture_output=True, text=True)
                    if result.stderr:
                        st.warning(f"Advertencias/Errores del generador de PDF: {result.stderr}")

                    if os.path.exists(output_filepath):
                        with open(output_filepath, "rb") as file:
                            btn = st.download_button(
                                label="Descargar PDF Consolidado",
                                data=file.read(),
                                file_name=os.path.basename(output_filepath),
                                mime="application/pdf"
                            )
                        st.success(f"PDF consolidado generado. Haz clic en el botón para descargarlo.")
                        # Clean up the generated file after offering for download
                        os.remove(output_filepath)
                    else:
                        st.error("Error: El archivo PDF consolidado no se generó correctamente.")

                except subprocess.CalledProcessError as e:
                    st.error(f"Error al generar PDF consolidado: {e}")
                    st.error(f"Salida del error: {e.stderr}")
                except FileNotFoundError:
                    st.error("Error: El script pdf_generator_v_cli.py no fue encontrado.")
            else:
                st.warning("No hay propuestas seleccionadas para generar el PDF.")

    