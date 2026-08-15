import os
import uuid
import traceback

from flask import Flask, request, jsonify, render_template, session

from .eml_parser import parse_eml
from .detector import analyze_email
from .gmail_service import (
    get_auth_url,
    exchange_code,
    credentials_to_dict,
    credentials_from_dict,
    fetch_inbox,
)

# ── Path config ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # phishy/

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static"),
)
app.secret_key = os.environ.get("PHISHY_SECRET", "phishy-dev-secret-key-change-in-prod")

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


# ── Gmail OAuth routes ─────────────────────────────────────────────────────

@app.route("/gmail/auth")
def gmail_auth():
    """Redirect user to Google's OAuth consent screen."""
    auth_url, state, code_verifier = get_auth_url()
    # Store PKCE verifier in session so callback can use it
    session["oauth_state"]    = state
    session["code_verifier"]  = code_verifier  # may be None if PKCE not used
    return jsonify({"auth_url": auth_url})


@app.route("/gmail/callback")
def gmail_callback():
    """Google redirects here with auth code. Exchange it for a token."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No authorization code received"}), 400

    # Retrieve and clear the PKCE verifier from session
    code_verifier = session.pop("code_verifier", None)

    try:
        creds = exchange_code(code, code_verifier=code_verifier)
        session["gmail_token"] = credentials_to_dict(creds)
    except Exception as e:
        return jsonify({"error": f"Token exchange failed: {str(e)}"}), 500

    from flask import redirect
    return redirect("/")


@app.route("/gmail/inbox")
def gmail_inbox():
    """
    Fetch the user's real Gmail inbox, run the detector on each email,
    and return a list of analyzed emails.
    """
    if "gmail_token" not in session:
        return jsonify({"error": "Not authenticated", "auth_required": True}), 401

    try:
        creds = credentials_from_dict(session["gmail_token"])
        raw_emails = fetch_inbox(creds, max_results=20)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch inbox: {str(e)}", "trace": traceback.format_exc()}), 500

    results = []
    for raw in raw_emails:
        try:
            parsed = parse_eml(raw)
            analysis = analyze_email(
                parsed["email_text"],
                parsed["sender_email"],
                parsed["sender_name"],
                parsed["attachments"],
                parsed["reply_to"],
                parsed["return_path"],
                parsed["subject"],
            )
            email_id = str(uuid.uuid4())
            email_store[email_id] = {"parsed": parsed, "analysis": analysis}

            results.append({
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
        except Exception:
            continue  # skip unparseable emails silently

    return jsonify(results)


@app.route("/gmail/logout")
def gmail_logout():
    """Clear the Gmail session token."""
    session.pop("gmail_token", None)
    return jsonify({"status": "logged out"})


@app.route("/gmail/status")
def gmail_status():
    """Check if the user is currently connected to Gmail."""
    return jsonify({"connected": "gmail_token" in session})


if __name__ == "__main__":
    app.run(debug=True)