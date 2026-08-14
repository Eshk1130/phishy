import os
import uuid

from flask import Flask, request, jsonify, render_template, session

from .eml_parser import parse_eml
from .detector import analyze_email

# ── Path config ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # phishy/

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static"),
)
app.secret_key = os.urandom(24)

# ── In-memory email store ──────────────────────────────────────────────────
# { email_id: { "parsed": {...}, "analysis": {...} } }
email_store = {}


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("inbox.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if not file.filename.lower().endswith(".eml"):
        return jsonify({"error": "Only .eml files are supported"}), 400

    file_bytes = file.read()

    try:
        parsed = parse_eml(file_bytes)
    except Exception as e:
        return jsonify({"error": f"Failed to parse email: {str(e)}"}), 500

    try:
        analysis = analyze_email(
            parsed["email_text"],
            parsed["sender_email"],
            parsed["sender_name"],
            parsed["attachments"],
            parsed["reply_to"],
            parsed["return_path"],
            parsed["subject"],
        )
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

    email_id = str(uuid.uuid4())
    email_store[email_id] = {"parsed": parsed, "analysis": analysis}

    return jsonify({
        "id":           email_id,
        "sender_name":  parsed["sender_name"],
        "sender_email": parsed["sender_email"],
        "subject":      parsed["subject"],
        "snippet":      parsed["email_text"][:120].replace("\n", " "),
        "risk_level":   analysis["risk_level"],
        "risk_score":   analysis["score"],
        "max_score":    analysis["max_score"],
        "risk_pct":     round(analysis["risk_percentage"], 1),
        "reasons":      analysis["reasons"],
        "attachments":  parsed["attachments"],
    })


@app.route("/emails", methods=["GET"])
def list_emails():
    result = []
    for email_id, data in email_store.items():
        p = data["parsed"]
        a = data["analysis"]
        result.append({
            "id":           email_id,
            "sender_name":  p["sender_name"],
            "sender_email": p["sender_email"],
            "subject":      p["subject"],
            "snippet":      p["email_text"][:120].replace("\n", " "),
            "risk_level":   a["risk_level"],
            "risk_score":   a["score"],
            "max_score":    a["max_score"],
            "risk_pct":     round(a["risk_percentage"], 1),
        })
    return jsonify(result)


@app.route("/emails/<email_id>", methods=["GET"])
def get_email(email_id):
    if email_id not in email_store:
        return jsonify({"error": "Email not found"}), 404

    data = email_store[email_id]
    p = data["parsed"]
    a = data["analysis"]

    return jsonify({
        "id":           email_id,
        "sender_name":  p["sender_name"],
        "sender_email": p["sender_email"],
        "raw_from":     p["raw_from"],
        "subject":      p["subject"],
        "reply_to":     p["reply_to"],
        "return_path":  p["return_path"],
        "body":         p["email_text"],
        "attachments":  p["attachments"],
        "risk_level":   a["risk_level"],
        "risk_score":   a["score"],
        "max_score":    a["max_score"],
        "risk_pct":     round(a["risk_percentage"], 1),
        "reasons":      a["reasons"],
    })


if __name__ == "__main__":
    app.run(debug=True)