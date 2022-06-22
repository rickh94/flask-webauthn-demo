import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlparse, urljoin

from flask import make_response, request, current_app


def make_json_response(body, status=200):
    res = make_response(json.dumps(body), status)
    res.headers["Content-Type"] = "application/json"
    return res


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def send_email(to, subject, body_text, body_html=None):
    """Utility function for sending email with smtplib."""
    mail_from = current_app.config["MAIL_FROM"]
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = mail_from
    message["To"] = to
    part1 = MIMEText(body_text, "plain")
    message.attach(part1)
    if body_html:
        part2 = MIMEText(body_html, "html")
        message.attach(part2)
    with smtplib.SMTP(
        current_app.config["MAIL_SERVER"], current_app.config["MAIL_PORT"]
    ) as server:
        server.starttls()
        server.login(
            current_app.config["MAIL_USERNAME"], current_app.config["MAIL_PASSWORD"]
        )
        server.sendmail(mail_from, to, message.as_string())
