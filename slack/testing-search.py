import json
import slack_sdk
import os
from dotenv import load_dotenv

# Slack app initialization
load_dotenv()
slack_token = os.getenv("SLACK_USER_TOKEN_TEST")
if not slack_token:
    raise ValueError("Please set the SLACK_USER_TOKEN environment variable")

slack_app = slack_sdk.web.WebClient(token=slack_token)

def process_search(queries):
    # Search Slack messages
    list_of_messages = []
    for query in queries:
        response = slack_app.search_messages(query=query)

        if response["ok"]:
            messages = response["messages"]["matches"]
            results = [msg["text"] for msg in messages]
            list_of_messages.append(messages)
        else:
            return quart.Response(response="Failed to search Slack.", status=500)


@app.post("/search")
async def search():
    # Get the JSON request body
    req = await request.get_json(force=True)
    if not req or "query" not in req:
        return quart.Response(response=json.dumps({"error": "Invalid request body. Must contain a 'query' key."}), status=400)

    queries = req["query"]

    results = process_search(queries)

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
            "search_description.txt"))
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
