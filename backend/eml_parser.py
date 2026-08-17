import re
import html as _html
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr


def _strip_html(raw):
    """Strip HTML tags and decode entities to plain readable text."""
    raw = re.sub(r'<(style|script)[^>]*>.*?</\1>', '', raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r'<[^>]+>', ' ', raw)
    raw = _html.unescape(raw)
    raw = re.sub(r'[ \t]+', ' ', raw)
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    return raw.strip()


def parse_eml(file_bytes):
    """
    Parse raw .eml bytes into a structured dict
    ready to be passed into analyze_email().

    Returns:
        dict with keys:
            sender_name, sender_email, subject, reply_to,
            return_path, email_text, attachments, raw_from
    """
    msg = BytesParser(policy=policy.default).parsebytes(file_bytes)

    raw_from = msg.get("From", "")
    sender_name, sender_email = parseaddr(raw_from)
    if not sender_email:
        sender_email = raw_from
        sender_name  = raw_from

    subject     = msg.get("Subject", "")
    reply_to    = msg.get("Reply-To", "")
    return_path = msg.get("Return-Path", "")

    if return_path.startswith("<") and return_path.endswith(">"):
        return_path = return_path[1:-1]

    # Prefer plain text; strip HTML tags if only HTML body available
    email_text = ""
    body_part  = msg.get_body(preferencelist=("plain", "html"))
    if body_part:
        content = body_part.get_content()
        if body_part.get_content_type() == "text/html":
            email_text = _strip_html(content)
        else:
            email_text = content

    attachments = []
    for part in msg.iter_attachments():
        filename = part.get_filename()
        if filename:
            attachments.append(filename)

    return {
        "sender_name":  sender_name,
        "sender_email": sender_email,
        "subject":      subject,
        "reply_to":     reply_to,
        "return_path":  return_path,
        "email_text":   email_text,
        "attachments":  attachments,
        "raw_from":     raw_from,
    }
