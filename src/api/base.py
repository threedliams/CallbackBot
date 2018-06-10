import json
import os
#TODO: handle unicode better instead of just ignoring it
from unidecode import unidecode

from abc import ABC, abstractmethod

import src.util.callbackUtil
import src.data.messages
import src.data.polls
import src.app


class API(ABC):
    def __init__(self, token):
        self.apiName = ""

        self.client = None

        self.isSavedReady = False
        self.isLiveReady = False
        self.savedChannelMap = {}
        self.liveChannelMap = {}

        self.birdUpText = ""

        self.callbackData = {}

        self.polls = []

        super().__init__()

    @abstractmethod
    def author(self, payload):
        pass

    @abstractmethod
    def authorName(self, payload):
        pass

    @abstractmethod
    def content(self, payload):
        pass

    @abstractmethod
    def messageChannel(self, payload):
        pass

    @abstractmethod
    def emoji(self, payload):
        pass

    @abstractmethod
    def reactionMessage(self, payload):
        pass

    @abstractmethod
    def clientName(self):
        pass

    @abstractmethod
    def clientID(self):
        pass

    @abstractmethod
    def clientUser(self):
        pass

    @abstractmethod
    def getServers(self):
        pass

    @abstractmethod
    def serverName(self, server):
        pass

    @abstractmethod
    def channels(self, server):
        pass

    @abstractmethod
    def channelName(self, channel):
        pass

    @abstractmethod
    def channelID(self, channel):
        pass

    @abstractmethod
    async def getLogs(self, channel):
        pass

    @abstractmethod
    async def editMessage(self, message, newContent):
        pass

    @abstractmethod
    async def playSong(self, message, songToPlay):
        pass

    @abstractmethod
    async def stopAndDisconnect(self, message):
        pass

    ################################################################################
    # onReady
    #
    # When the bot starts up, this runs all the startup functions
    #
    # Args:
    #
    #   None
    #
    # Returns - nothing
    ################################################################################
    async def onReady(self):
        print('Logged in as')
        print(self.clientName())
        print(self.clientID())
        print('------')

        rootFolder = "./servers/" + self.apiName + "/"
        callbackFile = "./callbacks/callbacks.json"

        #load eric andre transciptions
        with open('./birdup.txt', 'r') as birdUpFile:
            self.birdUpText = birdUpFile.read()

        #load callbackFile
        with open(callbackFile) as data_file:
            self.callbackData = json.load(data_file)

        servers = self.getServers()
        #preload any saved channels
        for server in servers:
            underscoredServerName = self.serverName(server).replace(" ", "_")
            if(os.path.isdir(rootFolder + underscoredServerName)):
                for channel in self.channels(server):
                    underscoredChannelName = self.channelName(channel).replace(" ", "_")
                    #TODO: channels with the same name on one server?
                    if(os.path.isdir(rootFolder + underscoredServerName + "/" + underscoredChannelName)):
                        if not(channel.id in list(self.savedChannelMap.keys())):
                            self.savedChannelMap[self.channelID(channel)] = {}
                        for fileName in os.listdir(rootFolder + underscoredServerName + "/" + underscoredChannelName):
                            f = open(rootFolder + underscoredServerName + "/" + underscoredChannelName + "/" + fileName, 'r')
                            #TODO: handle people with . in their name
                            self.savedChannelMap[self.channelID(channel)][fileName.split('.')[0]] = f.read()
        self.isSavedReady = True

        print("saved ready!")

        #catch up to current logs
        for server in servers:
            for channel in self.channels(server):
                if not(self.channelID(channel) in list(self.liveChannelMap.keys())):
                    self.liveChannelMap[self.channelID(channel)] = {}
                await self.getLogs(channel)

        #save current logs for next time
        for server in servers:
            underscoredServerName = self.serverName(server).replace(" ", "_")
            if not(os.path.isdir(rootFolder + underscoredServerName)):
                os.makedirs(rootFolder + underscoredServerName)
            if(os.path.isdir(rootFolder + underscoredServerName)):
                for channel in self.channels(server):
                    underscoredChannelName = self.channelName(channel).replace(" ", "_")
                    if not(os.path.isdir(rootFolder + underscoredServerName + "/" + underscoredChannelName)):
                        os.makedirs(rootFolder + underscoredServerName + "/" + underscoredChannelName)
                    if(os.path.isdir(rootFolder + underscoredServerName + "/" + underscoredChannelName)):
                        for username in self.liveChannelMap[self.channelID(channel)].keys():
                            f = open(rootFolder + underscoredServerName + "/" + underscoredChannelName + "/" + username + ".txt", 'w')
                            f.write(self.liveChannelMap[self.channelID(channel)][username])


        self.isLiveReady = True

        print("live ready!")

    ################################################################################
    # onMessage
    #
    # When someone sends a message in a channel with a bot, this function fires
    # so you can process the given message
    #
    # Args:
    #
    #   message - a Message object
    #
    # Returns - nothing
    ################################################################################
    async def onMessage(self, message):

        await src.util.callbackUtil.functionSwitcher(message)

        if(len(message.tokenizedMessage) > 2):
            await src.app.checkForClaps(message)

        if(self.isSavedReady and not self.isLiveReady):
            src.data.messages.saveMessage(message, self.savedChannelMap)

        if(self.isLiveReady):
            src.data.messages.saveMessage(message, self.liveChannelMap)

    ################################################################################
    # onReactionAdd
    #
    # When someone adds a reaction in a channel with a bot, this function fires
    # so you can process the given reaction
    #
    # Args:
    #
    #   reaction - a Reaction object
    #
    #   username - the reacting user
    #
    # Returns - nothing
    ################################################################################
    async def onReactionAdd(self, reaction, username):
        message = self.reactionMessage(reaction)

        isPoll = False
        savedPoll = None
        for poll in self.polls:
            if(self.content(message) == poll.content):
                savedPoll = poll
                isPoll = True
        if not(isPoll):
            return

        newPoll = await self.editMessage(message, src.data.polls.addVote(message, reaction, username))
        self.polls.append(newPoll)

    ################################################################################
    # onReactionRemove
    #
    # When someone removes a reaction in a channel with a bot, this function fires
    # so you can process the given reaction
    #
    # Args:
    #
    #   reaction - a Reaction object
    #
    #   username - the reacting user
    #
    # Returns - nothing
    ################################################################################
    async def onReactionRemove(self, reaction, username):
        message = self.reactionMessage(reaction)

        isPoll = False
        for poll in self.polls:
            if(poll != None):
                if(self.content(message) == poll.content):
                    isPoll = True
        if not(isPoll):
            return

        newPoll = await self.editMessage(message, src.data.polls.removeVote(message, reaction, username))
        self.polls.append(newPoll)

    ################################################################################
    # onReactionClear
    #
    # When someone clears a reaction in a channel with a bot, this function fires
    # so you can process the given reaction
    #
    # Args:
    #
    #   reaction - the Reaction object
    #
    #   username - the reacting user
    #
    # Returns - nothing
    ################################################################################
    async def onReactionClear(self, reaction, username):
        message = self.reactionMessage(reaction)

        isPoll = False

        for poll in self.polls:
            if(self.content(message) == poll.content):
                isPoll = True
        if not(isPoll):
            return

        newPoll = await self.editMessage(message, src.data.polls.removeVote(message, reaction, username))
        self.polls.append(newPoll)

    ################################################################################
    # sendFile
    #
    # Sends the given file to the given channel
    #
    # Args:
    #
    #   message - a Message object
    #
    #   fileToSend - a string with the path of the file to send
    #
    # Return - nothing
    ################################################################################
    @abstractmethod
    async def sendFile(self, message, fileToSend):
        pass

    ################################################################################
    # addReaction
    #
    # Adds the given reaction to the given message
    #
    # Args:
    #
    #   message - a Message object
    #
    #   reactionToAdd - a string with the name of the emoji to add, found in
    #   emojiDict
    #
    # Return - nothing
    ################################################################################
    @abstractmethod
    async def addReaction(self, message, reactionToAdd):
        pass

    ################################################################################
    # sendMessage
    #
    # Sends the given message to the given channel
    #
    # Args:
    #
    #   message - a Message object
    #
    #   messageToSend - a string message to send
    #
    # Return - nothing
    ################################################################################
    @abstractmethod
    async def sendMessage(self, message, messageToSend):
        pass