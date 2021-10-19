# personalprojects

This repository contains one simple AWS Lambda function in Python to redrive AWS SQS events from source queue to destination queue. This script can be triggered periodically via cloudwatch as well if source queue contains too many events and you dont want to redrive them  altogether.
* batch_size can be passed as input which will move only X events in one execution cycle. Default batch size is 10 if no value is passed.
* This script ensures that if same event is getting moved into DLQ again and again, it wont get retried more than 3 times.

**Disclaimer**: This script adds one additional field *'RetryCounter'* to keep track of number of retries in SQS's MessageAttributes. In 99.9% of cases, ideally this should cause any break in consumer code, because this is just an additional field added in attributes (NOT in body), but confirm the impact once before usage.
None of the existing data is touched upon.

## Sample Input
```
{
  "source_input_url" : "AWS source sqs queue URL",
  "destination_input_url" : "AWS destination sqs queue URL",
  "batch_size": 10
}
# Note: Only **batch_size** is optional here. queue URLs are mandatory fields.
```
