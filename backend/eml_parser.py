from email import policy
from email.parser import BytesParser
from email.utils import parseaddr


def parse_eml(file_bytes):
    """
    Parse raw .eml bytes into a structured dict
    ready to be passed into analyze_email().

    Returns:
        dict with keys:
            sender_name    (str)
            sender_email   (str)
            subject        (str)
            reply_to       (str)
            return_path    (str)
            email_text     (str)
            attachments    (list[str])
            raw_from       (str)  - original From header, for display
    """

    msg = BytesParser(policy=policy.default).parsebytes(file_bytes)

    # --- Sender ---
    raw_from = msg.get("From", "")
    sender_name, sender_email = parseaddr(raw_from)

    # Fallback: if sender_email is empty, use the raw value
    if not sender_email:
        sender_email = raw_from
        sender_name = raw_from

    # --- Headers ---
    subject     = msg.get("Subject", "")
    reply_to    = msg.get("Reply-To", "")
    return_path = msg.get("Return-Path", "")

    # Strip angle brackets from Return-Path if present  e.g. <user@domain.com>
    if return_path.startswith("<") and return_path.endswith(">"):
        return_path = return_path[1:-1]

    # --- Body ---
    # Prefer plain text; fall back to HTML
    email_text = ""
    body_part = msg.get_body(preferencelist=("plain", "html"))
    if body_part:
        email_text = body_part.get_content()

    # --- Attachments ---
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
