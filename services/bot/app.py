import json
import time
import botocore
from telegram.ext import Updater, MessageHandler, Filters
from loguru import logger
import boto3
from botocore.exceptions import ClientError




class Bot:

    def __init__(self, token):
        # create frontend object to the bot programmer
        self.updater = Updater(token, use_context=True)

        # add _message_handler as main internal msg handler
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self._message_handler))

    def start(self):
        """Start polling msgs from users, this function never returns"""
        self.updater.start_polling()
        logger.info(f'{self.__class__.__name__} is up and listening to new messages....')
        self.updater.idle()

    def _message_handler(self, update, context):
        """Main messages handler"""
        self.send_text(update, f'Your original message: {update.message.text}')

    def send_video(self, update, context, file_path):
        """Sends video to a chat"""
        context.bot.send_video(chat_id=update.message.chat_id, video=open(file_path, 'rb'), supports_streaming=True)

    def send_text(self, update, text, chat_id=None, quote=False):
        """Sends text to a chat"""
        if chat_id:
            self.updater.bot.send_message(chat_id, text=text)
        else:
            # retry https://github.com/python-telegram-bot/python-telegram-bot/issues/1124
            update.message.reply_text(text, quote=quote)

    #test from here until line 56 includee
    #def file_exist(self, update, chat_id, filename):
    def file_exist(self, update, filename):
        bucket_name = config.get('videos_bucket')
        #s3 = boto3.resource('s3')
        client = boto3.client('s3')
        chk = 1
        false_message = f'Check No: {chk}. The video {filename} doesn\'t exist on S3. Will check again in 5 sec'
        ok_message = f'The video {filename} was uploaded successfully to S3'
        results = client.list_objects(Bucket=bucket_name, Prefix=filename)
        ans = 'Contents' in results
        while ans != True and chk <=5:
        #if not ans:
            self.send_text(update, false_message)
            chk += 1
            time.sleep(10)
            results = client.list_objects(Bucket=bucket_name, Prefix=filename)
            ans = 'Contents' in results
        if ans:
            self.send_text(update, ok_message)

        '''
        #print(chat_id, filename)
        #self.send_text(update, f'file {filename} uploaded', chat_id=chat_id)'''

    '''def s3_list (self):#added 160123:23:25
        bucket_name = config.get('videos_bucket')
        client = boto3.resource('s3')
        my_bucket = client.list_objects(bucket_name)
        for myobj in my_bucket.objects.all():
            self.send_text(myobj)'''



class QuoteBot(Bot):
    def _message_handler(self, update, context):
        to_quote = True

        if update.message.text == 'Don\'t quote me please':
            to_quote = False

        self.send_text(update, f'Your original message: {update.message.text}', quote=to_quote)


class YoutubeObjectDetectBot(Bot):
    def __init__(self, token):
        super().__init__(token)

    def _message_handler(self, update, context):
        v_name = update.message.text
        '''if v_name == 'l_s3':#added 160123:23:25
            self.s3_list()#added 160123:23:25'''
        try:
            chat_id = str(update.effective_message.chat_id)
            response = workers_queue.send_message(
                MessageBody=update.message.text,
                MessageAttributes={
                    'chat_id': {'StringValue': chat_id, 'DataType': 'String'}
                }
            )
            logger.info(f'msg {response.get("MessageId")} has been sent to queue')
            self.send_text(update, f'Your message is being processed....', chat_id=chat_id)
            self.send_text(update, f'The file name is {v_name}') #test
            with open('common/s3_file.txt') as file:
                real_vname = file.readlines()[-1]
            #self.send_text(update, f'UPDATE = {update}, Video name = {v_name}, CHAT = {chat_id}')
            time.sleep(5)
            #self.send_text(update, self.file_exist(update, v_name))

            self.file_exist(update, real_vname) #test
            self.send_video(update, context,)#added 160123:22:03


        except botocore.exceptions.ClientError as error:
            logger.error(error)
            self.send_text(update, f'Something went wrong, please try again...')








if __name__ == '__main__':
    with open('secrets/.telegramToken') as f:
        _token = f.read()

    with open('common/config.json') as f:
        config = json.load(f)

    #with open('common/s3_file.txt', "a") as fileS3: #The bot print it, bot doesn't write to the file and worker doesn't work
        #fileS3.write('main of bot\n')



    sqs = boto3.resource('sqs', region_name=config.get('aws_region'))
    workers_queue = sqs.get_queue_by_name(QueueName=config.get('bot_to_worker_queue_name'))

    my_bot = YoutubeObjectDetectBot(_token)
    my_bot.start()
