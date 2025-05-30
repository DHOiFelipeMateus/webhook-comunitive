from slack_sdk import WebClient
from app.settings import settings

def send_slack_message(message):
    
    # Set up a WebClient with the Slack OAuth token
    client = WebClient(token=settings.SLACK_TOKEN)

    # Send a message
    client.chat_postMessage(
        channel="log-webhook-rh",
        text=message, 
        username='WebhookScormComunitive'
    )
       
