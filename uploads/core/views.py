from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from uploads.core.models import Document
from uploads.core.forms import DocumentForm

import boto3
import botocore

sqs = boto3.resource('sqs')

bucket_name = 'nurbolbucket'

queueIn = sqs.get_queue_by_name(QueueName='inbox')
queueOut = sqs.get_queue_by_name(QueueName='outbox')


def home(request):
    documents = Document.objects.all()
    return render(request, 'core/home.html', { 'documents': documents })


def simple_upload(request):
    if request.method == 'POST' and request.FILES['myfile']:
        filename = request.FILES['myfile'].name
        filedata = request.FILES['myfile']
        print(filename)

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
                    s3.Bucket(bucket_name).download_file(filename,  filename)
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == "404":
                        print("The object does not exist.")
                    else:
                        raise

        # fs = FileSystemStorage()
        # filename = fs.save(myfile.name, myfile)
        # uploaded_file_url = fs.url(filename)
        uploaded_file_url = filename
        return render(request, 'core/simple_upload.html', {
            'uploaded_file_url': uploaded_file_url
        })
    return render(request, 'core/simple_upload.html')  #


def model_form_upload(request):
    if request.method == 'POST':

        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = DocumentForm()
    return render(request, 'core/model_form_upload.html', {
        'form': form
    })