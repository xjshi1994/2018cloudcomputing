import boto3
import random
import uuid
from datetime import datetime
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('lex-runtime', 'us-east-1')
def encapsulate(output_msg):
    respond = {}
    responds = []
    respond['id'] = str(uuid.uuid4())
    respond['text'] = output_msg
    respond['timestamp'] = datetime.now().isoformat(timespec='seconds')
    responds.append(respond)
    return {"messages":responds}

def request_lex(input_msg, uid):
    response = client.post_text(
    botName='DiningConcierge',
    botAlias='David',
    userId=uid,
    inputText=input_msg
    )
    return response['message']
    
def extract_msg(event):
    messages = event['messages']
    uid = ''
    input_msg = ''
    for message in messages:
        unstructured = message["unstructured"]
        uid = unstructured["id"]
        input_msg = unstructured["text"]
    return input_msg, uid
    
    
def lambda_handler(event, context):
    input_msg, uid = extract_msg(event)
    logger.info(input_msg)
    output_msg = request_lex(input_msg, uid)
    return encapsulate(output_msg)
