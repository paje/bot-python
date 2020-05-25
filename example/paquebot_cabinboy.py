import json, re
import logging
import logging.config
from time import sleep


from alphabet_detector import AlphabetDetector

from bot.bot import Bot
from bot.filter import Filter
from bot.handler import HelpCommandHandler, UnknownCommandHandler, MessageHandler, FeedbackCommandHandler, \
	CommandHandler, NewChatMembersHandler, LeftChatMembersHandler, PinnedMessageHandler, UnPinnedMessageHandler, \
	EditedMessageHandler, DeletedMessageHandler, StartCommandHandler, BotButtonCommandHandler

import gettext
_ = gettext.gettext

import paquebot_marinegunner as gunner
from paquebot_party import PartyStatus as partystatus
import paquebot_report as report


log = logging.getLogger(__name__)

def springcleaning(bot, from_uid, cid):



	bot.send_text(chat_id=from_uid, text="Hello there, starting the springcleaning process on @[%s], that might be a long journey"%(cid))
	log.debug("Hello there, starting the springcleaning process that might be a long journey")
	report.send_report(bot, report.ReportStatus.INFO, "@[{from_uid}] ask me for a spring cleaning on @[{about_cid}]", from_uid=from_uid, about_cid=cid)

	# Spring cleaning on chat members
	cursor = "True"
	count=0
	while cursor != "":
		count += 1
		if cursor != "True":
			resp =bot.get_chat_members(chat_id=cid, cursor= cursor)
		else:
			resp =bot.get_chat_members(chat_id=cid)

		if resp.status_code == 200:
			chatinfo = json.loads(resp.text)
			if chatinfo.get('ok')  == True:
				log.debug("chat members: %s"%chatinfo)

				if chatinfo.get('cursor') != None:
					cursor = chatinfo.get('cursor') 
					log.debug("Now we have a cursor: %s for next request"%cursor)
				else:
					cursor = ""
					log.debug("unsetting cursor for next request")


				for user in chatinfo['members']:
					# Avoiding api flood
					sleep(0.5)

					resp = bot.get_chat_info(user['userId'])
					if resp.status_code == 200:
						userinfo = json.loads(resp.text)
						if userinfo['ok'] == True:
							if 'firstName' in userinfo:
								firstName = userinfo['firstName']
							else:
								firstName = ""
							if 'lastName' in userinfo:
								lastName = userinfo['lastName']
							else:
								lastName = ""
							if 'admin' in userinfo and userinfo['admin'] == 'true':
								admin = True
							else:
								admin = False

							if firstName == "[deleted]":
								if admin:
									log.debug("User @[%s] First: %s Last:%s\nis kept in the room @[%s]\nhe is admin there"%(user['userId'], firstName, lastName, cid))
									report.send_report(bot, report.ReportStatus.WARNING, "User @[{about_uid}]\nis kept in the room @[{about_cid}]\nhe is admin there!", from_uid=from_uid, about_uid=user['userId'], about_cid=cid)
								else:
									if bot.parties.is_admin(cid):
										#bot.send_text(chat_id=from_uid, text="Deleting user @[%s] First: %s Last:%s "%(user['userId'], firstName, lastName ))
										log.debug("Deleging user @[%s] First: %s Last:%s "%(user['userId'], firstName, lastName))
										# removing user from chan by blocking/unblocking it
										bot.chat_block_user(self, cid, user['userId'], del_last_messages=False)
										bot.chat_unblock_user(self, cid, user['userId'])
										report.send_report(bot, report.ReportStatus.ADMIN, "User @[{about_uid}]\ndeleted from the room @[{about_cid}]\ncause: deleted users spring cleaning", from_uid=from_uid, about_uid=user['userId'], about_cid=cid)
									else:
										#bot.send_text(chat_id=from_uid, text="User @[%s] First: %s Last:%s would be deleted if I was admin"%(user['userId'], firstName, lastName ))
										report.send_report(bot, report.ReportStatus.WARNING, "User @[{about_uid}]\nwould have deleted from the room @[{about_cid}]\nif i had an ADMIN level (and if i was admin there)", from_uid=from_uid, about_uid=user['userId'], about_cid=cid)
										log.debug("User @[%s] First: %s Last:%s would be deleted if I was admin"%(user['userId'], firstName, lastName))
						else:
							bot.send_text(chat_id=from_uid, text="Error on gettin info on user @[%s]"%(user['userId']))
							log.error("Error on gettin info on user @[%s]"%(user['userId']))

		sleep(2)
		log.debug("Iteration %d We will continue the list with cursor @[%s]"%(count, cursor))

	# Spring cleaning on blocked users
	cursor = "True"
	count=0
	while cursor != "":
		count += 1
		if cursor != "True":
			resp =bot.get_chat_blocked_users(chat_id=cid, cursor= cursor)
		else:
			resp =bot.get_chat_blocked_users(chat_id=cid)

		if resp.status_code == 200:
			chatinfo = json.loads(resp.text)
			if chatinfo.get('ok')  == True:
				log.debug("blocked user: %s"%chatinfo)

				if chatinfo.get('cursor') != None:
					cursor = chatinfo.get('cursor') 
					log.debug("Now we have a cursor: %s for next request"%cursor)
				else:
					cursor = ""
					log.debug("unsetting cursor for next request")


				for user in chatinfo['members']:
					# Avoiding api flood
					sleep(0.5)

					resp = bot.get_chat_info(user['userId'])
					if resp.status_code == 200:
						userinfo = json.loads(resp.text)
						if userinfo['ok'] == True:
							if 'firstName' in userinfo:
								firstName = userinfo['firstName']
							else:
								firstName = ""
							if 'lastName' in userinfo:
								lastName = userinfo['lastName']
							else:
								lastName = ""
							if 'admin' in userinfo and userinfo['admin'] == 'true':
								admin = True
							else:
								admin = False

							if firstName == "[deleted]":
								if bot.parties.is_admin(cid):
									log.debug("Unblocking user @[%s] First: %s Last:%s "%(user['userId'], firstName, lastName))
									bot.chat_unblock_user(self, cid, user['userId'])
									report.send_report(bot, report.ReportStatus.ADMIN, "User @[{about_uid}]\ndeleted from the room @[{about_cid}]\ncause: deleted users spring cleaning", from_uid=from_uid, about_uid=user['userId'], about_cid=cid)
								else:
									report.send_report(bot, report.ReportStatus.WARNING, "User @[{about_uid}]\nwould have deleted from the room @[{about_cid}]\nif i had an ADMIN level (and if i was admin there)", from_uid=from_uid, about_uid=user['userId'], about_cid=cid)
									log.debug("User @[%s] First: %s Last:%s would be deleted if I was admin"%(user['userId'], firstName, lastName))
						else:
							bot.send_text(chat_id=from_uid, text="Error on gettin info on user @[%s]"%(user['userId']))
							log.error("Error on gettin info on user @[%s]"%(user['userId']))

		sleep(2)
		log.debug("Iteration %d We will continue the list with cursor @[%s]"%(count, cursor))

	report.send_report(bot, report.ReportStatus.INFO, "Springcleaning on @[{about_cid}] is ended", from_uid=from_uid, about_cid=cid)





