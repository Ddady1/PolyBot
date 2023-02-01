import json
import time
import botocore
from telegram.ext import Updater, MessageHandler, Filters
from loguru import logger
import boto3
from botocore.exceptions import ClientError
import re
import pandas as pd




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

        '''
        #print(chat_id, filename)
        #self.send_text(update, f'file {filename} uploaded', chat_id=chat_id)'''

    def s3_list(self, update, bucket):#added 160123:23:25
        #bucket_name = bucket
        chat_id = str(update.effective_message.chat_id)
        client = boto3.client('s3')
        my_bucket = client.list_objects_v2(Bucket=bucket, Prefix=chat_id)
        for myobj in (my_bucket['Contents']):
            self.send_text(update, myobj['Key'])
            #print(myobj['Last modified']) # for testing

    def s3_del_list(self, update, bucket, lprint, dflag=0):
        chat_id = str(update.effective_message.chat_id)
        client = boto3.client('s3')
        my_bucket = client.list_objects_v2(Bucket=bucket, Prefix=chat_id)
        dict_list = {}
        count = 1
        for myobj in (my_bucket['Contents']):
            dict_list[count] = myobj['Key']
            d = dict_list[count]
            count += 1
            if lprint:
                self.send_text(update, f'{count - 1} - {d}')
        if dflag > 0:
            self.s3_del_obj(update, chat_id, bucket, dict_list[dflag])


    def s3_del_obj(self, update, chat_id, bucket, key):
        client = boto3.client('s3')
        client.delete_object(Bucket=bucket, Key=key)
        strip_key = key.lstrip(f'{chat_id}/')
        self.send_text(update, f'The object {strip_key} was deleted successfully')
        #print('Object was deleted successfully')

    def s3_empty_bucket(self, update, bucket):
        chat_id = str(update.effective_message.chat_id)
        client = boto3.client('s3')
        my_bucket = client.list_objects_v2(Bucket=bucket, Prefix=chat_id)
        for myobj in (my_bucket['Contents']):
            client.delete_object(Bucket=bucket, Key=myobj['Key'])
            strip_key = myobj['Key'].lstrip(f'{chat_id}/')
            self.send_text(update, f'The object {strip_key} was deleted successfully')
        self.send_text(update, "All objects were deleted from the bucket!!!")

    def s3_chat_folder(self, bucket, chat_id):
        client = boto3.client('s3')
        result = client.list_objects_v2(Bucket=bucket, Prefix=chat_id)
        if 'Contents' in result:
            return True
        else:
            return False





        #print(dict_list) ## For checking only


        ### Need to complete the delete object. Creating a Dictionary is done! Now need to tprint user with list of objects
        ### with numerator and delete object according numerator


    def menu(self, update, phrase):
        #if phrase == "sMenu" or phrase == "???":
        if re.search('smenu', phrase, re.IGNORECASE) or phrase == '???':
            self.send_text(update, 'Welcome to Telgram bot MENU! \nType sList - To list bucket objects. \nType sDel - To delete an object. \nType sEmpty - To empty the bucket'\
                                   '\nType gGit - To update swear file')
        elif re.search('slist', phrase, re.IGNORECASE):
            chat_folder_exist = self.s3_chat_folder(config.get('videos_bucket'), str(update.effective_message.chat_id))
            if chat_folder_exist:
                self.send_text(update, 'Preparing S3 Objects list...')
                time.sleep(3)
                #self.s3_list(update, config.get('videos_bucket'))
                self.s3_del_list(update, config.get('videos_bucket'), lprint=True)
                self.send_text(update, '------------------------------------\n----- End of object list -----\n------------------------------------')
                self.send_text(update, '--------------------------------------------------------------------------------------------\n'\
                                       '----                   If you would like to delete an object                    ----\n'\
                                       '----                   please type <sdel!<object number>>                   ----'\
                                       '\n----                         without the brackets. No case sensetivity.                         ----\n'\
                                       '-- Example: Type   sdel!3   in order to delete object number 3 --\n'\
                                       '--------------------------------------------------------------------------------------------')
            else:
                self.send_text(update, 'You haven\'t populated the bucket yet. No objects to display')
        elif re.search('\Asdel!', phrase, re.IGNORECASE):
            phrase = phrase.lower()
            snumber = phrase.lstrip('sdel!')
            #self.send_text(update, 'Deleting an object')
            #self.send_text(update, snumber)
            self.s3_del_list(update, config.get('videos_bucket'), lprint=False, dflag=int(snumber))
        elif re.search('sempty', phrase, re.IGNORECASE):
            self.send_text(update, '=========================================================\n'\
                                   '===                                     WARNING                       \n'\
                                   '=== This operation will DELETE completely all objects in the bucket!!!\n'\
                                   '===           Please type DELETE PERMANENTLY for confirmation         \n'\
                                   '=========================================================')
        elif re.search('igit', phrase, re.IGNORECASE):
            self.send_text(update, 'Updating git file')
            self.git_import()
        elif phrase == 'DELETE PERMANENTLY':
            self.s3_empty_bucket(update, config.get('videos_bucket'))
        else:
            return False
            #self.send_text(update, 'You havn\'t choose any option')

        return True

    def is_swear(self, swear_word):
        with open('services/bot/swear.txt', encoding="utf-8") as sw:
            swear_list = sw.read()
            swear_list = swear_list.split('\n')
        result = swear_list.count(swear_word)
        if result > 0:
            return True
        return False

    def git_import(self):
        url = 'https://raw.githubusercontent.com/coffee-and-fun/google-profanity-words/main/data/list.txt'
        gittest = pd.read_table(url)
        slist = gittest.values.tolist()
        with open('services/bot/swear.txt', 'w', encoding="utf-8") as g_file:
            for item in slist:
                item = ''.join(item)
                g_file.write(item)
                g_file.write('\n')




class QuoteBot(Bot):
    def _message_handler(self, update, context):
        '''to_quote = True

        if update.message.text == 'Don\'t quote me please':
            to_quote = False

        self.send_text(update, f'Your original message: {update.message.text}', quote=to_quote)'''
        #menu_text = update.message.text
        #self.menu(update, menu_text)




class YoutubeObjectDetectBot(Bot):
    def __init__(self, token):
        super().__init__(token)


    def _message_handler(self, update, context):

        chat_folder_exist = self.s3_chat_folder(config.get('videos_bucket'), str(update.effective_message.chat_id))
        if chat_folder_exist:
            self.s3_del_list(update, config.get('videos_bucket'), lprint=False)

        v_name = update.message.text
        '''if v_name == 'l_s3':#added 160123:23:25
            self.s3_list()#added 160123:23:25'''
        isSwear = self.is_swear(v_name)
        if isSwear:
            self.send_text(update, 'According to the BOT policy, swearing is NOT allowed,\nSO DONT SWEAR U MFUCKER \U0001F595')
            return

        menu_results = self.menu(update, v_name)
        if menu_results:
            return
        #self.menu(update, v_name) # for testing purposes if the menu function
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

                self.file_exist(update, v_name) #test
                #self.send_video(update, context)#added 160123:22:03
                #self.s3_list(update, config.get('videos_bucket'))


        except botocore.exceptions.ClientError as error:
            logger.error(error)
            self.send_text(update, f'Something went wrong, please try again...')








if __name__ == '__main__':
    with open('secrets/.telegramToken') as f:
        _token = f.read()

    with open('common/config.json') as f:
        config = json.load(f)

    '''with open('services/bot/swear.txt', encoding="utf-8") as sw:
        swear_list = sw.read()
        swear_list = swear_list.split('\n')'''




    #with open('common/s3_file.txt', "a") as fileS3: #The bot print it, bot doesn't write to the file and worker doesn't work
        #fileS3.write('main of bot\n')

    sqs = boto3.resource('sqs', region_name=config.get('aws_region'))
    workers_queue = sqs.get_queue_by_name(QueueName=config.get('bot_to_worker_queue_name'))

    my_bot = YoutubeObjectDetectBot(_token)
    my_bot.git_import()
    my_bot.start()




