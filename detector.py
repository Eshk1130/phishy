import re
def analyze_email(email_text):

#the dictionary containing scores and reasons 
    indicators = {
       "urgent": {
            "weight": 1,
            "reason": "Urgent language detected"
        },

       "account suspended": {
            "weight": 3,
            "reason": "Account suspension threat detected"
        },

      "has been suspended": {
            "weight": 3,
            "reason": "Account suspension threat detected"
        },

       "reset your password": {
            "weight": 3,
            "reason": "Password reset request detected"
       },

        "login": {
            "weight": 2,
            "reason": "Login request detected"
        },

       "immediately": {
             "weight": 1,
             "reason": "Immediate action requested"
       },

       "within 24 hours": {
            "weight": 2,
            "reason": "Urgency tactic detected"
        },

       "verify your identity": {
             "weight": 3,
             "reason": "Identity verification request detected"
        },

       "suspicious activity": {
            "weight": 2,
            "reason": "Security scare tactic detected"
        },

       "click here": {
            "weight": 2,
            "reason": "Suspicious link request detected"
        },

       "account blocked": {
        "weight": 3,
        "reason": "Account threat detected"
       },

       "update payment": {
        "weight": 3,
        "reason": "Payment information request detected"
      },

      "payment failed": {
        "weight": 2,
        "reason": "Payment failure warning detected"
     },

     "you've won": {
        "weight": 2,
        "reason": "Prize scam language detected"
     },

    "confirm your address": {
        "weight": 2,
        "reason": "Address verification request detected"
    }
}
    
#vars
    score = 0
    reasons = []
    max_score = 0

#converting to lowercase to avoid duplicacy problems+ url detection
    email_text = email_text.lower()
    urls = re.findall(r'https?://\S+', email_text)
    if len(urls) > 0:
     score += 2
     reasons.append("URL detected in email")


#traversing dict and adding scores and reasons 
    for keyword, indicator in indicators.items():
      if keyword in email_text:
        print("MATCHED:", keyword)
        score += indicators[keyword]["weight"]
        reasons.append(indicators[keyword]["reason"])

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
    
    return {
        "score": score,
        "reasons": reasons,
        "max_score": max_score,
        "risk_percentage": risk_percentage,
        "risk_level": risk_level
    }