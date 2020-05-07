import json, re
import logging
import logging.config



from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler

import paquebot_bot
import paquebot_db as db
import paquebot_party as party


log = logging.getLogger(__name__)


##########################################
#
# Crew module
# Crew mamagement functions
#
##########################################


#
# BOT ROLES
DIRECTOR = 40
CAPTAIN = 20
SECOND = 10
BARTENDER = 5

class Crew():

	def __init__(self, maindb, owner):

		# maindb = db.Storage()
		logging.getLogger(__name__).debug('Initializing Crew')
		logging.getLogger(__name__).debug('%d admins already defined'%(len(maindb.list_crewmembers())))

		self.maindb = maindb

		if len(self.maindb.list_crewmembers()) == 0:
			self.maindb.add_crewmember(owner, "OWNER", DIRECTOR)

			'''
			maindb.add_crewmember("12963645", "alapaje", DIRECTOR)
			maindb.add_crewmember("708800750", "Gaetan", CAPTAIN)
			maindb.add_crewmember("673338941", "Leo", SECOND)
			'''

			#db.add_crewmember({"Nick": "Zlata", "Role": DIRECTOR})
			#db.add_crewmember({"Nick": "12963645", "Role": DIRECTOR})
			#db.add_crewmember({"Nick": "708800750", "Role": CAPTAIN})
			#db.add_crewmember({"Nick": "673338941", "Role": SECOND})

		'''
		if db.is_crewmember('12963645'):
			print("%s is a crew member"%('12963645'))
		'''

	def is_member(self, Uid):
		return self.maindb.is_crewmember(Uid)

	def is_director(self, Uid):
		if self.maindb.get_crewmember(Uid)['Role'] >= DIRECTOR:
			return True
		else:
			return False

	def is_captain(self, Uid):
		crewmember = self.maindb.get_crewmember(Uid)

		if crewmember.grade >= CAPTAIN:
			return True
		else:
			return False

	def is_second(self, Uid):
		if self.maindb.get_crewmember(Uid)['Role'] >= SECOND:
			return True
		else:
			return False

	def is_bartender(self, Uid):
		if self.maindb.get_crewmember(Uid)['Role'] >= BARTENDER:
			return True
		else:
			return False

	def add(self):
		pass

	def delete(self):
		pass

	def promote(self):
		pass
