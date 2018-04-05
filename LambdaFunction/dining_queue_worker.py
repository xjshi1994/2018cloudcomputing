from __future__ import print_function
import boto3
import json
import logging
import pprint
from botocore.vendored import requests
from botocore.exceptions import ClientError
import sys
import urllib
import argparse
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode
    
SEARCH_LIMIT = 3
# Yelp Fusion no longer uses OAuth as of December 7, 2017.
# You no longer need to provide Client ID to fetch Data
# It now uses private keys to authenticate requests (API Key)
# You can find it on
# https://www.yelp.com/developers/v3/manage_app
API_KEY= '6uImrHfey43mC5vw3erNMKCMQ3W99yWex1PI8HFXcFyVyNYRCZU07hZ-sTOVt4jt-ijsZPsP8zzOBnYQOulauJNB1Gb3hEytsIRduDeiZQrpJpylxQQmBLR6bvrCWnYx' 


# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.
# log
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# sqs
sqs_url = 'https://sqs.us-east-1.amazonaws.com/401272897508/dining_order'
sqs_client = boto3.client('sqs')
TOPIC_ARN = 'arn:aws:sns:us-east-1:401272897508:dining_suggestions_sns'

#SES
SENDER = "xjshi1994@hotmail.com"
AWS_REGION = "us-east-1"
SUBJECT = "Dining suggestions"
CHARSET = "UTF-8"
def request(host, path, api_key, url_params=None):
    """Given your API_KEY, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }

    print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()
    
def search(api_key, term, location):
    """Query the Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
    Returns:
        dict: The JSON response from the request.
    """

    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)

def get_business(api_key, business_id):
    """Query the Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path, api_key)


def query_api(term, location):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """
    response = search(API_KEY, term, location)

    businesses = response.get('businesses')

    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return

    business_id = businesses[0]['id']

    print(u'{0} businesses found, querying business info ' \
        'for the top result "{1}" ...'.format(
            len(businesses), business_id))
    response = get_business(API_KEY, business_id)
    
    logger.info(u'Result for business "{0}" found:'.format(business_id))
    print(u'Result for business "{0}" found:'.format(business_id))
    pprint.pprint(response, indent=2)
    
    return response

def get_value_from_message(body_dict, attribute):
    return body_dict[attribute]

def processMessage(message):
    
    dining = {}
    
    body_json = message['Messages'][0]['Body']
    body_dict = json.loads(body_json)
    receipt_handle = message['Messages'][0]['ReceiptHandle']
    
    dining['city_area'] = get_value_from_message(body_dict, 'CityArea')
    dining['cuisine']  = get_value_from_message(body_dict, 'Cuisine')
    dining['date']  = get_value_from_message(body_dict, 'Date')
    dining['number_of_people']  = get_value_from_message(body_dict, 'NumberOfPeople')
    dining['phone_number']  = get_value_from_message(body_dict, 'PhoneNumber')
    dining['time']  = get_value_from_message(body_dict, 'Time')
    
    #delete message
    sqs_client.delete_message(QueueUrl = sqs_url, ReceiptHandle = receipt_handle)
    return dining
    
def poll():
    message = sqs_client.receive_message(QueueUrl = sqs_url)
    return message

def get_html_p(html_dict):
    html_body = ''
    for key, value in html_dict.items():
        html_body += '<p>' + key + ' :' + value + '</p>'
        
    return html_body

def json2html(input, dining_info_dict):
    html_dict = {}
    #from dict to html
    html_dict['name'] = input['name']
    html_dict['phone'] = input['phone']
    html_dict['rating'] = str(input['rating'])
    address_list = input['location']['display_address']
    address = ''
    # get full address
    for a in address_list:
        address = address + ' ' + a
    html_dict['address'] = address
    image_url = input['image_url']
    
    img_tag = '<img src="{0}">'.format(image_url)
    html_open = '<p>' + 'Hello! Here are my {0} restaurant suggestions for {1} people, for {2} at {3}'.format(dining_info_dict['cuisine'], dining_info_dict['number_of_people'],dining_info_dict['date'],dining_info_dict['time'])+'</p>'
    html = html_open + get_html_p(html_dict) + img_tag
    return html

def send_email(query_result, email_address, dining_info_dict):
    client_ses = boto3.client('ses', region_name = AWS_REGION)
    #json to html
    BODY_HTML = json2html(query_result, dining_info_dict)
    RECIPIENT = email_address
    BODY_TEXT = 'Have a good day!'
    try:
    #Provide the contents of the email.
        response = client_ses.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['ResponseMetadata']['RequestId'])
    

def yelp_api(message, dining_info_dict):

    # yelp search
    DEFAULT_TERM = dining_info_dict['cuisine']
    DEFAULT_LOCATION = dining_info_dict['city_area']
    
    parser = argparse.ArgumentParser()

    parser.add_argument('-q', '--term', dest='term', default=DEFAULT_TERM,
                    type=str, help='Search term (default: %(default)s)')
    parser.add_argument('-l', '--location', dest='location',
                    default=DEFAULT_LOCATION, type=str,
                    help='Search location (default: %(default)s)')

    input_values = parser.parse_args()
    
    try:
        query_result = query_api(input_values.term, input_values.location)
    except HTTPError as error:
        sys.exit(
        'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
            error.code,
            error.url,
            error.read(),
            )
        )
    return query_result
    
def lambda_handler(event, context):
    message = poll()
    dining_info_dict = {}
    # get dining info
    if 'Messages' in message:
        dining_info_dict = processMessage(message)
        email_address = dining_info_dict['phone_number']
        query_result = yelp_api(message, dining_info_dict)
        send_email(query_result, email_address, dining_info_dict);
        return 'success'
    else:
        logger.error("there is no message in the queue")
        
        
   # return 'Hello from Lambda'
