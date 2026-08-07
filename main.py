from detector import analyze_email

email_text = """
URGENT!

Your account has been suspended.
Reset your password within 24 hours.
Verify your identity immediately.

Click here:
http://192.168.1.10/login

We detected suspicious activity.
"""

result = analyze_email(email_text)

print(result)