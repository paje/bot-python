import json, re
import logging
import logging.config
logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

# BOT ROLES
DIRECTOR = 40
CAPTAIN = 20
SECOND = 10
BARTENDER = 5