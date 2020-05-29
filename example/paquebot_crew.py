import json, re
import logging
import logging.config
import operator


from enum import IntEnum, Enum, unique

from sqlalchemy import create_engine, inspect, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler

import paquebot_bot
import paquebot_db as db
from paquebot_db import PersonStorage as personstorage
from paquebot_whoiswhere import Whoiswhere as wiw

log = logging.getLogger(__name__)


@unique
class CrewGrades(IntEnum):
	OWNER = 80
	DIRECTOR = 40
	CAPTAIN = 20
	SECOND = 10
	BARTENDER = 5
	SEAMAN = 1
	GUEST = 0


	'''
	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_ 
	'''

class CrewManStorage(personstorage, db.Base):
	__tablename__ = 'Crew'

	grade = Column(Integer, default=CrewGrades.GUEST)

	def __init__(self, Uid=0, Nickname="", Grade=CrewGrades.GUEST):
		self.id = Uid
		self.grade = Grade
		self.nickname = Nickname

	def get_asjson(self):
		json_values = json.dumps({
			'id': self.id,
			'grade': self.grade,
			'nickname': self.nickname
			})
		log.debug('returning json : %s'%json_values)
		return json_values

	def load_fromjson(self, json_str):
		json_values = json.loads(json_str)
		for key, value in json_values.items():
			if hasattr(self, key): # in self.__dict__.keys()
				setattr(self, key, value)
			else:
				log.warning("%s has no %s attribule"%(self.__class_.__name__, key))

		return True



##########################################
#
# Crew module
# Crew mamagement functions
#
##########################################

class Crew():


	def __init__(self, mainsession, owner):
		logging.getLogger(__name__).debug('Initializing Crew')

		self.db_session = mainsession

		self.crew_ls = []
		self.crew_ls = self.db_session.query(CrewManStorage).all()

		logging.getLogger(__name__).debug('%d crew members already defined'%(self.size()))

		if self.size() == 0:

			self.add(owner, "OWNER", CrewGrades.OWNER)

			'''
			maindb.add_crewmember("12963645", "alapaje", DIRECTOR)
			maindb.add_crewmember("708800750", "Gaetan", CAPTAIN)
			maindb.add_crewmember("673338941", "Leo", SECOND)
			'''

			#db.add_crewmember({"Nick": "Zlata", "Role": DIRECTOR})
			#db.add_crewmember({"Nick": "12963645", "Role": DIRECTOR})
			#db.add_crewmember({"Nick": "708800750", "Role": CAPTAIN})
			#db.add_crewmember({"Nick": "673338941", "Role": SECOND})




	def get_asjson(self):
		log.debug("Returning the list of crewmembers as json")
		crew = []
		for crewman in self.crew_ls:
			crew.append(json.loads(crewman.get_asjson()))

		log.debug("Crew json : %s"%str(json.dumps(crew)))			
		return json.dumps(crew)


	# Count team members
	def size(self):
		log.debug('Crew: returning the crew size')
		count = len(self.crew_ls)
		if count is not None and count > 0:
			return count
		else:
			return 0

	# Returns True if the UId is a crew member
	def is_member(self, Uid):
		log.debug("Crew: Returning if %s is a member or not"%Uid)

		for crewmember in self.crew_ls:
			if Uid == crewmember.id and CrewGrades(crewmember.grade) > CrewGrades.GUEST:
				log.debug('%s is in the Navy !!'%Uid)
				return True
		log.debug('no crewman with the corresponding ID %s'%Uid)
		return False

	def get_index(self, Uid):
		log.debug('Parties: gettin crew index for %s'%(Uid))
		for crewmember in self.crew_ls:
			if Uid == crewmember.id:
				return self.crew_ls.index(crewmember)
		log.debug('no crewman with the corresponding ID %s'%Uid)
		return False


	def add(self, Uid, Nickname, Grade):
		log.debug("crew: adding a crew member %s"%Uid)
		

		if not self.is_member(Uid):
			intGrade = int(Grade)
			if intGrade == CrewGrades.OWNER \
				or intGrade == CrewGrades.DIRECTOR \
				or intGrade == CrewGrades.CAPTAIN \
				or intGrade == CrewGrades.SECOND \
				or intGrade == CrewGrades.BARTENDER \
				or intGrade == CrewGrades.CREWMAN \
				or intGrade == CrewGrades.GUEST:

				newcrewman = CrewManStorage(Uid, Nickname, Grade)
				self.db_session.add(newcrewman)
				self.db_session.commit()
				self.db_session.flush()
				self.crew_ls.append(self.db_session.query(CrewManStorage).filter(CrewManStorage.id == Uid).first())
				self.crew_ls.sort(key=operator.attrgetter('id'))
				return True

			else:
				log.debug('Grade %s is not valid'%Grade)
				return False

		log.debug("crew: crew member %s is already exising"%Uid)
		return False

	def delete(self, Uid):
		log.debug('Crew deleting member %s'%(Uid))
		index = self.get_index(Uid)
		if index is not False:
			self.db_session.delete(self.crew_ls[index])
			self.crew_ls.remove(self.crew_ls[index])
			log.debug( 'Crew Uid: %s at index %d deleted'%(Uid, index))
			return True
		log.debug( '%s is not a managed member'%(Uid))
		return False

	# returns a list of crewmembers + grade
	def list(self):
		log.debug("Returnin the list of crew member with grades")
		return_value_ls = []
		for crew in self.crew_ls:
			return_value_ls.append({"id": crew.id, "grade": CrewGrades(crew.grade).name})

		log.debug("returning dict %s"%return_value_ls)
		return return_value_ls

	def is_director(self, Uid):
		log.debug("Crew: Returnin True if %s is a %s"%(Uid, CrewGrades.DIRECTOR.name))
		index = self.get_index(Uid)
		if index is not False:
			if self.crew_ls[index].grade >= CrewGrades.DIRECTOR:
				log.debug('%s is %s !!'%(Uid, CrewGrades.DIRECTOR.name))
				return True
			else:
				return False
		else:
			return False	


	def is_captain(self, Uid):
		log.debug("Crew: Returnin True if %s is a %s"%(Uid, CrewGrades.CAPTAIN.name))
		index = self.get_index(Uid)
		if index is not False:
			if self.crew_ls[index].grade >= CrewGrades.CAPTAIN:
				log.debug('%s is %s !!'%(Uid, CrewGrades.CAPTAIN.name))
				return True
			else:
				return False
		else:
			return False


	def is_second(self, Uid):
		log.debug("Crew: Returnin True if %s is a %s"%(Uid, CrewGrades.SECOND.name))
		index = self.get_index(Uid)
		if index is not False:
			if self.crew_ls[index].grade >= CrewGrades.SECOND:
				log.debug('%s is %s !!'%(Uid, CrewGrades.SECOND.name))
				return True
			else:
				return False
		else:
			return False


	def is_bartender(self, Uid):
		log.debug("Crew: Returnin True if %s is a %s"%(Uid, CrewGrades.BARTENDER.name))
		index = self.get_index(Uid)
		if index is not False:
			if self.crew_ls[index].grade >= CrewGrades.BARTENDER:
				log.debug('%s is %s !!'%(Uid, CrewGrades.BARTENDER.name))
				return True
			else:
				return False
		else:
			return False

	def is_allowed(self, Uid, requested_grade):
		log.debug("Crew: Returnin True if crew  %s has enough rights %s"%(Uid, requested_grade))
		index = self.get_index(Uid)
		if index is not False:
			if self.crew_ls[index].grade >= CrewGrades(requested_grade):
				log.debug("Allowed")
				return True
			else:
				log.debug("Unsufficient rights")
				return False
		else:
			return False

	def get_grade(self, Uid):
		log.debug("Crew: Returnin grade for %s"%(Uid))
		index = self.get_index(Uid)
		if index is not False:
			if self.crew_ls[index].grade >= CrewGrades.GUEST:
				log.debug('%s is %s !!'%(Uid, CrewGrades(self.crew_ls[index].grade).name))
				return self.crew_ls[index].grade
			else:
				return None
		else:
			return None

	def set_grade(self, Uid, Grade):
		log.debug('Promoting crewmember %s to %s'%(Uid, CrewGrades(Grade).name))

		index = self.get_index(Uid)
		if index is not False:
			intGrade = int(Grade)
			if intGrade == CrewGrades.OWNER \
				or intGrade == CrewGrades.DIRECTOR \
				or intGrade == CrewGrades.CAPTAIN \
				or intGrade == CrewGrades.SECOND \
				or intGrade == CrewGrades.BARTENDER \
				or intGrade == CrewGrades.CREWMAN \
				or intGrade == CrewGrades.GUEST:
				setattr(self.crew_ls[index], 'grade', CrewGrades(Grade))
				self.db_session.commit()
				self.db_session.flush()
				return True
			else:
				log.debug('Grade %s is not valid'%Grade)
				return False
		else:
			return False

	def get_nickname(self, Uid):
		log.debug('Gettin Nickame from %s'%(Uid))


		index = self.get_index(Uid)
		if index is not False:
			setattr(self.crew_ls[index], 'nickname', Nickname)
			self.db_session.commit()
			self.db_session.flush()
			return True
		else:
			return False

	def set_nickname(self, Uid, Nickname):
		log.debug('Changing Nickame from %s to %s'%(Uid, Nickname))


		index = self.get_index(Uid)
		if index is not False:
			return self.crew_ls[index].nickname
			return True
		else:
			return False

	def get_all(self):

		log.debug("Returning the list of crew members")

		return self.crew_ls






