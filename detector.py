import re

def analyze_email(email_text, sender_email, sender_name, attachments):
    # the dictionary containing scores and reasons
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
                "confirm your account",
                "login"
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
                "click here"
            ],
            "weight": 2,
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
        "url_detection": {
            "keywords": [],
            "weight": 2,
            "reason": "URL detected in email"
        },
        "raw_ip_url": {
            "keywords": [],
            "weight": 3,
            "reason": "Raw IP address detected in URL"
        },
        "multiple_urls": {
            "keywords": [],
            "weight": 2,
            "reason": "Multiple URLs detected"
        },
        "suspicious_domain": {
            "keywords": [],
            "weight": 3,
            "reason": "Suspicious domain detected"
        },
        "sender_mismatch": {
          "keywords": [],
          "weight": 3,
          "reason": "Sender identity and email domain do not match"
        },
        "executable_attachment": {
         "keywords": [],
         "weight": 3,
         "reason": "Executable attachment detected"
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

    suspicious_extensions = [
    ".exe",
    ".scr",
    ".bat",
    ".cmd",
    ".js"
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

        if any(tld in domain for tld in suspicious_tlds):
           suspicious_domain_found = True

        elif any(word in domain for word in suspicious_domain_words):
           suspicious_domain_found = True

    if suspicious_domain_found:
          score += indicators["suspicious_domain"]["weight"]
          reasons.append(indicators["suspicious_domain"]["reason"])

#temp
    print("ATTACHMENTS:", attachments)

#version 3.1- sender analysis
    sender_domain = sender_email.split("@")[1]
    sender_name_lower = sender_name.lower()

    for brand in protected_brands:
        if brand in sender_name_lower:
            if brand not in sender_domain:
               score += indicators["sender_mismatch"]["weight"]
               reasons.append(indicators["sender_mismatch"]["reason"])
            break

# Version 3.2 - Executable Attachment Detection

    executable_attachment_found = False
    for attachment in attachments:
         print("CHECKING:", attachment)

         if any(attachment.endswith(ext) for ext in suspicious_extensions):
            executable_attachment_found = True
            print("EXECUTABLE FOUND:", attachment)
            break

    if executable_attachment_found:
      score += indicators["executable_attachment"]["weight"]
      reasons.append(indicators["executable_attachment"]["reason"])

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

    # avoid division by zero
    risk_percentage = (score / max_score) * 100 if max_score else 0

    # for determining risk level- high med low, if block
    if risk_percentage < 30:
        risk_level = "Low"
    elif risk_percentage < 70:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # returning the final result as a dictionary    
    return {
        "score": score,
        "reasons": reasons,
        "max_score": max_score,
        "risk_percentage": risk_percentage,
        "risk_level": risk_level
    }
