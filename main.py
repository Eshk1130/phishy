from detector import analyze_email

email_text = """
URGENT!

Your account has been suspended.

Please verify your account.
"""

result = analyze_email(email_text)

print(result)