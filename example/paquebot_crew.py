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
from paquebot_db import CrewGrades as grades


log = logging.getLogger(__name__)


##########################################
#
# Crew module
# Crew mamagement functions
#
##########################################


class Crew():

	def __init__(self, maindb, owner):

		# maindb = db.Storage()
		logging.getLogger(__name__).debug('Initializing Crew')

		self.maindb = maindb

		logging.getLogger(__name__).debug('%d admins already defined'%(self.size()))

		if self.size() == 0:
			self.add(owner, "OWNER", grades.DIRECTOR)

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

	def add(self, Uid, Nickname, Grade):
		log.debug("crew: adding a crew member %s"%Uid)
		
		if not self.is_member(Uid):
			crewman = db.CrewManStorage(Uid, Nickname, Grade)

			if crewman is not None:
				db.store_crewman(self.maindb, crewman)
				return True
			else:
				log.debug("crewman creation problem")
				return False
		else:
			log.debug("crew:  crew member %s is already exising"%Uid)
			return False

	def size(self):
		return db.size_crew(self.maindb)

	def is_member(self, Uid):
		log.debug("Returning if %s is a member or not", Uid)

		if  db.is_crewman(self.maindb, Uid):
			return True
		else:
			return False


	def is_director(self, Uid):

		if self.maindb.get_crewmember(Uid).grade >= db.CrewGrades.DIRECTOR:
			return True
		else:
			return False

	def is_captain(self, Uid):

		if self.is_member(Uid):
			crewman = db.load_crewman(self.maindb, Uid)

		if crewman.grade >= grades.CAPTAIN:
			return True
		else:
			return False

	def is_second(self, Uid):
		if self.maindb.get_crewmember(Uid).grade >= db.CrewGrades.SECOND:
			return True
		else:
			return False

	def is_bartender(self, Uid):
		if self.maindb.get_crewmember(Uid).grade >= db.CrewGrades.BARTENDER:
			return True
		else:
			return False

	def get_grade(self, Uid):
		if self.maindb.get_crewmember(Uid).grade >= db.CrewGrades.BARTENDER:
			pass



	def delete(self):
		pass

	def promote(self):
		pass
