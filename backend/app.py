import os
import uuid
import base64
import traceback
import email.message

from flask import Flask, request, jsonify, render_template, session, redirect
from googleapiclient.discovery import build

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


# ── Core routes ─────────────────────────────────────────────────────────────

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
    session["oauth_state"]   = state
    session["code_verifier"] = code_verifier
    return jsonify({"auth_url": auth_url})


@app.route("/gmail/callback")
def gmail_callback():
    """Google redirects here with auth code. Exchange it for a token."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No authorization code received"}), 400

    code_verifier = session.pop("code_verifier", None)

    try:
        creds = exchange_code(code, code_verifier=code_verifier)
        session["gmail_token"] = credentials_to_dict(creds)
    except Exception as e:
        return jsonify({"error": f"Token exchange failed: {str(e)}"}), 500

    return redirect("/")


@app.route("/gmail/inbox")
def gmail_inbox():
    """
    Fetch the user's Gmail inbox.
    Supports optional pagination via `page_token` query param.
    Returns JSON containing `messages` and optionally `next_page_token`.
    """
    if "gmail_token" not in session:
        return jsonify({"error": "Not authenticated – connect Gmail first.", "auth_required": True}), 401

    try:
        creds        = credentials_from_dict(session["gmail_token"])
        page_token   = request.args.get("page_token")
        max_results  = min(int(request.args.get("max_results", 200)), 500)
        label        = request.args.get("label")  # optional Gmail label ID
        raw_emails, next_token = fetch_inbox(
            creds, max_results=max_results, page_token=page_token, label_id=label
        )
    except Exception as e:
        return jsonify({"error": f"Failed to fetch inbox: {e}", "trace": traceback.format_exc()}), 500

    results = []
    for raw in raw_emails:
        try:
            parsed   = parse_eml(raw)
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
        except Exception as exc:
            import traceback as _tb
            # Don't drop the email — include a minimal safe fallback entry
            fallback_id = str(uuid.uuid4())
            results.append({
                "id":           fallback_id,
                "sender_name":  "Unknown Sender",
                "sender_email": "",
                "subject":      "(Email could not be parsed)",
                "snippet":      str(exc)[:120],
                "risk_level":   "Low",
                "risk_score":   0,
                "max_score":    100,
                "risk_pct":     0,
                "reasons":      [],
                "attachments":  [],
            })

    payload = {"messages": results}
    if next_token:
        payload["next_page_token"] = next_token
    return jsonify(payload)


@app.route("/gmail/labels")
def gmail_labels():
    """Return all Gmail labels for the authenticated user."""
    if "gmail_token" not in session:
        return jsonify({"error": "Not authenticated", "auth_required": True}), 401
    try:
        creds   = credentials_from_dict(session["gmail_token"])
        service = build("gmail", "v1", credentials=creds)
        result  = service.users().labels().list(userId="me").execute()
        labels  = result.get("labels", [])
        return jsonify([{"id": lbl["id"], "name": lbl.get("name", "")} for lbl in labels])
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/gmail/send", methods=["POST"])
def gmail_send():
    """Send an email via Gmail on behalf of the authenticated user."""
    if "gmail_token" not in session:
        return jsonify({"error": "Not authenticated", "auth_required": True}), 401

    data    = request.get_json(silent=True) or {}
    to      = data.get("to")
    subject = data.get("subject", "(No Subject)")
    body    = data.get("body", "")

    if not to:
        return jsonify({"error": "'to' field required"}), 400

    try:
        creds   = credentials_from_dict(session["gmail_token"])
        service = build("gmail", "v1", credentials=creds)
        msg = email.message.EmailMessage()
        msg["To"]      = to
        msg["From"]    = "me"
        msg["Subject"] = subject
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return jsonify({"status": "sent"})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


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