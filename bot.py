from telegram.ext import Updater, MessageHandler, Filters
from utils import search_download_youtube_video
from loguru import logger
import os #- only when running localy

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

    def send_text(self, update,  text, quote=False):
        """Sends text to a chat"""
        # retry https://github.com/python-telegram-bot/python-telegram-bot/issues/1124
        update.message.reply_text(text, quote=quote)


class QuoteBot(Bot):
    def _message_handler(self, update, context):
        to_quote = True

        if update.message.text == 'Don\'t quote me please':
            to_quote = False

        self.send_text(update, f'Quote message  : {update.message.text}', quote=to_quote)


class YoutubeBot(Bot):
    def _message_handler(self, update, context):
        videoname = update.message.text
        self.send_text(update, 'Downloading video...')
        v_name = search_download_youtube_video(video_name=videoname, num_results=1)
        v_name = ''.join(v_name)
        #wrkdir = os.getcwd() + '\\' + v_name   #use only when running local and use Import OS
        self.send_text(update, f'The video clip {v_name} was downloaded and soon will be playing')
        self.send_video(update, context, v_name) #Use wrkdir when working locally and v_name when online


if __name__ == '__main__':
    with open('.telegramToken') as f:
        _token = f.read()

    my_bot = YoutubeBot(_token)
    my_bot.start()

