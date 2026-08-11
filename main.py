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
https://paypal-login-security.xyz

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

print("\n PHISHY REPORT \n")

print(f"Risk Level      : {result['risk_level']}")
print(f"Risk Score      : {result['score']}/{result['max_score']}")
print(f"Risk Percentage : {result['risk_percentage']:.2f}%")

print("\nReasons:")

for reason in result["reasons"]:
    print(f"- {reason}")

print("\nRecommendation:")

if result["risk_level"] == "High":
    print("Do NOT interact with this email.")
elif result["risk_level"] == "Medium":
    print("Proceed with caution and verify the sender.")
else:
    print("No major phishing indicators detected.")

print("\n")