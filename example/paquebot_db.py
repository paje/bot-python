import json, re
import logging
import logging.config

from tinydb import TinyDB, Query
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage
from tinydb import Query

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


paquebot_db = TinyDB('paquebot_db.json', storage=CachingMiddleware(JSONStorage))
crew 		= paquebot_db.table("crew")
party 		= paquebot_db.table("party")

def init():

	log.debug('Initializing DB')
	log.debug("DB: ", paquebot_db)
	log.debug("Crew: ", crew)
	log.debug("Party:", party)

def close():
	log.debug('Closing db')
	paquebot_db.close()

def add_crewmember(seaman):
	if len(list_crewmembers()) > 0:

		log.debug('Upserting a crew member')
		crew.upsert(seaman, Query()['Nick'] == seaman['Nick'])

	else:
		log.debug('Adding the 1st crew member')
		crew.insert(seaman)

	paquebot_db.update(crew)
	
def get_crewmember(Uid):
	log.debug('get_crewmember %s'%(Uid))
	return crew.get(Query()['Nick'] == Uid)

def del_crewmember(Nick):
	if crew.remove(Query()['Nick'] == Nick) > 0:
		paquebot_db.update(crew)
		return True
	else:
		return False


def is_crewmember(Uid):
	if crew.get(Query()['Nick'] == Uid):
		return True
	else:
		return False

def list_crewmembers():
	return crew

def add_party(channelId):
	log.debug('Adding party %s'%(channelId))
	if len(list_parties()) > 0:	
		log.debug("Updating %s"%(channelId))
		party.upsert({'channel': channelId}, Query()['channel'] == channelId)		
	else:
		log.debug('Adding the 1st party channel %s'%(channelId))
		party.insert({'channel': channelId})
	# paquebot_db.update(party)
	return True


def is_partyon(channelId):
	log.debug('Is party on %s'%(channelId))
	if party.get(Query()['channel'] == channelId):
		return True
	else:
		return False

def store_party(channelId, channelInfos):
	log.debug('Store party %s with %s'%(channelId, channelInfos))

	party.upsert({'channel': channelId, 'infos': channelInfos}, Query()['channel'] == channelId)
	paquebot_db.update(party)


def read_party(channelId):
	log.debug('Read party %s s'%(channelId))

	return party.get(Query()['channelId'] == channelId)

def del_party(channelId):
	pass

def list_parties():
	return party

