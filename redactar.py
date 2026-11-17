"""Le pide a Claude que elija qué importa y redacte el informe, usando solo los datos juntados."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import anthropic

import config

INSTRUCCIONES = """\
Sos el editor del "Radar diario", un informe matutino para un lector argentino informado, \
interesado en mercados, economía, geopolítica y tecnología. Escribís en español rioplatense \
(voseo), claro y directo, sin relleno.

Reglas de fuentes (son estrictas):
- Usá SOLO la información de las noticias y el tablero que te paso. No agregues hechos, cifras \
ni citas que no estén ahí. Si algo importante falta, decilo ("no hay datos en las fuentes de hoy").
- El tablero de mercados ya lo arma el código y va aparte: no lo repitas como tabla. Podés \
mencionar cifras del tablero en el texto, siempre con su etiqueta de calidad entre paréntesis \
cuando no sea "primaria" (por ejemplo: "bitcoin en USD 62.006 (no verificado)").
- Priorizá comunicados oficiales y medios de referencia. Si dos fuentes se contradicen, mostrá ambas.
- Cada afirmación relevante lleva un enlace a la nota de origen.
- Algunos medios con paywall solo dan título y bajada: no inventes el resto de la nota.

Estructura (devolvé un fragmento HTML con <h2>, <h3>, <p>, <ul>, <li>, <a>, <strong>; sin \
<html>, <head>, <body>, estilos ni scripts):
1. <h2>Lo esencial</h2>: 3 a 5 viñetas con lo más importante y por qué importa.
2. <h2>Por tema</h2>: subsecciones <h3> (Mercados y finanzas, Economía global, Geopolítica, \
Tecnología y empresas; omití las que no tengan material). Cada tema: qué pasó y por qué importa. \
Si hay una conexión real con la biblioteca del lector, agregá una línea \
<p><strong>Biblioteca:</strong> ...</p>. Nunca fuerces la conexión.
3. <h2>Argentina y región</h2>.
4. <h2>Qué vigilar hoy y esta semana</h2>: solo eventos que aparezcan en las fuentes.
5. Solo si te indico que es lunes: <h2>Caso de estudio</h2>: tomá un tema de las noticias y \
explicalo en profundidad (contexto, mecanismo, qué podría pasar), con 2 o 3 preguntas para pensar. \
Podés usar conocimiento general para explicar conceptos, pero ninguna cifra o hecho puntual que \
no esté en las fuentes.
6. Solo si te paso biblioteca y hay conexiones reales: <h2>Desde tu biblioteca</h2> con 1 a 3 \
conexiones concretas (qué idea del texto ilumina qué noticia).
7. <h2>Fuentes</h2>: lista de los medios y enlaces usados.
"""


def _texto_biblioteca() -> str | None:
    archivo = Path(__file__).parent / config.ARCHIVO_BIBLIOTECA
    if not archivo.exists():
        return None
    texto = archivo.read_text(encoding="utf-8")
    return texto[: config.MAX_CARACTERES_BIBLIOTECA]


def redactar(hoy: date, periodo: str, tablero: list[dict], noticias: list[dict]) -> str:
    client = anthropic.Anthropic()  # usa ANTHROPIC_API_KEY del entorno
    biblioteca = _texto_biblioteca()

    partes = [
        f"Fecha del informe: {hoy:%d/%m/%Y}. Período cubierto: {periodo}.",
        "Hoy es lunes: incluí el caso de estudio." if hoy.weekday() == 0
        else "Hoy no es lunes: no incluyas caso de estudio.",
        "<tablero>\n" + json.dumps(tablero, ensure_ascii=False, indent=1) + "\n</tablero>",
        "<noticias>\n" + json.dumps(noticias, ensure_ascii=False, indent=1) + "\n</noticias>",
    ]
    if biblioteca:
        partes.append("<biblioteca>\n" + biblioteca + "\n</biblioteca>")
    else:
        partes.append("No hay biblioteca disponible hoy: omití las líneas y la sección de biblioteca.")
    partes.append("Redactá el informe siguiendo la estructura.")

    with client.beta.messages.stream(
        model=config.MODELO,
        max_tokens=32000,
        thinking={"type": "adaptive"},
        output_config={"effort": config.ESFUERZO},
        # Si el modelo declina por política, la API reintenta en otro modelo dentro de la misma llamada.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=INSTRUCCIONES,
        messages=[{"role": "user", "content": "\n\n".join(partes)}],
    ) as stream:
        respuesta = stream.get_final_message()

    if respuesta.stop_reason == "refusal":
        raise RuntimeError("Claude declinó redactar el informe (stop_reason=refusal).")
    if respuesta.stop_reason == "max_tokens":
        raise RuntimeError("La respuesta se cortó por max_tokens; subí el límite en redactar.py.")

    cuerpo = "".join(b.text for b in respuesta.content if b.type == "text").strip()
    # Por si el modelo envuelve el HTML en un bloque de código.
    cuerpo = re.sub(r"^```(?:html)?\s*|\s*```$", "", cuerpo)
    uso = respuesta.usage
    print(f"Claude: {uso.input_tokens} tokens de entrada, {uso.output_tokens} de salida.")
    return cuerpo
