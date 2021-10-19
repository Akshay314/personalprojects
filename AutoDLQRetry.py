import json
import boto3

def lambda_handler(event, context):
   
    # Create SQS client
    sqs = boto3.client('sqs')
    print("Starting the event migration workfllow.");
    
    max_retry_counter = 3
    maxRetriedEvents = [] # This list will store the events that have already reached their max retry count
    
    source_queue_url = event['source_queue_url']
    destination_queue_url = event['destination_queue_url']
    
    if('batch_size' in event):
        batch_size = event['batch_size']
    else:
        # set the default batch size as 10
        batch_size = 10
    

    while batch_size :
        batch_size-=1
        # Receive message from SQS queue
        response = sqs.receive_message(
            QueueUrl=source_queue_url,
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
            
        )
        
        if('Messages' not in response):
            print("No more events found in queue - " + source_queue_url)
            break
        
        message = response['Messages'][0]
        
        # if message Attributes doesnt exist, create a new one
        if('MessageAttributes' not in message):
            messageAttributes = {"RetryCounter":{"StringValue":"0","DataType":"Number"}}
        else:
            messageAttributes = message['MessageAttributes']
            
        # if RetryCounter is not present in existing attributes, initialise it.
        if('RetryCounter' not in messageAttributes):
            messageAttributes["RetryCounter"] = {"StringValue":"0","DataType":"Number"};
        
        # Ensure that we do not retry infinitely.
        if(int(messageAttributes["RetryCounter"]["StringValue"]) >= max_retry_counter):
            print("message id % rreached max retry count" % message['MessageId'])
            
            # to keep this msg unavailable for sometime to not get read again, delete and publish back into the same queue.
            delete_sqs_message(sqs, message, source_queue_url)
            maxRetriedEvents.append(message)
            continue
        
        # increment the retry counter.
        messageAttributes["RetryCounter"]["StringValue"] = str(int(messageAttributes["RetryCounter"]["StringValue"]) + 1)
        
        send_sqs_message(sqs, destination_queue_url,messageAttributes, message)
        delete_sqs_message(sqs, message, source_queue_url)
        
    # publish the max retried events again into source queue
    print("Reinstalling retry exhausted events into source queue")
    for message in maxRetriedEvents:
        send_sqs_message(sqs, source_queue_url,message['MessageAttributes'], message)
        
        
def send_sqs_message(sqs, destination_queue, messageAttributes, message):
    sent_message = sqs.send_message(
        QueueUrl=destination_queue,
        MessageAttributes= messageAttributes,
        MessageBody=message['Body']
    )
    print('Message with id %s sent succesfully to queue %s' % (sent_message['MessageId'],destination_queue) )
        
    
def delete_sqs_message(sqs, message, queue):
    # deleting from source DLQ
    receipt_handle = message['ReceiptHandle']
    
    # Delete received message from queue
    sqs.delete_message(
        QueueUrl=queue,
        ReceiptHandle=receipt_handle
    )
    print('Received & deleted message: %s from queue %s' % (message, queue))
        
       
    
