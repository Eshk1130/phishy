def analyze_email(email_text):

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

    score = 0
    reasons = []
    email_text = email_text.lower()
    for keyword in indicators:
        print(keyword)

    return {
        "score": score,
        "reasons": reasons
    }