

import datetime
import math

def calcular_desembolso_inicial(
    plazo_operacion: int,
    mfn: float,
    tasa_avance: float,
    interes_mensual: float,
    comision_estructuracion_pct: float,
    moneda_factura: str,
    comision_min_pen: float,
    comision_min_usd: float,
    igv_pct: float,
    comision_afiliacion_valor: float = 0.0,
    comision_afiliacion_usd_valor: float = 0.0, # NUEVO PARAMETRO
    aplicar_comision_afiliacion: bool = False
) -> dict:
    """
    Calcula los detalles de una operación de factoring basándose en una tasa de avance fija.
    Corresponde al cálculo "PRE REDONDEO" del Excel.
    """
    # --- Validaciones y Conversiones Iniciales ---
    if plazo_operacion < 0:
        return {"error": "El plazo de operación no puede ser negativo."}

    # --- El Valor Neto Real es un input directo ---
    valor_neto_real = mfn

    # --- Paso 1: Calcular Capital ---
    capital = valor_neto_real * tasa_avance

    # --- Paso 2: Calcular Intereses (COMPUESTO) ---
    tasa_diaria = interes_mensual / 30
    interes = capital * (((1 + tasa_diaria) ** plazo_operacion) - 1)
    igv_interes = interes * igv_pct

    # --- Paso 3: Comisión de estructuración ---
    comision_estructuracion_base = capital * comision_estructuracion_pct
    comision_minima = comision_min_usd if moneda_factura == "USD" else comision_min_pen
    comision_estructuracion = max(comision_estructuracion_base, comision_minima)
    igv_comision = comision_estructuracion * igv_pct

    # --- Paso 4: Calcular Abono Real Teórico ---
    abono_real_teorico = capital - interes - igv_interes - comision_estructuracion - igv_comision

    # Aplicar Comisión de Afiliación si el checkbox está marcado
    comision_afiliacion = 0.0
    igv_afiliacion = 0.0
    if aplicar_comision_afiliacion:
        if moneda_factura == "PEN":
            comision_afiliacion = comision_afiliacion_valor
        elif moneda_factura == "USD":
            comision_afiliacion = comision_afiliacion_usd_valor
        else:
            comision_afiliacion = 0.0 # Valor por defecto si la moneda no es PEN ni USD
        igv_afiliacion = comision_afiliacion * igv_pct
        abono_real_teorico -= (comision_afiliacion + igv_afiliacion)

    # --- Paso 5: Desembolso final ---
    monto_desembolsar = math.floor(abono_real_teorico)

    # --- Paso 6: Margen de seguridad ---
    margen_seguridad = valor_neto_real - capital

    return {
        "capital": round(capital, 2),
        "interes": round(interes, 2),
        "igv_interes": round(igv_interes, 2),
        "comision_estructuracion": round(comision_estructuracion, 2),
        "igv_comision": round(igv_comision, 2),
        "comision_afiliacion": round(comision_afiliacion, 2),
        "igv_afiliacion": round(igv_afiliacion, 2),
        "abono_real_teorico": round(abono_real_teorico, 2),
        "monto_desembolsado": round(monto_desembolsar, 2),
        "margen_seguridad": round(margen_seguridad, 2),
        "plazo_operacion": plazo_operacion
    }

def encontrar_tasa_de_avance(
    plazo_operacion: int,
    mfn: float,
    interes_mensual: float,
    comision_estructuracion_pct: float,
    moneda_factura: str,
    comision_min_pen: float,
    comision_min_usd: float,
    igv_pct: float,
    monto_objetivo: float,
    comision_afiliacion_valor: float = 0.0,
    comision_afiliacion_usd_valor: float = 0.0, # NUEVO PARAMETRO
    aplicar_comision_afiliacion: bool = False,
    tasa_avance_min: float = 0.90,
    tasa_avance_max: float = 1.00,
    tolerancia: float = 0.01,
    max_iteraciones: int = 100
) -> dict:
    """
    Encuentra la tasa de avance (descuento) necesaria para alcanzar un monto de desembolso objetivo.
    Utiliza la lógica de cálculo inverso del Excel.
    """
    # --- El Valor Neto Real es un input directo ---
    valor_neto_real = mfn

    # --- Lógica de Cálculo Inverso ---
    # Factores de costo
    tasa_diaria = interes_mensual / 30
    factor_interes = ((1 + tasa_diaria) ** plazo_operacion) - 1
    factor_comision_estructuracion = comision_estructuracion_pct

    # Costo total como un factor del capital
    costo_bruto_factor = factor_interes + factor_comision_estructuracion
    costo_total_factor = costo_bruto_factor * (1 + igv_pct)

    # Ecuación: Capital - (Capital * costo_total_factor) = monto_objetivo
    # Capital * (1 - costo_total_factor) = monto_objetivo
    capital_necesario = monto_objetivo / (1 - costo_total_factor)

    # La comisión podría ser la mínima, hay que verificar
    comision_estructuracion_base_recalculada = capital_necesario * factor_comision_estructuracion
    comision_minima = comision_min_usd if moneda_factura == "USD" else comision_min_pen
    comision_estructuracion_final = max(comision_estructuracion_base_recalculada, comision_minima)

    # Si la comisión fue la mínima, el costo total cambia y hay que recalcular el capital
    if comision_estructuracion_final == comision_minima:
        costo_bruto_sin_comision = factor_interes
        costo_total_sin_comision = costo_bruto_sin_comision * (1 + igv_pct)
        comision_minima_con_igv = comision_minima * (1 + igv_pct)
        capital_necesario = (monto_objetivo + comision_minima_con_igv) / (1 - costo_total_sin_comision)

    # Tasa de avance encontrada
    tasa_avance_encontrada = capital_necesario / valor_neto_real

    # --- Verificación y Desglose Final ---
    capital = capital_necesario
    interes = capital * factor_interes
    igv_interes = interes * igv_pct
    comision_estructuracion = max(capital * factor_comision_estructuracion, comision_minima)
    igv_comision_estructuracion = comision_estructuracion * igv_pct
    abono_real = capital - interes - igv_interes - comision_estructuracion - igv_comision_estructuracion

    comision_afiliacion = 0.0
    igv_afiliacion = 0.0
    if aplicar_comision_afiliacion:
        if moneda_factura == "PEN":
            comision_afiliacion = comision_afiliacion_valor
        elif moneda_factura == "USD":
            comision_afiliacion = comision_afiliacion_usd_valor
        else:
            comision_afiliacion = 0.0 # Valor por defecto si la moneda no es PEN ni USD
        igv_afiliacion = comision_afiliacion * igv_pct
        abono_real -= (comision_afiliacion + igv_afiliacion)

    margen_seguridad = valor_neto_real - capital

    return {
        "resultado_busqueda": {
            "tasa_avance_encontrada": round(tasa_avance_encontrada, 4),
            "abono_real_calculado": round(abono_real, 2),
            "monto_objetivo": monto_objetivo
        },
        "calculo_con_tasa_encontrada": {
            "capital": round(capital, 2),
            "interes": round(interes, 2),
            "igv_interes": round(igv_interes, 2),
            "comision_estructuracion": round(comision_estructuracion, 2),
            "igv_comision_estructuracion": round(igv_comision_estructuracion, 2),
            "comision_afiliacion": round(comision_afiliacion, 2),
            "igv_afiliacion": round(igv_afiliacion, 2),
            "margen_seguridad": round(margen_seguridad, 2),
            "plazo_operacion": plazo_operacion
        }
    }

# --- Ejemplo de uso con los datos del pseudocódigo ---
if __name__ == '__main__':
    # Datos de ejemplo validados con el Excel
    datos_ejemplo = {
        "plazo_operacion": 56,
        "mfn": 5669.90, # Valor Neto definitivo
        "tasa_avance": 0.98, # Descuento (%)
        "interes_mensual": 0.0125,
        "comision_estructuracion_pct": 0.005,
        "moneda_factura": "PEN",
        "comision_min_pen": 10,
        "comision_min_usd": 3,
        "igv_pct": 0.18
    }

    print("--- FASE 1: Cálculo Inicial (PRE REDONDEO) ---")
    datos_ejemplo["comision_afiliacion_usd_valor"] = 50.0 # Añadir para el ejemplo
    resultado_directo = calcular_desembolso_inicial(**datos_ejemplo)
    print(resultado_directo)

    print("\n--- FASE 2: Búsqueda de Tasa para Monto Objetivo ---")
    datos_busqueda = datos_ejemplo.copy()
    datos_busqueda["monto_objetivo"] = 5360.00 # ESTE TARGET LO FIJAN
    del datos_busqueda["tasa_avance"]
    datos_busqueda["comision_afiliacion_usd_valor"] = 50.0 # Añadir para el ejemplo
    resultado_busqueda = encontrar_tasa_de_avance(**datos_busqueda)
    print(resultado_busqueda)

