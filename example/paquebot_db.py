import json, re
import logging
import logging.config

from datetime import datetime
import pytz	

from enum import IntEnum, Enum, unique

from sqlalchemy import create_engine, inspect, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

log = logging.getLogger(__name__)

Base = declarative_base()

@unique
class CrewGrades(IntEnum):
	DIRECTOR = 40
	CAPTAIN = 20
	SECOND = 10
	BARTENDER = 5
	SEAMAN = 1
	GUEST = 0

class PersonStorage(object):
	id = Column(String(128), primary_key=True, index=True)
	nickname = Column(String(128))
	lastaction_ts = Column(DateTime, onupdate=func.now(), index=True)

	def __init__(self, id, nickname):
		self.id = id
		self.nickname = nickname


class GuestStorage(PersonStorage, Base):
	__tablename__ = 'Guest'



class CrewManStorage(PersonStorage, Base):
	__tablename__ = 'Crew'

	grade = Column(Integer, default=CrewGrades.GUEST)

	def __init__(self, Uid=0, Nickname="", Grade=CrewGrades.GUEST):
		self.id = Uid
		self.nickname = Nickname
		self.grade = Grade


@unique
class PartyStatus(IntEnum):
	# Status
	ADMIN = 4
	VOLUBILE = 3
	WATCHING = 2
	NONMANAGED = 1

def levelexists(level):
	intLevel = int(level)
	log.debug("Checking if %d level exists in the hierarchie"%intLevel)
	if intLevel == PartyStatus.ADMIN or intLevel == PartyStatus.VOLUBILE or intLevel == PartyStatus.WATCHING or intLevel == PartyStatus.NONMANAGED:
		return True
	else:
		return False

class PartyStorage(Base):
	__tablename__ = 'Party'

	alphabets = [
		'GREEK',
		'CYRILLIC',
		'LATIN',
		'ARABIC',
		'HEBREW',
		'CJK',
		'HANGUL',
		'HIRAGANA',
		'KATAKANA',
		'THAI'
	]

	id = Column(String(128), primary_key=True)


	status = Column(Integer, default=PartyStatus.NONMANAGED)

	timezone = Column(String(128), default="UTC" )
	locale = Column(String(2), default="en")
	authorized_charsets = Column(String(128), default="")
	authorized_languages = Column(String(128), default="")
	# lastaction_ts = Column(DateTime, onupdate=func.now(), index=True)

	rules_msg = Column(String(256), default="")
	language_msg = Column(String(256), default="")



	def __init__(self, cid):
		self.id = cid
		self.status = int(PartyStatus.NONMANAGED)


		status = PartyStatus.NONMANAGED

		timezone = "UTC"
		locale = "en"
		authorized_charsets = ""
		authorized_languages = ""

		rules_msg = ""
		language_msg = ""




@unique
class PersonJoinStatus(IntEnum):
	# Join Status 
	PENDING = 3
	BLOCKED = 2
	MEMBER = 1
	UNKNOWN = 0


@unique
class PersonAdminStatus(IntEnum):
	# admin Status 
	UNKNOWN = 0
	MEMBER = 1
	ADMIN = 2
	CREATOR = 3

@unique
class PersonSpeakStatus(IntEnum):
	# mute Status 
	UNKNOWN = 0
	SPEAKS = 1
	MUTED = 2

class WhoiswhereStorage(Base):
	__tablename__ = 'Whoiswhere'

	uid = Column(String(128),  primary_key=True)
	cid = Column(String(128), ForeignKey('Party.id'), primary_key=True)

	firsttime_ts = Column(DateTime, server_default=func.now(), index=True)
	lastaction_ts = Column(DateTime, onupdate=func.now(), index=True)
	adminstatus = Column(Integer, default=PersonAdminStatus.UNKNOWN)
	joinstatus = Column(Integer, default=PersonJoinStatus.UNKNOWN)
	mutestatus = Column(Integer, default=PersonSpeakStatus.UNKNOWN)

	def __init__(self, uid, cid, adminstatus=PersonAdminStatus.UNKNOWN, joinstatus=PersonJoinStatus.UNKNOWN, mutestatus=PersonSpeakStatus.UNKNOWN):
		self.uid = uid
		self.cid = cid
		self.adminstatus = adminstatus
		self.joinstatus = joinstatus
		self.mutestatus = mutestatus
		self.lastaction_ts = datetime.utcnow()
		self.firsttime_ts = datetime.utcnow()

		self.languagewarning_ts = datetime.fromtimestamp(0)
		self.behaviourwarning_ts = datetime.fromtimestamp(0)


class Storage():

	def __init__(self):
		log.debug('Opening session db')
		engine = create_engine('sqlite:///db/paquebot.db')
		Session = sessionmaker(bind=engine)
		Base.metadata.create_all(engine)
		self.paquebot_db = Session()

	def close(self):
		log.debug('Closing db')
		self.paquebot_db.close()


	def add_crewmember(self, Uid, Nickname, Role):
		log.debug('adding crewmember %s %s %d'%(Uid, Nickname, Role))
		if self.paquebot_db.query(CrewManStorage).filter(CrewManStorage.id == Uid).count() == 0:
			newcrew = CrewManStorage(Uid, Nickname, Role)
			self.paquebot_db.add(newcrew)
			self.paquebot_db.commit()
			self.paquebot_db.flush()
			return True
		else:
			return False

	def get_crewmember(self, Uid):
		log.debug('get_crewmember %s'%(Uid))
		return self.paquebot_db.query(CrewManStorage).filter(CrewManStorage.id == Uid).first()

	def del_crewmember(self, Uid):
		log.debug('Deleting crewmember %s'%(Uid))
		if  self.paquebot_db.query(CrewManStorage).delete(CrewManStorage.id == Uid):
			self.paquebot_db.commit()
			return True
		else:
			return False

	def list_crewmembers(self):
		log.debug('Listing all crewmembers')

		return

	def add_party(self, channelId):
		log.debug('adding party %s'%(channelId))

		if self.paquebot_db.query(PartyStorage).filter(PartyStorage.id == channelId).count() == 0:
			newparty = PartyStorage(channelId)
			self.paquebot_db.add(newparty)
			self.paquebot_db.commit()
			self.paquebot_db.flush()
			return True
		else:
			return False

	def is_partyon(self, channelId):
		log.debug('returning party  %s status'%(channelId))
	 
		if self.paquebot_db.query(PartyStorage).filter(PartyStorage.id == channelId).count() > 0:
			party = self.paquebot_db.query(PartyStorage).filter(PartyStorage.id == channelId).first()
			return party.status
		else:
			return False

	def del_party(self, channelId):
		log.debug('Deleting party %s'%(channelId))
		if  self.paquebot_db.query(PartyStorage).delete(PartyStorage.id == channelId):
			self.paquebot_db.commit()
			return True
		else:
			return False

	def list_parties(self):
		log.debug('Listing all parties')
		return self.paquebot_db.query(PartyStorage).all()


	def add_whoiswhere(self, uid, cid, joinstatus=PersonJoinStatus.UNKNOWN, adminstatus=PersonJoinStatus.UNKNOWN, mutestatus=PersonSpeakStatus.UNKNOWN):
		log.debug('Adding an entry into whoiswhere')

		if self.paquebot_db.query(WhoiswhereStorage).filter(WhoiswhereStorage.cid == cid and WhoiswhereStorage.uid == uid).count() == 0:
			newwisw = WhoiswhereStorage(uid, cid, joinstatus=joinstatus, adminstatus=adminstatus, mutestatus=mutestatus)

			self.paquebot_db.add(newwisw)
			self.paquebot_db.commit()

		else:
			# we should refresh data
			wiw = self.paquebot_db.query(WhoiswhereStorage).filter(WhoiswhereStorage.cid == cid and WhoiswhereStorage.uid == uid).first()
			wiw.joinstatus = joinstatus
			wiw.adminstatus = adminstatus
			wiw.mutestatus = mutestatus
			# wiw.lastaction_ts = timezone.utcnow()

			#self.paquebot_db.update(newwisw)
			self.paquebot_db.commit()

		return True

	def touch_whoiswhere(self, uid, cid):

		log.debug('Touching an entry into whoiswhere')

		if self.paquebot_db.query(WhoiswhereStorage).filter(WhoiswhereStorage.cid == cid and WhoiswhereStorage.uid == uid).count() == 0:
			log.debug('Creating the entry in whoiswhere')

			# We should add en ebtry
			newwisw = WhoiswhereStorage(uid, cid)

			self.paquebot_db.add(newwisw)
			self.paquebot_db.commit()
			return True

		else:
			# entry update
			log.debug('Update the entry in whoiswhere')

			wiw = self.paquebot_db.query(WhoiswhereStorage).filter(WhoiswhereStorage.cid == cid and WhoiswhereStorage.uid == uid).first()
			if wiw is not None:
				#wiw.lastaction_ts = timezone.utcnow()
				#self.paquebot_db.update(wiw)
				self.paquebot_db.commit()

				return True
			else:
				log.debug('Something gets wrong')
				return False



	def get_whoisiswhereperseaman(self, uid):
		log.debug('Get entry from whoiswhere')
		pass

	def get_whoisiswhereperparty(self, uid):
		log.debug('Get entries from whoiswhere')
		pass


	def del_whoiswhere(self, uid, cid):
		log.debug('Deleting an entry in whoiswhere')
		pass


def size_parties(db):
	return db.paquebot_db.query(PartyStorage).count()


def is_party(db, channelId):
	log.debug('DB: testing if a party exists %s'%(channelId))

	if db.paquebot_db.query(PartyStorage).filter(PartyStorage.id == channelId).count() > 0:
		return True
	else:
		return False

def load_party(db, channelId):
	log.debug('DB: gettin party %s'%(channelId))
	return db.paquebot_db.query(PartyStorage).filter(PartyStorage.id == channelId).first()


def store_party(db, party):
	log.debug('DB: storiing party %s'%(party.id))

	if db.paquebot_db.query(PartyStorage).filter(PartyStorage.id == party.id).count() > 0:
		log.debug('Party %s found in DB, updating it'%party.id)

		stored_party = db.paquebot_db.query(PartyStorage).filter(PartyStorage.id == party.id).first()
		stored_party.status = party.status
		stored_party.timezone = party.timezone
		stored_party.locale = party.locale
		stored_party.authorized_charsets = party.authorized_charsets
		stored_party.authorized_languages = party.authorized_languages

		stored_party.rules_msg = party.rules_msg
		stored_party.language_msg = party.language_msg

		# stored_party = party
		db.paquebot_db.commit()
	else:
		log.debug('Creating a new row for party %s'%party.id)
		db.paquebot_db.add(party)
		db.paquebot_db.commit()
	return True

def list_parties(db):
	log.debug('DB: listing parties')
	return db.paquebot_db.query(PartyStorage).all()


def size_crew(db):
	return db.paquebot_db.query(CrewManStorage).count()

def is_crewman(db, Uid):
	log.debug('DB: Is %s a crewman ?'%(Uid))

	if db.paquebot_db.query(CrewManStorage).filter(CrewManStorage.id == Uid).count() > 0:
		wcman = db.paquebot_db.query(CrewManStorage).filter(CrewManStorage.id == Uid).first()

		if wcman.grade > CrewGrades.GUEST:
			log.debug('%s is in the Navy !!'%Uid)

			return True
		else:
			log.debug('grade is unsufficient %d to be considered as a crew'%wcman.grade)
			return False
	else:
		log.debug('no crewman with the corresponding ID %s'%Uid)
		return False

def load_crewman(db, Uid):
	log.debug('DB: gettin crewman %s'%(Uid))
	return db.paquebot_db.query(CrewManStorage).filter(CrewManStorage.id == Uid).first()


def store_crewman(db, crewman):
	log.debug('DB: storing crew %s'%(crewman.id))

	if db.paquebot_db.query(CrewManStorage).filter(CrewManStorage.id == crewman.id).count() > 0:
		log.debug('Crew  %s found in DB, updating it'%crewman.id)

		stored_crewman = db.paquebot_db.query(CrewManStorage).filter(CrewManStorage.id == crewman.id).first()
		stored_crewman = party
		db.paquebot_db.commit()

	else:
		log.debug('Creating a new row for crewman %s'%crewman.id)

		db.paquebot_db.add(crewman)
		db.paquebot_db.commit()
	return True


