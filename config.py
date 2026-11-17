"""Configuración del Radar diario: fuentes, series y parámetros.

Editá este archivo para agregar o sacar fuentes. No hace falta tocar el resto del código.
"""

from zoneinfo import ZoneInfo

ZONA = ZoneInfo("America/Argentina/Buenos_Aires")

# Modelo de Claude que redacta el informe.
MODELO = "claude-opus-5-5"
ESFUERZO = "high"  # low | medium | high | xhigh | max

# Etiquetas de calidad de cada cifra (criterio acordado).
PRIMARIA = "primaria"
SECUNDARIA = "fuente secundaria"
NO_VERIFICADO = "no verificado"

# ---------------------------------------------------------------------------
# Tablero de mercados
# ---------------------------------------------------------------------------

# Series de FRED (Reserva Federal de St. Louis). Necesitan FRED_API_KEY (gratis).
# nombre visible -> (id de la serie, unidad, fuente original)
SERIES_FRED = {
    "S&P 500": ("SP500", "pts", "S&P Dow Jones vía FRED"),
    "Nasdaq Composite": ("NASDAQCOM", "pts", "Nasdaq vía FRED"),
    "VIX": ("VIXCLS", "pts", "Cboe vía FRED"),
    "Bono EE.UU. 10 años": ("DGS10", "%", "Treasury vía FRED"),
    "Bono EE.UU. 2 años": ("DGS2", "%", "Treasury vía FRED"),
    "Tasa de fondos federales": ("DFF", "%", "Fed vía FRED"),
    "Petróleo WTI": ("DCOILWTICO", "USD/barril", "EIA vía FRED"),
    "Petróleo Brent": ("DCOILBRENTEU", "USD/barril", "EIA vía FRED"),
    "Euro / dólar": ("DEXUSEU", "USD por EUR", "Fed vía FRED"),
}

# Variables del BCRA (API de estadísticas v4.0, "Principales Variables").
# nombre visible -> (idVariable, unidad). Ids verificados el 17/11/2026.
# La inflación es el dato del INDEC que el BCRA republica (se actualiza antes que datos.gob.ar).
VARIABLES_BCRA = {
    "Dólar mayorista (referencia)": (5, "$ por USD"),
    "Dólar minorista (promedio vendedor)": (4, "$ por USD"),
    "Banda cambiaria: techo": (1188, "$ por USD"),
    "Reservas internacionales": (1, "millones de USD"),
    "Tasa BADLAR bancos privados": (7, "% TNA"),
    "Inflación mensual (INDEC)": (27, "%"),
    "Inflación interanual (INDEC)": (28, "%"),
}

# Fuentes sin origen primario: se muestran con la etiqueta "no verificado".
USAR_COINGECKO = True       # bitcoin
USAR_RIESGO_PAIS = True     # argentinadatos.com (agregador)
USAR_DOLAR_BLUE = True      # dolarapi.com (agregador)

# ---------------------------------------------------------------------------
# Noticias por RSS
# ---------------------------------------------------------------------------

# nombre -> (url del feed, tipo). Tipo: "oficial" o "referencia".
# Varios medios con paywall solo exponen título y bajada en el RSS: alcanza para elegir temas.
FEEDS = {
    # Comunicados oficiales
    "Reserva Federal": ("https://www.federalreserve.gov/feeds/press_all.xml", "oficial"),
    "SEC (comunicados)": ("https://www.sec.gov/news/pressreleases.rss", "oficial"),
    # Internacionales de referencia
    "NYT Business": ("https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "referencia"),
    "NYT World": ("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "referencia"),
    "WSJ Markets": ("https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "referencia"),
    "WSJ World": ("https://feeds.a.dj.com/rss/RSSWorldNews.xml", "referencia"),
    "The Economist Finance": ("https://www.economist.com/finance-and-economics/rss.xml", "referencia"),
    "BBC Business": ("https://feeds.bbci.co.uk/news/business/rss.xml", "referencia"),
    "BBC Mundo": ("https://feeds.bbci.co.uk/mundo/rss.xml", "referencia"),
    # Argentina y región
    "La Nación Economía": ("https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/economia/?outputType=xml", "referencia"),
    "Ámbito Economía": ("https://www.ambito.com/rss/pages/economia.xml", "referencia"),
    "Infobae Economía": ("https://www.infobae.com/arc/outboundfeeds/rss/category/economia/", "referencia"),
}

MAX_NOTICIAS_POR_FEED = 25
MAX_NOTICIAS_TOTAL = 220

# Archivo opcional con tu biblioteca exportada (notas, resúmenes de libros, etc.).
# Si no existe, se omite la sección "Desde tu biblioteca".
ARCHIVO_BIBLIOTECA = "biblioteca.md"
MAX_CARACTERES_BIBLIOTECA = 150_000
