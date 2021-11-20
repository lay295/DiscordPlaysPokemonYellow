import json

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from pyboy import PyBoy
from base64 import b64decode, b64encode
from PIL import Image
from pyboy import WindowEvent
import boto3
import io
import random
import string
import binascii
import os

PUBLIC_KEY = '61a5bac59316241719607f9730308266f868817002d714a5c988d4b24a7c25f1'
PING_PONG = {"type": 1}
RESPONSE_TYPES =  { 
                    "PONG": 1, 
                    "ACK_NO_SOURCE": 2, 
                    "MESSAGE_NO_SOURCE": 3, 
                    "MESSAGE_WITH_SOURCE": 4, 
                    "ACK_WITH_SOURCE": 5
                  }


def verify_signature(event):
    raw_body = event.get("body")
    auth_sig = event['headers'].get('x-signature-ed25519')
    auth_ts  = event['headers'].get('x-signature-timestamp')
    
    message = auth_ts.encode() + raw_body.encode()
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    verify_key.verify(message, bytes.fromhex(auth_sig)) # raises an error if unequal
    
def get_random_string(length):
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
    return result_str

def ping_pong(body):
    if body.get("type") == 1:
        return True
    return False
    
def lambda_handler(event, context):
    print(f"event {event}") # debug print
    
    if 'data' in event:
        if event['data'] == 'PING':
            return {
                "statusCode": 200,
                "headers": {},
                "body": "PONG",
                "isBase64Encoded": False
            }
    
    # verify the signature
    try:
        verify_signature(event)
    except Exception as e:
        raise Exception(f"[UNAUTHORIZED] Invalid request signature: {e}")

    # check if message is a ping
    body = json.loads(event.get('body'))
    if ping_pong(body):
        return PING_PONG
        
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(TableName='pokemon_yellow', Key={'guild_id':{'N': body['guild_id']}})
    print(f"response {response}")
    pyboy = PyBoy('/opt/yellow.gbc', disable_renderer=True)
    
    f = open('/tmp/ram.state', 'wb')
    if 'Item' in response:
        print('Found save state')
        f.write(b64decode(response['Item']['state']['B']))
        f.close()
        state = open('/tmp/ram.state', "rb")
        pyboy.load_state(state)
        state.close()
    
    pyboy.set_emulation_speed(0)
    
    if 'data' in body and 'custom_id' in body['data']:
        command = body['data']['custom_id']
        if command == "UP":
            pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
            for x in range(14):
                pyboy.tick()
            pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)
        elif command == "DOWN":
            pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
            for x in range(15):
                pyboy.tick()
            pyboy.send_input(WindowEvent.RELEASE_ARROW_DOWN)
        elif command == "LEFT":
            pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)
            for x in range(14):
                pyboy.tick()
            pyboy.send_input(WindowEvent.RELEASE_ARROW_LEFT)
        elif command == "RIGHT":
            pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)
            for x in range(15):
                pyboy.tick()
            pyboy.send_input(WindowEvent.RELEASE_ARROW_RIGHT)
        elif command == "A":
            pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
            for x in range(14):
                pyboy.tick()
            pyboy.send_input(WindowEvent.RELEASE_BUTTON_A)
        elif command == "B":
            pyboy.send_input(WindowEvent.PRESS_BUTTON_B)
            for x in range(15):
                pyboy.tick()
            pyboy.send_input(WindowEvent.RELEASE_BUTTON_B)
        elif command == "START":
            pyboy.send_input(WindowEvent.PRESS_BUTTON_START)
            for x in range(14):
                pyboy.tick()
            pyboy.send_input(WindowEvent.RELEASE_BUTTON_START)
        elif command == "SELECT":
            pyboy.send_input(WindowEvent.PRESS_BUTTON_SELECT)
            for x in range(15):
                pyboy.tick()
            pyboy.send_input(WindowEvent.RELEASE_BUTTON_SELECT)
    
    for x in range(60*5):
        pyboy.tick()
        
    state = io.BytesIO()
    state.seek(0)
    
    pyboy.save_state(state)
    pyboy.stop(save=False)
    
    dynamodb.put_item(TableName='pokemon_yellow', Item={'guild_id': { 'N': body['guild_id'] }, 'state': { 'B': b64encode(state.getvalue()).decode() }})
    
    s3 = boto3.client('s3')
    name = body['guild_id'] + get_random_string(12)
    pyboy.screen_image().resize((480,432), resample=Image.NEAREST).save("/tmp/" + name + ".png", format="png")
    with open("/tmp/" + name + ".png", mode='rb') as file:
        fileContent = file.read()
        
    boundary = binascii.hexlify(os.urandom(16)).decode('ascii')
    body = json.dumps({
            "type": RESPONSE_TYPES['MESSAGE_WITH_SOURCE'],
            "data": {
                "tts": False,
                "attachments": [ {'id': 0, 'filename': "screenshot.png" } ],
                #"embeds": [ { "image": {"url": "attachment://screenshot.png", "width": 480, "height": 432} } ],
                "components": [ {"type": 1, "components": [
                        {"type": 2, "custom_id": "UP", "style": 1, "emoji": { "id": "904722142430654474", "name": ":pokemon_up:", "animated": False}},
                        {"type": 2, "custom_id": "DOWN", "style": 1, "emoji": { "id": "904724131591897098", "name": ":pokemon_dowm:", "animated": False}},
                        {"type": 2, "custom_id": "LEFT", "style": 1, "emoji": { "id": "904724142199300116", "name": ":pokemon_left:", "animated": False}},
                        {"type": 2, "custom_id": "RIGHT", "style": 1, "emoji": { "id": "904724155931459604", "name": ":pokemon_right:", "animated": False}},
                        {"type": 2, "custom_id": "REFRESH", "style": 1, "emoji": { "id": "904731380037091358", "name": ":pokemon_refresh:", "animated": False}}
                    ] },
                    
                    {"type": 1, "components": [
                        {"type": 2, "custom_id": "A", "style": 1, "emoji": { "id": "904731161891332126", "name": ":pokemon_a:", "animated": False}},
                        {"type": 2, "custom_id": "B", "style": 1, "emoji": { "id": "904731279357014067", "name": ":pokemon_b:", "animated": False}},
                        {"type": 2, "custom_id": "START", "style": 1, "emoji": { "id": "904741277717909516", "name": ":pokemon_start:", "animated": False}},
                        {"type": 2, "custom_id": "SELECT", "style": 1, "emoji": { "id": "904741289499693107", "name": ":pokemon_select:", "animated": False}}
                    ] }],
                "allowed_mentions": []
            }
        })
    
    response = "--" + boundary + '\r\n'
    response += 'Content-Disposition: form-data; name="payload_json"\nContent-Type: application/json\r\n\r\n'
    response += body + '\r\n'
    response += "--" + boundary + '\r\n'
    response += 'Content-Disposition: form-data; name="files[0]"; filename="screenshot.png\r\nContent-Type: image/png\r\nContent-Transfer-Encoding: base64\r\n\r\n'
    response += b64encode(fileContent).decode() + '\r\n'
    response += "--" + boundary + '--'
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "multipart/form-data; boundary=" + boundary
        },
        "body": response,
        "isBase64Encoded": False
    }
   
