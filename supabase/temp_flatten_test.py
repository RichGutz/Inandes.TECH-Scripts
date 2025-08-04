import sys
sys.path.append('C:/Users/rguti/Inandes.TECH/backend')

from variable_data_pdf_generator import flatten_dict
import json

# Simular un st.session_state con datos de ejemplo
sample_session_state = {
    "emisor_nombre": "EMPRESA_EJEMPLO_SAC",
    "emisor_ruc": "12345678901",
    "numero_factura": "F001-123",
    "monto_total_factura": 1000.0,
    "monto_neto_factura": 850.0,
    "moneda_factura": "PEN",
    "fecha_emision_factura": "01-07-2025",
    "plazo_credito_dias": 30,
    "fecha_desembolso_factoring": "01-08-2025",
    "plazo_operacion_calculado": 30,
    "tasa_de_avance": 90.0,
    "interes_mensual": 1.5,
    "comision_de_estructuracion": 0.5,
    "comision_minima_pen": 10.0,
    "comision_minima_usd": 3.0,
    "aplicar_comision_afiliacion": True,
    "comision_afiliacion_pen": 200.0,
    "comision_afiliacion_usd": 50.0,
    "initial_calc_result": {
        "capital": 800.0,
        "interes": 12.0,
        "igv_interes": 2.16,
        "comision_estructuracion": 4.0,
        "igv_comision": 0.72,
        "comision_afiliacion": 200.0,
        "igv_afiliacion": 36.0,
        "abono_real_teorico": 545.12,
        "monto_desembolsado": 545.0,
        "margen_seguridad": 50.0,
        "plazo_operacion": 30
    },
    "recalculate_result": {
        "resultado_busqueda": {
            "tasa_avance_encontrada": 0.92,
            "abono_real_calculado": 820.0,
            "monto_objetivo": 820.0
        },
        "calculo_con_tasa_encontrada": {
            "capital": 820.0,
            "interes": 12.3,
            "igv_interes": 2.21,
            "comision_estructuracion": 4.1,
            "igv_comision_estructuracion": 0.74,
            "comision_afiliacion": 200.0,
            "igv_afiliacion": 36.0,
            "margen_seguridad": 30.0,
            "plazo_operacion": 30
        }
    }
}

# Aplanar el diccionario
flattened_data = flatten_dict(sample_session_state)

# Imprimir el resultado
print(json.dumps(flattened_data, indent=4, ensure_ascii=False))
