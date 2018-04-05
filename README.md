# 2018cloudcomputing_assignment1
2018.3.27
v 1.1
build basic instructure of chatbot

2018.4.5  
v1.2  
combine the chatbot with lex, making it more intelligent  
DiningConcierge:  
This lambda function handle the intent and get the dining information from user. Then it pushes information to SQS.  

dining_queue_worker:  
This lambda function pulls a message from SQS queue. Then it gets the information to search restaurant by using yelp api. At last, By using ses, a suggestion email will be sent the user.  

chatbot  
This lambda function bascially text message to the Lex chatbot and forward response to the user.  


