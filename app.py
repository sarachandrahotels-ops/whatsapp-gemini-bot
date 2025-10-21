from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Environment variables - you'll set these in Render.com
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'mytoken123')
WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN', '')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # WhatsApp verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print('Webhook verified successfully!')
            return challenge, 200
        else:
            return 'Verification failed', 403
    
    elif request.method == 'POST':
        # Handle incoming messages
        data = request.get_json()
        
        try:
            # Extract message details
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            
            if 'messages' in value:
                message = value['messages'][0]
                from_number = message['from']
                message_body = message['text']['body']
                
                print(f"Received message from {from_number}: {message_body}")
                
                # Get AI response from Gemini
                ai_response = get_gemini_response(message_body)
                
                # Send reply via WhatsApp
                send_whatsapp_message(from_number, ai_response)
                
        except Exception as e:
            print(f"Error processing message: {e}")
        
        return jsonify({'status': 'success'}), 200

def get_gemini_response(user_message):
    """Get response from Gemini AI"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": user_message
            }]
        }]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        result = response.json()
        
        ai_text = result['candidates'][0]['content']['parts'][0]['text']
        return ai_text
    
    except Exception as e:
        print(f"Gemini API error: {e}")
        return "Sorry, I couldn't process your request at the moment."

def send_whatsapp_message(to_number, message):
    """Send message via WhatsApp Business API"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "text": {"body": message}
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Message sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending message: {e}")

@app.route('/')
def home():
    return "WhatsApp Gemini Bot is running! ✅"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)