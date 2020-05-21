import io
import json
import logging
import logging.config
import configparser

from time import sleep
from gtts import gTTS
import os

import gettext
_ = gettext.gettext

from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler

import signal, time


logging.config.fileConfig("logging.ini")
log = logging.getLogger("Paquebot")

import paquebot_bot

import paquebot_commands as c

com_logger = logging.getLogger("paquebot_commands")

import paquebot_crew as crew

crew_logger = logging.getLogger("paquebot_crew")

import paquebot_db as db
import paquebot_party as party

	

###########################################
config = configparser.ConfigParser()
config.read('paquebot.ini')
NAME = config['default']['ICQBOT_NAME']
VERSION = config['default']['ICQBOT_VERSION']
TOKEN = config['default']['ICQBOT_TOKEN']
OWNER = config['default']['ICQBOT_OWNER']
API_URL = config['default']['ICQBOT_API_URL']

'''
NAME = os.getenv('ICQBOT_NAME', "BOT")
VERSION = os.getenv('ICQBOT_VERSION', "1.0.0")
TOKEN = os.getenv('ICQBOT_TOKEN', "XXX.XXXXXXXXXX.XXXXXXXXXX:XXXXXXXXX")
OWNER = os.getenv('ICQBOT_OWNER', "XXXXXXXXX")
API_URL = "https://api.icq.net/bot/v1"
'''

###########################################


# Creating a new backend-storage or accessing the existing one
loveboat_hold = db.Storage()

# Creating a new crew
loveboat_crew = crew.Crew(
	mainsession=loveboat_hold.paquebot_db, 
	owner = OWNER
)

# Creating a new bot instance.
loveboat = paquebot_bot.PaqueBot(token=TOKEN,
	crew=loveboat_crew,
	maindb=loveboat_hold,
	name=NAME,
	version=VERSION,
	owner=OWNER,
	api_url_base=API_URL,
	timeout_s=5,
	poll_time_s=5
)



# Intercepting stop signals
def sigterm_handler(_signo, _stack_frame):
	log.info('No Panic.. were are not the Titanic: %s'%(id))	
	print("No Panic.. were are not the Titanic")
	# Send alive message
	loveboat.send_text(chat_id=OWNER, text="[Dying] I have offended my Master and mankind because my work did not reach the quality it should have.")
	log.debug('Stopping bot')
	loveboat.running = False
	sleep(2)
	loveboat_hold.close()
	log.debug('Exiting')
	os._exit(0)


def main():


	log.debug('Launching %s with token %s owner %s'%(NAME, TOKEN, OWNER))
	print('Launching %s with token %s owner %s'%(NAME, TOKEN, OWNER))

	catchable_sigs = set(signal.Signals) - {signal.SIGKILL, signal.SIGSTOP}
	for sig in catchable_sigs:
		signal.signal(sig, sigterm_handler)  # Substitute handler of choice for `print`

	# Send alive message
	loveboat.send_text(chat_id=OWNER, text="[Alive] Hello my Master, i'm alive now")


	# Starting a polling thread watching for new events from server. This is a non-blocking call
	# ---------------------------------------------------------------------------------------- #
	loveboat.start_polling()

	# Call bot methods
	# -------------- #
	# Get info about bot
	# bot.self_get()

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

	'''
	try:


		loveboat.idle()
		while loveboat.running:
			log.debug(" polling inside the main procedure")
			sleep(1)
	finally:
		print('Goodbye')
	'''


if __name__ == "__main__":
	main()
