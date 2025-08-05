import streamlit as st
import requests
import os
import pdf_parser
import datetime
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
def update_date_calculations(invoice):
    try:
        if invoice.get('fecha_emision_factura') and invoice.get('plazo_credito_dias', 0) > 0:
            fecha_emision_dt = datetime.datetime.strptime(invoice['fecha_emision_factura'], "%d-%m-%Y")
            fecha_pago_dt = fecha_emision_dt + datetime.timedelta(days=int(invoice['plazo_credito_dias']))
            invoice['fecha_pago_calculada'] = fecha_pago_dt.strftime("%d-%m-%Y")
        else:
            invoice['fecha_pago_calculada'] = ""

        if invoice.get('fecha_pago_calculada') and invoice.get('fecha_desembolso_factoring'):
            fecha_pago_dt = datetime.datetime.strptime(invoice['fecha_pago_calculada'], "%d-%m-%Y")
            fecha_desembolso_dt = datetime.datetime.strptime(invoice['fecha_desembolso_factoring'], "%d-%m-%Y")
            invoice['plazo_operacion_calculado'] = (fecha_pago_dt - fecha_desembolso_dt).days if fecha_pago_dt >= fecha_desembolso_dt else 0
        else:
            invoice['plazo_operacion_calculado'] = 0
    except (ValueError, TypeError, AttributeError):
        invoice['fecha_pago_calculada'] = ""
        invoice['plazo_operacion_calculado'] = 0

def validate_inputs(invoice):
    required_fields = {
        "emisor_nombre": "Nombre del Emisor", "emisor_ruc": "RUC del Emisor",
        "aceptante_nombre": "Nombre del Aceptante", "aceptante_ruc": "RUC del Aceptante",
        "numero_factura": "Número de Factura", "moneda_factura": "Moneda de Factura",
        "fecha_emision_factura": "Fecha de Emisión",
        "tasa_de_avance": "Tasa de Avance",
        "interes_mensual": "Interés Mensual", "comision_de_estructuracion": "Comisión de Estructuración",
        "plazo_credito_dias": "Plazo de Crédito (días)", "fecha_desembolso_factoring": "Fecha de Desembolso",
    }
    is_valid = True
    for key, name in required_fields.items():
        if not invoice.get(key):
            is_valid = False
    
    numeric_fields = {
        "monto_total_factura": "Monto Factura Total", "monto_neto_factura": "Monto Factura Neto",
        "tasa_de_avance": "Tasa de Avance", "interes_mensual": "Interés Mensual"
    }
    for key, name in numeric_fields.items():
        if invoice.get(key, 0) <= 0:
            is_valid = False
    return is_valid

def propagate_commission_changes():
    # This function is called on_change. It will trigger a rerun.
    # On the next run, the UI will be updated based on the new state.
    if st.session_state.get('fijar_condiciones', False) and st.session_state.invoices_data and len(st.session_state.invoices_data) > 1:
        # Get the most recent values directly from the session state of the first invoice's widgets
        # This ensures we are using the value that just changed, before the full rerun.
        first_invoice = st.session_state.invoices_data[0]
        first_invoice['tasa_de_avance'] = st.session_state.get(f"tasa_de_avance_0", first_invoice['tasa_de_avance'])
        first_invoice['interes_mensual'] = st.session_state.get(f"interes_mensual_0", first_invoice['interes_mensual'])
        first_invoice['comision_de_estructuracion'] = st.session_state.get(f"comision_de_estructuracion_0", first_invoice['comision_de_estructuracion'])
        first_invoice['comision_minima_pen'] = st.session_state.get(f"comision_minima_pen_0", first_invoice['comision_minima_pen'])
        first_invoice['comision_minima_usd'] = st.session_state.get(f"comision_minima_usd_0", first_invoice['comision_minima_usd'])
        first_invoice['comision_afiliacion_pen'] = st.session_state.get(f"comision_afiliacion_pen_0", first_invoice['comision_afiliacion_pen'])
        first_invoice['comision_afiliacion_usd'] = st.session_state.get(f"comision_afiliacion_usd_0", first_invoice['comision_afiliacion_usd'])

        # Now that the first invoice's dictionary is up-to-date, propagate its values
        for i in range(1, len(st.session_state.invoices_data)):
            invoice = st.session_state.invoices_data[i]
            invoice['tasa_de_avance'] = first_invoice['tasa_de_avance']
            invoice['interes_mensual'] = first_invoice['interes_mensual']
            invoice['comision_de_estructuracion'] = first_invoice['comision_de_estructuracion']
            invoice['comision_minima_pen'] = first_invoice['comision_minima_pen']
            invoice['comision_minima_usd'] = first_invoice['comision_minima_usd']
            invoice['comision_afiliacion_pen'] = first_invoice['comision_afiliacion_pen']
            invoice['comision_afiliacion_usd'] = first_invoice['comision_afiliacion_usd']

# --- Inicialización del Session State ---

# --- Inicialización del Session State ---
if 'invoices_data' not in st.session_state: st.session_state.invoices_data = []
if 'pdf_datos_cargados' not in st.session_state: st.session_state.pdf_datos_cargados = False
if 'last_uploaded_pdf_files_ids' not in st.session_state: st.session_state.last_uploaded_pdf_files_ids = []
if 'last_saved_proposal_id' not in st.session_state: st.session_state.last_saved_proposal_id = ''
if 'anexo_number' not in st.session_state: st.session_state.anexo_number = ''
if 'contract_number' not in st.session_state: st.session_state.contract_number = ''
if 'fijar_condiciones' not in st.session_state: st.session_state.fijar_condiciones = False
# Default values for new invoices (these will be copied into each invoice's dict)
if 'default_comision_afiliacion_pen' not in st.session_state: st.session_state.default_comision_afiliacion_pen = 200.0
if 'default_comision_afiliacion_usd' not in st.session_state: st.session_state.default_comision_afiliacion_usd = 50.0
if 'default_tasa_de_avance' not in st.session_state: st.session_state.default_tasa_de_avance = 98.0
if 'default_interes_mensual' not in st.session_state: st.session_state.default_interes_mensual = 1.25
if 'default_comision_de_estructuracion' not in st.session_state: st.session_state.default_comision_de_estructuracion = 0.5
if 'default_comision_minima_pen' not in st.session_state: st.session_state.default_comision_minima_pen = 10.0
if 'default_comision_minima_usd' not in st.session_state: st.session_state.default_comision_minima_usd = 3.0

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
with st.expander("", expanded=True):
    col1, col2 = st.columns([1, 0.00001])
    with col1:
        uploaded_pdf_files = st.file_uploader("Seleccionar archivos", type=["pdf"], key="pdf_uploader_main", accept_multiple_files=True)
    with col2:
        pass # Button removed

    if uploaded_pdf_files:
        # Clear previous data if new files are uploaded or file IDs change
        current_file_ids = [f.file_id for f in uploaded_pdf_files]
        if "last_uploaded_pdf_files_ids" not in st.session_state or \
           current_file_ids != st.session_state.last_uploaded_pdf_files_ids:
            st.session_state.invoices_data = []
            st.session_state.last_uploaded_pdf_files_ids = current_file_ids
            st.session_state.pdf_datos_cargados = False # Reset this flag

        if not st.session_state.pdf_datos_cargados: # Process only if not already processed for current files
            for uploaded_file in uploaded_pdf_files:
                temp_file_path = os.path.join("C:/Users/rguti/Inandes.TECH/backend", f"temp_uploaded_pdf_{uploaded_file.file_id}.pdf")
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                with st.spinner(f"Procesando {uploaded_file.name} y consultando base de datos..."):
                    try:
                        parsed_data = pdf_parser.extract_fields_from_pdf(temp_file_path)
                        if parsed_data.get("error"):
                            st.error(f"Error al procesar el PDF {uploaded_file.name}: {parsed_data['error']}")
                        else:
                            invoice_entry = {
                                'emisor_ruc': parsed_data.get('emisor_ruc', ''),
                                'aceptante_ruc': parsed_data.get('aceptante_ruc', ''),
                                'fecha_emision_factura': parsed_data.get('fecha_emision', ''),
                                'monto_total_factura': parsed_data.get('monto_total', 0.0),
                                'monto_neto_factura': parsed_data.get('monto_neto', 0.0),
                                'moneda_factura': parsed_data.get('moneda', 'PEN'),
                                'numero_factura': parsed_data.get('invoice_id', ''),
                                'parsed_pdf_name': uploaded_file.name,
                                'file_id': uploaded_file.file_id,
                                'emisor_nombre': '',
                                'aceptante_nombre': '',
                                'plazo_credito_dias': None,
                                'fecha_desembolso_factoring': '',
                                'tasa_de_avance': st.session_state.default_tasa_de_avance,
                                'interes_mensual': st.session_state.default_interes_mensual,
                                'comision_de_estructuracion': st.session_state.default_comision_de_estructuracion,
                                'comision_minima_pen': st.session_state.default_comision_minima_pen,
                                'comision_minima_usd': st.session_state.default_comision_minima_usd,
                                'comision_afiliacion_pen': st.session_state.default_comision_afiliacion_pen,
                                'comision_afiliacion_usd': st.session_state.default_comision_afiliacion_usd,
                                'aplicar_comision_afiliacion': False,
                                'detraccion_porcentaje': 0.0, # Will be calculated later
                                'fecha_pago_calculada': '', # Will be calculated later
                                'plazo_operacion_calculado': 0, # Will be calculated later
                                'initial_calc_result': None,
                                'recalculate_result': None,
                            }

                            if invoice_entry['emisor_ruc']:
                                invoice_entry['emisor_nombre'] = supabase_handler.get_razon_social_by_ruc(invoice_entry['emisor_ruc'])
                            if invoice_entry['aceptante_ruc']:
                                invoice_entry['aceptante_nombre'] = supabase_handler.get_razon_social_by_ruc(invoice_entry['aceptante_ruc'])
                            
                            st.session_state.invoices_data.append(invoice_entry)
                            st.success(f"Datos de {uploaded_file.name} cargados y enriquecidos. Revisa el formulario.")

                    except Exception as e:
                        st.error(f"Error al parsear el PDF {uploaded_file.name}: {e}")
                    finally:
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
            st.session_state.pdf_datos_cargados = True

    elif "invoices_data" not in st.session_state:
        st.session_state.invoices_data = []
        st.session_state.pdf_datos_cargados = False
        st.session_state.last_uploaded_pdf_files_ids = []

# --- UI: Formulario Principal ---
if st.session_state.invoices_data:
    for idx, invoice in enumerate(st.session_state.invoices_data):
        st.markdown("--- ")
        st.write(f"### Factura {idx + 1}: {invoice.get('parsed_pdf_name', 'N/A')}")

        # --- UI: Formulario Principal (adaptado para múltiples facturas) ---
        # Involucrados
        with st.container():
            st.write("##### Involucrados")
            col_emisor_nombre, col_emisor_ruc, col_aceptante_nombre, col_aceptante_ruc = st.columns(4)
            with col_emisor_nombre:
                invoice['emisor_nombre'] = st.text_input(" NOMBRE DEL EMISOR", value=invoice.get('emisor_nombre', ''), key=f"emisor_nombre_{idx}", label_visibility="visible")
            with col_emisor_ruc:
                invoice['emisor_ruc'] = st.text_input("RUC DEL EMISOR", value=invoice.get('emisor_ruc', ''), key=f"emisor_ruc_{idx}", label_visibility="visible")
            with col_aceptante_nombre:
                invoice['aceptante_nombre'] = st.text_input("NOMBRE DEL ACEPTANTE", value=invoice.get('aceptante_nombre', ''), key=f"aceptante_nombre_{idx}", label_visibility="visible")
            with col_aceptante_ruc:
                invoice['aceptante_ruc'] = st.text_input("RUC DEL ACEPTANTE", value=invoice.get('aceptante_ruc', ''), key=f"aceptante_ruc_{idx}", label_visibility="visible")

        # Montos y Moneda
        with st.container():
            st.write("##### Montos y Moneda")
            col_num_factura, col_monto_total, col_monto_neto, col_moneda, col_detraccion = st.columns(5)
            with col_num_factura:
                invoice['numero_factura'] = st.text_input("NÚMERO DE FACTURA", value=invoice.get('numero_factura', ''), key=f"numero_factura_{idx}", label_visibility="visible")
            with col_monto_total:
                invoice['monto_total_factura'] = st.number_input("MONTO FACTURA TOTAL (CON IGV)", min_value=0.0, value=invoice.get('monto_total_factura', 0.0), format="%.2f", key=f"monto_total_factura_{idx}", label_visibility="visible")
            with col_monto_neto:
                invoice['monto_neto_factura'] = st.number_input("MONTO FACTURA NETO", min_value=0.0, value=invoice.get('monto_neto_factura', 0.0), format="%.2f", key=f"monto_neto_factura_{idx}", label_visibility="visible")
            with col_moneda:
                invoice['moneda_factura'] = st.selectbox("MONEDA DE FACTURA", ["PEN", "USD"], index=["PEN", "USD"].index(invoice.get('moneda_factura', 'PEN')), key=f"moneda_factura_{idx}", label_visibility="visible")
            with col_detraccion:
                detraccion_retencion_pct = 0.0
                if invoice.get('monto_total_factura', 0) > 0:
                    detraccion_retencion_pct = ((invoice['monto_total_factura'] - invoice['monto_neto_factura']) / invoice['monto_total_factura']) * 100
                invoice['detraccion_porcentaje'] = detraccion_retencion_pct
                st.text_input("Detracción / Retención (%)", value=f"{detraccion_retencion_pct:.2f}%", disabled=True, key=f"detraccion_porcentaje_{idx}", label_visibility="visible")

        # Fechas y Plazos
        with st.container():
            st.write("##### Fechas y Plazos")

            # Helper to parse date string to date object, returns None on failure
            def to_date_obj(date_str):
                if not date_str or not isinstance(date_str, str): return None
                try:
                    return datetime.datetime.strptime(date_str, '%d-%m-%Y').date()
                except (ValueError, TypeError):
                    return None

            col_fecha_emision, col_plazo_credito, col_fecha_pago, col_fecha_desembolso, col_plazo_operacion = st.columns(5)

            with col_fecha_emision:
                fecha_emision_obj = to_date_obj(invoice.get('fecha_emision_factura'))
                
                # Disable the input if a date was successfully parsed from the PDF
                is_disabled = bool(fecha_emision_obj)

                nueva_fecha_emision_obj = st.date_input(
                    "Fecha de Emisión",
                    value=fecha_emision_obj,
                    key=f"fecha_emision_factura_{idx}",
                    format="DD-MM-YYYY",
                    disabled=is_disabled
                )

                # If the field is enabled (i.e., not parsed from PDF), update the session state with the user's input
                if not is_disabled:
                    if nueva_fecha_emision_obj:
                        invoice['fecha_emision_factura'] = nueva_fecha_emision_obj.strftime('%d-%m-%Y')
                    else:
                        # If the user clears the date, set it to an empty string
                        invoice['fecha_emision_factura'] = ''

            with col_plazo_credito:
                invoice['plazo_credito_dias'] = st.number_input(
                    "Plazo de Crédito (días)",
                    min_value=1,
                    step=1,
                    value=invoice.get('plazo_credito_dias'), # No fallback default
                    key=f"plazo_credito_dias_{idx}"
                )

            with col_fecha_desembolso:
                fecha_desembolso_obj = to_date_obj(invoice.get('fecha_desembolso_factoring'))
                nueva_fecha_desembolso_obj = st.date_input(
                    "Fecha de Desembolso",
                    value=fecha_desembolso_obj,
                    key=f"fecha_desembolso_factoring_{idx}",
                    format="DD-MM-YYYY"
                )
                if nueva_fecha_desembolso_obj:
                    invoice['fecha_desembolso_factoring'] = nueva_fecha_desembolso_obj.strftime('%d-%m-%Y')
                else:
                    invoice['fecha_desembolso_factoring'] = ''

            # --- Dynamic Calculation ---
            # This function is called on every script rerun, ensuring calculations are always up-to-date
            update_date_calculations(invoice)

            with col_fecha_pago:
                st.text_input("Fecha de Pago (Calculada)", value=invoice.get('fecha_pago_calculada', ''), disabled=True, key=f"fecha_pago_calculada_{idx}", label_visibility="visible")

            with col_plazo_operacion:
                st.number_input("Plazo de Operación (días)", value=invoice.get('plazo_operacion_calculado', 0), disabled=True, key=f"plazo_operacion_calculado_{idx}", label_visibility="visible")

        # Tasas y Comisiones
        with st.container():
            st.write("##### Tasas y Comisiones")
            st.write("") # Empty row for spacing

            # Determine if fields should be disabled (i.e., if it's not the first invoice and conditions are fixed)
            is_disabled = idx > 0 and st.session_state.fijar_condiciones

            col_tasa_avance, col_interes_mensual, col_comision_estructuracion, col_comision_min_pen, col_comision_min_usd, col_comision_afil_pen, col_comision_afil_usd = st.columns([0.8, 0.8, 1.4, 1, 1, 1, 1])
            with col_tasa_avance:
                invoice['tasa_de_avance'] = st.number_input("Tasa de Avance (%)", min_value=0.0, value=invoice.get('tasa_de_avance', st.session_state.default_tasa_de_avance), format="%.2f", key=f"tasa_de_avance_{idx}", label_visibility="visible", on_change=propagate_commission_changes, disabled=is_disabled)
            with col_interes_mensual:
                invoice['interes_mensual'] = st.number_input("Interés Mensual (%)", min_value=0.0, value=invoice.get('interes_mensual', st.session_state.default_interes_mensual), format="%.2f", key=f"interes_mensual_{idx}", label_visibility="visible", on_change=propagate_commission_changes, disabled=is_disabled)
            with col_comision_estructuracion:
                invoice['comision_de_estructuracion'] = st.number_input("Comisión de Estructuración (%)", min_value=0.0, value=invoice.get('comision_de_estructuracion', st.session_state.default_comision_de_estructuracion), format="%.2f", key=f"comision_de_estructuracion_{idx}", label_visibility="visible", on_change=propagate_commission_changes, disabled=is_disabled)
            with col_comision_min_pen:
                invoice['comision_minima_pen'] = st.number_input("Comisión Mínima (PEN)", min_value=0.0, value=invoice.get('comision_minima_pen', st.session_state.default_comision_minima_pen), format="%.2f", key=f"comision_minima_pen_{idx}", label_visibility="visible", on_change=propagate_commission_changes, disabled=is_disabled)
            with col_comision_min_usd:
                invoice['comision_minima_usd'] = st.number_input("Comisión Mínima (USD)", min_value=0.0, value=invoice.get('comision_minima_usd', st.session_state.default_comision_minima_usd), format="%.2f", key=f"comision_minima_usd_{idx}", label_visibility="visible", on_change=propagate_commission_changes, disabled=is_disabled)
            with col_comision_afil_pen:
                invoice['comision_afiliacion_pen'] = st.number_input("Comisión de Afiliación (PEN)", min_value=0.0, value=invoice.get('comision_afiliacion_pen', st.session_state.default_comision_afiliacion_pen), format="%.2f", key=f"comision_afiliacion_pen_{idx}", label_visibility="visible", on_change=propagate_commission_changes, disabled=is_disabled)
            with col_comision_afil_usd:
                invoice['comision_afiliacion_usd'] = st.number_input("Comisión de Afiliación (USD)", min_value=0.0, value=invoice.get('comision_afiliacion_usd', st.session_state.default_comision_afiliacion_usd), format="%.2f", key=f"comision_afiliacion_usd_{idx}", label_visibility="visible", on_change=propagate_commission_changes, disabled=is_disabled)

        # Checkboxes are placed after the main commission inputs
        col_fijar, col_afiliacion = st.columns(2)
        with col_fijar:
            # The "Fijar condiciones" checkbox is only shown for the first invoice
            if idx == 0:
                st.checkbox("Fijar condiciones", key='fijar_condiciones', on_change=propagate_commission_changes)
        with col_afiliacion:
            invoice['aplicar_comision_afiliacion'] = st.checkbox("Aplicar Comisión de Afiliación", value=invoice.get('aplicar_comision_afiliacion', False), key=f"aplicar_comision_afiliacion_{idx}")

        st.markdown("--- ")

        # --- Pasos de Cálculo y Acción (adaptado para múltiples facturas) ---
        col_paso1, col_resultados = st.columns([0.2, 3.8]) # Narrow for button, wide for table

        with col_paso1:
            

            # The button is active only when all required fields are filled
            campos_requeridos_completos = validate_inputs(invoice)

            if st.button(f"Calcular", key=f"calc_initial_disbursement_{idx}", disabled=not campos_requeridos_completos):
                if campos_requeridos_completos:
                    api_data = {
                        "plazo_operacion": invoice['plazo_operacion_calculado'],
                        "mfn": invoice['monto_neto_factura'],
                        "tasa_avance": invoice['tasa_de_avance'] / 100,
                        "interes_mensual": invoice['interes_mensual'] / 100,
                        "comision_estructuracion_pct": invoice['comision_de_estructuracion'] / 100,
                        "moneda_factura": invoice['moneda_factura'],
                        "comision_min_pen": invoice['comision_minima_pen'],
                        "comision_min_usd": invoice['comision_minima_usd'],
                        "igv_pct": 0.18,
                        "comision_afiliacion_valor": invoice['comision_afiliacion_pen'],
                        "comision_afiliacion_usd_valor": invoice['comision_afiliacion_usd'],
                        "aplicar_comision_afiliacion": invoice['aplicar_comision_afiliacion'],
                        "monto_desembolsar_manual": 0
                    }
                    with st.spinner(f'Calculando desembolso para Factura {idx + 1}...'):
                        try:
                            response = requests.post(f"{API_BASE_URL}/calcular_desembolso", json=api_data)
                            response.raise_for_status()
                            invoice['initial_calc_result'] = response.json()

                            # Automatizar el Paso 2
                            if invoice['initial_calc_result'] and 'abono_real_teorico' in invoice['initial_calc_result']:
                                abono_real_teorico = invoice['initial_calc_result']['abono_real_teorico']
                                monto_desembolsar_objetivo = (abono_real_teorico // 10) * 10 # Redondear a la decena inferior

                                api_data_recalculate = {
                                    "plazo_operacion": invoice['plazo_operacion_calculado'],
                                    "mfn": invoice['monto_neto_factura'],
                                    "interes_mensual": invoice['interes_mensual'] / 100,
                                    "comision_estructuracion_pct": invoice['comision_de_estructuracion'] / 100,
                                    "moneda_factura": invoice['moneda_factura'],
                                    "comision_min_pen": invoice['comision_minima_pen'],
                                    "comision_min_usd": invoice['comision_minima_usd'],
                                    "igv_pct": 0.18,
                                    "comision_afiliacion_valor": invoice['comision_afiliacion_pen'],
                                    "comision_afiliacion_usd_valor": invoice['comision_afiliacion_usd'],
                                    "aplicar_comision_afiliacion": invoice['aplicar_comision_afiliacion'],
                                    "monto_objetivo": monto_desembolsar_objetivo
                                }
                                with st.spinner(f'Buscando tasa de avance automáticamente para Factura {idx + 1}...'):
                                    response_recalculate = requests.post(f"{API_BASE_URL}/encontrar_tasa", json=api_data_recalculate)
                                    response_recalculate.raise_for_status()
                                    invoice['recalculate_result'] = response_recalculate.json()
                            else:
                                invoice['recalculate_result'] = None

                        except requests.exceptions.RequestException as e:
                            st.error(f"Error de conexión con la API para Factura {idx + 1}: {e}")

        with col_resultados:
            # CSS para reducir el tamaño de la fuente de los labels en los resultados iterativos
            st.markdown("""
            <style>
            /* Reduce font size for the 'Calcular' button */
            .stButton>button {
                font-size: 0.8em; /* Adjust as needed */
                padding: 0.25em 0.5em; /* Adjust padding to fit text */
            }
            label {
                font-size: 0.1em !important; /* Reducido al mínimo para prueba */
            }
            </style>
            """, unsafe_allow_html=True)

            if invoice.get('recalculate_result'):
                st.write("##### Resultados del Cálculo")
                recalc_result = invoice['recalculate_result']
                desglose = recalc_result.get('desglose_final_detallado', {})
                calculos = recalc_result.get('calculo_con_tasa_encontrada', {})
                busqueda = recalc_result.get('resultado_busqueda', {})
                moneda = invoice.get('moneda_factura', 'PEN')

                # --- Preparar todos los datos necesarios ---
                tasa_avance_pct = busqueda.get('tasa_avance_encontrada', 0) * 100
                monto_neto = invoice.get('monto_neto_factura', 0)
                capital = calculos.get('capital', 0)
                
                abono = desglose.get('abono', {})
                interes = desglose.get('interes', {})
                com_est = desglose.get('comision_estructuracion', {})
                com_afi = desglose.get('comision_afiliacion', {})
                igv = desglose.get('igv_total', {})
                margen = desglose.get('margen_seguridad', {})

                costos_totales = interes.get('monto', 0) + com_est.get('monto', 0) + com_afi.get('monto', 0) + igv.get('monto', 0)
                tasa_diaria_pct = (invoice.get('interes_mensual', 0) / 30) 

                # --- Construir la tabla en Markdown línea por línea para evitar errores de formato ---
                lines = []
                lines.append(f"| Item | % sobre Neto | Monto ({moneda}) | Fórmula de Cálculo | Detalle del Cálculo |")
                lines.append("| :--- | :--- | :--- | :--- | :--- |")
                lines.append(f"| Monto Neto de Factura | 100.00% | {monto_neto:,.2f} | `Dato de entrada` | Monto total de la factura sin IGV. |")
                lines.append(f"| Tasa de Avance Aplicada | {tasa_avance_pct:.2f}% | N/A | `Tasa final de la operación` | N/A |")
                lines.append(f"| Capital | {((capital / monto_neto) * 100) if monto_neto else 0:.2f}% | {capital:,.2f} | `Monto Neto * (Tasa de Avance / 100)` | `{monto_neto:,.2f} * ({tasa_avance_pct:.2f} / 100) = {capital:,.2f}` |")
                lines.append(f"| Intereses | {interes.get('porcentaje', 0):.2f}% | {interes.get('monto', 0):,.2f} | `Capital * ((1 + Tasa Diaria)^Plazo - 1)` | Tasa Diaria: `{invoice.get('interes_mensual', 0):.2f}% / 30 = {tasa_diaria_pct:.4f}%`, Plazo: `{calculos.get('plazo_operacion', 0)} días`. Cálculo: `{capital:,.2f} * ((1 + {tasa_diaria_pct/100:.6f})^{calculos.get('plazo_operacion', 0)} - 1) = {interes.get('monto', 0):,.2f}` |")
                lines.append(f"| Comisión de Estructuración | {com_est.get('porcentaje', 0):.2f}% | {com_est.get('monto', 0):,.2f} | `MAX(Capital * %Comisión, Mínima)` | Base: `{capital:,.2f} * ({invoice.get('comision_de_estructuracion',0):.2f} / 100) = {capital * (invoice.get('comision_de_estructuracion',0)/100):.2f}`, Mín: `{invoice.get('comision_minima_pen',0) if moneda == 'PEN' else invoice.get('comision_minima_usd',0):.2f}`. Resultado: `{com_est.get('monto', 0):,.2f}` |")
                if com_afi.get('monto', 0) > 0:
                    lines.append(f"| Comisión de Afiliación | {com_afi.get('porcentaje', 0):.2f}% | {com_afi.get('monto', 0):,.2f} | `Valor Fijo (si aplica)` | Monto fijo para la moneda {moneda}. |")
                lines.append(f"| IGV Total | {igv.get('porcentaje', 0):.2f}% | {igv.get('monto', 0):,.2f} | `(Intereses + Comisiones) * 18%` | IGV Int: `{calculos.get('igv_interes',0):.2f}`, IGV ComEst: `{calculos.get('igv_comision_estructuracion',0):.2f}`, IGV ComAfil: `{calculos.get('igv_afiliacion',0):.2f}`. Total: `{calculos.get('igv_interes',0) + calculos.get('igv_comision_estructuracion',0) + calculos.get('igv_afiliacion',0):,.2f}` |")
                lines.append("| | | | | |")
                lines.append(f"| **Monto a Desembolsar** | **{abono.get('porcentaje', 0):.2f}%** | **{abono.get('monto', 0):,.2f}** | `Capital - Costos Totales` | `{capital:,.2f} - {costos_totales:,.2f} = {abono.get('monto', 0):,.2f}` |")
                lines.append(f"| Margen de Seguridad | {margen.get('porcentaje', 0):.2f}% | {margen.get('monto', 0):,.2f} | `Monto Neto - Capital` | `{monto_neto:,.2f} - {capital:,.2f} = {margen.get('monto', 0):,.2f}` |")
                lines.append("| | | | | |")
                lines.append(f"| **Total (Monto Neto Factura)** | **100.00%** | **{monto_neto:,.2f}** | `Abono + Costos + Margen` | `{abono.get('monto', 0):,.2f} + {costos_totales:,.2f} + {margen.get('monto', 0):,.2f} = {monto_neto:,.2f}` |")
                
                tabla_md = "\n".join(lines)
                st.markdown(tabla_md, unsafe_allow_html=True)

        st.markdown("--- ") # Separador después del botón


# --- Pasos 3 y 4: Grabar e Imprimir ---
st.markdown("--- ")
st.write("#### Paso 3: Grabar Propuesta")

# Input fields for Anexo and Contract Number
with st.container():
    st.write("##### Información Adicional para la Propuesta")
    col_anexo, col_contrato = st.columns(2)
    with col_anexo:
        st.session_state.anexo_number = st.text_input("Número de Anexo", value=st.session_state.anexo_number, key="anexo_number_global")
    with col_contrato:
        st.session_state.contract_number = st.text_input("Número de Contrato", value=st.session_state.contract_number, key="contract_number_global")

# Check if any invoice has a recalculate_result to enable the save button
can_save_proposal = any(invoice.get('recalculate_result') for invoice in st.session_state.invoices_data)

if st.button("GRABAR Propuesta en Base de Datos", disabled=not can_save_proposal):
    if can_save_proposal:
        for idx, invoice in enumerate(st.session_state.invoices_data):
            if invoice.get('recalculate_result'):
                with st.spinner(f"Guardando propuesta para Factura {idx + 1}..."):
                    # Create a temporary session_data dictionary for the current invoice
                    # This is a simplified approach; a more robust solution might involve
                    # passing only the relevant invoice data to save_proposal
                    # or modifying save_proposal to accept an invoice dict directly.
                    # For now, we'll mimic the session_data structure for a single invoice.
                    temp_session_data = {
                        'emisor_nombre': invoice.get('emisor_nombre'),
                        'emisor_ruc': invoice.get('emisor_ruc'),
                        'aceptante_nombre': invoice.get('aceptante_nombre'),
                        'aceptante_ruc': invoice.get('aceptante_ruc'),
                        'numero_factura': invoice.get('numero_factura'),
                        'monto_total_factura': invoice.get('monto_total_factura'),
                        'monto_neto_factura': invoice.get('monto_neto_factura'),
                        'moneda_factura': invoice.get('moneda_factura'),
                        'fecha_emision_factura': invoice.get('fecha_emision_factura'),
                        'plazo_credito_dias': invoice.get('plazo_credito_dias'),
                        'fecha_desembolso_factoring': invoice.get('fecha_desembolso_factoring'),
                        'tasa_de_avance': invoice.get('tasa_de_avance'),
                        'interes_mensual': invoice.get('interes_mensual'),
                        'comision_de_estructuracion': invoice.get('comision_de_estructuracion'),
                        'comision_minima_pen': invoice.get('comision_minima_pen'),
                        'comision_minima_usd': invoice.get('comision_minima_usd'),
                        'comision_afiliacion_pen': invoice.get('comision_afiliacion_pen'),
                        'comision_afiliacion_usd': invoice.get('comision_afiliacion_usd'),
                        'aplicar_comision_afiliacion': invoice.get('aplicar_comision_afiliacion'),
                        'detraccion_porcentaje': invoice.get('detraccion_porcentaje'),
                        'fecha_pago_calculada': invoice.get('fecha_pago_calculada'),
                        'plazo_operacion_calculado': invoice.get('plazo_operacion_calculado'),
                        'initial_calc_result': invoice.get('initial_calc_result'),
                        'recalculate_result': invoice.get('recalculate_result'),
                        'anexo_number': st.session_state.anexo_number,
                        'contract_number': st.session_state.contract_number,
                    }
                    success, message = supabase_handler.save_proposal(temp_session_data)
                    if success:
                        st.success(message)
                        if "Propuesta con ID" in message:
                            start_index = message.find("ID ") + 3
                            end_index = message.find(" guardada")
                            st.session_state.last_saved_proposal_id = message[start_index:end_index]
                    else:
                        st.error(message)
    else:
        st.warning("No hay resultados de cálculo para guardar.")

st.markdown("--- ") # Divider between Paso 3 and Paso 4

# --- UI: Consulta y Selección de Propuestas ---
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