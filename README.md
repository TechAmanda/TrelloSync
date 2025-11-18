# Trello to Airtable Sync

Automatically syncs cards from Trello to Airtable on a scheduled basis.

## Features
- Syncs every 5 minutes
- Maps Trello custom fields to Airtable columns
- Handles date formatting and data type conversion

## Setup

1. **Install dependencies:**
```bash
pip install requests
```

2. **Get API credentials:**
   - Trello API key & token
   - Airtable API key

3. **Configure the script:**
   - Update API keys in the config section
   - Set your Board ID and Table name

4. **Run:**
```bash
python trello_airtable_sync.py
```

## Configuration
Edit these variables in the script:
```python
TRELLO_API_KEY = 'your_key_here'
TRELLO_TOKEN = 'your_token_here'
AIRTABLE_API_KEY = 'your_airtable_token'
```
