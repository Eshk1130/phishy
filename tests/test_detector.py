"""
tests/test_detector.py
Run with: python -m pytest tests/
"""
from backend.detector import analyze_email


def make_result(text="", sender_email="test@example.com", sender_name="Test",
                attachments=None, reply_to="", return_path="", subject=""):
    return analyze_email(text, sender_email, sender_name,
                         attachments or [], reply_to, return_path, subject)


# ── Basic smoke tests ──────────────────────────────────────────────────────

def test_clean_email_is_low_risk():
    r = make_result(text="Hello, just checking in!", subject="Hello")
    assert r["risk_level"] == "Low"

def test_urgency_raises_score():
    r1 = make_result(text="Hello!")
    r2 = make_result(text="URGENT! Verify your account immediately.")
    assert r2["score"] > r1["score"]

def test_sender_mismatch_detected():
    r = make_result(
        text="Please login",
        sender_email="support@totally-not-paypal.com",
        sender_name="PayPal Support",
        subject="Account"
    )
    assert "Sender identity and email domain do not match" in r["reasons"]

def test_reply_to_mismatch_detected():
    r = make_result(
        text="Hi",
        sender_email="noreply@amazon.com",
        reply_to="hacker@evil.xyz"
    )
    assert "Reply-To address differs from sender" in r["reasons"]

def test_executable_attachment_detected():
    r = make_result(attachments=["invoice.exe"])
    assert "Executable attachment detected" in r["reasons"]

def test_double_extension_detected():
    r = make_result(attachments=["document.pdf.exe"])
    assert "Double extension attachment detected" in r["reasons"]

def test_raw_ip_url_detected():
    r = make_result(text="Click http://192.168.1.1/login to continue")
    assert "Raw IP address detected in URL" in r["reasons"]

def test_brand_impersonation_url():
    r = make_result(text="Visit https://paypal-login.xyz/verify now")
    assert "Possible brand impersonation detected in URL" in r["reasons"]

def test_high_risk_label():
    r = make_result(
        text="URGENT! Your account has been suspended. Reset your password within 24 hours. Click here: https://paypal-fake.xyz/login",
        sender_email="support@gmail.com",
        sender_name="PayPal Support",
        attachments=["invoice.pdf.exe"],
        reply_to="scam@evil.xyz",
        subject="Verify Your Account"
    )
    assert r["risk_level"] in ("High", "Medium")

def test_risk_percentage_in_range():
    r = make_result(text="Hello world")
    assert 0 <= r["risk_percentage"] <= 100

def test_reasons_is_list():
    r = make_result(text="Test")
    assert isinstance(r["reasons"], list)
