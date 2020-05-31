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



class PersonStorage(object):
	id = Column(String(128), primary_key=True, index=True)
	nickname = Column(String(128))
	lastaction_ts = Column(DateTime, onupdate=func.now(), index=True)

	def __init__(self, id, nickname):
		self.id = id
		self.nickname = nickname


class GuestStorage(PersonStorage, Base):
	__tablename__ = 'Guest'





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
	mutewarningcount = Column(Integer, default=0)
	lastmutewarning_ts = Column(DateTime)

	def __init__(self, uid, cid, adminstatus=PersonAdminStatus.UNKNOWN, joinstatus=PersonJoinStatus.UNKNOWN, mutestatus=PersonSpeakStatus.UNKNOWN):
		self.uid = uid
		self.cid = cid
		self.adminstatus = adminstatus
		self.joinstatus = joinstatus
		self.mutestatus = mutestatus
		self.lastaction_ts = datetime.utcnow()
		self.firsttime_ts = datetime.utcnow()

		self.languagewarning_ts = datetime.fromtimestamp(0)
		self.mutewarningcount = 0
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


	def get_crewmember(self, Uid):
		log.debug('get_crewmember %s'%(Uid))
		return self.paquebot_db.query(CrewManStorage).filter(CrewManStorage.id == Uid).first()


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


def list_crewmembers(db):
	log.debug('DB: listing crewmembers')
	return db.paquebot_db.query(CrewManStorage).all()
