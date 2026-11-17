"""Tablero de mercados: trae cifras de APIs y las etiqueta por calidad de fuente.

Se puede correr solo para probar:  python tablero.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass, asdict

import requests

import config

TIMEOUT = 20
SESION = requests.Session()
SESION.headers["User-Agent"] = "radar-diario/1.0"


@dataclass
class Dato:
    nombre: str
    valor: float | None
    unidad: str
    fecha: str | None          # fecha del dato (AAAA-MM-DD)
    variacion: float | None    # variación contra el dato anterior
    tipo_variacion: str        # "%" (porcentual) o "pb" (puntos básicos) o ""
    fuente: str
    calidad: str               # primaria | fuente secundaria | no verificado
    error: str | None = None

    def a_dict(self) -> dict:
        return asdict(self)


def _fallido(nombre, unidad, fuente, calidad, error) -> Dato:
    return Dato(nombre, None, unidad, None, None, "", fuente, calidad, str(error)[:200])


# ---------------------------------------------------------------------------
# FRED
# ---------------------------------------------------------------------------

def datos_fred() -> list[Dato]:
    clave = os.environ.get("FRED_API_KEY")
    salida = []
    for nombre, (serie, unidad, fuente) in config.SERIES_FRED.items():
        if not clave:
            salida.append(_fallido(nombre, unidad, fuente, config.PRIMARIA, "falta FRED_API_KEY"))
            continue
        try:
            r = SESION.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={"series_id": serie, "api_key": clave, "file_type": "json",
                        "sort_order": "desc", "limit": 15},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            obs = [o for o in r.json()["observations"] if o["value"] not in (".", "")]
            if not obs:
                raise ValueError("sin observaciones")
            actual, fecha = float(obs[0]["value"]), obs[0]["date"]
            variacion, tipo = None, ""
            if len(obs) > 1:
                previo = float(obs[1]["value"])
                if unidad == "%":   # tasas: variación en puntos básicos
                    variacion, tipo = round((actual - previo) * 100), "pb"
                elif previo:
                    variacion, tipo = round((actual / previo - 1) * 100, 2), "%"
            salida.append(Dato(nombre, actual, unidad, fecha, variacion, tipo, fuente, config.PRIMARIA))
        except Exception as e:  # noqa: BLE001 - un dato caído no frena el informe
            salida.append(_fallido(nombre, unidad, fuente, config.PRIMARIA, e))
    return salida


# ---------------------------------------------------------------------------
# BCRA
# ---------------------------------------------------------------------------

def datos_bcra() -> list[Dato]:
    """Una sola llamada trae todas las variables con su último valor informado."""
    fuente = "BCRA"
    try:
        r = SESION.get("https://api.bcra.gob.ar/estadisticas/v4.0/monetarias",
                       params={"limit": 3000}, timeout=TIMEOUT)
        r.raise_for_status()
        por_id = {v["idVariable"]: v for v in r.json()["results"]}
    except Exception as e:  # noqa: BLE001
        return [_fallido(n, u, fuente, config.PRIMARIA, f"API del BCRA no disponible: {e}")
                for n, (_, u) in config.VARIABLES_BCRA.items()]

    salida = []
    for nombre, (id_variable, unidad) in config.VARIABLES_BCRA.items():
        v = por_id.get(id_variable)
        if not v or v.get("ultValorInformado") is None:
            salida.append(_fallido(nombre, unidad, fuente, config.PRIMARIA,
                                   f"variable {id_variable} no encontrada"))
            continue
        salida.append(Dato(nombre, float(v["ultValorInformado"]), unidad,
                           v.get("ultFechaInformada"), None, "", fuente, config.PRIMARIA))
    return salida


# ---------------------------------------------------------------------------
# Fuentes sin origen primario (se marcan "no verificado")
# ---------------------------------------------------------------------------

def dato_bitcoin() -> Dato:
    nombre, unidad, fuente = "Bitcoin", "USD", "CoinGecko (agregador)"
    try:
        r = SESION.get("https://api.coingecko.com/api/v3/simple/price",
                       params={"ids": "bitcoin", "vs_currencies": "usd",
                               "include_24hr_change": "true", "include_last_updated_at": "true"},
                       timeout=TIMEOUT)
        r.raise_for_status()
        btc = r.json()["bitcoin"]
        from datetime import datetime
        fecha = datetime.fromtimestamp(btc["last_updated_at"], config.ZONA).strftime("%Y-%m-%d %H:%M")
        return Dato(nombre, round(btc["usd"]), unidad, fecha,
                    round(btc["usd_24h_change"], 2), "%", fuente, config.NO_VERIFICADO)
    except Exception as e:  # noqa: BLE001
        return _fallido(nombre, unidad, fuente, config.NO_VERIFICADO, e)


def dato_riesgo_pais() -> Dato:
    nombre, unidad, fuente = "Riesgo país", "pb", "argentinadatos.com (agregador)"
    try:
        r = SESION.get("https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais/ultimo",
                       timeout=TIMEOUT)
        r.raise_for_status()
        d = r.json()
        return Dato(nombre, float(d["valor"]), unidad, d["fecha"][:10], None, "",
                    fuente, config.NO_VERIFICADO)
    except Exception as e:  # noqa: BLE001
        return _fallido(nombre, unidad, fuente, config.NO_VERIFICADO, e)


def dato_dolar_blue() -> Dato:
    nombre, unidad, fuente = "Dólar blue (venta)", "$ por USD", "dolarapi.com (agregador)"
    try:
        r = SESION.get("https://dolarapi.com/v1/dolares/blue", timeout=TIMEOUT)
        r.raise_for_status()
        d = r.json()
        return Dato(nombre, float(d["venta"]), unidad, d["fechaActualizacion"][:10], None, "",
                    fuente, config.NO_VERIFICADO)
    except Exception as e:  # noqa: BLE001
        return _fallido(nombre, unidad, fuente, config.NO_VERIFICADO, e)


# ---------------------------------------------------------------------------

def armar_tablero() -> list[Dato]:
    datos = datos_fred() + datos_bcra()
    if config.USAR_RIESGO_PAIS:
        datos.append(dato_riesgo_pais())
    if config.USAR_DOLAR_BLUE:
        datos.append(dato_dolar_blue())
    if config.USAR_COINGECKO:
        datos.append(dato_bitcoin())
    return datos


def formatear_valor(d: Dato) -> str:
    if d.valor is None:
        return "no disponible"
    decimales = 2 if abs(d.valor) < 1000 else 0
    texto = f"{d.valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto} {d.unidad}"


def formatear_variacion(d: Dato) -> str:
    if d.variacion is None:
        return ""
    signo = "+" if d.variacion > 0 else ""
    numero = f"{d.variacion}".replace(".", ",")
    return f"{signo}{numero} {d.tipo_variacion}"


if __name__ == "__main__":
    from entorno import cargar_env
    cargar_env()
    for d in armar_tablero():
        extra = f"  [ERROR: {d.error}]" if d.error else ""
        print(f"{d.nombre:32} {formatear_valor(d):>26} {formatear_variacion(d):>10}  "
              f"{d.fecha or '':16} ({d.calidad}){extra}")
