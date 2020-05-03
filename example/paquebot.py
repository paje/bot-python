import io
import json
import logging
import logging.config

from time import sleep
from gtts import gTTS
import os

import gettext

from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler

from tinydb import TinyDB, Query
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage

import signal, time


logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)


import paquebot_commands as c
import paquebot_crew as crew
import paquebot_db as db
import paquebot_party as party

	

###########################################


NAME = os.getenv('ICQBOT_NAME', "BOT")
VERSION = os.getenv('ICQBOT_VERSION', "1.0.0")
TOKEN = os.getenv('ICQBOT_TOKEN', "XXX.XXXXXXXXXX.XXXXXXXXXX:XXXXXXXXX")
OWNER = os.getenv('ICQBOT_OWNER', "XXXXXXXXX")
TEST_CHAT = os.getenv('ICQBOT_TESTCHAT', "XXXXX")
TEST_USER = os.getenv('ICQBOT_TESTUSER', "XXXXX")
API_URL = "https://api.icq.net/bot/v1"


###########################################



# Creating a new bot instance.
bot = Bot(token=TOKEN, name=NAME, version=VERSION, api_url_base=API_URL)


def sigterm_handler(_signo, _stack_frame):
	log.info('No Panic.. were are not the Titanic: %s'%(id))	
	print("No Panic.. were are not the Titanic")
	log.debug('Stopping bot')
	bot.running = False
	sleep(2)
	db.close()
	log.debug('Exiting')
	os._exit(0)

'''
signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigterm_handler)
'''



def init():

	db.init()

	crew.init()




def add_handlers(bot):

	# Registering handlers #
	# -------------------- #
	# Handler for start command
	bot.dispatcher.add_handler(StartCommandHandler(callback=c.start_cb))

	# Handler for help command
	bot.dispatcher.add_handler(HelpCommandHandler(callback=c.help_cb))

	# Any other user command handler
	bot.dispatcher.add_handler(CommandHandler(command="test", callback=c.test_cb))

	# Handler for feedback command
	bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER))

	# Handler for unknown commands
	bot.dispatcher.add_handler(UnknownCommandHandler(callback=c.unknown_command_cb))

	# Handler for private command with filter by user
	bot.dispatcher.add_handler(CommandHandler(
		command="restart",
		filters=Filter.sender(user_id=OWNER),
		callback=c.private_command_cb
	))


	# Handler for add user to chat
	bot.dispatcher.add_handler(NewChatMembersHandler(callback=party.do_guestwelcome))

	# Handler for left user from chat
	bot.dispatcher.add_handler(LeftChatMembersHandler(callback=party.do_guestgoodbye))

	# Handler for pinned message
	bot.dispatcher.add_handler(PinnedMessageHandler(callback=c.pinned_message_cb))

	# Handler for unpinned message
	bot.dispatcher.add_handler(UnPinnedMessageHandler(callback=c.unpinned_message_cb))

	# Handler for edited message
	#bot.dispatcher.add_handler(EditedMessageHandler(callback=c.edited_message_cb))

	# Handler for deleted message
	bot.dispatcher.add_handler(DeletedMessageHandler(callback=c.deleted_message_cb))

	# Handler for message with bot mention
	bot.dispatcher.add_handler(MessageHandler(
		filters=Filter.message & Filter.mention(user_id=bot.uin),
		callback=c.message_with_bot_mention_cb
	))

	# Handler for mention something else
	bot.dispatcher.add_handler(MessageHandler(
		filters=Filter.mention() & ~Filter.mention(user_id=bot.uin),
		callback=c.mention_cb
	))

	# Handler for simple text message without media content
	bot.dispatcher.add_handler(MessageHandler(filters=Filter.text, callback=party.do_keepaneyeon))

	# Handler with regexp filter
	bot.dispatcher.add_handler(MessageHandler(filters=Filter.regexp("^\d*$"), callback=c.regexp_only_dig_cb))

	# Handler for no media file. For example, text file
	bot.dispatcher.add_handler(MessageHandler(filters=Filter.data, callback=c.file_cb))

	# Handlers for other file types
	bot.dispatcher.add_handler(MessageHandler(filters=Filter.image, callback=c.image_cb))
	bot.dispatcher.add_handler(MessageHandler(filters=Filter.video, callback=c.video_cb))
	bot.dispatcher.add_handler(MessageHandler(filters=Filter.audio, callback=c.audio_cb))

	# Handler for sticker
	bot.dispatcher.add_handler(MessageHandler(filters=Filter.sticker, callback=c.sticker_cb))

	# Handler for url
	bot.dispatcher.add_handler(MessageHandler(filters=Filter.url & ~Filter.sticker, callback=c.url_cb))

	# Handlers for forward and reply getting
	bot.dispatcher.add_handler(MessageHandler(filters=Filter.forward, callback=c.forward_cb))
	bot.dispatcher.add_handler(MessageHandler(filters=Filter.reply, callback=c.reply_cb))

	# Send command like this:
	# /pin 6752793278973351456
	# 6752793278973351456 - msgId
	# Handler for pin command
	# bot.dispatcher.add_handler(CommandHandler(command="pin", callback=c.pin_cb))

	# Send command like this:
	# /unpin 6752793278973351456
	# 6752793278973351456 - msgId
	# Handler for unpin command
	# bot.dispatcher.add_handler(CommandHandler(command="unpin", callback=c.unpin_cb))

	# Handler for bot buttons reply.
	bot.dispatcher.add_handler(BotButtonCommandHandler(callback=c.buttons_answer_cb))


	bot.dispatcher.add_handler(CommandHandler(command="joinparty", callback=c.join_party))
	bot.dispatcher.add_handler(CommandHandler(command="refreshparty", callback=c.refresh_party))

	bot.dispatcher.add_handler(CommandHandler(command="info", callback=c.info))	


def main():

	init()

	catchable_sigs = set(signal.Signals) - {signal.SIGKILL, signal.SIGSTOP}
	for sig in catchable_sigs:
		signal.signal(sig, sigterm_handler)  # Substitute handler of choice for `print`

	add_handlers(bot)

	# Starting a polling thread watching for new events from server. This is a non-blocking call
	# ---------------------------------------------------------------------------------------- #
	bot.start_polling()

	# Call bot methods
	# -------------- #
	# Get info about bot
	bot.self_get()

	'''
	# Send message
	response = bot.send_text(chat_id=OWNER, text="Hello")
	msg_id = response.json()['msgId']

	# Reply
	bot.send_text(chat_id=OWNER, text="Reply to 'Hello'", reply_msg_id=msg_id)

	# Forward
	bot.send_text(chat_id=OWNER, text="Forward 'Hello'", forward_msg_id=msg_id, forward_chat_id=OWNER)

	# Send binary file
	with io.StringIO() as file:
		file.write('x'*100)
		file.name = "file.txt"
		file.seek(0)
		response = bot.send_file(chat_id=OWNER, file=file.read(), caption="binary file caption")
		file_id = response.json()['fileId']

	# Get file info
	''
	bot.get_file_info(file_id=file_id)

	# Send file by file_id
	bot.send_file(chat_id=OWNER, file_id=file_id, caption="file_id file caption")

	# Send file by file_id as reply to message
	bot.send_file(chat_id=OWNER, file_id=file_id, caption="file_id file caption", reply_msg_id=msg_id)

	# Forward file by file_id
	bot.send_file(
		chat_id=OWNER,
		file_id=file_id,
		caption="file_id file caption",
		forward_msg_id=msg_id,
		forward_chat_id=OWNER
	)

	# Send voice file
	with io.BytesIO() as file:
		gTTS('Hello everybody!').write_to_fp(file)
		file.name = "hello_voice.mp3"
		file.seek(0)
		response = bot.send_voice(chat_id=OWNER, file=file.read())
		hello_voice_file_id = response.json()['fileId']

	# Send voice by file_id
	bot.send_voice(chat_id=OWNER, file_id=hello_voice_file_id)

	# Edit text
	msg_id = bot.send_text(chat_id=OWNER, text="Message to be edited").json()['msgId']
	bot.edit_text(chat_id=OWNER, msg_id=msg_id, text="edited text")

	# Delete message
	msg_id = bot.send_text(chat_id=OWNER, text="Message to be deleted").json()['msgId']
	bot.delete_messages(chat_id=OWNER, msg_id=msg_id)

	# Send typing action
	bot.send_actions(chat_id=OWNER, actions=["typing"])
	sleep(1)
	# Stop typing
	bot.send_actions(chat_id=OWNER, actions=[])

	'''
	# Get info about chat
	#bot.get_chat_info(chat_id="Test_Paquebot")	
	'''

	# Get chat admins
	bot.get_chat_admins(chat_id=TEST_CHAT)
	# Get chat members
	bot.get_chat_members(chat_id=TEST_CHAT)
	# Get chat blocked users
	bot.get_chat_blocked_users(chat_id=TEST_CHAT)
	# Get chat pending users
	bot.get_chat_pending_users(chat_id=TEST_CHAT)

	# Block user in chat
	bot.chat_block_user(chat_id=TEST_CHAT, user_id=TEST_USER, del_last_messages=True)
	# Unlock user in chat
	bot.chat_unblock_user(chat_id=TEST_CHAT, user_id=TEST_USER)

	# Chat resolve pending user or everyone
	bot.chat_resolve_pending(chat_id=TEST_CHAT, approve=True, user_id=TEST_USER, everyone=False)

	# Set chat title
	bot.set_chat_title(chat_id=TEST_CHAT, title="TEST TITLE")
	# Set chat about
	bot.set_chat_about(chat_id=TEST_CHAT, about="TEST ABOUT")
	# Set chat title
	bot.set_chat_rules(chat_id=TEST_CHAT, rules="TEST RULES")

	# Send bot buttons
	bot.send_text(chat_id=OWNER,
				  text="Hello with buttons.",
				  inline_keyboard_markup="[{}]".format(json.dumps([
					  {"text": "Action 1", "url": "http://mail.ru"},
					  {"text": "Action 2", "callbackData": "call_back_id_2"},
					  {"text": "Action 3", "callbackData": "call_back_id_3"}
				  ])))

	'''
	try:

#		bot.idle()
		while bot.running:
			sleep(1)
	finally:
		print('Goodbye')


if __name__ == "__main__":
	main()
