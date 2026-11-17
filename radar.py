"""Radar diario: punto de entrada.

Uso:
  python radar.py                  # informe completo + mail
  python radar.py --sin-mail       # arma el informe y lo guarda, sin enviar
  python radar.py --sin-claude     # solo tablero + titulares, sin gastar API (para probar)
  python radar.py --fecha 2026-11-16   # simula otro día
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import config
from entorno import cargar_env
from noticias import juntar_noticias, ventana
from tablero import armar_tablero, formatear_valor, formatear_variacion

COLORES_CALIDAD = {
    config.PRIMARIA: "#1a7f37",
    config.SECUNDARIA: "#9a6700",
    config.NO_VERIFICADO: "#cf222e",
}


def tabla_tablero(datos) -> str:
    filas = []
    for d in datos:
        color = COLORES_CALIDAD.get(d.calidad, "#555")
        variacion = formatear_variacion(d)
        color_var = "#1a7f37" if (d.variacion or 0) > 0 else "#cf222e" if (d.variacion or 0) < 0 else "#555"
        filas.append(
            "<tr>"
            f"<td style='padding:4px 8px'>{html.escape(d.nombre)}</td>"
            f"<td style='padding:4px 8px;text-align:right'><strong>{html.escape(formatear_valor(d))}</strong></td>"
            f"<td style='padding:4px 8px;text-align:right;color:{color_var}'>{html.escape(variacion)}</td>"
            f"<td style='padding:4px 8px;color:#666;font-size:12px'>{html.escape(d.fecha or '')}</td>"
            f"<td style='padding:4px 8px;font-size:12px'>{html.escape(d.fuente)} · "
            f"<span style='color:{color}'>{html.escape(d.calidad)}</span></td>"
            "</tr>"
        )
    return (
        "<h2>Tablero de mercados</h2>"
        "<table style='border-collapse:collapse;font-size:14px;width:100%'>"
        "<tr style='text-align:left;border-bottom:1px solid #ddd'>"
        "<th style='padding:4px 8px'>Indicador</th><th style='padding:4px 8px;text-align:right'>Último</th>"
        "<th style='padding:4px 8px;text-align:right'>Var.</th><th style='padding:4px 8px'>Fecha</th>"
        "<th style='padding:4px 8px'>Fuente · calidad</th></tr>"
        + "".join(filas) +
        "</table>"
        "<p style='font-size:12px;color:#666'>Var.: % contra el dato anterior; pb = puntos básicos; "
        "pp = puntos porcentuales. Cada cifra muestra la fecha de su último dato publicado.</p>"
    )


def titulares_sin_claude(noticias) -> str:
    items = "".join(
        f"<li>[{html.escape(n['medio'])}] <a href='{html.escape(n['link'])}'>{html.escape(n['titulo'])}</a></li>"
        for n in noticias[:60]
    )
    return f"<h2>Titulares (modo prueba, sin Claude)</h2><ul>{items}</ul>"


def envolver(titulo: str, periodo: str, cuerpo: str) -> str:
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>{html.escape(titulo)}</title></head>
<body style="font-family:Georgia,serif;max-width:760px;margin:0 auto;padding:16px;color:#1f2328;line-height:1.5">
<h1 style="margin-bottom:0">{html.escape(titulo)}</h1>
<p style="color:#666;margin-top:4px">Cubre: {html.escape(periodo)}</p>
{cuerpo}
</body></html>"""


def a_texto_plano(fragmento: str) -> str:
    texto = re.sub(r"<(br|/p|/li|/h[1-3]|/tr)>", "\n", fragmento)
    texto = re.sub(r"<[^>]+>", "", texto)
    return html.unescape(re.sub(r"\n{3,}", "\n\n", texto)).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Radar diario")
    parser.add_argument("--sin-mail", action="store_true")
    parser.add_argument("--sin-claude", action="store_true")
    parser.add_argument("--fecha", help="AAAA-MM-DD (por defecto, hoy en Buenos Aires)")
    args = parser.parse_args()

    cargar_env()
    hoy = date.fromisoformat(args.fecha) if args.fecha else datetime.now(config.ZONA).date()
    desde, hasta = ventana(hoy)
    ultimo = hasta - timedelta(days=1)
    periodo = (f"{desde:%d/%m} al {ultimo:%d/%m/%Y}" if desde.date() != ultimo.date()
               else f"{ultimo:%d/%m/%Y}")
    titulo = f"Radar diario - {hoy:%d/%m/%Y}"

    print("Armando tablero...")
    tablero = armar_tablero()
    for d in tablero:
        if d.error:
            print(f"  aviso: {d.nombre}: {d.error}")

    print("Juntando noticias...")
    noticias, avisos = juntar_noticias(desde, hasta)
    print(f"  {len(noticias)} notas")
    for a in avisos:
        print(f"  aviso: {a}")

    if args.sin_claude:
        cuerpo = titulares_sin_claude(noticias)
    else:
        from redactar import redactar
        print("Redactando con Claude...")
        cuerpo = redactar(hoy, periodo, [d.a_dict() for d in tablero], noticias)

    # El tablero lo pone el código, así las cifras no pasan por el modelo.
    pos = cuerpo.find("<h2>Lo esencial</h2>")
    if pos >= 0:
        fin = cuerpo.find("<h2>", pos + 5)
        fin = fin if fin >= 0 else len(cuerpo)
        cuerpo = cuerpo[:fin] + tabla_tablero(tablero) + cuerpo[fin:]
    else:
        cuerpo = tabla_tablero(tablero) + cuerpo

    pagina = envolver(titulo, periodo, cuerpo)
    salida = Path(__file__).parent / "salida" / f"radar-{hoy:%Y-%m-%d}.html"
    salida.parent.mkdir(exist_ok=True)
    salida.write_text(pagina, encoding="utf-8")
    print(f"Guardado en {salida}")

    if not args.sin_mail:
        from enviar import enviar_mail
        enviar_mail(titulo, pagina, a_texto_plano(cuerpo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
