
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

# Importar las nuevas funciones de la calculadora
from calculadora_factoring_V_CLI import calcular_desembolso_inicial, encontrar_tasa_de_avance

app = FastAPI(
    title="API de Calculadora de Factoring INANDES",
    description="Provee endpoints para los cálculos de factoring.",
    version="2.0.0",
)

# --- Middleware de CORS ---
# Permite que el frontend (ej. en Vercel) se comunique con este backend (ej. en Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, deberías restringir esto a tu dominio de frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modelos de Datos (Pydantic) ---

class CalcularDesembolsoRequest(BaseModel):
    plazo_operacion: int
    mfn: float
    tasa_avance: float
    interes_mensual: float
    comision_estructuracion_pct: float
    moneda_factura: str
    comision_min_pen: float
    comision_min_usd: float
    igv_pct: float
    comision_afiliacion_valor: float = 0.0
    aplicar_comision_afiliacion: bool = False

class EncontrarTasaRequest(BaseModel):
    plazo_operacion: int
    mfn: float
    interes_mensual: float
    comision_estructuracion_pct: float
    moneda_factura: str
    comision_min_pen: float
    comision_min_usd: float
    igv_pct: float
    monto_objetivo: float
    comision_afiliacion_valor: float = 0.0
    aplicar_comision_afiliacion: bool = False

# --- Endpoints de la API ---

@app.get("/")
async def read_root():
    return {"message": "Bienvenido a la API de la Calculadora de Factoring v2"}

@app.post("/calcular_desembolso")
async def calcular_desembolso_endpoint(request: CalcularDesembolsoRequest):
    """
    Endpoint para el Modo 1: Cálculo Directo.
    """
    resultado = calcular_desembolso_inicial(**request.dict(exclude_unset=False))
    return resultado

@app.post("/encontrar_tasa")
async def encontrar_tasa_endpoint(request: EncontrarTasaRequest):
    """
    Endpoint para el Modo 2: Búsqueda de Tasa de Avance.
    """
    resultado = encontrar_tasa_de_avance(**request.dict(exclude_unset=False))
    return resultado

# Para ejecutar la aplicación localmente:
# uvicorn main:app --reload
