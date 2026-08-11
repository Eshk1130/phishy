from detector import analyze_email
#test cases 
sender_email = "support@amazon.com"
sender_name = "Customer Support"

email_text = """
URGENT!

Your account has been suspended.
Reset your password within 24 hours.
Verify your identity immediately.

Click here:
http://192.168.1.10/login
http://192.168.2.10/login
http://192.168.3.10/login
https://verify-login-bank.xyz/reset

We detected suspicious activity.
"""
attachments = [
    "invoice.pdf.exe",
]
result = analyze_email(
    email_text,
    sender_email,
    sender_name,
    attachments
)

print(result)