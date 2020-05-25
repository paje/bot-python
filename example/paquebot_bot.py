import json, re
import threading


from bot.bot import Bot, LoggingHTTPAdapter, BotLoggingHTTPAdapter, FileNotFoundException, SkipDuplicateMessageHandler
from bot.filter import Filter
from bot.handler import UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler
from bot.util import signal_name_by_code
from bot.event import Event, EventType
from bot.dispatcher import Dispatcher, StopDispatching


from threading import Thread, Lock
from expiringdict import ExpiringDict

import logging
import logging.config

import paquebot_db
import paquebot_commands as command
import paquebot_party as party
import paquebot_marinegunner as gunner

from paquebot_crew import CrewGrades as grades
from paquebot_whoiswhere import Whoiswhere as wiw
from paquebot_party import Parties as parties
import paquebot_report as report


log = logging.getLogger(__name__)


# log = logging.getLogger(__name__)


# Manage interactions with ICQ
class PaqueBot(Bot):


	def __init__(self, token, crew, maindb, api_url_base=None, name=None, version=None, owner=None, timeout_s=20, poll_time_s=60):

		super(Bot, self).__init__()

		self.log = logging.getLogger(__name__)

		self.token = token
		self.api_base_url = "https://api.icq.net/bot/v1" if api_url_base is None else api_url_base
		self.name = name
		self.version = version
		self.owner = owner
		self.timeout_s = timeout_s
		self.poll_time_s = poll_time_s
		self.last_event_id = 0

		self.dispatcher = Dispatcher(self)
		self.running = False

		self._uin = token.split(":")[-1]

		self.__lock = Lock()
		self.__polling_thread = None

		self.__sent_im_cache = ExpiringDict(max_len=2 ** 10, max_age_seconds=60)
		self.dispatcher.add_handler(SkipDuplicateMessageHandler(self.__sent_im_cache))

		self.crew = crew
		self.maindb = maindb
		

		self.parties = parties(self, maindb.paquebot_db)


		resp = self.self_get()
		if resp.status_code == 200:
			myselfinfo = json.loads(resp.text)
			if 'nick' in myselfinfo:
				self.nick = myselfinfo['nick']
			else:
				self.nick = "unknown"
		else:
			self.log.error('Unable to retrive my own infos')

			sys.exit(1)
		self.log.debug('Bot is alive, my ID is %s and my nickname is %s'%(self.uin, self.nick))


		'''
		  Buttons
		'''

		# Handler for bot buttons reply.
		self.dispatcher.add_handler(BotButtonCommandHandler(callback=command.answer_buttons))




		'''
		  Commands
		'''

		self.dispatcher.add_handler(StartCommandHandler(callback=command.start))

		# Handler for help command
		#self.dispatcher.add_handler(HelpCommandHandler(callback=command.help))
		self.dispatcher.add_handler(CommandHandler(command="help", callback=command.help))




		# Start obersing a channel
		self.dispatcher.add_handler(CommandHandler(command="joinparty", callback=command.join_party))

		# List managed channels
		self.dispatcher.add_handler(CommandHandler(command="listparties", callback=command.list_parties))

		# List managed channels
		self.dispatcher.add_handler(CommandHandler(command="setpartylevel", callback=command.set_partyinteraction))


		'''
		# Refresh channel informations (admins, memnbers, blocked, ...)
		self.dispatcher.add_handler(CommandHandler(command="refreshparty", callback=command.refresh_party))
		'''

		# Fix the allowed charsets
		self.dispatcher.add_handler(CommandHandler(command="setpartycharsets", callback=command.set_partycharsets))

		'''
		self.dispatcher.add_handler(CommandHandler(command="addpartycharset", callback=command.add_partycharset))
		'''

		# List allowed charsets in a party
		self.dispatcher.add_handler(CommandHandler(command="listpartycharsets", callback=command.list_partycharsets))


		# Setting language msg
		self.dispatcher.add_handler(CommandHandler(command="setlanguagemsg", callback=command.set_languagemsg))

		# Gettin language msg
		self.dispatcher.add_handler(CommandHandler(command="getlanguagemsg", callback=command.get_languagemsg))


		self.dispatcher.add_handler(CommandHandler(command="getinfo", callback=command.get_info))


		# List allowed charsets in a party
		self.dispatcher.add_handler(CommandHandler(command="listcrew", callback=command.list_crewmembers))
		self.dispatcher.add_handler(CommandHandler(command="addcrewmember", callback=command.add_crewmember))
		self.dispatcher.add_handler(CommandHandler(command="delcrewmember", callback=command.del_crewmember))



		# Spring cleaning
		self.dispatcher.add_handler(CommandHandler(command="springcleaning", callback=command.do_springcleaning))


		# Export/Import
		self.dispatcher.add_handler(CommandHandler(command="exportdb", callback=command.do_exportdb))
		self.dispatcher.add_handler(CommandHandler(command="importdb", callback=command.do_importdb))


		'''
		  non-command handlers
		'''

		# Handler for message with bot mention
		self.dispatcher.add_handler(MessageHandler(
			filters=Filter.message & Filter.mention(user_id=self.uin),
			callback=command.message_with_bot_mention_cb
		))	

		# Handler for simple text message without text content
		self.dispatcher.add_handler(MessageHandler(filters=Filter.text, callback=gunner.watch_txt))
		# same for forward and reply getting
		self.dispatcher.add_handler(MessageHandler(filters=Filter.forward, callback=gunner.watch_txt))
		self.dispatcher.add_handler(MessageHandler(filters=Filter.reply, callback=gunner.watch_txt))	

		# Any other user command handler
		#self.dispatcher.add_handler(CommandHandler(command="test", callback=command.test_cb))

		'''
		# Handler for feedback command
		self.dispatcher.add_handler(FeedbackCommandHandler(target=self.owner))
		'''

		'''
		# Handler for unknown commands
		self.dispatcher.add_handler(UnknownCommandHandler(callback=command.unknown_command_cb))
		'''



		'''
		# Handler for private command with filter by user
		self.dispatcher.add_handler(CommandHandler(
			command="restart",
			filters=Filter.sender(user_id=self.owner),
			callback=command.private_command_cb
		))
		'''

		'''
		# Handler for add user to chat
		self.dispatcher.add_handler(NewChatMembersHandler(callback=command.do_guestwelcome))
		'''

		'''
		# Handler for left user from chat
		self.dispatcher.add_handler(LeftChatMembersHandler(callback=command.do_guestgoodbye))
		'''

		'''
		# Handler for pinned message
		self.dispatcher.add_handler(PinnedMessageHandler(callback=command.pinned_message_cb))
		'''

		'''
		# Handler for unpinned message
		self.dispatcher.add_handler(UnPinnedMessageHandler(callback=command.unpinned_message_cb))
		'''

		'''
		# Handler for edited message
		bot.dispatcher.add_handler(EditedMessageHandler(callback=c.edited_message_cb))
		'''

		'''
		# Handler for deleted message
		self.dispatcher.add_handler(DeletedMessageHandler(callback=command.deleted_message_cb))
		'''



		'''
		# Handler for mention something else
		self.dispatcher.add_handler(MessageHandler(
			filters=Filter.mention() & ~Filter.mention(user_id=self.uin),
			callback=command.mention_cb
		))
		'''

		


		# Handler with regexp filter
		#self.dispatcher.add_handler(MessageHandler(filters=Filter.regexp("^\d*$"), callback=command.regexp_only_dig_cb))

		'''
		# Handler for no media file. For example, text file
		self.dispatcher.add_handler(MessageHandler(filters=Filter.data, callback=command.file_cb))
		'''

		'''
		# Handlers for other file types
		self.dispatcher.add_handler(MessageHandler(filters=Filter.image, callback=command.image_cb))
		self.dispatcher.add_handler(MessageHandler(filters=Filter.video, callback=command.video_cb))
		self.dispatcher.add_handler(MessageHandler(filters=Filter.audio, callback=command.audio_cb))
		'''
	
		'''
		# Handler for sticker
		self.dispatcher.add_handler(MessageHandler(filters=Filter.sticker, callback=command.sticker_cb))
		'''

		'''
		# Handler for url
		self.dispatcher.add_handler(MessageHandler(filters=Filter.url & ~Filter.sticker, callback=command.url_cb))
		'''

		'''		
		# Handlers for forward and reply getting
		self.dispatcher.add_handler(MessageHandler(filters=Filter.forward, callback=command.forward_cb))
		self.dispatcher.add_handler(MessageHandler(filters=Filter.reply, callback=command.reply_cb))
		'''

		# Send command like this:
		# /pin 6752793278973351456
		# 6752793278973351456 - msgId
		# Handler for pin command
		# self.dispatcher.add_handler(CommandHandler(command="pin", callback=command.pin_cb))

		# Send command like this:
		# /unpin 6752793278973351456
		# 6752793278973351456 - msgId
		# Handler for unpin command
		# self.dispatcher.add_handler(CommandHandler(command="unpin", callback=command.unpin_cb))











		'''
		# List available charsets
		self.dispatcher.add_handler(CommandHandler(command="listcharsets", callback=command.list_charsets))
		'''
		'''

		self.dispatcher.add_handler(CommandHandler(command="info", callback=command.info))	
		'''

	def get_crew(self):
		return self.crew


	def _start_polling(self):
		self.log.debug('_start_polling')
		#paquebot_db = db.Storage()
		while self.running:
			# Exceptions should not stop polling thread.
			# noinspection PyBroadException
			try:
				response = self.events_get()
				for event in response.json()["events"]:
					self.dispatcher.dispatch(Event(type_=EventType(event["type"]), data=event["payload"]))
			except Exception:
				self.log.exception("Exception while polling!")

	def start_polling(self):
		self.log.info("start_polling")
		self.running = True
		while self.running:
			log.debug(" polling inside the bot polling procedure")

			'''
			log.debug("Flushin the db on disk")
			self.maindb.flush()
			'''

			# Exceptions should not stop polling thread.
			# noinspection PyBroadException
			try:
				log.debug("Gettin ICQ events")
				response = self.events_get()
				for event in response.json()["events"]:
					self.dispatcher.dispatch(Event(type_=EventType(event["type"]), data=event["payload"]))
			except Exception:
				self.log.exception("Exception while polling!")


	def stop(self):
		self.log.debug("Stopping Paquebot bot.")
		with self.__lock:
			if self.running:
				self.running = False
			self.__polling_thread.join()


