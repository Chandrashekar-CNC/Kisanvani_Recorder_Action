import requests
import os
import time
import sys

# Get credentials from environment variables
CHANNEL_ID = os.environ.get('CNC_CH_ID')
BOT_TOKEN = os.environ.get('CHATHUR_BOT')

def send_telegram(message: str):
    if not CHANNEL_ID or not BOT_TOKEN:
        print("❌ Error: CNC_CH_ID or CHATHUR_BOT environment variable is missing!")
        return None

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': CHANNEL_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_notification': True
    }

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()

            if result.get('ok'):
                message_id = result['result']['message_id']
                print(f"✅ Telegram message sent successfully (ID: {message_id})")
                return message_id
            else:
                error_code = result.get('error_code')
                if error_code == 429:  # Too Many Requests
                    retry_after = result.get('parameters', {}).get('retry_after', 5)
                    print(f"⚠️  Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    retry_count += 1
                    continue
                else:
                    print(f"❌ Telegram API Error: {result}")
                    return None

        except Exception as e:
            print(f"❌ Request failed: {e}")
            retry_count += 1
            time.sleep(2)

    print("❌ Failed to send Telegram message after retries.")
    return None


# Allow running with message from command line argument (for GitHub Actions)
if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = sys.argv[1]
    else:
        message = "Test message from Kisanvani Recorder"

    send_telegram(message)
