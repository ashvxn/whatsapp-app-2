def get_conversation_cost(phone, category="marketing"):
    """
    Returns the estimated cost of a WhatsApp conversation based on Meta's 2026 pricing.
    """
    # Detect Country Code
    is_india = phone.startswith("91")
    
    rates = {
        "india": {
            "marketing": 0.80,  # ₹ per message
            "utility":   0.14,  # ₹ per message
            "service":   0.00   # free within 1,000/month
        },
        "global": {
            "marketing": 3.78,  # ₹ equivalent (~$0.045)
            "utility":   1.68,  # ₹ equivalent (~$0.020)
            "service":   0.00
        }
    }
    
    region = "india" if is_india else "global"
    return rates[region].get(category.lower(), rates[region]["marketing"])

def estimate_campaign_cost(contact_count, phone_list, category="marketing"):
    total = 0
    for phone in phone_list:
        total += get_conversation_cost(phone, category)
    return round(total, 4)