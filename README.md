# Radar diario

Informe matutino con noticias del día anterior (los lunes, de viernes a domingo), tablero de mercados y envío por mail.

- **El código** trae las cifras del tablero (FRED, BCRA, INDEC y, marcados "no verificado", CoinGecko, riesgo país y dólar blue), junta noticias por RSS, arma el HTML y lo manda por mail.
- **Claude** (por API) elige qué importa, explica por qué y conecta con tu biblioteca, usando solo lo que juntó el código. Las cifras del tablero no pasan por el modelo: la tabla la arma el código.

## Archivos

| Archivo | Qué hace |
|---|---|
| `config.py` | Fuentes, series, feeds y modelo. Lo que más vas a tocar. |
| `tablero.py` | Cifras del tablero con etiqueta de calidad. |
| `noticias.py` | Noticias por RSS dentro de la ventana de fechas. |
| `redactar.py` | Instrucciones para Claude y llamada a la API. |
| `enviar.py` | Envío por SMTP. |
| `radar.py` | Junta todo. |
| `.github/workflows/radar.yml` | Lo programa todos los días a las 6:48 (hora de Buenos Aires). |

## 1. Probarlo en tu computadora

1. Instalá Python 3.12 desde https://www.python.org/downloads/ (en tu Mac todavía no está instalado).
2. En la Terminal, parado en esta carpeta:

```bash
python3 -m venv .venv && source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

3. Copiá `.env.example` como `.env` y completá las claves:

```bash
cp .env.example .env
```

   - `FRED_API_KEY`: gratis en https://fredaccount.stlouisfed.org (API Keys).
   - `ANTHROPIC_API_KEY`: en https://console.anthropic.com (se paga por uso).
   - `SMTP_USER` / `SMTP_PASSWORD`: tu Gmail y una *contraseña de aplicación* (Cuenta de Google > Seguridad > Verificación en 2 pasos > Contraseñas de aplicación). No uses tu contraseña normal.

4. Probá por partes, de lo más barato a lo completo:

```bash
python tablero.py
```

```bash
python noticias.py
```

```bash
python radar.py --sin-claude --sin-mail
```

```bash
python radar.py --sin-mail
```

```bash
python radar.py
```

Cada corrida deja el informe en `salida/radar-AAAA-MM-DD.html`; abrilo en el navegador para revisarlo.

## 2. Programarlo (GitHub Actions)

Así corre solo, aunque tu computadora esté apagada.

1. Creá un repositorio **privado** en GitHub y subí esta carpeta.
2. En el repo: *Settings > Secrets and variables > Actions > New repository secret*. Cargá `ANTHROPIC_API_KEY`, `FRED_API_KEY`, `SMTP_USER`, `SMTP_PASSWORD` y `MAIL_TO`.
3. En la pestaña *Actions*, abrí "Radar diario" y tocá *Run workflow* para probarlo una vez.
4. Desde ahí corre todos los días a las 6:48. GitHub a veces arranca con unos minutos de demora.

## Biblioteca

Exportá tus notas o resúmenes a un archivo `biblioteca.md` en esta carpeta. Si existe, Claude agrega líneas "Biblioteca:" y la sección "Desde tu biblioteca"; si no, las omite. Está en `.gitignore` para no subirlo por error: si el repo es privado y querés que GitHub lo use, sacalo de ahí.

## Calidad de las cifras

- **primaria**: BCRA (incluida la inflación del INDEC que republica), Fed/Treasury/EIA vía FRED.
- **fuente secundaria**: medio de referencia (reservado para cifras que agregues desde medios).
- **no verificado**: agregadores (CoinGecko, argentinadatos.com, dolarapi.com).

Si una API falla, la cifra aparece como "no disponible" y el informe sale igual.

## Costos aproximados

Cada informe manda unas 200 notas a Claude (~40.000–60.000 tokens de entrada, más la biblioteca si la usás). Con Claude Opus 5.5 ($4 por millón de tokens de entrada y $20 por millón de salida) son aproximadamente USD 0,30 a 0,60 por informe (USD 10 a 18 por mes), según cuánto razone el modelo. Para gastar menos, bajá `ESFUERZO` o `MAX_NOTICIAS_TOTAL` en `config.py`.

## Qué falta o conviene revisar

- **Oro y CME FedWatch** no tienen API gratuita confiable: quedan afuera del tablero; Claude los menciona solo si aparecen en las noticias.
- **API del BCRA**: usa la v4.0 (la v3 ya fue dada de baja). Los ids de cada variable están en `config.py`; si el BCRA los cambia, el tablero muestra "no disponible" en esa fila.
- **FT**: su RSS público trae una sola nota, así que quedó afuera; aparece solo si otro medio lo cita.
- **Feeds RSS**: algunos medios cambian o cierran sus feeds sin aviso. Los avisos de la corrida te dicen cuál no trajo notas; corregilo en `config.py`.
