from detector import analyze_email

email_text = """
URGENT!

We detected suspicious activity on your account.

Your account has been suspended.

Please verify your identity within 24 hours.

Click here to reset your password.
"""

result = analyze_email(email_text)

print(result)