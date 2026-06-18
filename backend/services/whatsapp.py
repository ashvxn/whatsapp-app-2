import time
import requests
from flask import current_app, g

def get_headers():
    return {
        "Authorization": f"Bearer {current_app.config['WHATSAPP_TOKEN']}",
        "Content-Type": "application/json"
    }

def get_url():
    phone_id = getattr(g, 'current_phone_id', None) or current_app.config['PHONE_NUMBER_ID']
    return f"https://graph.facebook.com/v21.0/{phone_id}/messages"

def send_api_request(payload, retries=3):
    url = get_url()
    headers = get_headers()
    print(f"DEBUG: Sending message from Phone ID: {url.split('/')[-2]}")
    for attempt in range(retries):
        response = requests.post(url, json=payload, headers=headers)
        print(f"DEBUG: WhatsApp API Status: {response.status_code}")
        print(f"DEBUG: Response: {response.text}")
        if response.status_code == 429:
            wait = 2 ** attempt  # 1s, 2s, 4s
            print(f"Rate limited. Retrying in {wait}s...")
            time.sleep(wait)
            continue
        return response
    return response

def send_template(to, template_name, image_url=None, body_text=None):
    components = []
    if image_url:
        components.append({
            "type": "header",
            "parameters": [{"type": "image", "image": {"link": image_url}}]
        })
    if body_text:
        components.append({
            "type": "body",
            "parameters": [{"type": "text", "parameter_name": "text_content", "text": body_text}]
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            "components": components
        }
    }
    return send_api_request(payload)

def send_text(to, text):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    return send_api_request(payload)

def send_image(to, image_url, caption=None):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": image_url}
    }
    if caption:
        payload["image"]["caption"] = caption
    return send_api_request(payload)

def send_interactive_buttons(to, text, buttons):
    interactive_buttons = [{"type": "reply", "reply": btn} for btn in buttons[:3]]
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": interactive_buttons}
        }
    }
    return send_api_request(payload)

def mark_as_read(message_id):
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {"type": "text"}
    }
    send_api_request(payload)

def send_list_message(to, text, button_text, sections):
    """
    Sends a list message (up to 10 options).
    sections: [{"title": "Header", "rows": [{"id": "id1", "title": "Label", "description": "desc"}]}]
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": text},
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
    }
    return send_api_request(payload)