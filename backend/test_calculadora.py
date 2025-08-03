import sys
import os

# Añadir el directorio padre al path para poder importar calculadora_factoring
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from calculadora_factoring import calcular_desembolso_inicial, encontrar_tasa_de_avance

print("--- Probando calculadora_factoring.py ---")

# --- Datos de prueba base (similares a los del pseudocódigo) ---
base_data = {
    "plazo_operacion": 56,
    "mfn": 5669.90,
    "interes_mensual": 0.0125,
    "comision_estructuracion_pct": 0.005,
    "moneda_factura": "PEN",
    "comision_min_pen": 10,
    "comision_min_usd": 3,
    "igv_pct": 0.18
}

# --- Prueba 1: calcular_desembolso_inicial SIN comisión de afiliación ---
print("\n--- FASE 1: Cálculo Inicial (SIN Comisión de Afiliación) ---")
data_sin_afiliacion = base_data.copy()
data_sin_afiliacion["tasa_avance"] = 0.98
resultado_sin_afiliacion = calcular_desembolso_inicial(**data_sin_afiliacion)
print(f"Resultado SIN afiliación: {resultado_sin_afiliacion}")

# --- Prueba 2: calcular_desembolso_inicial CON comisión de afiliación ---
print("\n--- FASE 1: Cálculo Inicial (CON Comisión de Afiliación) ---")
data_con_afiliacion = base_data.copy()
data_con_afiliacion["tasa_avance"] = 0.98
data_con_afiliacion["comision_afiliacion_valor"] = 200.0
data_con_afiliacion["aplicar_comision_afiliacion"] = True
resultado_con_afiliacion = calcular_desembolso_inicial(**data_con_afiliacion)
print(f"Resultado CON afiliación: {resultado_con_afiliacion}")

# --- Prueba 3: encontrar_tasa_de_avance SIN comisión de afiliación ---
print("\n--- FASE 2: Búsqueda de Tasa (SIN Comisión de Afiliación) ---")
data_busqueda_sin_afiliacion = base_data.copy()
data_busqueda_sin_afiliacion["monto_objetivo"] = 5360.00
resultado_busqueda_sin_afiliacion = encontrar_tasa_de_avance(**data_busqueda_sin_afiliacion)
print(f"Resultado Búsqueda SIN afiliación: {resultado_busqueda_sin_afiliacion}")

# --- Prueba 4: encontrar_tasa_de_avance CON comisión de afiliación ---
print("\n--- FASE 2: Búsqueda de Tasa (CON Comisión de Afiliación) ---")
data_busqueda_con_afiliacion = base_data.copy()
data_busqueda_con_afiliacion["monto_objetivo"] = 5360.00
data_busqueda_con_afiliacion["comision_afiliacion_valor"] = 200.0
data_busqueda_con_afiliacion["aplicar_comision_afiliacion"] = True
resultado_busqueda_con_afiliacion = encontrar_tasa_de_avance(**data_busqueda_con_afiliacion)
print(f"Resultado Búsqueda CON afiliación: {resultado_busqueda_con_afiliacion}")
