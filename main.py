from detector import analyze_email

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
sender_email = "support@example.com"
sender_name = "Example Support"
result = analyze_email(email_text, sender_email, sender_name)

print(result)