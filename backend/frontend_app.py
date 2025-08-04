import streamlit as st
import requests
import os
import pdf_parser
import datetime
import pdf_generator # Importar el módulo pdf_generator
import variable_data_pdf_generator # Importar el nuevo módulo para generar PDF de variables

API_BASE_URL = "http://127.0.0.1:8000" # <<< ¡IMPORTANTE! Reemplaza esto con tu URL de ngrok

# Función para preparar los datos para el PDF
def prepare_pdf_data(tipo_documento: str) -> dict:
    data = {
        "tipo_documento": tipo_documento,
        "contract_name": "CONTRATO DE FACTORING", # Valor fijo por ahora
        "client_name": st.session_state.emisor_nombre,
        "client_ruc": st.session_state.er,
        "relation_type": "FACTURA(S)", # Valor fijo por ahora
        "anexo_number": "N/A", # Se generará en pdf_generator o se pasará si existe
        "document_date": datetime.datetime.now().strftime("%d-%m-%Y"),
        "facturas_comision": [],
        "facturas_descuento": [],
        "signatures": [], # Se llenará en pdf_generator o se pasará si existe
    }

    # Datos de la factura (Tabla 1)
    data["facturas_comision"].append({
        "nro_factura": st.session_state.numero_factura,
        "fecha_vencimiento": st.session_state.fecha_pago_calculada,
        "fecha_desembolso": st.session_state.fecha_desembolso_factoring,
        "dias": st.session_state.plazo_operacion_calculado,
        "girador": st.session_state.emisor_nombre, # El emisor es el girador
        "aceptante": st.session_state.aceptante_nombre,
        "monto_neto": st.session_state.monto_neto_factura,
        "detraccion_retencion": round(((st.session_state.monto_total_factura - st.session_state.monto_neto_factura) / st.session_state.monto_total_factura) * 100, 2) if st.session_state.monto_total_factura > 0 else 0.0,
    })

    # Resultados del cálculo (Tabla 2 y Tablas Inferiores)
    if st.session_state.recalculate_result:
        calc_results = st.session_state.recalculate_result["calculo_con_tasa_encontrada"]
        data["facturas_descuento"].append({
            "nro_factura": st.session_state.numero_factura,
            "base_descuento": calc_results["capital"],
            "interes_cobrado": calc_results["interes"],
            "igv": calc_results["igv_interes"],
            "abono": calc_results["abono_real_calculado"], # Este es el abono real final
        })
        # Asegurar que facturas_descuento siempre tenga al menos dos entradas para la tabla
        while len(data["facturas_descuento"]) < 2:
            data["facturas_descuento"].append({})

        data["total_monto_neto"] = st.session_state.monto_neto_factura # Asumiendo que es el total de la única factura
        data["detracciones_total"] = round(st.session_state.monto_total_factura - st.session_state.monto_neto_factura, 2)
        data["total_neto"] = st.session_state.monto_neto_factura

        data["total_base_descuento"] = calc_results["capital"]
        data["total_interes_cobrado"] = calc_results["interes"]
        data["total_igv_descuento"] = calc_results["igv_interes"]
        data["total_abono"] = calc_results["abono_real_calculado"]

        data["margen_seguridad"] = calc_results["margen_seguridad"]
        data["comision_mas_igv"] = calc_results["comision_estructuracion"] + calc_results["igv_comision_estructuracion"]
        data["total_a_depositar"] = calc_results["abono_real_calculado"]

        data["intereses_pactados_interes"] = calc_results["interes"]
        data["intereses_pactados_igv"] = calc_results["igv_interes"]
        data["intereses_pactados_total"] = calc_results["interes"] + calc_results["igv_interes"]

        data["comision_estructuracion_comision"] = calc_results["comision_estructuracion"]
        data["comision_estructuracion_igv"] = calc_results["igv_comision_estructuracion"]
        data["comision_estructuracion_total"] = calc_results["comision_estructuracion"] + calc_results["igv_comision_estructuracion"]

        data["imprimir_comision_afiliacion"] = st.session_state.aplicar_comision_afiliacion
        data["comision_afiliacion_comision"] = calc_results["comision_afiliacion"]
        data["comision_afiliacion_igv"] = calc_results["igv_afiliacion"]
        data["comision_afiliacion_total"] = calc_results["comision_afiliacion"] + calc_results["igv_afiliacion"]

        # Intereses adicionales (siempre 0 por ahora, o se calcularán en el futuro)
        data["intereses_adicionales_int"] = 0.0
        data["intereses_adicionales_igv"] = 0.0
        data["intereses_adicionales_total"] = 0.0

    return data

# Función para simular el guardado en Supabase
def save_proforma_to_supabase(pdf_data: dict):
    tipo_documento = pdf_data.get("tipo_documento", "Documento")
    st.success(f"{tipo_documento} grabada en Supabase (simulado). Datos: {pdf_data}")

API_BASE_URL = "http://127.0.0.1:8000" # <<< ¡IMPORTANTE! Reemplaza esto con tu URL de ngrok

try:
    from supabase import create_client, Client
except ImportError:
    st.error("La librería de Supabase no está instalada. Por favor, ejecute 'pip install supabase' en su terminal y reinicie la aplicación.")
    st.stop()

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
    page_title="Calculadora de Factoring INANDES",
    page_icon="📊",
)

# --- Inicialización de Supabase ---
SUPABASE_URL = "https://bqyouppbgylodvdbctcf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJxeW91cHBiZ3lsb2R2ZGJjdGNmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM5Mjk3MTcsImV4cCI6MjA2OTUwNTcxN30.cXRXV4Owm7nSQheyWHvjVxfE8mmuRGECxm6Pm3RSR4k"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Error al inicializar Supabase: {e}")
    supabase = None

def get_razon_social_by_ruc(ruc: str) -> str:
    if not supabase or not ruc:
        return ""
    try:
        response = supabase.table('EMISORES.DEUDORES').select('"Razon Social"').eq('RUC', ruc).single().execute()
        if response.data:
            return response.data.get('Razon Social', '')
    except Exception:
        pass # Falla silenciosamente si no lo encuentra
    return ""

# --- Lógica de Cálculo de Fechas (Callback) ---
def update_date_calculations():
    try:
        # Calcular Fecha de Pago
        if st.session_state.get('fecha_emision_factura') and st.session_state.get('plazo_credito_dias', 0) > 0:
            fecha_emision_dt = datetime.datetime.strptime(st.session_state.fecha_emision_factura, "%d-%m-%Y")
            fecha_pago_dt = fecha_emision_dt + datetime.timedelta(days=int(st.session_state.plazo_credito_dias))
            st.session_state.fecha_pago_calculada = fecha_pago_dt.strftime("%d-%m-%Y")
        else:
            st.session_state.fecha_pago_calculada = ""

        # Calcular Plazo de Operación
        if st.session_state.get('fecha_pago_calculada') and st.session_state.get('fecha_desembolso_factoring'):
            fecha_pago_dt = datetime.datetime.strptime(st.session_state.fecha_pago_calculada, "%d-%m-%Y")
            fecha_desembolso_dt = datetime.datetime.strptime(st.session_state.fecha_desembolso_factoring, "%d-%m-%Y")
            if fecha_pago_dt >= fecha_desembolso_dt:
                st.session_state.plazo_operacion_calculado = (fecha_pago_dt - fecha_desembolso_dt).days
            else:
                st.session_state.plazo_operacion_calculado = 0
        else:
            st.session_state.plazo_operacion_calculado = 0
    except (ValueError, TypeError, AttributeError):
        st.session_state.fecha_pago_calculada = ""
        st.session_state.plazo_operacion_calculado = 0



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
if 'moneda_factura' not in st.session_state: st.session_state.moneda_factura = ""
if 'numero_factura' not in st.session_state: st.session_state.numero_factura = ""
if 'pdf_datos_cargados' not in st.session_state: st.session_state.pdf_datos_cargados = False
if 'initial_calc_result' not in st.session_state: st.session_state.initial_calc_result = None
if 'recalculate_result' not in st.session_state: st.session_state.recalculate_result = None
if 'comision_afiliacion_pen' not in st.session_state: st.session_state.comision_afiliacion_pen = 200.0
if 'comision_afiliacion_usd' not in st.session_state: st.session_state.comision_afiliacion_usd = 50.0 # Nuevo campo
if 'aplicar_comision_afiliacion' not in st.session_state: st.session_state.aplicar_comision_afiliacion = False

# --- Cargar CSS ---
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

# --- Sección de Carga de Archivos ---
with st.expander("Cargar datos automáticamente desde PDF (Opcional)", expanded=True):
    uploaded_pdf_file = st.file_uploader("Sube tu archivo PDF de factura", type=["pdf"], key="pdf_uploader_main")
    if uploaded_pdf_file is not None:
        temp_file_path = "C:/Users/rguti/Inandes.TECH/backend/temp_uploaded_pdf.pdf"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_pdf_file.getbuffer())

        with st.spinner("Procesando PDF y consultando base de datos..."):
            try:
                parsed_data = pdf_parser.extract_fields_from_pdf(temp_file_path)
                if parsed_data.get("error"):
                    st.error(f"Error al procesar el PDF: {parsed_data['error']}")
                else:
                    # Actualizar session state con datos del parser SOLO SI NO HAN SIDO CARGADOS O ES UN NUEVO PDF
                    if not st.session_state.pdf_datos_cargados or uploaded_pdf_file.file_id != st.session_state.get('last_uploaded_pdf_id'):
                        st.session_state.emisor_ruc = parsed_data.get('emisor_ruc', '')
                        st.session_state.aceptante_ruc = parsed_data.get('aceptante_ruc', '')
                        st.session_state.fecha_emision_factura = parsed_data.get('fecha_emision', '')
                        st.session_state.monto_total_factura = parsed_data.get('monto_total', 0.0)
                        st.session_state.monto_neto_factura = parsed_data.get('monto_neto', 0.0)
                        st.session_state.moneda_factura = parsed_data.get('moneda', 'PEN')
                        st.session_state.numero_factura = parsed_data.get('invoice_id', '') # Corregido: el parser devuelve 'invoice_id'
                        st.session_state.pdf_datos_cargados = True
                        st.session_state.last_uploaded_pdf_id = uploaded_pdf_file.file_id

                    # Enriquecer con Supabase
                    if st.session_state.emisor_ruc:
                                                st.session_state.emisor_nombre = get_razon_social_by_ruc(st.session_state.emisor_ruc)
                    if st.session_state.aceptante_ruc:
                                                st.session_state.aceptante_nombre = get_razon_social_by_ruc(st.session_state.aceptante_ruc)
                    
                    st.success("Datos cargados y enriquecidos. Revisa el formulario.")

            except Exception as e:
                st.error(f"Error al parsear el PDF: {e}")
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

def validate_inputs():
    required_fields = {
        "emisor_nombre": "Nombre del Emisor",
        "emisor_ruc": "RUC del Emisor",
        "aceptante_nombre": "Nombre del Aceptante",
        "aceptante_ruc": "RUC del Aceptante",
        "numero_factura": "Número de Factura",
        "monto_total_factura": "Monto Factura Total (con IGV)",
        "monto_neto_factura": "Monto Factura Neto",
        "moneda_factura": "Moneda de Factura",
        "fecha_emision_factura": "Fecha de Emisión",
        "plazo_credito_dias": "Plazo de Crédito",
        "fecha_desembolso_factoring": "Fecha de Desembolso",
        "tasa_de_avance": "Tasa de Avance",
        "interes_mensual": "Interés Mensual",
        "comision_de_estructuracion": "Comisión de Estructuración",
        "comision_minima_pen": "Comisión Mínima (PEN)",
        "comision_minima_usd": "Comisión Mínima (USD)",
    }

    is_valid = True
    for key, display_name in required_fields.items():
        value = st.session_state.get(key)
        if value is None or (isinstance(value, (str, list)) and not value) or (isinstance(value, (int, float)) and value <= 0 and key not in ["monto_total_factura", "monto_neto_factura"]):
            st.error(f"El campo '{display_name}' es obligatorio y no puede estar vacío o ser cero.")
            is_valid = False

    # Validar campos numéricos que deben ser > 0
        numeric_fields_gt_zero = {"monto_total_factura": "Monto Factura Total", "monto_neto_factura": "Monto Factura Neto", "tasa_de_avance": "Tasa de Avance", "interes_mensual": "Interés Mensual", "comision_de_estructuracion": "Comisión de Estructuración", "comision_minima_pen": "Comisión Mínima (PEN)", "comision_minima_usd": "Comisión Mínima (USD)"}
    for key, display_name in numeric_fields_gt_zero.items():
        value = st.session_state.get(key)
        if isinstance(value, (int, float)) and value <= 0:
            st.error(f"El campo '{display_name}' debe ser mayor que cero.")
            is_valid = False

    # Validar comisión de afiliación condicionalmente
    if st.session_state.get('aplicar_comision_afiliacion'):
        comision_afiliacion_val = st.session_state.get('comision_afiliacion_pen')
        if comision_afiliacion_val is None or comision_afiliacion_val <= 0:
            st.error("Si 'Aplicar Comisión de Afiliación' está marcado, el 'Comisión de Afiliación (PEN)' debe ser mayor que cero.")
            is_valid = False

    return is_valid

# --- Formulario principal ---
update_date_calculations() # Calcular fechas antes de dibujar el formulario
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
    st.text_input("NÚMERO DE FACTURA", key="numero_factura", disabled=True)
    st.number_input("MONTO FACTURA TOTAL (CON IGV)", min_value=0.0, key="monto_total_factura", format="%.2f", value=st.session_state.monto_total_factura)
    st.number_input("MONTO FACTURA NETO", min_value=0.0, key="monto_neto_factura", format="%.2f", value=st.session_state.monto_neto_factura)
    currency_options = ["PEN", "USD"]
    moneda_factura_index = currency_options.index(st.session_state.moneda_factura) if st.session_state.moneda_factura in currency_options else None
    st.selectbox("MONEDA DE FACTURA", currency_options, index=moneda_factura_index, key="moneda_factura")

    # Campo calculado: Detracción / Retención
    detraccion_retencion_pct = 0.0
    if st.session_state.monto_total_factura > 0:
        detraccion_retencion_pct = ((st.session_state.monto_total_factura - st.session_state.monto_neto_factura) / st.session_state.monto_total_factura) * 100
    st.text_input("Detracción / Retención (%)", value=f"{detraccion_retencion_pct:.2f}%", disabled=True)

with col3:
    st.write("##### Fechas y Plazos")
    st.text_input("Fecha de Emisión (DD-MM-YYYY)", key='fecha_emision_factura', on_change=update_date_calculations)
    st.number_input("Plazo de Crédito (días)", min_value=1, step=1, key='plazo_credito_dias', on_change=update_date_calculations)
    st.text_input("Fecha de Pago (Calculada)", key='fecha_pago_calculada', disabled=True)
    st.text_input("Fecha de Desembolso (DD-MM-YYYY)", key='fecha_desembolso_factoring', on_change=update_date_calculations)
    st.number_input("Plazo de Operación (días)", key='plazo_operacion_calculado', disabled=True, help="Se calcula como: Fecha de Pago - Fecha de Desembolso")

with col4:
    st.write("##### Tasas y Comisiones")
    st.number_input("Tasa de Avance (%)", min_value=0.0, value=98.0, format="%.2f", key="tasa_de_avance")
    st.number_input("Interés Mensual (%)", min_value=0.0, value=1.25, format="%.2f", key="interes_mensual")
    st.number_input("Comisión de Estructuración (%)", min_value=0.0, value=0.5, format="%.2f", key="comision_de_estructuracion")
    st.number_input("Comisión Mínima (PEN)", min_value=0.0, value=10.0, format="%.2f", key="comision_minima_pen")
    st.number_input("Comisión Mínima (USD)", min_value=0.0, value=3.0, format="%.2f", key="comision_minima_usd")
    st.number_input("Comisión de Afiliación (PEN)", min_value=0.0, value=200.0, format="%.2f", key="comision_afiliacion_pen")
    st.number_input("Comisión de Afiliación (USD)", min_value=0.0, value=50.0, format="%.2f", key="comision_afiliacion_usd") # Nuevo campo
    st.checkbox("Aplicar Comisión de Afiliación", key="aplicar_comision_afiliacion")

st.markdown("---")

col_paso1, col_paso2 = st.columns(2)

with col_paso1:
    st.write("#### Paso 1: Calcular Desembolso Inicial")
    submitted_initial_calc = st.button("Calcular Desembolso Inicial")

    if submitted_initial_calc:
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
                "comision_afiliacion_usd_valor": st.session_state.comision_afiliacion_usd, # NUEVO PARAMETRO
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
    st.write("#### Paso 2: Encontrar Tasa de Avance para un Monto Objetivo")
    with st.form("recalculate_form"):
        monto_desembolsar_manual = st.number_input("Monto a Desembolsar Objetivo", min_value=0.0, value=0.0, format="%.2f", key="mdm_recalc")
        submitted_recalculate = st.form_submit_button("Encontrar Tasa de Avance", disabled=not st.session_state.initial_calc_result)

        if submitted_recalculate:
            if monto_desembolsar_manual > 0:
                if validate_inputs(): # Añadir validación aquí también
                    # Re-captura los valores del estado de sesión por si cambiaron
                    api_data = {
                        "plazo_operacion": st.session_state.plazo_operacion_calculado,
                        "mfn": st.session_state.monto_neto_factura, # Usar valor del state
                        "interes_mensual": st.session_state.interes_mensual / 100 if 'interes_mensual' in st.session_state else 0.0125,
                        "comision_estructuracion_pct": st.session_state.comision_de_estructuracion / 100 if 'comision_de_estructuracion' in st.session_state else 0.005,
                        "moneda_factura": st.session_state.moneda_factura,
                        "comision_min_pen": st.session_state.comision_minima_pen if 'comision_minima_pen' in st.session_state else 10.0,
                        "comision_min_usd": st.session_state.comision_minima_usd if 'comision_minima_usd' in st.session_state else 3.0,
                        "igv_pct": 0.18,
                        "comision_afiliacion_valor": st.session_state.comision_afiliacion_pen,
                        "comision_afiliacion_usd_valor": st.session_state.comision_afiliacion_usd, # NUEVO PARAMETRO
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
            else:
                st.error("Debe ingresar un Monto a Desembolsar Objetivo mayor a 0.")

    if st.session_state.recalculate_result:
        st.write("##### Resultado de la Búsqueda")
        st.json(st.session_state.recalculate_result)

# Nueva sección para Grabar e Imprimir Documento
st.markdown("---")

# Paso 3: Grabar Documento
gr_title_col, gr_cot_btn_col, gr_prop_btn_col = st.columns([0.4, 0.3, 0.3])
with gr_title_col:
    st.write("#### Paso 3: Grabar Documento")
 
with gr_prop_btn_col:
    if st.button("GRABAR Propuesta", disabled=not st.session_state.recalculate_result, key="grabar_propuesta_btn"):
        with st.spinner("Generando PDF de variables..."):
            # Recopilar todas las variables relevantes del session_state
            all_vars = {
                key: value for key, value in st.session_state.items()
                if not key.startswith("pdf_uploader") and key not in ["initial_calc_result", "recalculate_result"]
            }

            # Añadir resultados de los cálculos si existen
            if st.session_state.initial_calc_result:
                all_vars["initial_calc_result"] = st.session_state.initial_calc_result
            if st.session_state.recalculate_result:
                all_vars["recalculate_result"] = st.session_state.recalculate_result

            # Guardar en Supabase
            output_filename = f"Variables_Propuesta_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"
            output_filepath = os.path.join("C:/Users/rguti/Inandes.TECH/generated_pdfs", output_filename)
            variable_data_pdf_generator.generate_variable_pdf(all_vars, output_filepath)
            st.success(f"PDF de variables generado en: {output_filepath}")

st.markdown("---")

# Paso 4: Imprimir Documento
imp_title_col, imp_cot_btn_col, imp_prop_btn_col = st.columns([0.4, 0.3, 0.3])
with imp_title_col:
    st.write("#### Paso 4: Imprimir Documento")
 
with imp_prop_btn_col:
    if st.button("IMPRIMIR Propuesta", disabled=not st.session_state.recalculate_result, key="imprimir_propuesta_btn"):
        with st.spinner("Generando Propuesta para impresión..."):
            pdf_data = prepare_pdf_data("Propuesta")
            output_filepath = os.path.join("C:/Users/rguti/Inandes.TECH/generated_pdfs", f"Propuesta_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf")
            pdf_generator.generate_pdf(output_filepath, pdf_data)
            st.success(f"Propuesta generada para impresión en: {output_filepath}")