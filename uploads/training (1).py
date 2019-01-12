import boto3
import botocore

sqs = boto3.resource('sqs')

bucket_name = 'nurbolbucket'

queueIn = sqs.get_queue_by_name(QueueName='inbox')
queueOut = sqs.get_queue_by_name(QueueName='outbox')

while True:

    filename = input('Enter your image name: ')
    s3 = boto3.client('s3')
    s3.upload_file(filename, bucket_name, filename)

    queueIn.send_message(MessageBody='Numbers', MessageAttributes={
        'Author': {
            'StringValue': filename,
            'DataType': 'String'
        }
    })

    author_text = ''

    while author_text == '':
        for message in queueOut.receive_messages(MessageAttributeNames=['Author']):
            author_text = ''
            if message.message_attributes is not None:
                author_name = message.message_attributes.get('Author').get('StringValue')
                if author_name:
                    author_text = '{0}'.format(author_name)

        if author_text == '':
            print('Waiting for response...')
        else:
            print('Image: {1} successfully processed!'.format(message.body, author_text))
            message.delete()
            filename = author_text
            try:
                s3 = boto3.resource('s3')
                s3.Bucket(bucket_name).download_file(filename, filename)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print("The object does not exist.")
                else:
                    raise