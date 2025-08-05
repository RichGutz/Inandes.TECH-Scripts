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
        "fecha_emision_factura": "Fecha de Emisión", "plazo_credito_dias": "Plazo de Crédito",
        "fecha_desembolso_factoring": "Fecha de Desembolso", "tasa_de_avance": "Tasa de Avance",
        "interes_mensual": "Interés Mensual", "comision_de_estructuracion": "Comisión de Estructuración",
    }
    is_valid = True
    for key, name in required_fields.items():
        if not invoice.get(key):
            st.error(f"El campo '{name}' es obligatorio para la factura {invoice.get('parsed_pdf_name', 'N/A')}.")
            is_valid = False
    
    numeric_fields = {
        "monto_total_factura": "Monto Factura Total", "monto_neto_factura": "Monto Factura Neto",
        "tasa_de_avance": "Tasa de Avance", "interes_mensual": "Interés Mensual"
    }
    for key, name in numeric_fields.items():
        if invoice.get(key, 0) <= 0:
            st.error(f"El campo '{name}' debe ser mayor que cero para la factura {invoice.get('parsed_pdf_name', 'N/A')}.")
            is_valid = False
    return is_valid

def propagate_commission_changes():
    print("propagate_commission_changes called!")
    if st.session_state.invoices_data:
        # Get values from the first invoice (index 0)
        first_invoice = st.session_state.invoices_data[0]
        tasa_de_avance = first_invoice['tasa_de_avance']
        interes_mensual = first_invoice['interes_mensual']
        comision_de_estructuracion = first_invoice['comision_de_estructuracion']
        comision_minima_pen = first_invoice['comision_minima_pen']
        comision_minima_usd = first_invoice['comision_minima_usd']
        comision_afiliacion_pen = first_invoice['comision_afiliacion_pen']
        comision_afiliacion_usd = first_invoice['comision_afiliacion_usd']
        aplicar_comision_afiliacion = first_invoice['aplicar_comision_afiliacion']

        # Propagate to all other invoices (from index 1 onwards)
        for i in range(1, len(st.session_state.invoices_data)):
            current_invoice = st.session_state.invoices_data[i]
            current_invoice['tasa_de_avance'] = tasa_de_avance
            current_invoice['interes_mensual'] = interes_mensual
            current_invoice['comision_de_estructuracion'] = comision_de_estructuracion
            current_invoice['comision_minima_pen'] = comision_minima_pen
            current_invoice['comision_minima_usd'] = comision_minima_usd
            current_invoice['comision_afiliacion_pen'] = comision_afiliacion_pen
            current_invoice['comision_afiliacion_usd'] = comision_afiliacion_usd
            current_invoice['aplicar_comision_afiliacion'] = aplicar_comision_afiliacion

        # Force a rerun to ensure UI updates immediately
        st.rerun()

# --- Inicialización del Session State ---

# --- Inicialización del Session State ---
if 'invoices_data' not in st.session_state: st.session_state.invoices_data = []
if 'pdf_datos_cargados' not in st.session_state: st.session_state.pdf_datos_cargados = False
if 'last_uploaded_pdf_files_ids' not in st.session_state: st.session_state.last_uploaded_pdf_files_ids = []
if 'last_saved_proposal_id' not in st.session_state: st.session_state.last_saved_proposal_id = ''
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
with st.expander("Cargar datos automáticamente desde PDF (Opcional)", expanded=True):
    uploaded_pdf_files = st.file_uploader("Sube tus archivos PDF de factura", type=["pdf"], key="pdf_uploader_main", accept_multiple_files=True)
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
                                'plazo_credito_dias': 30, # Default value
                                'fecha_desembolso_factoring': datetime.date.today().strftime('%d-%m-%Y'), # Default value
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
            col_fecha_emision, col_plazo_credito, col_fecha_pago, col_fecha_desembolso, col_plazo_operacion = st.columns(5)
            with col_fecha_emision:
                invoice['fecha_emision_factura'] = st.text_input("Fecha de Emisión (DD-MM-YYYY)", value=invoice.get('fecha_emision_factura', ''), key=f"fecha_emision_factura_{idx}", on_change=update_date_calculations, args=(invoice,), label_visibility="visible")
            with col_plazo_credito:
                invoice['plazo_credito_dias'] = st.number_input("Plazo de Crédito (días)", min_value=1, step=1, value=invoice.get('plazo_credito_dias', 30), key=f"plazo_credito_dias_{idx}", on_change=update_date_calculations, args=(invoice,), label_visibility="visible")
            with col_fecha_pago:
                st.text_input("Fecha de Pago (Calculada)", value=invoice.get('fecha_pago_calculada', ''), disabled=True, key=f"fecha_pago_calculada_{idx}", label_visibility="visible")
            with col_fecha_desembolso:
                invoice['fecha_desembolso_factoring'] = st.text_input("Fecha de Desembolso (DD-MM-YYYY)", value=invoice.get('fecha_desembolso_factoring', datetime.date.today().strftime('%d-%m-%Y')), key=f"fecha_desembolso_factoring_{idx}", on_change=update_date_calculations, args=(invoice,), label_visibility="visible")
            with col_plazo_operacion:
                st.number_input("Plazo de Operación (días)", value=invoice.get('plazo_operacion_calculado', 0), disabled=True, key=f"plazo_operacion_calculado_{idx}", label_visibility="visible")

        # Tasas y Comisiones
        with st.container():
            st.write("##### Tasas y Comisiones")
            st.write("") # Empty row for spacing
            col_tasa_avance, col_interes_mensual, col_comision_estructuracion, col_comision_min_pen, col_comision_min_usd, col_comision_afil_pen, col_comision_afil_usd = st.columns([0.8, 0.8, 1.4, 1, 1, 1, 1])
            with col_tasa_avance:
                invoice['tasa_de_avance'] = st.number_input("Tasa de Avance (%)", min_value=0.0, value=invoice.get('tasa_de_avance', st.session_state.default_tasa_de_avance), format="%.2f", key=f"tasa_de_avance_{idx}", label_visibility="visible", on_change=propagate_commission_changes if idx == 0 else None)
            with col_interes_mensual:
                invoice['interes_mensual'] = st.number_input("Interés Mensual (%)", min_value=0.0, value=invoice.get('interes_mensual', st.session_state.default_interes_mensual), format="%.2f", key=f"interes_mensual_{idx}", label_visibility="visible", on_change=propagate_commission_changes if idx == 0 else None)
            with col_comision_estructuracion:
                invoice['comision_de_estructuracion'] = st.number_input("Comisión de Estructuración (%)", min_value=0.0, value=invoice.get('comision_de_estructuracion', st.session_state.default_comision_de_estructuracion), format="%.2f", key=f"comision_de_estructuracion_{idx}", label_visibility="visible", on_change=propagate_commission_changes if idx == 0 else None)
            with col_comision_min_pen:
                invoice['comision_minima_pen'] = st.number_input("Comisión Mínima (PEN)", min_value=0.0, value=invoice.get('comision_minima_pen', st.session_state.default_comision_minima_pen), format="%.2f", key=f"comision_minima_pen_{idx}", label_visibility="visible", on_change=propagate_commission_changes if idx == 0 else None)
            with col_comision_min_usd:
                invoice['comision_minima_usd'] = st.number_input("Comisión Mínima (USD)", min_value=0.0, value=invoice.get('comision_minima_usd', st.session_state.default_comision_minima_usd), format="%.2f", key=f"comision_minima_usd_{idx}", label_visibility="visible", on_change=propagate_commission_changes if idx == 0 else None)
            with col_comision_afil_pen:
                invoice['comision_afiliacion_pen'] = st.number_input("Comisión de Afiliación (PEN)", min_value=0.0, value=invoice.get('comision_afiliacion_pen', st.session_state.default_comision_afiliacion_pen), format="%.2f", key=f"comision_afiliacion_pen_{idx}", label_visibility="visible", on_change=propagate_commission_changes if idx == 0 else None)
            with col_comision_afil_usd:
                invoice['comision_afiliacion_usd'] = st.number_input("Comisión de Afiliación (USD)", min_value=0.0, value=invoice.get('comision_afiliacion_usd', st.session_state.default_comision_afiliacion_usd), format="%.2f", key=f"comision_afiliacion_usd_{idx}", label_visibility="visible", on_change=propagate_commission_changes if idx == 0 else None)
        invoice['aplicar_comision_afiliacion'] = st.checkbox("Aplicar Comisión de Afiliación", value=invoice.get('aplicar_comision_afiliacion', False), key=f"aplicar_comision_afiliacion_{idx}", on_change=propagate_commission_changes if idx == 0 else None)

        st.markdown("--- ")

        # --- Pasos de Cálculo y Acción (adaptado para múltiples facturas) ---
        st.write("#### Paso 1: Calcular Desembolso Inicial")
        if st.button(f"Calcular Desembolso Inicial para Factura {idx + 1}", key=f"calc_initial_disbursement_{idx}"):
            if validate_inputs(invoice):
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

        st.markdown("--- ") # Separador después del botón

        # CSS para reducir el tamaño de la fuente de los labels en los resultados iterativos
        st.markdown("""
        <style>
        label {
            font-size: 0.1em !important; /* Reducido al mínimo para prueba */
        }
        </style>
        """, unsafe_allow_html=True)

        if invoice['recalculate_result']:
            st.write("##### Resultados del Cálculo Iterativo")
            recalc_result = invoice['recalculate_result']

            # Define the order and labels for the results
            results_data = [
                ("Tasa de Avance Encontrada", recalc_result.get('resultado_busqueda', {}).get('tasa_avance_encontrada', 0.0) * 100, ".2f"),
                ("Monto Desembolsar Objetivo", recalc_result.get('resultado_busqueda', {}).get('monto_objetivo', 0.0), ".2f"),
                ("Capital", recalc_result.get('calculo_con_tasa_encontrada', {}).get('capital', 0.0), ".2f"),
                ("Interés", recalc_result.get('calculo_con_tasa_encontrada', {}).get('interes', 0.0), ".2f"),
                ("IGV Interés", recalc_result.get('calculo_con_tasa_encontrada', {}).get('igv_interes', 0.0), ".2f"),
                ("Comisión Estructuración", recalc_result.get('calculo_con_tasa_encontrada', {}).get('comision_estructuracion', 0.0), ".2f"),
                ("IGV Comisión Estructuración", recalc_result.get('calculo_con_tasa_encontrada', {}).get('igv_comision_estructuracion', 0.0), ".2f"),
                ("Comisión Afiliación", recalc_result.get('calculo_con_tasa_encontrada', {}).get('comision_afiliacion', 0.0), ".2f"),
                ("IGV Afiliación", recalc_result.get('igv_afiliacion', 0.0), ".2f"),
                ("Margen Seguridad", recalc_result.get('calculo_con_tasa_encontrada', {}).get('margen_seguridad', 0.0), ".2f"),
            ]

            # Create two rows of 5 columns each for the results
            cols_results_row1 = st.columns(5)
            for i, (label, value, format_str) in enumerate(results_data[:5]):
                with cols_results_row1[i]:
                    st.metric(label, value=format(value, format_str))

            cols_results_row2 = st.columns(5)
            for i, (label, value, format_str) in enumerate(results_data[5:]):
                with cols_results_row2[i]:
                    st.metric(label, value=format(value, format_str))

else:
    st.info("Carga uno o más archivos PDF para comenzar.")


# --- UI: Consulta y Selección de Propuestas ---
st.markdown("--- ")
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