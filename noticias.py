"""Junta noticias por RSS dentro de la ventana de fechas del informe."""

from __future__ import annotations

import html
import re
from datetime import date, datetime, time, timedelta
from calendar import timegm

import feedparser

import config


def ventana(hoy: date) -> tuple[datetime, datetime]:
    """Devuelve (desde, hasta) en hora de Buenos Aires.

    Martes a domingo: el día anterior completo. Lunes: de viernes a domingo.
    """
    dias_atras = 3 if hoy.weekday() == 0 else 1
    desde = datetime.combine(hoy - timedelta(days=dias_atras), time.min, config.ZONA)
    hasta = datetime.combine(hoy, time.min, config.ZONA)
    return desde, hasta


def _limpiar(texto: str, limite: int = 400) -> str:
    texto = re.sub(r"<[^>]+>", " ", html.unescape(texto or ""))
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto[:limite]


def _fecha(entrada) -> datetime | None:
    estructura = entrada.get("published_parsed") or entrada.get("updated_parsed")
    if not estructura:
        return None
    return datetime.fromtimestamp(timegm(estructura), config.ZONA)


def juntar_noticias(desde: datetime, hasta: datetime) -> tuple[list[dict], list[str]]:
    """Devuelve (noticias, avisos). Los avisos indican feeds que fallaron."""
    noticias, avisos = [], []
    for medio, (url, tipo) in config.FEEDS.items():
        try:
            feed = feedparser.parse(url, agent="radar-diario/1.0")
            if feed.bozo and not feed.entries:
                raise ValueError(feed.bozo_exception)
        except Exception as e:  # noqa: BLE001
            avisos.append(f"{medio}: {e}")
            continue

        tomadas = 0
        for entrada in feed.entries:
            publicada = _fecha(entrada)
            if publicada is None or not (desde <= publicada < hasta):
                continue
            noticias.append({
                "medio": medio,
                "tipo": tipo,
                "titulo": _limpiar(entrada.get("title", ""), 250),
                "resumen": _limpiar(entrada.get("summary", "")),
                "link": entrada.get("link", ""),
                "fecha": publicada.strftime("%Y-%m-%d %H:%M"),
            })
            tomadas += 1
            if tomadas >= config.MAX_NOTICIAS_POR_FEED:
                break
        if tomadas == 0:
            avisos.append(f"{medio}: sin notas en la ventana")

    noticias.sort(key=lambda n: n["fecha"], reverse=True)
    return noticias[: config.MAX_NOTICIAS_TOTAL], avisos


if __name__ == "__main__":
    d, h = ventana(datetime.now(config.ZONA).date())
    notas, avisos = juntar_noticias(d, h)
    print(f"Ventana: {d:%d/%m %H:%M} a {h:%d/%m %H:%M} — {len(notas)} notas")
    for n in notas[:30]:
        print(f"- [{n['medio']}] {n['titulo']}")
    for a in avisos:
        print(f"AVISO {a}")
