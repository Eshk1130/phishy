from email.message import EmailMessage

msg = EmailMessage()

msg["From"] = "PayPal Support <support@gmail.com>"
msg["To"] = "victim@example.com"
msg["Subject"] = "Verify Your Account"
msg["Reply-To"] = "scammer@evil-domain.xyz"
msg["Return-Path"] = "bounce@evil-domain.xyz"

msg.set_content("""
URGENT!

Your account has been suspended.

Verify your identity immediately.

Reset your password within 24 hours.

Click here:

https://paypal-login-security.xyz/reset
""")

# fake attachment
msg.add_attachment(
    b"fake attachment content",
    maintype="application",
    subtype="octet-stream",
    filename="invoice.pdf.exe"
)

with open("sample_emails/phishing_email.eml", "wb") as f:
    f.write(msg.as_bytes())

print("Email created successfully!")