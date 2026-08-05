def analyze_email(email_text):

#the dictionary containing scores and reasons 
    indicators = {
        "urgent": {
            "weight": 1,
            "reason": "Urgent language detected"
        },

        "verify": {
            "weight": 1,
            "reason": "Verification request detected"
        },

        "account suspended": {
            "weight": 2,
            "reason": "Account suspension threat detected"
        }
    }
#vars
    score = 0
    reasons = []
    max_score = 0

#converting to lowercase to avoid duplicacy problems
    email_text = email_text.lower()

#traversing dict and adding scores and reasons 
    for keyword, indicator in indicators.items():
        if keyword in email_text:
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