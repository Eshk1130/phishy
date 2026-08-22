import re

def analyze_email(
    email_text,
    sender_email,
    sender_name,
    attachments,
    reply_to,
    return_path,
    subject
):
    print("ATTACHMENTS RECEIVED:", attachments)

    # the dictionary containing scores and reasons
    #
    # Weights are grouped into four evenly-spaced severity tiers (1/2/3/4)
    # instead of the previous ad hoc 0-5 spread, so a couple of mid-severity
    # keyword hits can't stack into Medium/High as fast as they could when
    # several unrelated indicators all happened to sit at the same weight
    # (e.g. 3 or 5) for no consistent reason.
    #
    # Tier 1 (weight 1) - weak/contextual signals, common in legitimate mail
    # Tier 2 (weight 2) - moderate social-engineering language
    # Tier 3 (weight 3) - high-risk requests (credentials, fees, brand-linked)
    # Tier 4 (weight 4) - critical/severe signals (direct credential/OTP theft,
    #                     confirmed domain or brand spoofing)
    #
    # url_detection and multiple_urls stay at weight 0: they are informational
    # flags only (having a URL, or several, isn't itself suspicious) and were
    # never meant to score on their own in the original design - only the
    # raw-IP and suspicious-domain checks that inspect those URLs carry weight.
    indicators = {
        "urgency": {
            "keywords": [
                "urgent",
                "immediately",
                "within 24 hours"
            ],
            "weight": 2,
            "reason": "Urgency tactic detected"
        },

        "verification": {
    "keywords": [
        "verify",
        "verify your identity",
        "verify your account",
        "confirm your identity",
        "confirm your account"
    ],
    "weight": 3,
    "reason": "Identity verification request detected"
},

        "account_threat": {
            "keywords": [
                "account suspended",
                "has been suspended",
                "account blocked"
            ],
            "weight": 3,
            "reason": "Account threat detected"
        },

        "password_reset": {
            "keywords": [
                "reset your password"
            ],
            "weight": 3,
            "reason": "Password reset request detected"
        },

        "security_scare": {
            "keywords": [
                "suspicious activity"
            ],
            "weight": 2,
            "reason": "Security scare tactic detected"
        },

        "link_request": {
    "keywords": [
        "click here",
        "click the link below",
        "follow this link"
    ],
    "weight": 1,
    "reason": "Suspicious link request detected"
},
        "payment": {
            "keywords": [
                "update payment",
                "payment failed"
            ],
            "weight": 3,
            "reason": "Payment information request detected"
        },

        "prize_scam": {
            "keywords": [
                "you've won"
            ],
            "weight": 2,
            "reason": "Prize scam language detected"
        },

        "address_verification": {
            "keywords": [
                "confirm your address"
            ],
            "weight": 2,
            "reason": "Address verification request detected"
        },

        # --- Job / internship scam detection ---
        "job_scam": {
            "keywords": [
                "no interview required",
                "guaranteed selection",
                "selected without applying",
                "instant joining",
                "earn money from home",
                "work only 2 hours a day",
                "processing fee",
                "registration fee",
                "security deposit",
                "pay to apply",
                "limited seats",
                "immediate joining",
                "100% placement guarantee",
                "training fee",
                "deposit before joining",
                "mandatory paid training"
            ],
            "weight": 3,
            "reason": "Potential job or internship scam detected"
        },

        # --- UPI payment request detection ---
        "upi_request": {
            "keywords": [
                "@paytm",
                "@ybl",
                "@ibl",
                "@axl",
                "@oksbi",
                "@okhdfcbank",
                "@okicici"
            ],
            "weight": 3,
            "reason": "UPI payment request detected"
        },

        # --- QR code payment detection ---
        "qr_payment": {
            "keywords": [
                "scan qr",
                "scan the qr",
                "qr code payment",
                "pay via qr"
            ],
            "weight": 2,
            "reason": "QR code payment request detected"
        },

        # --- Gift card scam detection ---
        "gift_card": {
            "keywords": [
                "amazon gift card",
                "google play card",
                "steam gift card",
                "itunes gift card"
            ],
            "weight": 3,
            "reason": "Gift card payment request detected"
        },

        # --- Crypto payment detection ---
        "crypto_payment": {
            "keywords": [
                "bitcoin",
                "btc",
                "ethereum",
                "eth wallet",
                "crypto transfer"
            ],
            "weight": 3,
            "reason": "Cryptocurrency payment request detected"
        },

        # --- OTP harvesting detection ---
        "otp_request": {
            "keywords": [
                "share your otp",
                "provide otp",
                "send otp",
                "tell us your otp"
            ],
            "weight": 4,
            "reason": "OTP harvesting attempt detected"
        },

        # --- Banking credential theft detection ---
        "banking_credentials": {
            "keywords": [
                "cvv",
                "debit card number",
                "credit card number",
                "bank account number",
                "internet banking password"
            ],
            "weight": 4,
            "reason": "Banking credential request detected"
        },

        # --- Aadhaar / PAN theft detection ---
        "identity_documents": {
            "keywords": [
                "aadhaar card",
                "aadhaar number",
                "pan card",
                "upload your pan",
                "upload your aadhaar"
            ],
            "weight": 3,
            "reason": "Sensitive identity document request detected"
        },

        "url_detection": {
    "keywords": [],
    "weight": 0,
    "reason": "URL detected in email"
},
        "raw_ip_url": {
            "keywords": [],
            "weight": 4,
            "reason": "Raw IP address detected in URL"
        },
       "multiple_urls": {
    "keywords": [],
    "weight": 0,
    "reason": "Multiple URLs detected"
},
        "suspicious_domain": {
            "keywords": [],
            "weight": 4,
            "reason": "Suspicious domain detected"
        },
        "sender_mismatch": {
          "keywords": [],
          "weight": 2,
          "reason": "Sender identity and email domain do not match"
        },
        "executable_attachment": {
         "keywords": [],
         "weight": 2,
         "reason": "Executable attachment detected"
        },
        "double_extension_attachment": {
          "keywords": [],
          "weight": 2,
    "reason": "Double extension attachment detected"
},
"brand_impersonation": {
    "keywords": [],
    "weight": 4,
    "reason": "Possible brand impersonation detected in URL"
},
"reply_to_mismatch": {
    "keywords": [],
    "weight": 1,
    "reason": "Reply-To address differs from sender"
},
"return_path_mismatch": {
    "keywords": [],
    "weight": 1,
    "reason": "Return-Path differs from sender"
},
"subject_threat": {
    "keywords": [],
    "weight": 2,
    "reason": "Suspicious subject line detected"
},


    }

# list 1 for suspicious tlds
    suspicious_tlds = [
        ".xyz",
        ".tk",
        ".top",
        ".click",
    ]

 # list 2 for suspicious domains
    suspicious_domain_words = [
        "verify",
        "login",
        "secure",
        "bank",
        "update",
        "account"
    ]
#sender analysis- list of protected brands
    protected_brands = [
    "paypal",
    "microsoft",
    "google",
    "amazon",
    "netflix",
    "apple",
    "linkedin"
]

    brand_domains = {
    "paypal": "paypal.com",
    "google": "google.com",
    "amazon": "amazon.com",
    "microsoft": "microsoft.com",
    "netflix": "netflix.com",
    "apple": "apple.com",
    "linkedin": "linkedin.com"
}

    suspicious_extensions = [
    ".exe",
    ".scr",
    ".bat",
    ".cmd",
    ".js"
]

    suspicious_subject_keywords = [
    "urgent",
    "verify",
    "suspended",
    "reset",
    "action required",
    "security alert",
    "password"
]

    # vars
    score = 0
    reasons = []
    max_score = 0

    # converting to lowercase to avoid duplicacy problems + url detection
    email_text = email_text.lower()
    urls = re.findall(r'https?://\S+', email_text)
    if len(urls) > 0:
        score += indicators["url_detection"]["weight"]
        reasons.append(indicators["url_detection"]["reason"])

    # ipv4 check
    for url in urls:
        if re.search(r'\d+\.\d+\.\d+\.\d+', url):
            score += indicators["raw_ip_url"]["weight"]
            reasons.append(indicators["raw_ip_url"]["reason"])
            break
    
    # multiple url check
    url_count = len(urls)
    if url_count >= 3:
        score += indicators["multiple_urls"]["weight"]
        reasons.append(indicators["multiple_urls"]["reason"])

#loop to check for suspicious tlds and domains
    suspicious_domain_found = False

    for url in urls:
        domain = url.split("/")[2]
        for brand in protected_brands:

          if brand in domain:

            if brand_domains[brand] not in domain:

                score += indicators["brand_impersonation"]["weight"]
                reasons.append(
                indicators["brand_impersonation"]["reason"]
            )

            break

        if any(tld in domain for tld in suspicious_tlds):
           suspicious_domain_found = True

        elif any(word in domain for word in suspicious_domain_words):
           suspicious_domain_found = True

    if suspicious_domain_found:
          score += indicators["suspicious_domain"]["weight"]
          reasons.append(indicators["suspicious_domain"]["reason"])

#temp print("ATTACHMENTS:", attachments)

#version 3.1- sender analysis
    sender_domain = sender_email.split("@")[1]
    sender_name_lower = sender_name.lower()

    for brand in protected_brands:
        if brand in sender_name_lower:
            if brand not in sender_domain:
               score += indicators["sender_mismatch"]["weight"]
               reasons.append(indicators["sender_mismatch"]["reason"])
            break

        # Version 4.3 - Reply-To analysis

    if reply_to:

        sender_domain = sender_email.split("@")[1]
        reply_domain = reply_to.split("@")[1]

        if sender_domain != reply_domain:
           score += indicators["reply_to_mismatch"]["weight"]
           reasons.append(
            indicators["reply_to_mismatch"]["reason"]
        )

    # Version 4.3 - Return-Path analysis

    print("RETURN PATH RECEIVED:", return_path)

    if return_path:
        sender_domain = sender_email.split("@")[1]
        return_domain = return_path.split("@")[1]

        if sender_domain != return_domain:
            score += indicators["return_path_mismatch"]["weight"]
            reasons.append(
                indicators["return_path_mismatch"]["reason"]
            )

# Version 4.3 - Subject Analysis

    print("SUBJECT RECEIVED:", subject)
    subject_lower = subject.lower()

    for keyword in suspicious_subject_keywords:
        print("CHECKING:", keyword)
        if keyword in subject_lower:
            print("MATCH FOUND:", keyword)
            score += indicators["subject_threat"]["weight"]
            reasons.append(
                indicators["subject_threat"]["reason"]
            )
            break

# Version 3.2 - Executable Attachment Detection

    executable_attachment_found = False
    for attachment in attachments:
        # print("CHECKING:", attachment)

         if any(attachment.endswith(ext) for ext in suspicious_extensions):
            executable_attachment_found = True
            #print("EXECUTABLE FOUND:", attachment)
            break

    if executable_attachment_found:
      score += indicators["executable_attachment"]["weight"]
      reasons.append(indicators["executable_attachment"]["reason"])

#version 3.2- double attachment detection
    double_extension_found = False

    for attachment in attachments:
        parts = attachment.split(".")
        if len(parts) >= 3:
           if parts[-1] in ["exe", "scr", "bat", "cmd", "js"]:
              double_extension_found = True
              #print("DOUBLE EXTENSION FOUND:", attachment)
              break

    if double_extension_found:
       score += indicators["double_extension_attachment"]["weight"]
       reasons.append(
        indicators["double_extension_attachment"]["reason"]
    )

# traversing dict and adding scores and reasons
    for category, indicator in indicators.items():
        for keyword in indicator["keywords"]:
            if keyword in email_text:
                score += indicator["weight"]
                reasons.append(indicator["reason"])
                break

   # calculating max score dynamically
    for indicator in indicators.values():
        max_score += indicator["weight"]

# keep percentage for display
    # NOTE: this was hardcoded to /15 from an earlier, smaller version of the
    # indicator set. Now that there are many more indicators (and weights as
    # high as 5), that denominator badly under-represents max_score and can
    # push risk_percentage to 100% on a single mid-weight hit. Using the
    # dynamically computed max_score keeps this proportional as indicators
    # are added/removed/reweighted in the future.
    risk_percentage = min((score / max_score) * 100, 100) if max_score else 0

    # confidence: how sure the model is that this is a scam, based on how
    # many independent signals fired, not just their combined weight. This
    # is deliberately a simple heuristic for display purposes only, not a
    # statistically calibrated probability.
    confidence = min(score * 10, 100)

# determine risk level using raw score
    if score < 5:
        risk_level = "Low"
    elif score < 10:
        risk_level = "Medium"
    else:
        risk_level = "High"
    print("SCORE:", score)
    print("REASONS:", reasons)
    print("RISK %:", risk_percentage)
    print("RISK LEVEL:", risk_level)
    print("CONFIDENCE:", confidence)
    # returning the final result as a dictionary    
    return {
        "score": score,
        "reasons": reasons,
        "max_score": max_score,
        "risk_percentage": risk_percentage,
        "risk_level": risk_level,
        "confidence": confidence
    }