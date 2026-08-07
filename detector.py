import re
def analyze_email(email_text):

#the dictionary containing scores and reasons 
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
}


    
#vars
    score = 0
    reasons = []
    max_score = 0



#converting to lowercase to avoid duplicacy problems+ url detection
    email_text = email_text.lower()
    urls = re.findall(r'https?://\S+', email_text)
    if len(urls) > 0:
     score += indicators["url_detection"]["weight"]
     reasons.append(indicators["url_detection"]["reason"])

    for url in urls:
       if re.search(r'\d+\.\d+\.\d+\.\d+', url):
        score += indicators["raw_ip_url"]["weight"]
        reasons.append(indicators["raw_ip_url"]["reason"])
        break



#traversing dict and adding scores and reasons 
    for category, indicator in indicators.items():

      for keyword in indicator["keywords"]:

        if keyword in email_text:
            score += indicator["weight"]
            reasons.append(indicator["reason"])
            break


#calculating max score dynamically 
    for indicator in indicators.values():
        max_score += indicator["weight"]
        risk_percentage = (score / max_score) * 100


#for determining risk level- high med low, if block
    if risk_percentage < 30:
        risk_level = "Low"
    elif risk_percentage < 70:
        risk_level = "Medium"
    else:
        risk_level = "High"


#returning the final result as a dictionary    
    return {
        "score": score,
        "reasons": reasons,
        "max_score": max_score,
        "risk_percentage": risk_percentage,
        "risk_level": risk_level
    }