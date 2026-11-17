"""Envía el informe por mail con SMTP (por ejemplo Gmail con contraseña de aplicación)."""

import os
import smtplib
from email.message import EmailMessage


def enviar_mail(asunto: str, html: str, texto_plano: str) -> None:
    servidor = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    puerto = int(os.environ.get("SMTP_PORT", "465"))
    usuario = os.environ["SMTP_USER"]
    clave = os.environ["SMTP_PASSWORD"]
    destinatarios = [d.strip() for d in os.environ.get("MAIL_TO", usuario).split(",") if d.strip()]

    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = os.environ.get("MAIL_FROM", usuario)
    msg["To"] = ", ".join(destinatarios)
    msg.set_content(texto_plano)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL(servidor, puerto, timeout=60) as smtp:
        smtp.login(usuario, clave)
        smtp.send_message(msg)
    print(f"Mail enviado a {len(destinatarios)} destinatario(s).")
