
import json, requests, os
from collections import defaultdict
from datetime import datetime


# ================== CONFIGURATION ==================
TOKEN = os.environ.get('USAGE_MINUTES')
USERNAME = "chandrashekar-cnc" # ← Your GitHub username
CHANNEL_ID = os.environ.get('CNC_CH_ID')
BOT_TOKEN = os.environ.get('CHATHUR_BOT')

# ===================================================

def get_actions_usage():
    url = f"https://api.github.com/users/{USERNAME}/settings/billing/usage"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    print("🔄 Fetching GitHub Actions usage...\n")
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None


def send_telegram_text_message(message: str):
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
            else:
                print(f"❌ Telegram API Error: {result}")
                return None

    except Exception as e:
        print(f"❌ Request failed: {e}")



def parse_and_display(data):

    if not data or 'usageItems' not in data:
        print("No usage data found.")
        return

    # Build the nested grouping structure: Product -> SKU -> Month Data
    # Using a lambda function to construct a multi-layered dictionary automatically
    grouped_data = defaultdict(lambda: defaultdict(list))

    for item in data['usageItems']:
        product = item['product']
        sku = item['sku']

        # Parse the raw date string and convert it into a 'YYYY-MM' format
        date_obj = datetime.strptime(item['date'], '%Y-%m-%dT%H:%M:%SZ')
        month_str = date_obj.strftime('%Y-%m')

        # Extract data fields for easier reporting
        monthly_entry = {
            'month': month_str,
            'used': item['quantity'],
            'unit': item['unitType'],
            'cost': item['grossAmount'],  # using grossAmount for your cost
            'net': item['netAmount']
        }

        # Append the extracted row into our nested structure
        grouped_data[product][sku].append(monthly_entry)


    # 3. Iterate through the grouped data to display the formatting you requested
    for product_name, skus in grouped_data.items():
        print("=" * 50)
        print(f"PRODUCT: {product_name.upper()}")
        print("=" * 50)

        for sku_name, monthly_records in skus.items():
            print(f"\n  → SKU: {sku_name}")
            print("    " + "-" * 45)
            print(f"    {'Year-Month':<12} | {'Used':<15} | {'Cost':<10}")
            print("    " + "-" * 45)

            total_used = 0
            total_cost = 0
            unit_type = ""
            net_amount = 0
            # Display each month inside this SKU
            for record in monthly_records:
                unit_type = record['unit'] # Track unit type dynamically (Minutes/Hours/etc.)
                total_used += record['used']
                total_cost += record['cost']
                net_amount += record['net']
                # Format numbers cleanly: floats limited to 4 decimal places where appropriate
                used_str = f"{record['used']:.2f} {unit_type}"
                cost_str = f"${record['cost']:.4f}"

                print(f"    {record['month']:<12} | {used_str:>15} | {cost_str:<10}")

            print("    " + "-" * 45)
            # Display the aggregated totals for the SKU
            print(f"    TOTAL USED:  {total_used:.2f} {unit_type}")
            print(f"    TOTAL COST:  ${total_cost:.4f}")
            print(f"    NET AMOUNT:  ${net_amount:.4f}")
            print("    " + "=" * 45)
        print("\n")



def parse_for_telegram(data):
    if not data or 'usageItems' not in data:
        print("No usage data found.")
        return

    # Build the nested grouping structure: Product -> SKU -> Month Data
    # Using a lambda function to construct a multi-layered dictionary automatically
    grouped_data = defaultdict(lambda: defaultdict(list))

    for item in data['usageItems']:
        product = item['product']
        sku = item['sku']

        # Parse the raw date string and convert it into a 'YYYY-MM' format
        date_obj = datetime.strptime(item['date'], '%Y-%m-%dT%H:%M:%SZ')
        month_str = date_obj.strftime('%Y-%m')

        # Extract data fields for easier reporting
        monthly_entry = {
            'month': month_str,
            'used': str(item['quantity']).replace(".0",""),
            'unit': item['unitType'].replace("Minutes","Min").replace("GigabyteHours","GB Hr").replace("Hours","Hr"),
            'cost': item['grossAmount'],  # using grossAmount for your cost
            'net': item['netAmount']
        }

        # Append the extracted row into our nested structure
        grouped_data[product][sku].append(monthly_entry)

    telegram_message = ""
    # 3. Iterate through the grouped data to display the formatting you requested
    for product_name, skus in grouped_data.items():
        telegram_message += "------------------------------\n"
        telegram_message += product_name.upper()+"\n"
        telegram_message += "------------------------------\n"
        for sku_name, monthly_records in skus.items():
            telegram_message += f"-> {sku_name}\n"
            for record in monthly_records:
                t = f"      {record['month']:<9}{record['used']:<110}\n"
                telegram_message += t
            telegram_message += f"      NET AMOUNT $0.00\n"

    return telegram_message
    #send_telegram_text_message(telegram_message)


if __name__ == "__main__":
    data = get_actions_usage()

    if data:
        parse_and_display(data)
        send_telegram_text_message(parse_for_telegram(data))

