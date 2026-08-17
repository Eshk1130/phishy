"""
backend/gmail_service.py
Handles all Gmail API interactions:
  - Building the OAuth flow
  - Exchanging auth codes for tokens
  - Fetching inbox messages
  - Decoding raw MIME email data
"""

import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# ── Config ─────────────────────────────────────────────────────────────────

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

REDIRECT_URI = "http://127.0.0.1:5000/gmail/callback"


# ── OAuth helpers ───────────────────────────────────────────────────────────

def build_flow():
    """Create an OAuth flow from credentials.json."""
    return Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )


def get_auth_url():
    """Return the Google OAuth consent screen URL + state + code_verifier."""
    flow = build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    # PKCE: newer google-auth-oauthlib versions generate a code_verifier
    code_verifier = getattr(flow, "code_verifier", None)
    return auth_url, state, code_verifier


def exchange_code(code, code_verifier=None):
    """
    Exchange the authorization code for credentials.
    Pass code_verifier if PKCE was used during the auth URL generation.
    Returns a Credentials object.
    """
    flow = build_flow()
    flow.fetch_token(code=code, code_verifier=code_verifier)
    return flow.credentials


def credentials_to_dict(creds):
    """Serialize Credentials to a session-safe dict."""
    return {
        "token":         creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri":     creds.token_uri,
        "client_id":     creds.client_id,
        "client_secret": creds.client_secret,
        # frozenset is not JSON-serializable — convert to list
        "scopes":        list(creds.scopes) if creds.scopes else [],
    }


def credentials_from_dict(d):
    """Deserialize Credentials from a session dict."""
    return Credentials(
        token=d["token"],
        refresh_token=d["refresh_token"],
        token_uri=d["token_uri"],
        client_id=d["client_id"],
        client_secret=d["client_secret"],
        scopes=d["scopes"],
    )


# ── Gmail API ───────────────────────────────────────────────────────────────

def fetch_inbox(creds, max_results=100, page_token=None, label_id=None):
    """
    Fetch the latest `max_results` emails from the user's inbox.
    Supports optional `page_token` for pagination and `label_id` for label filtering.
    Returns a tuple (list_of_raw_emails, next_page_token). `next_page_token` may be None.
    """
    service = build("gmail", "v1", credentials=creds)

    # Build request params
    params = {
        "userId": "me",
        "labelIds": [label_id if label_id else "INBOX"],
        "maxResults": max_results,
    }
    if page_token:
        params["pageToken"] = page_token

    result = service.users().messages().list(**params).execute()
    messages = result.get("messages", [])
    raw_emails = []
    for msg in messages:
        msg_id = msg["id"]
        raw = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="raw",
        ).execute()
        raw_data = raw.get("raw", "")
        email_bytes = base64.urlsafe_b64decode(raw_data + "==")
        raw_emails.append(email_bytes)
    next_token = result.get("nextPageToken")
    return raw_emails, next_token
