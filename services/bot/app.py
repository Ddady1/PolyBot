import json
import time
import botocore
from telegram.ext import Updater, MessageHandler, Filters
from loguru import logger
import boto3
from botocore.exceptions import ClientError
import re
import pandas as pd
import datetime
from pytz import timezone
import urllib.request




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


    def file_exist(self, update, filename):
        bucket_name = config.get('videos_bucket')
        chat_id = str(update.effective_message.chat_id)
        #s3 = boto3.resource('s3')
        client = boto3.client('s3')
        check = 1
        false_message = f'Check No: {check:n}. The video {filename} doesn\'t exist on S3. Will check again in 5 sec'
        ok_message = f'The video {filename} was uploaded successfully to S3'
        results = client.list_objects(Bucket=bucket_name, Prefix=chat_id)
        ans = 'Contents' in results
        while ans != True and check <= 5:
        #if not ans:
            self.send_text(update, false_message)
            check += 1
            time.sleep(1)
            results = client.list_objects(Bucket=bucket_name, Prefix=filename)
            ans = 'Contents' in results
        if ans:
            self.send_text(update, ok_message)



    def s3_list(self, update, bucket):
        # Gets bucket name and print list of objects from the user's folder
        chat_id = str(update.effective_message.chat_id)
        client = boto3.client('s3')
        my_bucket = client.list_objects_v2(Bucket=bucket, Prefix=chat_id)
        for myobj in (my_bucket['Contents']):
            self.send_text(update, myobj['Key'])


    def s3_del_list(self, update, bucket, lprint, dflag=0):
        # Multi function. Gets bucket name and 2 flags.
        # If the flag 'lprint' receive TRUE will print list of objects from the user's folder with dedicated numbers.
        # If the flag 'dflag' receive any number above 0 will send data function that delete objects.
        chat_id = str(update.effective_message.chat_id)
        client = boto3.client('s3')
        my_bucket = client.list_objects_v2(Bucket=bucket, Prefix=chat_id)
        dict_list = {}
        count = 1
        for myobj in (my_bucket['Contents']):
            dict_list[count] = myobj['Key']
            d = self.strip_parenthesis(dict_list[count].lstrip(f'{chat_id}/')) # Using function to strip name from parenthesis
            count += 1
            if lprint:
                self.send_text(update, f'{count - 1}: {d}')
        if dflag > 0:
            self.s3_del_obj(update, chat_id, bucket, dict_list[dflag]) # Sending data to object deletion function



    def s3_del_obj(self, update, chat_id, bucket, key):
        # Getting data of number of the object from the list and erase object from bucket
        client = boto3.client('s3')
        client.delete_object(Bucket=bucket, Key=key)
        strip_key = key.lstrip(f'{chat_id}/')
        self.send_text(update, f'The object {strip_key} was deleted successfully')


    def s3_empty_bucket(self, update, bucket):
        # Deletes all objects from user's folder
        chat_id = str(update.effective_message.chat_id)
        client = boto3.client('s3')
        my_bucket = client.list_objects_v2(Bucket=bucket, Prefix=chat_id)
        for myobj in (my_bucket['Contents']):
            client.delete_object(Bucket=bucket, Key=myobj['Key'])
            strip_key = myobj['Key'].lstrip(f'{chat_id}/')
            self.send_text(update, f'The object {strip_key} was deleted successfully')
        self.send_text(update, "All objects were deleted from the bucket!!!")


    def s3_chat_folder(self, bucket, chat_id):
        # Checks if users folder exists
        client = boto3.client('s3')
        result = client.list_objects_v2(Bucket=bucket, Prefix=chat_id)
        if 'Contents' in result:
            return True
        else:
            return False


    def strip_parenthesis(self, phrase):
        # Cleans object name from un-necessary parenthesis
        cleaned = ''
        for char in phrase:
            if char == ('(') or char == ('['):
                break
            else:
                cleaned += char
        return cleaned.rstrip(' ')


    def get_latest(self, update, bucket):
        # Gets the object's name in the bucket that was uploaded the latest

        chat_id = str(update.effective_message.chat_id)
        client = boto3.client('s3')
        my_bucket = client.list_objects_v2(Bucket=bucket, Prefix=chat_id)
        dict_list = {}
        naive = datetime.datetime(1000, 1, 1, 00)
        last = timezone('UTC').localize(naive)
        for myobj in (my_bucket['Contents']):
            dict_list[myobj['Key']] = myobj['LastModified']

        for key, value in dict_list.items():
            if last < value:
                last = value
                ckey = key
        return ckey


    def make_link(self, fcode):
        # Creating the YOUTUBE link of the uploaded objects
        youtube_link = f'https://www.youtube.com/watch?v={fcode}'
        return youtube_link


    def delete_flag(self, bucket, filename):
        client = boto3.client('s3')
        client.delete_object(Bucket=bucket, Key=filename)
        logger.info('The flag file was deleted.successfully!')
        #strip_key = key.lstrip(f'{chat_id}/')
        #self.send_text(update, f'The object {strip_key} was deleted successfully')



    def menu(self, update, phrase):
        # Menus function for interaction with the users
        if re.search('/smenu', phrase, re.IGNORECASE) or phrase == '/???':
            self.send_text(update, 'Welcome to Telgram bot MENU! \nType /sList - To list bucket objects. \nType /sDel - To delete an object. \nType /sEmpty - To empty the bucket'\
                                   '\nType /sGit - To update swear file\nType /sLink!<song number>- To get some song inf.')
        elif re.search('/slist', phrase, re.IGNORECASE):
            chat_folder_exist = self.s3_chat_folder(config.get('videos_bucket'), str(update.effective_message.chat_id))
            if chat_folder_exist:
                self.send_text(update, 'Preparing S3 Objects list...')
                time.sleep(3)
                #self.s3_list(update, config.get('videos_bucket'))
                self.s3_del_list(update, config.get('videos_bucket'), lprint=True)
                self.send_text(update, '------------------------------------\n----- End of object list -----\n------------------------------------')
                self.send_text(update, '--------------------------------------------------------------------------------------------\n'\
                                       '----                   If you would like to delete an object                    ----\n'\
                                       '----                   please type </sDel!<object number>>                   ----'\
                                       '\n----                         without the brackets. No case sensetivity.                         ----\n'\
                                       '-- Example: Type   /sDel!3   in order to delete object number 3 --\n'\
                                       '--------------------------------------------------------------------------------------------')
            else:
                self.send_text(update, 'You haven\'t populated the bucket yet. No objects to display')
        elif re.search('\A/sdel!', phrase, re.IGNORECASE):
            phrase = phrase.lower()
            snumber = phrase.lstrip('/sdel!')
            self.s3_del_list(update, config.get('videos_bucket'), lprint=False, dflag=int(snumber))
        elif re.search('/sempty', phrase, re.IGNORECASE):
            self.send_text(update, '=========================================================\n'\
                                   '===                                     WARNING                       \n'\
                                   '=== This operation will DELETE completely all objects in the bucket!!!\n'\
                                   '===           Please type DELETE PERMANENTLY for confirmation         \n'\
                                   '=========================================================')
        elif re.search('/sgit', phrase, re.IGNORECASE):
            self.send_text(update, 'Updating git file')
            self.git_import()
        elif re.search('\A/slink', phrase, re.IGNORECASE):
            self.get_latest(update, config.get('videos_bucket'))
            self.send_text(update, 'https://www.songfacts.com/facts/the-jacksons/blame-it-on-the-boogie')
            self.send_text(update, 'https://www.youtube.com/watch?v=g_jUtiKSf1Y')
        elif phrase == 'DELETE PERMANENTLY':
            self.s3_empty_bucket(update, config.get('videos_bucket'))
        #elif phrase == 'exist_file':
            #result = self.s3_chat_folder(config.get('videos_bucket'), phrase)
            #print(result)
            #self.delete_flag(config.get('videos_bucket'), phrase)
        else:
            return False
            #self.send_text(update, 'You havn\'t choose any option')

        return True


    def is_swear(self, swear_word):
        # Checking if a user is swearing in the bot
        with open('services/bot/swear.txt', encoding="utf-8") as sw:
            swear_list = sw.read()
            swear_list = swear_list.split('\n')
        result = swear_list.count(swear_word)
        if result > 0:
            return True
        return False


    def git_import(self):
        # Manually updating the swearing file from github
        url = 'https://raw.githubusercontent.com/coffee-and-fun/google-profanity-words/main/data/list.txt'
        gittest = pd.read_table(url)
        slist = gittest.values.tolist()
        with open('services/bot/swear.txt', 'w', encoding="utf-8") as g_file:
            for item in slist:
                item = ''.join(item)
                g_file.write(item)
                g_file.write('\n')


    def strip_youtube_code(self, filename, chat_id):
        # Strips out the youtube part of the link that represent the object on youtube
        stripped = filename.lstrip(f'{chat_id}/')
        stripped = stripped.rsplit(']', 1)[0]
        stripped = stripped.split('[', 1)[1]
        return stripped


    def info_link(self, filename):
        # Creating the object info link
        splitted = filename.split(' - ')
        full = []
        for item in splitted:
            part = item.replace(' ', '-')
            full.append(part + '/')
        full = ''.join(full)
        songfact = f'https://www.songfacts.com/facts/{full}'
        return songfact




class QuoteBot(Bot):
    def _message_handler(self, update, context):
        '''to_quote = True

        if update.message.text == 'Don\'t quote me please':
            to_quote = False

        self.send_text(update, f'Your original message: {update.message.text}', quote=to_quote)'''



class YoutubeObjectDetectBot(Bot):
    def __init__(self, token):
        super().__init__(token)


    def _message_handler(self, update, context):

        global bucketname
        # Checks if the chat_id folder exists
        chat_folder_exist = self.s3_chat_folder(config.get('videos_bucket'), str(update.effective_message.chat_id))
        if chat_folder_exist:
        #Populating the dictionary list with bucket objects.
            self.s3_del_list(update, config.get('videos_bucket'), lprint=False)

        v_name = update.message.text
        '''#Check if the input is a command or not.
        if not v_name.startswith('/'):
            return'''

        isSwear = self.is_swear(v_name)
        if isSwear:
            self.send_text(update, 'According to the BOT policy, swearing is NOT allowed,\nSO DONT SWEAR U MFUCKER \U0001F595')
            return

        menu_results = self.menu(update, v_name)
        if menu_results:
            return

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
            time.sleep(5)
            result = self.s3_chat_folder(config.get('videos_bucket'), 'exist_file')
            while not result:
                self.send_text(update, 'Upload still in process...')
                time.sleep(10)
                result = self.s3_chat_folder(config.get('videos_bucket'), 'exist_file')
            self.delete_flag(config.get('videos_bucket'), 'exist_file')
            actual_name = self.get_latest(update, config.get('videos_bucket')).lstrip(f'{chat_id}/')
            self.send_text(update, f'The object by the name: {actual_name} was uploaded successfully to S3')
            video_link = self.make_link(self.strip_youtube_code(actual_name, chat_id))
            self.send_text(update, video_link)
            info_link = self.info_link(self.strip_parenthesis(actual_name))
            self.send_text(update, info_link)



        except botocore.exceptions.ClientError as error:
            logger.error(error)
            self.send_text(update, f'Something went wrong, please try again...')




if __name__ == '__main__':
    with open('secrets/.telegramToken') as f:
        _token = f.read()

    with open('common/config.json') as f:
        config = json.load(f)

    bucketname = config.get('videos_bucket')



    sqs = boto3.resource('sqs', region_name=config.get('aws_region'))
    workers_queue = sqs.get_queue_by_name(QueueName=config.get('bot_to_worker_queue_name'))

    my_bot = YoutubeObjectDetectBot(_token)
    my_bot.git_import() # Importing the swearing file from github on first interaction on the bot
    my_bot.start()




