from flask import Flask
from detector import analyze_email

app = Flask(__name__)

@app.route("/")
def home():
    return "Phishy Running"

@app.route("/test")
def test_detector():

    result = analyze_email(
        "URGENT! Verify your account immediately.",
        "support@gmail.com",
        "PayPal Support",
        [],
        "",
        "",
        "Verify Your Account"
    )

    return str(result)

if __name__ == "__main__":
    app.run(debug=True)