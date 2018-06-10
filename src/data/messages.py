#TODO: handle unicode better instead of just ignoring it
from unidecode import unidecode

import src.app

class Reaction:
    def __init__(self, api, payload):
        self.api = api
        self.payload = payload
        self.reaction = payload
        self.messageText = api.reactionMessage(payload)
        self.emoji = api.emoji(self.payload)

class Message:
    def __init__(self, api, payload):
        self.api = api
        self.payload = payload

        self.channel = api.messageChannel(payload)
        self.channelID = api.channelID(self.channel)
        self.author = api.author(payload)
        self.content = api.content(payload)
        self.tokenizedMessage = src.app.tokenize(api.content(payload))
        self.username = api.authorName(payload)
        self.clientName = api.clientName()
        self.clientUser = api.clientUser()

################################################################################
# saveMessage
#
# Saves a message into one of the channel maps for later markoving
#
# Args:
#
#   message - the given message
#
#   channelMap - the channel map to save to
#
# Returns - nothing
################################################################################
def saveMessage(message, channelMap):
    if not(message.channel.id in channelMap):
            channelMap[message.channel.id] = {}

    usermap = channelMap[message.channel.id]

    if not(message.author.name in usermap):
        usermap[message.author.name] = unidecode(message.content)
    else:
        usermap[message.author.name] = usermap[message.author.name] + "\n" + unidecode(message.content)