from email import policy
from email.parser import BytesParser
from backend.detector import analyze_email
#test cases 
sender_email = "support@amazon.com"

sender_name = "Customer Support"
#Version 1,2,3
#email_text = """
#URGENT!

#Your account has been suspended.
#Reset your password within 24 hours.
#Verify your identity immediately.

#Click here:
#http://192.168.1.10/login
#http://192.168.2.10/login
#http://192.168.3.10/login
#https://verify-login-bank.xyz/reset
#https://paypal-login-security.xyz
#We detected suspicious activity.
#""" 

#version 4
filename = input("Enter email file name: ")

with open(f"sample_emails/{filename}", "rb") as file:
    msg = BytesParser(policy=policy.default).parse(file)

sender = msg["From"]
print(sender)

from email.utils import parseaddr

sender_name, sender_email = parseaddr(sender)
reply_to = msg.get("Reply-To", "")
print("REPLY TO:", reply_to)

return_path = msg.get("Return-Path", "")

print("RETURN PATH:", return_path)

subject = msg.get("Subject", "")
print("SUBJECT:", subject)

print("SENDER NAME:", sender_name)
print("SENDER EMAIL:", sender_email)


email_text = msg.get_body(preferencelist=("plain")).get_content()
attachments = []

for attachment in msg.iter_attachments():
    filename = attachment.get_filename()

    if filename:
        attachments.append(filename)

print("ATTACHMENTS:", attachments)

print(email_text)

#attachments = []

result = analyze_email(
    email_text,
    sender_email,
    sender_name,
    attachments,
    reply_to,
    return_path,
    subject
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