from common import *
import json
from urllib.request import urlopen, Request

EMOJI_WARNING = "\u26a0\ufe0f"
EMOJI_TICK = "\u2705"
EMOJI_STARS = "\u2728"

def send_tgm_message(bot_token, chat_id, message, parse_mode="Markdown"):

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode
    }
    
    req = Request(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                  data=json.dumps(payload).encode('utf-8'))
    req.add_header("Content-Type", "application/json")

    with urlopen(req, timeout=10) as res:
        response = res.read()
        

def handle_call(event, context):
    bot_token = env_or_failure("NOTIFY_BOT_TOKEN")
    receivers = env_or_failure("NOTIFY_TGM_CHATS").split(' ')
    message_title = env_or_default("NOTIFY_TGM_TITLE", "Monitor Service")
    
    for record in event["Records"]:
        mon_info = json.loads(record["Sns"]["Message"])
        endpoint = mon_info["endpoint"]
        new_state = mon_info["new_state"]

        if new_state == ServiceState.HEALTHY:
            emoji = EMOJI_TICK
        else:
            emoji = EMOJI_WARNING

        text = f"{EMOJI_STARS} *{message_title}*\n\n"
        text += f"*Endpoint:* {endpoint}\n"
        text += f"*State:* {emoji} *{ServiceState.name(new_state)}* {emoji}"

        if new_state == ServiceState.UNHEALTHY:
            last_check_message = mon_info["last_health_check_result_desc"]
            text += f"\n\n*Last health check result: *\n{last_check_message}"
        
        for receiver in receivers:
            try:
                send_tgm_message(bot_token, receiver, text)
            except Exception as ex:
                print(f"Cannot deliver message to {receiver}: {ex}")

def test():
    payload = {
        "Records": [{
            "Message": json.dumps({
                "endpoint": "https://google.asdf",
                "new_state": 2,
                "last_health_check_result_desc": "Request failure!"
            })
        }]
    }

    handle_call(payload, None)
