from slack_sdk import WebClient
from datetime import datetime, timedelta
import json
import os

# Slack app initialization
slack_token = os.environ.get("SLACK_USER_TOKEN")
if not slack_token:
    raise ValueError("Please set the SLACK_USER_TOKEN environment variable")

# Initialize the Slack WebClient with your access token
client = WebClient(token=slack_token)

# Calculate the date range for the last week
today = datetime.today()
last_week = today - timedelta(days=7)

# Convert dates to UNIX timestamps
start_timestamp = int(last_week.timestamp())
end_timestamp = int(today.timestamp())

# Fetch the list of channels
channels_response = client.conversations_list()
channels = channels_response['channels']

# Prepare a dictionary to store messages
all_messages = {}

# Helper function to get username from user ID
def get_username(user_id):
    user_info_response = client.users_info(user=user_id)
    if user_info_response['ok']:
        return user_info_response['user']['real_name']
    return "Unknown User"

# Loop through each channel to fetch messages
for channel in channels:
    channel_id = channel['id']
    channel_name = channel['name']
    
    messages_response = client.conversations_history(
        channel=channel_id,
        oldest=start_timestamp,
        latest=end_timestamp
    )
    
    messages = messages_response['messages']
    
    for message in messages:
        user_id = message.get('user', '')  # Handle cases where user ID is not available
        timestamp = message['ts']
        text = message.get('text', '')
        
        username = get_username(user_id)
        
        # Add message to the dictionary
        if channel_id not in all_messages:
            all_messages[channel_id] = []
        all_messages[channel_id].append({
            'user': username,
            'timestamp': timestamp,
            'text': text
        })

# Convert the dictionary to JSON
json_output = json.dumps(all_messages, indent=2)

# Print the JSON output or save it to a file
print(json_output)
