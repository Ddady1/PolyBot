import json
import time
import boto3
import botocore
from loguru import logger
from common.utils import search_download_youtube_video
import os



def process_msg(msg, chatID):
    downloaded_videos = search_download_youtube_video(msg)
    s3 = boto3.client('s3')
    for video in downloaded_videos:
        s3.upload_file(video, config.get('videos_bucket'), f'{chatID}/{video}')
        #s3.upload_file(f'./new/{video}', config.get('videos_bucket'), video)
        os.remove(f'./{video}')


'''def is_folder_exists(path):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(config.get('videos_bucket'))
    for folder_object in bucket.objects.filter(Prefix=path):
        return True
    return False


def create_folder(path)'''

def main():
    while True:
        try:
            messages = queue.receive_messages(
                MessageAttributeNames=['All'],
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )
            #print(queue.receive_messages(MessageAttributeNames=['All']))
            #print(messages)
            for msg in messages:
                logger.info(f'processing message {msg}')
                process_msg(msg.body, msg.message_attributes['chat_id']['StringValue'])

                # delete message from the queue after is was. handled
                response = queue.delete_messages(Entries=[{
                    'Id': msg.message_id,
                    'ReceiptHandle': msg.receipt_handle
                }])
                if 'Successful' in response:
                    logger.info(f'msg {msg} has been handled successfully')

        except botocore.exceptions.ClientError as err:
            logger.exception(f"Couldn't receive messages {err}")
            time.sleep(10)


if __name__ == '__main__':
    with open('common/config.json') as f:
        config = json.load(f)

    #with open('common/s3_file.txt', "a") as fileS3: #Not working here
        #fileS3.write('main of worker\n')

    sqs = boto3.resource('sqs', region_name=config.get('aws_region'))
    queue = sqs.get_queue_by_name(QueueName=config.get('bot_to_worker_queue_name'))

    main()
