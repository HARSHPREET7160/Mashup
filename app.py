from __future__ import annotations

import os
import tempfile
import zipfile
from email.message import EmailMessage
from pathlib import Path
import smtplib

from email_validator import EmailNotValidError, validate_email
from flask import Flask, render_template_string, request

from mashup_core import MashupError, create_mashup, sanitize_filename

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Mashup Service</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 16px; }
    form { display: grid; gap: 12px; }
    input, button { padding: 10px; font-size: 14px; }
    .msg { margin-top: 16px; font-weight: bold; }
  </style>
</head>
<body>
  <h1>Mashup Web Service</h1>
  <p>Enter singer details to receive a mashup zip file via email.</p>
  <form method="post">
    <input name="singer" placeholder="Singer name" required />
    <input name="videos" type="number" min="11" placeholder="Number of videos (>10)" required />
    <input name="duration" type="number" min="21" placeholder="Audio duration in sec (>20)" required />
    <input name="email" type="email" placeholder="Email address" required />
    <button type="submit">Create and Send Mashup</button>
  </form>
  {% if message %}<div class="msg">{{ message }}</div>{% endif %}
</body>
</html>
"""


def send_email_with_attachment(to_email: str, attachment_path: Path) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "")

    if not all([smtp_host, smtp_user, smtp_pass, smtp_from]):
        raise MashupError(
            "SMTP settings missing. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM."
        )

    msg = EmailMessage()
    msg["Subject"] = "Your Mashup ZIP File"
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg.set_content("Please find your requested mashup zip file attached.")

    data = attachment_path.read_bytes()
    msg.add_attachment(
        data,
        maintype="application",
        subtype="zip",
        filename=attachment_path.name,
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        singer = (request.form.get("singer") or "").strip()
        videos = request.form.get("videos") or ""
        duration = request.form.get("duration") or ""
        email = (request.form.get("email") or "").strip()

        try:
            if not singer:
                raise MashupError("Singer name is required.")

            try:
                video_count = int(videos)
                duration_sec = int(duration)
            except ValueError as exc:
                raise MashupError("Number of videos and duration must be integers.") from exc

            if video_count <= 10:
                raise MashupError("Number of videos must be greater than 10.")
            if duration_sec <= 20:
                raise MashupError("Duration must be greater than 20 seconds.")

            validated_email = validate_email(email)
            clean_email = validated_email.email

            with tempfile.TemporaryDirectory(prefix="mashup_web_") as tmp:
                tmp_path = Path(tmp)
                mashup_name = f"{sanitize_filename(singer)}_mashup.mp3"
                output_mp3 = tmp_path / mashup_name

                create_mashup(
                    singer_name=singer,
                    number_of_videos=video_count,
                    audio_duration_sec=duration_sec,
                    output_filename=str(output_mp3),
                    base_work_dir=tmp_path / "work",
                )

                zip_file = tmp_path / f"{sanitize_filename(singer)}_mashup.zip"
                with zipfile.ZipFile(zip_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    zf.write(output_mp3, arcname=output_mp3.name)

                send_email_with_attachment(clean_email, zip_file)

            message = f"Success: mashup zip sent to {clean_email}."

        except EmailNotValidError:
            message = "Error: Invalid email address."
        except MashupError as exc:
            message = f"Error: {exc}"
        except Exception as exc:  # pragma: no cover
            message = f"Unexpected error: {exc}"

    return render_template_string(HTML_TEMPLATE, message=message)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
