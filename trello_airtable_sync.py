import requests
import time
from datetime import datetime
from datetime import timezone

# ============================
# CONFIG
# ============================
TRELLO_API_KEY = ''
TRELLO_TOKEN = ''
BOARD_ID = 'Wgt4FZEc'
TARGET_LIST_NAME = 'Approved - In progresss'

# Airtable
AIRTABLE_API_KEY = ''
AIRTABLE_BASE_ID = ''
AIRTABLE_TABLE_NAME = 'Employees'

SYNC_INTERVAL = 300  # seconds

# Trello Custom Field IDs
FIELD_IDS = {
    'lead_type': '6909b80ef955601d929edbfb',
    'sales_person': '6909b9641be83c1ad89eaeb9',
    'years_in_business': '6909ba1cfaed35e623eba7d5',
    'applied_amount': '6909ba8dfe57159a70c43261',
    'approved_amount': '6909baa119e54a1a6161fd15',
    'paid_amount': '6909baaee9e44ffed21f4f95',
    'score': '6909babb73188ab3320ec574',
    'client_type': '6909baf946844a254713a3e4',
    'status': '6909bb2c9b555e045cfa4ba6',
    'app_date': '6909bbbf0eab791fc5569fe8',
    'approved_or_declined': '6909bbd2e10eeac93f022031',
    'payout_date': '6909bbe374c02324b20d61bc',
    'priority': '6909bbe93f85080c002899ad',
    'site_name': '6909bbfa1ae6499e6abbd21b',
    'loan_no': '6909bc0a0420f856c7a7fbdd',
    'region': '6909bcae0f2ef8e8daba8d2c'
}

# ============================
# FUNCTIONS
# ============================
def test_airtable_connection():
    """Test if Airtable connection works"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    params = {"maxRecords": 1}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        print("✅ Airtable connection successful!")
        return True
    elif response.status_code == 401:
        print("❌ Airtable authentication failed. Please check your API key.")
        return False
    elif response.status_code == 404:
        print("❌ Airtable base or table not found.")
        return False
    else:
        print(f"❌ Airtable connection error: {response.status_code} - {response.text}")
        return False

def get_trello_lists(board_id):
    url = f"https://api.trello.com/1/boards/{board_id}/lists"
    params = {'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Error fetching lists: {response.status_code}")
        return None
    return response.json()

def get_list_cards(list_id):
    url = f"https://api.trello.com/1/lists/{list_id}/cards"
    params = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_TOKEN,
        'customFieldItems': 'true'
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Error fetching cards: {response.status_code}")
        return []
    return response.json()

def get_card_custom_fields(card_id):
    """Get custom field values for a card"""
    url = f"https://api.trello.com/1/cards/{card_id}/customFieldItems"
    params = {'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Error fetching custom fields for card {card_id}: {response.status_code}")
        return []
    return response.json()

def format_date_for_airtable(date_string):
    """
    Convert Trello date to Airtable format.
    Airtable expects: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.SSSZ
    """
    if not date_string:
        return None
    
    try:
        # Handle ISO format with timezone (2025-11-04T10:00:00.000Z)
        if 'T' in date_string:
            # Parse with timezone awareness
            if date_string.endswith('Z'):
                dt = datetime.fromisoformat(date_string[:-1] + '+00:00')
            else:
                dt = datetime.fromisoformat(date_string)
            
            # Return in Airtable date format (YYYY-MM-DD)
            return dt.strftime('%Y-%m-%d')
        else:
            # Try other common date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    dt = datetime.strptime(date_string, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            print(f"⚠️  Could not parse date: {date_string}")
            return None
            
    except Exception as e:
        print(f"⚠️  Error formatting date '{date_string}': {e}")
        return None

def extract_custom_field_value(field_item):
    """Extract the actual value from a custom field item"""
    if not field_item or not isinstance(field_item, dict):
        return None
    
    if 'value' not in field_item:
        return None
    
    value = field_item['value']
    
    if value is None:
        return None
    
    if isinstance(value, dict):
        if 'text' in value:
            return value['text']
        elif 'number' in value:
            return str(value['number'])
        elif 'date' in value:
            return value['date']
        elif 'checked' in value:
            return 'Yes' if value['checked'] == 'true' else 'No'
        else:
            for key, val in value.items():
                if val is not None:
                    return str(val)
            return None
    else:
        return str(value)

def convert_to_number(value):
    """Convert string to number, handling spaces and commas"""
    if not value:
        return None
    try:
        # Remove spaces and commas, then convert to float
        cleaned = str(value).replace(' ', '').replace(',', '')
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def create_airtable_record(record_data):
    """Send a record to Airtable"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {"fields": record_data}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code in (200, 201):
            print(f"✅ Record added to Airtable: {record_data.get('Site name', 'No Name')}")
            return True
        else:
            print(f"❌ Airtable API error: {response.status_code} - {response.text}")
            print(f"📤 Data sent: {record_data}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while connecting to Airtable: {e}")
        return False

def process_card(card):
    """Extract card info safely and send to Airtable"""
    name = card.get('name', 'No Name')
    print(f"📝 Processing card: {name}")
    
    custom_fields_raw = get_card_custom_fields(card['id'])
    
    field_values = {}
    for field_item in custom_fields_raw:
        if not field_item or not isinstance(field_item, dict):
            continue
        field_id = field_item.get('idCustomField')
        if field_id:
            field_values[field_id] = extract_custom_field_value(field_item)
    
    # Format ALL date fields for Airtable
    app_date = format_date_for_airtable(field_values.get(FIELD_IDS['app_date']))
    payout_date = format_date_for_airtable(field_values.get(FIELD_IDS['payout_date']))
    approved_or_declined_date = format_date_for_airtable(field_values.get(FIELD_IDS['approved_or_declined']))
    
    # Convert numeric fields to actual numbers
    loan_no = convert_to_number(field_values.get(FIELD_IDS['loan_no']))
    applied_amount = convert_to_number(field_values.get(FIELD_IDS['applied_amount']))
    approved_amount = convert_to_number(field_values.get(FIELD_IDS['approved_amount']))
    paid_amount = convert_to_number(field_values.get(FIELD_IDS['paid_amount']))
    score = convert_to_number(field_values.get(FIELD_IDS['score']))
    
    # Build the record with EXACT Airtable field names
    record = {
        "Month Reporting": datetime.now().strftime('%Y-%m-%d'),  # Date field needs proper date format
        "Site name": name,
        "App Date": app_date,
        "Approved or Declined": approved_or_declined_date,
        "Payout Date": payout_date,
        "Status": field_values.get(FIELD_IDS['status']),
        "Loan No": loan_no,  # Number field
        "# Applied Amount": applied_amount,  # Exact field name from Airtable
        "Approved Amount": approved_amount,  # Exact field name from Airtable
        "Paid Amount": paid_amount,  # Exact field name from Airtable
        "Score": score,  # Number field
        "Sales Person": field_values.get(FIELD_IDS['sales_person']),
        "Client Type": field_values.get(FIELD_IDS['client_type']),
        "Region": field_values.get(FIELD_IDS['region']),
    }
    
    # Remove None values (but keep empty strings for some fields if needed)
    record = {k: v for k, v in record.items() if v is not None}
    print(f"📊 Sending record with {len(record)} fields to Airtable")
    
    # Debug: print the actual record being sent
    print(f"🔍 Record data: {record}")
    
    return create_airtable_record(record)

def check_airtable_schema():
    """Check what fields exist in Airtable and their types"""
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tables = response.json().get('tables', [])
            for table in tables:
                if table['name'] == AIRTABLE_TABLE_NAME:
                    print(f"📋 Table '{AIRTABLE_TABLE_NAME}' fields:")
                    for field in table.get('fields', []):
                        print(f"   - {field['name']}: {field['type']}")
                    return True
        else:
            print(f"❌ Could not fetch schema: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
    
    return False

def debug_trello_fields(card_id, card_name):
    """Debug function to see what's actually in the Trello custom fields"""
    print(f"🔍 Debugging fields for card: {card_name}")
    custom_fields = get_card_custom_fields(card_id)
    
    for field in custom_fields:
        field_id = field.get('idCustomField')
        field_name = [k for k, v in FIELD_IDS.items() if v == field_id]
        field_name = field_name[0] if field_name else 'Unknown'
        value = extract_custom_field_value(field)
        print(f"   - {field_name} ({field_id}): {value} (type: {type(value)})")

def sync_trello_to_airtable():
    """Main sync loop"""
    # Test Airtable connection first
    if not test_airtable_connection():
        print("🛑 Stopping sync due to Airtable connection issues")
        return
    
    # Optional: Check Airtable schema to see field types
    print("🔍 Checking Airtable table structure...")
    check_airtable_schema()
    
    lists = get_trello_lists(BOARD_ID)
    if not lists:
        print("❌ No lists found on the board")
        return
    
    target_list_id = None
    for lst in lists:
        print(f"📋 Found list: '{lst.get('name', 'No Name')}' (ID: {lst.get('id')})")
        if lst.get('name') == TARGET_LIST_NAME:
            target_list_id = lst.get('id')
    
    if not target_list_id:
        print(f"❌ Could not find list '{TARGET_LIST_NAME}'")
        return
    
    cards = get_list_cards(target_list_id)
    if not cards:
        print("📭 No cards found in the list")
        return
    
    print(f"🃏 Found {len(cards)} cards to process")
    
    success_count = 0
    error_count = 0
    
    for card in cards:
        try:
            # Debug: show what's in the Trello fields
            debug_trello_fields(card['id'], card.get('name', 'Unknown'))
            
            if process_card(card):
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            error_count += 1
            print(f"❌ Error processing card '{card.get('name', 'Unknown')}': {e}")
    
    print(f"📊 Sync completed: {success_count} successful, {error_count} errors")

# ============================
# RUN CONTINUOUS SYNC
# ============================
print(f"🤖 Starting Trello to Airtable sync every {SYNC_INTERVAL} seconds")
print("⚙️  Testing connections...")

while True:
    print("\n" + "="*50)
    print(f"🔄 Sync started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    try:
        sync_trello_to_airtable()
    except Exception as e:
        print(f"❌ Unexpected error in main loop: {e}")
    
    print(f"⏰ Waiting {SYNC_INTERVAL} seconds until next sync...")
    time.sleep(SYNC_INTERVAL)