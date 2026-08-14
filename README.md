# 🛡️ Phishy

**Phishy** is a Python-based email phishing detection and threat analysis tool with a Gmail-style web interface.

It analyzes email content, URLs, sender information, and attachments to identify phishing indicators and produces a detailed risk report explaining exactly why an email was flagged.

---

## Why Phishy?

Spam filters make a binary decision — spam or not. Phishy goes further:

| Spam Filter | Phishy |
|---|---|
| Binary: spam or not | Graded 0–100 risk score |
| Black box — no explanation | Tells you exactly what's suspicious |
| Can miss targeted spear-phishing | Catches logic-level tricks (sender mismatch, reply-to hijack, brand impersonation) |
| No user education | Teaches you what makes an email dangerous |

> A sophisticated phishing email written specifically for you will often pass Gmail's spam filter. Phishy still flags the red flags.

---

## Features

### Email Content Analysis

Detects common social-engineering techniques:

- Urgency tactics (`urgent`, `immediately`, `within 24 hours`)
- Identity verification requests (`verify your account`, `confirm your identity`)
- Account threats (`account suspended`, `account blocked`)
- Password reset requests
- Security scare tactics (`suspicious activity`)
- Suspicious link requests (`click here`)
- Payment-related language (`payment failed`, `update payment`)
- Prize scam language (`you've won`)

### URL Analysis

- URL presence detection
- Raw IP address URLs (e.g. `http://192.168.1.1/login`)
- Multiple URL detection
- Suspicious TLDs (`.xyz`, `.tk`, `.top`, `.click`)
- Suspicious domain keywords (`verify`, `login`, `secure`, `bank`)
- Brand impersonation in URLs (e.g. `paypal-login.xyz`)

### Sender Analysis

- Sender name vs. email domain mismatch
- Protected brand comparison (PayPal, Google, Amazon, Microsoft, Netflix, Apple, LinkedIn)
- Reply-To address mismatch detection
- Return-Path mismatch detection

### Attachment Analysis

- Executable attachment detection (`.exe`, `.scr`, `.bat`, `.cmd`, `.js`)
- Double-extension detection (e.g. `invoice.pdf.exe`)

### Subject Analysis

- Suspicious subject line keywords (`urgent`, `verify`, `suspended`, `action required`, `security alert`)

### Risk Scoring

Every detected indicator has a weight. Phishy calculates:

- **Risk score** — sum of triggered indicator weights
- **Max possible score** — sum of all indicator weights
- **Risk percentage** — `(score / max_score) × 100`
- **Risk level** — `Low` (<30%), `Medium` (30–69%), `High` (≥70%)
- **Reasons list** — every triggered indicator explained in plain English

---

## Web Interface

Phishy includes a Gmail-style dark-mode web UI with a three-panel layout:

```
[Left Sidebar] | [Inbox List] | [Email Viewer + Phishy Report Panel]
```

### Panels

**Sidebar** — Compose (upload trigger), Inbox, Starred, Sent, Drafts, Spam, Trash, Labels

**Inbox List** — Each uploaded email appears as a row with:
- Colour-coded risk badge (🔴 High / 🟡 Medium / 🟢 Low)
- Sender name, subject, snippet, timestamp

**Email Viewer** — Subject + risk badge, sender info, warning banner for High/Medium emails, body, Reply/Forward

**Phishy Report Panel** — Risk shield, score bar, all flagged reasons with human-readable descriptions, recommendations, Report Phishing button

### Uploading Emails

- Click the **Upload .eml** button in the inbox toolbar
- Or **drag and drop** a `.eml` file anywhere on the page
- The email is instantly analyzed and added to the inbox

---

## Project Structure

```
phishy/
│
├── run.py                        ← Entry point: python run.py
├── pyrightconfig.json            ← IDE path config (Pylance/Pyright)
├── requirements.txt
├── README.md
│
├── backend/
│   ├── __init__.py
│   ├── app.py                    ← Flask routes (/upload, /emails, /emails/<id>)
│   ├── detector.py               ← Core phishing detection engine
│   └── eml_parser.py             ← .eml file parser
│
├── frontend/
│   ├── templates/
│   │   └── inbox.html            ← Gmail-style three-panel UI
│   └── static/
│       ├── css/
│       │   └── style.css         ← Dark theme stylesheet
│       └── js/
│           └── app.js            ← Upload, render, Phishy panel logic
│
├── tests/
│   └── test_detector.py          ← Pytest unit tests for the detector
│
└── sample_emails/
    └── phishing_email.eml        ← Sample .eml for testing
```

---

## API Routes

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Serves the inbox UI |
| `POST` | `/upload` | Upload a `.eml` file → analyze → return JSON |
| `GET` | `/emails` | List all analyzed emails |
| `GET` | `/emails/<id>` | Full email data + analysis for one email |

### `POST /upload` — Response example

```json
{
  "id": "fa2df42c-...",
  "sender_name": "PayPal Support",
  "sender_email": "support@gmail.com",
  "subject": "Verify Your Account",
  "snippet": "URGENT! Your account has been suspended...",
  "risk_level": "Medium",
  "risk_score": 35,
  "max_score": 52,
  "risk_pct": 67.3,
  "reasons": [
    "URL detected in email",
    "Possible brand impersonation detected in URL",
    "Sender identity and email domain do not match",
    "Reply-To address differs from sender",
    "Executable attachment detected",
    "Double extension attachment detected",
    "Urgency tactic detected",
    "..."
  ],
  "attachments": ["invoice.pdf.exe"]
}
```

---

## Getting Started

### Requirements

```
Python 3.8+
Flask
```

Install dependencies:

```bash
pip install flask
```

### Run

```bash
python run.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

### Tests

```bash
python -m pytest tests/
```

---

## Architecture

```
Browser (Gmail-style UI)
        │  fetch() / form POST
        ▼
Flask (backend/app.py)
  POST /upload  →  eml_parser.py  →  detector.py  →  JSON response
  GET  /emails  →  in-memory store → JSON list
        │
        ▼
   detector.py
   analyze_email(text, sender, attachments, headers, subject)
        │
        ▼
   Risk Score + Reasons + Level
```

---

## How It Works

```
.eml File Upload
      │
      ▼
eml_parser.py
      ├── Sender name & email
      ├── Subject
      ├── Reply-To
      ├── Return-Path
      ├── Plain-text body
      └── Attachments
              │
              ▼
        detector.py
              ├── Content analysis (keywords)
              ├── URL analysis
              ├── Sender analysis
              ├── Reply-To / Return-Path analysis
              ├── Subject analysis
              └── Attachment analysis
                      │
                      ▼
                Risk Scoring
                      │
                      ▼
               Phishy Report
           (rendered in browser)
```

---

## Risk Levels

| Level | Risk % | Meaning |
|---|---|---|
| 🟢 Low | < 30% | No major phishing indicators |
| 🟡 Medium | 30–69% | Suspicious signals — proceed with caution |
| 🔴 High | ≥ 70% | Do NOT interact with this email |

---

## Technologies

- **Python** — Backend logic
- **Flask** — Web server and API
- **Python `email` / `email.parser`** — `.eml` MIME parsing
- **Python `re`** — URL and pattern detection
- **HTML / CSS / Vanilla JS** — Frontend (no frameworks)
- **Google Fonts** — Google Sans / Roboto

---

## Development Status

### ✅ Version 3 — Detection Engine
- Email content analysis (keywords, urgency, social engineering)
- URL detection, raw IP, multiple URLs, suspicious domains
- Brand impersonation in URLs
- Sender mismatch detection
- Executable and double-extension attachment detection
- Risk scoring and classification

### ✅ Version 4 — .eml Parsing
- Real `.eml` file input
- Automatic header extraction (sender, subject, reply-to, return-path)
- MIME attachment extraction
- Subject and reply-to threat detection

### ✅ Version 5 — Web Platform (In Progress)

| Milestone | Status |
|---|---|
| 5.1 Flask ↔ Detector | ✅ Done |
| 5.2 Upload real `.eml` | ✅ Done |
| 5.3 Show report in browser | ✅ Done |
| 5.4 Gmail-style inbox | ✅ Done |
| 5.5 Multiple emails | 🔨 Next |
| 5.6 OAuth + Gmail API | 🔨 Planned |

### 🔨 Planned
- Gmail OAuth integration (read-only inbox access)
- Automated inbox scanning via Gmail API
- SPF / DKIM / DMARC header analysis
- Batch email scanning
- Persistent storage (SQLite)

---

## Important Note

Phishy is an educational cybersecurity project demonstrating email threat analysis techniques.

Its results should not be treated as definitive proof that an email is malicious or legitimate. A phishing detector can produce false positives and false negatives — suspicious emails should always be investigated carefully through official channels.

---

## Project Goal

The long-term goal of Phishy is to evolve from a rule-based phishing detector into a practical email threat analysis tool capable of automatically scanning a real Gmail inbox and surfacing security-focused insights in a clean, transparent UI.
