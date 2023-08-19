import json
import slack_sdk
import quart
import quart_cors
from quart import request
from datetime import datetime, timedelta
import io
import os

app = quart_cors.cors(
    quart.Quart(__name__),
    allow_origin="https://chat.openai.com"
)

# Slack app initialization
slack_token = os.environ.get("SLACK_USER_TOKEN")
if not slack_token:
    raise ValueError("Please set the SLACK_USER_TOKEN environment variable")

slack_app = slack_sdk.web.WebClient(token=slack_token)


def read_file_contents(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return json.dumps(content)

def process_search(query):
    # Search Slack messages
    response = slack_app.search_messages(query=query)

    if response["ok"]:
        messages = response["messages"]["matches"]
        results = [msg["text"] for msg in messages]
        return messages
    else:
        return quart.Response(response="Failed to search Slack.", status=500)

def get_all_messages(days):
    today = datetime.today()
    last_week = today - timedelta(days=days)

    # Convert dates to UNIX timestamps
    start_timestamp = int(last_week.timestamp())
    end_timestamp = int(today.timestamp())

    # Fetch the list of channels
    channels_response = slack_app.conversations_list()
    channels = channels_response['channels']

    # Prepare a dictionary to store messages
    all_messages = {}

    # Helper function to get username from user ID
    def get_username(user_id):
        user_info_response = slack_app.users_info(user=user_id)
        if user_info_response['ok']:
            return user_info_response['user']['real_name']
        return "Unknown User"

    # Loop through each channel to fetch messages
    for channel in channels:
        channel_id = channel['id']
        channel_name = channel['name']
        
        messages_response = slack_app.conversations_history(
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

    return all_messages
    
@app.post("/search")
async def search():
    # Get the JSON request body
    req = await request.get_json(force=True)
    if not req or "query" not in req:
        return quart.Response(response=json.dumps({"error": "Invalid request body. Must contain a 'query' key."}), status=400)

    query = req["query"]
    
    results = get_all_messages(int(query))

    return quart.Response(response=json.dumps({"results": results}), status=200)


@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers["Host"]
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        text = text.replace("\"PLUGIN_DESCRIPTION_FOR_MODEL\"", read_file_contents(
            "description_for_model.txt"))
        text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
        app.logger.info("Received plugin text: %s", text)
        return quart.Response(text, mimetype="text/json")


@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers["Host"]
    with open("openapi.yaml") as f:
        text = f.read()
        text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
    return quart.Response(text, mimetype="text/yaml")


def main():
    app.run(debug=True, host="0.0.0.0", port=5003)


if __name__ == "__main__":
    main()
