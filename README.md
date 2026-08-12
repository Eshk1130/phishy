# Phishy

**Phishy** is a Python-based email phishing detection and threat analysis tool.

It analyzes email content, URLs, sender information, and attachments to identify common phishing indicators and produces a risk score with an explanation of why an email was flagged.

The project started as a simple rule-based phishing detector and is being developed toward a more realistic email threat analysis tool.

---

## Features

### Email Content Analysis

Phishy looks for common social-engineering techniques such as:

* Urgency tactics
* Identity verification requests
* Account threats
* Password reset requests
* Security scare tactics
* Suspicious link requests

### URL Analysis

Phishy analyzes URLs found inside emails for:

* URL presence
* Raw IP addresses
* Multiple URLs
* Suspicious domains
* Suspicious top-level domains
* Possible brand impersonation

### Sender Analysis

Phishy can identify potential sender impersonation by comparing:

* Displayed sender identity
* Sender email domain
* Protected brand names

For example:

```text
PayPal Support <support@gmail.com>
```

can be flagged when the displayed identity does not match the email domain.

### Attachment Analysis

Phishy currently detects:

* Executable attachments
* Suspicious double-extension filenames

Examples:

```text
payment.exe
invoice.pdf.exe
document.docx.scr
```

### Risk Scoring

Each detected indicator contributes to an overall score.

Phishy calculates:

* Risk score
* Maximum possible score
* Risk percentage
* Risk level
* Reasons for detection

Example:

```text
PHISHY REPORT

Risk Level      : High
Risk Score      : 34/44
Risk Percentage : 77.27%

Reasons:

- URL detected in email
- Raw IP address detected in URL
- Possible brand impersonation detected in URL
- Executable attachment detected
- Double extension attachment detected

Recommendation:
Do NOT interact with this email.
```

---

## Current Email Input

Phishy can currently work with email content stored in files.

### Text files

Example:

```text
emails/
├── phishing_email.txt
└── legitimate_email.txt
```

The program reads the selected file and passes its contents to the detection engine.

### `.eml` files

Phishy is currently being expanded to support real saved email files.

It can already:

* Parse `.eml` files
* Extract the `From` field
* Extract sender name
* Extract sender email
* Extract the plain-text email body

Automatic attachment extraction is currently under development.

---

## Project Structure

```text
phishy/
│
├── main.py
├── detector.py
├── README.md
│
├── emails/
│   ├── phishing_email.txt
│   └── legitimate_email.txt
│
├── sample_emails/
│   └── phishing_email.eml
│
└── reports/
```

### `main.py`

Handles:

* User input
* Email file loading
* `.eml` parsing
* Passing extracted information to the detector
* Displaying the final report

### `detector.py`

Contains the core phishing detection engine, including:

* Indicators
* Scoring
* URL analysis
* Sender analysis
* Attachment analysis
* Risk classification

---

## How It Works

The current architecture follows this general flow:

```text
Email File
    │
    ▼
Email Parsing
    │
    ├── Sender
    ├── Body
    └── Attachments
            │
            ▼
     Detection Engine
            │
            ├── Content Analysis
            ├── URL Analysis
            ├── Sender Analysis
            └── Attachment Analysis
                    │
                    ▼
              Risk Scoring
                    │
                    ▼
             PHISHY REPORT
```

---

## Risk Levels

The calculated risk percentage is used to classify an email as:

```text
Low
Medium
High
```

The report also provides the individual indicators that contributed to the result rather than returning only a simple phishing/not-phishing decision.

---

## Technologies

* **Python**
* Python `re` module for pattern detection
* Python `email` package for `.eml` parsing
* Regular expressions
* Rule-based threat detection
* Risk scoring

No external machine-learning model is currently required.

---

## Current Development Status

### Version 3

**Completed**

* Email content analysis
* URL detection
* Raw IP detection
* Multiple URL detection
* Suspicious domain detection
* Brand impersonation detection
* Sender mismatch detection
* Executable attachment detection
* Double-extension detection
* Risk scoring
* Human-readable reports

### Version 4

**In progress**

* File-based email input
* `.eml` parsing
* Automatic sender extraction
* Automatic email body extraction
* Automatic attachment extraction
* Email header analysis

### Planned Version 5

Future development will focus on more advanced cybersecurity capabilities, including:

* Threat intelligence integration
* SPF analysis
* DKIM analysis
* DMARC analysis
* Batch email scanning
* Improved reporting
* Possible web-based interface

---

## Important Note

Phishy is an educational cybersecurity project designed to demonstrate email threat analysis techniques.

Its results should not be treated as definitive proof that an email is malicious or legitimate.

A phishing detector can produce both false positives and false negatives, so suspicious emails should always be investigated carefully.

---

## Project Goal

The long-term goal of Phishy is to evolve from a basic rule-based phishing detector into a practical email threat analysis tool capable of automatically processing real email files and providing security-focused analysis.

---
