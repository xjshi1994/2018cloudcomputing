import json
import dateutil.parser
import datetime
import time
import os
import math
import random
import logging
import boto3
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }
def validate_order(city_area, cuisine, number_of_people, date, time, phone_number):
    return (city_area != None and cuisine != None and number_of_people != None and date != None and time != None and phone_number != None)


def thank_you_response(intent_request):
    return {"dialogAction": {
    "type": "Close",
    "fulfillmentState": "Fulfilled",
    "message": {
      "contentType": "PlainText",
      "content": "You are welcome."
    }
    }} 


def dining_suggestion_response(intent_request):
    city_area = get_slots(intent_request)['CityArea']
    cuisine = get_slots(intent_request)['Cuisine']
    number_of_people = get_slots(intent_request)['NumberOfPeople']
    date = get_slots(intent_request)['Date']
    time = get_slots(intent_request)['Time']
    phone_number = get_slots(intent_request)['PhoneNumber']
    source = intent_request['invocationSource']
    
    
    #SQS
    if validate_order (city_area, cuisine, number_of_people, time, phone_number, source):
        slots = get_slots(intent_request)
        #get the service resource
        sqs = boto3.resource('sqs')
        #get queue
        queue = sqs.get_queue_by_name(QueueName = 'dining_order')
        #send messages
        response = queue.send_message(MessageBody = json.dumps(slots))
        
    return {"dialogAction": {
    "type": "Close",
    "fulfillmentState": "Fulfilled",
    "message": {
      "contentType": "PlainText",
      "content": "You¡¯re all set. Expect my recommendations shortly! Have a good day."
    }
    }}
    

def greeting_response(intent_request):
     return {"dialogAction": {
    "type": "Close",
    "fulfillmentState": "Fulfilled",
    "message": {
      "contentType": "PlainText",
      "content": "Hi there, how can I help?"
    }
    }} 


def dispatch(intent_request):
    intent_name = intent_request['currentIntent']['name']
    
    if intent_name == 'GreetingIntent':
        return greeting_response(intent_request)
    elif intent_name == 'DiningSuggestionIntent':
        return dining_suggestion_response(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank_you_response(intent_request)
    raise Exception("Intent with name" + intent_name + 'not supported')
        


def lambda_handler(event, context):
    #set default time zone
    os.environ['TZ'] = 'America/New_York'
    time.tzset();
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
